#!/usr/bin/env python3
"""
2026年1月バックテスト実行スクリプト
期間: 2026-01-02 ~ 2026-01-30
"""

import psycopg2
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

# データベース接続
DB_CONFIG = {
    'host': 'localhost',
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

# 出力ディレクトリ
BACKTEST_DIR = Path("/home/user/eoi-pl/backtest")
BACKTEST_DIR.mkdir(exist_ok=True)

def connect_db():
    """データベース接続"""
    return psycopg2.connect(**DB_CONFIG)

def train_model(conn):
    """学習モデル（2020-2024年のデータで学習）"""
    cur = conn.cursor()
    
    # 馬ごとの平均順位を計算
    cur.execute("""
        SELECT 
            e.ketto_toroku_bango,
            AVG(e.kakutei_chakujun) as avg_rank,
            COUNT(*) as race_count
        FROM entries e
        JOIN races r ON e.race_id = r.race_id
        WHERE r.kaisai_nen >= 2020 AND r.kaisai_nen <= 2024
          AND e.kakutei_chakujun IS NOT NULL
          AND e.kakutei_chakujun > 0
          AND e.ketto_toroku_bango IS NOT NULL
        GROUP BY e.ketto_toroku_bango
        HAVING COUNT(*) >= 1
    """)
    
    # スキル辞書を作成
    skills = {}
    for ketto, avg_rank, count in cur.fetchall():
        # スキル = -log(avg_rank) (順位が小さいほど高スキル)
        skill = -np.log(max(float(avg_rank), 1.0))
        skills[ketto] = skill
    
    cur.close()
    
    print(f"✅ 学習完了: {len(skills)}頭の馬のスキルを計算")
    return skills

def predict_race(skills, horses):
    """レースの予測（Plackett-Luceモデル）"""
    predictions = []
    
    for horse in horses:
        ketto = horse['ketto']
        skill = skills.get(ketto, -5.0)  # 未知馬はデフォルトスキル
        
        # 勝率 = exp(skill) / sum(exp(skill))
        predictions.append({
            'ketto': ketto,
            'umaban': horse['umaban'],
            'bamei': horse['bamei'],
            'kakutei_chakujun': horse['kakutei_chakujun'],
            'skill': skill,
            'p_win': 0.0  # 後で計算
        })
    
    # 勝率を計算
    total_exp_skill = sum(np.exp(p['skill']) for p in predictions)
    for p in predictions:
        p['p_win'] = np.exp(p['skill']) / total_exp_skill
    
    # 勝率順にソート
    predictions.sort(key=lambda x: x['p_win'], reverse=True)
    
    # 予測順位を追加
    for i, p in enumerate(predictions, 1):
        p['predicted_rank'] = i
    
    return predictions

def run_backtest(conn, skills, start_date, end_date):
    """バックテスト実行"""
    cur = conn.cursor()
    
    # 2026年のレースデータを取得
    cur.execute("""
        SELECT 
            r.race_id,
            r.kaisai_nen,
            r.kaisai_tsukihi,
            r.keibajo_code,
            r.race_bango
        FROM races r
        WHERE r.kaisai_nen = 2026
          AND r.kaisai_tsukihi BETWEEN %s AND %s
        ORDER BY r.kaisai_tsukihi, r.keibajo_code, r.race_bango
    """, (start_date, end_date))
    
    races = cur.fetchall()
    
    results = []
    
    for race_id, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango in races:
        # レースの出走馬を取得
        cur.execute("""
            SELECT 
                e.umaban,
                e.bamei,
                e.ketto_toroku_bango,
                e.kakutei_chakujun
            FROM entries e
            WHERE e.race_id = %s
            ORDER BY e.umaban
        """, (race_id,))
        
        horses = []
        for umaban, bamei, ketto, kakutei in cur.fetchall():
            horses.append({
                'umaban': umaban,
                'bamei': bamei.strip() if bamei else '',
                'ketto': ketto,
                'kakutei_chakujun': kakutei
            })
        
        if len(horses) == 0:
            continue
        
        # 予測実行
        predictions = predict_race(skills, horses)
        
        # Top3予測
        top3_predicted = [p['umaban'] for p in predictions[:3]]
        top3_actual = sorted(
            [h for h in horses if h['kakutei_chakujun'] and h['kakutei_chakujun'] <= 3],
            key=lambda x: x['kakutei_chakujun']
        )
        top3_actual_umaban = [h['umaban'] for h in top3_actual]
        
        # Top5予測
        top5_predicted = [p['umaban'] for p in predictions[:5]]
        top5_actual = sorted(
            [h for h in horses if h['kakutei_chakujun'] and h['kakutei_chakujun'] <= 5],
            key=lambda x: x['kakutei_chakujun']
        )
        top5_actual_umaban = [h['umaban'] for h in top5_actual]
        
        # 的中判定
        top3_hit_count = len(set(top3_predicted) & set(top3_actual_umaban))
        top5_hit_count = len(set(top5_predicted) & set(top5_actual_umaban))
        
        results.append({
            'kaisai_nen': kaisai_nen,
            'kaisai_tsukihi': kaisai_tsukihi,
            'keibajo_code': keibajo_code,
            'race_bango': race_bango,
            'race_id': race_id,
            'top3_predicted': top3_predicted,
            'top3_actual': top3_actual_umaban,
            'top3_hit_count': top3_hit_count,
            'top5_predicted': top5_predicted,
            'top5_actual': top5_actual_umaban,
            'top5_hit_count': top5_hit_count,
            'predictions': predictions
        })
    
    cur.close()
    
    return results

def generate_summary(results):
    """サマリー生成"""
    df = pd.DataFrame(results)
    
    # 日別集計
    daily_summary = df.groupby('kaisai_tsukihi').agg({
        'race_id': 'count',
        'top3_hit_count': lambda x: sum(x >= 1),
        'top5_hit_count': lambda x: sum(x >= 3)
    }).rename(columns={
        'race_id': 'race_count',
        'top3_hit_count': 'top3_ge1',
        'top5_hit_count': 'top5_ge3'
    })
    
    daily_summary['top3_ge1_rate'] = daily_summary['top3_ge1'] / daily_summary['race_count']
    daily_summary['top5_ge3_rate'] = daily_summary['top5_ge3'] / daily_summary['race_count']
    
    # 全体集計
    total_races = len(results)
    top3_ge1_count = sum(1 for r in results if r['top3_hit_count'] >= 1)
    top3_ge2_count = sum(1 for r in results if r['top3_hit_count'] >= 2)
    top3_eq3_count = sum(1 for r in results if r['top3_hit_count'] == 3)
    top5_ge3_count = sum(1 for r in results if r['top5_hit_count'] >= 3)
    top5_eq5_count = sum(1 for r in results if r['top5_hit_count'] == 5)
    
    summary = {
        'total_races': total_races,
        'top3_ge1': top3_ge1_count,
        'top3_ge1_rate': top3_ge1_count / total_races,
        'top3_ge2': top3_ge2_count,
        'top3_ge2_rate': top3_ge2_count / total_races,
        'top3_eq3': top3_eq3_count,
        'top3_eq3_rate': top3_eq3_count / total_races,
        'top5_ge3': top5_ge3_count,
        'top5_ge3_rate': top5_ge3_count / total_races,
        'top5_eq5': top5_eq5_count,
        'top5_eq5_rate': top5_eq5_count / total_races,
    }
    
    return daily_summary, summary

def main():
    print("🚀 2026年1月バックテスト実行開始")
    print("=" * 60)
    
    # データベース接続
    conn = connect_db()
    
    # 学習フェーズ
    print("\n📚 Phase 1: モデル学習 (2020-2024年データ)")
    skills = train_model(conn)
    
    # バックテストフェーズ
    print("\n🔍 Phase 2: バックテスト実行 (2026-01-02 ~ 2026-01-30)")
    results = run_backtest(conn, skills, 102, 130)
    
    print(f"   - 対象レース数: {len(results)}")
    
    # サマリー生成
    print("\n📊 Phase 3: サマリー生成")
    daily_summary, summary = generate_summary(results)
    
    # 結果出力
    print("\n" + "=" * 60)
    print("🎯 バックテスト結果サマリー (2026-01-02 ~ 2026-01-30)")
    print("=" * 60)
    print(f"対象レース数: {summary['total_races']}")
    print(f"\n【Top3予測】")
    print(f"  Top3≥1: {summary['top3_ge1']}/{summary['total_races']} ({summary['top3_ge1_rate']:.2%})")
    print(f"  Top3≥2: {summary['top3_ge2']}/{summary['total_races']} ({summary['top3_ge2_rate']:.2%})")
    print(f"  Top3=3: {summary['top3_eq3']}/{summary['total_races']} ({summary['top3_eq3_rate']:.2%})")
    print(f"\n【Top5予測】")
    print(f"  Top5≥3: {summary['top5_ge3']}/{summary['total_races']} ({summary['top5_ge3_rate']:.2%})")
    print(f"  Top5=5: {summary['top5_eq5']}/{summary['total_races']} ({summary['top5_eq5_rate']:.2%})")
    
    # CSVファイル保存
    detail_csv = BACKTEST_DIR / "backtest_2026_01_detail.csv"
    detail_df = pd.DataFrame([{
        'kaisai_tsukihi': r['kaisai_tsukihi'],
        'keibajo_code': r['keibajo_code'],
        'race_bango': r['race_bango'],
        'top3_hit_count': r['top3_hit_count'],
        'top5_hit_count': r['top5_hit_count'],
        'top3_predicted': ','.join(map(str, r['top3_predicted'])),
        'top3_actual': ','.join(map(str, r['top3_actual'])),
        'top5_predicted': ','.join(map(str, r['top5_predicted'])),
        'top5_actual': ','.join(map(str, r['top5_actual']))
    } for r in results])
    detail_df.to_csv(detail_csv, index=False, encoding='utf-8')
    print(f"\n✅ 詳細CSV保存: {detail_csv}")
    
    # 日別サマリーCSV保存
    summary_csv = BACKTEST_DIR / "backtest_2026_01_summary.csv"
    daily_summary.to_csv(summary_csv, encoding='utf-8')
    print(f"✅ サマリーCSV保存: {summary_csv}")
    
    # JSON保存
    summary_json = BACKTEST_DIR / "backtest_2026_01_summary.json"
    with open(summary_json, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✅ サマリーJSON保存: {summary_json}")
    
    print("\n🎉 バックテスト完了！")
    
    conn.close()

if __name__ == '__main__':
    main()
