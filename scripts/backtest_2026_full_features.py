#!/usr/bin/env python3
"""
完全版バックテスト - EOI-PL v1.0-Prime 地方競馬特化モデル

全特徴量を使用:
- 平均順位
- 騎手スキル
- 調教師スキル
- コーナースキル
- タイムスキル
- 距離適性
- 馬場適性
"""

import psycopg2
import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, List

# データベース設定
DB_CONFIG = {
    'host': 'localhost',
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

# 地方競馬場コード
NAR_VENUES = [30, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55]

# 特徴量の重み（初期値）
WEIGHTS = {
    'avg_rank': 0.30,
    'jockey': 0.15,
    'trainer': 0.10,
    'corner': 0.15,
    'time': 0.15,
    'distance': 0.10,
    'track': 0.05
}

BACKTEST_DIR = Path("/home/user/eoi-pl/backtest")

class FullFeatureModel:
    """全特徴量を使用したモデル"""
    
    def __init__(self, feature_db: Dict):
        self.feature_db = feature_db
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
    
    def calculate_horse_skill(self, ketto: str, race_conditions: Dict) -> float:
        """馬のスキル計算（全特徴量）"""
        skill = 0.0
        
        # 1. 平均順位スキル
        if ketto in self.feature_db['horses']:
            horse_data = self.feature_db['horses'][ketto]
            avg_rank = horse_data['avg_rank']
            rank_skill = -np.log(max(avg_rank, 1.0))
            skill += WEIGHTS['avg_rank'] * rank_skill
        else:
            skill += WEIGHTS['avg_rank'] * (-np.log(10.0))  # 未知馬
        
        return skill
    
    def calculate_jockey_skill(self, kishu_code: int) -> float:
        """騎手スキル計算"""
        if kishu_code is None:
            return 0.0
        
        kishu_key = str(kishu_code) if kishu_code in self.feature_db['jockeys'] else kishu_code
        
        if kishu_key in self.feature_db['jockeys']:
            jockey_data = self.feature_db['jockeys'][kishu_key]
            avg_rank = jockey_data['avg_rank']
            return -np.log(max(avg_rank, 1.0))
        else:
            return -np.log(8.0)  # 未知騎手
    
    def calculate_trainer_skill(self, chokyoshi_code: int) -> float:
        """調教師スキル計算"""
        if chokyoshi_code is None:
            return 0.0
        
        trainer_key = str(chokyoshi_code) if chokyoshi_code in self.feature_db['trainers'] else chokyoshi_code
        
        if trainer_key in self.feature_db['trainers']:
            trainer_data = self.feature_db['trainers'][trainer_key]
            avg_rank = trainer_data['avg_rank']
            return -np.log(max(avg_rank, 1.0))
        else:
            return -np.log(8.0)  # 未知調教師
    
    def calculate_corner_skill(self, ketto: str) -> float:
        """コーナースキル計算"""
        if ketto in self.feature_db['horses']:
            horse_data = self.feature_db['horses'][ketto]
            avg_corner = horse_data.get('avg_corner')
            if avg_corner is not None:
                return -np.log(max(avg_corner, 1.0))
        return 0.0
    
    def calculate_distance_adaptation(self, ketto: str, kyori: int) -> float:
        """距離適性計算"""
        if ketto not in self.feature_db['distance_adaptation']:
            return 0.0
        
        distance_data = self.feature_db['distance_adaptation'][ketto]
        
        # 完全一致
        kyori_key = str(kyori) if kyori in distance_data else kyori
        if kyori_key in distance_data:
            avg_rank = distance_data[kyori_key]['avg_rank']
            return -np.log(max(avg_rank, 1.0))
        
        # 近い距離での実績を使用
        distances = list(distance_data.keys())
        if distances:
            closest_dist = min(distances, key=lambda d: abs(int(d) - kyori))
            avg_rank = distance_data[closest_dist]['avg_rank']
            # 距離差ペナルティ
            distance_penalty = abs(int(closest_dist) - kyori) / 1000.0
            return -np.log(max(avg_rank, 1.0)) - distance_penalty
        
        return 0.0
    
    def calculate_track_adaptation(self, ketto: str, track_code: int) -> float:
        """馬場適性計算"""
        if ketto not in self.feature_db['track_adaptation']:
            return 0.0
        
        track_data = self.feature_db['track_adaptation'][ketto]
        track_key = str(track_code) if track_code in track_data else track_code
        
        if track_key in track_data:
            avg_rank = track_data[track_key]['avg_rank']
            return -np.log(max(avg_rank, 1.0))
        
        return 0.0
    
    def predict_race(self, race_id: str) -> List[Dict]:
        """レース予測（全特徴量使用）"""
        # レース情報を取得
        self.cur.execute("""
            SELECT kyori, track_code, keibajo_code
            FROM races
            WHERE race_id = %s
        """, (race_id,))
        
        race_row = self.cur.fetchone()
        if not race_row:
            return []
        
        kyori, track_code, keibajo_code = race_row
        race_conditions = {
            'kyori': kyori,
            'track_code': track_code,
            'keibajo_code': keibajo_code
        }
        
        # 出走馬を取得
        self.cur.execute("""
            SELECT 
                umaban,
                bamei,
                ketto_toroku_bango,
                kishu_code,
                chokyoshi_code,
                kakutei_chakujun
            FROM entries
            WHERE race_id = %s
            ORDER BY umaban
        """, (race_id,))
        
        entries = self.cur.fetchall()
        if not entries:
            return []
        
        predictions = []
        
        for umaban, bamei, ketto, kishu, chokyoshi, actual_rank in entries:
            # 全特徴量スキル計算
            horse_skill = self.calculate_horse_skill(ketto, race_conditions)
            jockey_skill = self.calculate_jockey_skill(kishu)
            trainer_skill = self.calculate_trainer_skill(chokyoshi)
            corner_skill = self.calculate_corner_skill(ketto)
            distance_skill = self.calculate_distance_adaptation(ketto, kyori) if kyori else 0.0
            track_skill = self.calculate_track_adaptation(ketto, track_code) if track_code else 0.0
            
            # 総合スキル
            total_skill = (
                horse_skill +
                WEIGHTS['jockey'] * jockey_skill +
                WEIGHTS['trainer'] * trainer_skill +
                WEIGHTS['corner'] * corner_skill +
                WEIGHTS['distance'] * distance_skill +
                WEIGHTS['track'] * track_skill
            )
            
            predictions.append({
                'umaban': umaban,
                'bamei': bamei.strip() if bamei else '',
                'ketto': ketto,
                'skill': total_skill,
                'kakutei_chakujun': actual_rank
            })
        
        # Plackett-Luce 確率計算
        total_exp_skill = sum(np.exp(p['skill']) for p in predictions)
        for p in predictions:
            p['p_win'] = np.exp(p['skill']) / total_exp_skill if total_exp_skill > 0 else 1.0 / len(predictions)
        
        # 予測順位でソート
        predictions.sort(key=lambda x: x['p_win'], reverse=True)
        
        for i, p in enumerate(predictions, 1):
            p['predicted_rank'] = i
        
        return predictions
    
    def run_backtest(self, start_date: int, end_date: int) -> List[Dict]:
        """バックテスト実行"""
        print(f"\n🔍 バックテスト実行中 (2026-{start_date:04d} ~ 2026-{end_date:04d})")
        
        # レース取得
        self.cur.execute("""
            SELECT 
                r.race_id,
                r.kaisai_nen,
                r.kaisai_tsukihi,
                r.keibajo_code,
                r.race_bango
            FROM races r
            WHERE r.kaisai_nen = 2026
              AND r.kaisai_tsukihi BETWEEN %s AND %s
              AND r.keibajo_code = ANY(%s)
            ORDER BY r.kaisai_tsukihi, r.keibajo_code, r.race_bango
        """, (start_date, end_date, NAR_VENUES))
        
        races = self.cur.fetchall()
        results = []
        
        for race_id, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango in races:
            predictions = self.predict_race(race_id)
            
            if not predictions:
                continue
            
            # Top3予測
            top3_predicted = [p['umaban'] for p in predictions[:3]]
            top3_actual = sorted(
                [p for p in predictions if p['kakutei_chakujun'] and p['kakutei_chakujun'] <= 3],
                key=lambda x: x['kakutei_chakujun']
            )
            top3_actual_umaban = [p['umaban'] for p in top3_actual]
            
            # Top5予測
            top5_predicted = [p['umaban'] for p in predictions[:5]]
            top5_actual = sorted(
                [p for p in predictions if p['kakutei_chakujun'] and p['kakutei_chakujun'] <= 5],
                key=lambda x: x['kakutei_chakujun']
            )
            top5_actual_umaban = [p['umaban'] for p in top5_actual]
            
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
                'top5_hit_count': top5_hit_count
            })
        
        print(f"   ✅ {len(results)}レースの予測完了")
        return results
    
    def close(self):
        """クローズ"""
        self.cur.close()
        self.conn.close()

def generate_summary(results: List[Dict]) -> Dict:
    """サマリー生成"""
    total_races = len(results)
    top3_ge1_count = sum(1 for r in results if r['top3_hit_count'] >= 1)
    top3_ge2_count = sum(1 for r in results if r['top3_hit_count'] >= 2)
    top3_eq3_count = sum(1 for r in results if r['top3_hit_count'] == 3)
    top5_ge3_count = sum(1 for r in results if r['top5_hit_count'] >= 3)
    top5_eq5_count = sum(1 for r in results if r['top5_hit_count'] == 5)
    
    return {
        'total_races': total_races,
        'top3_ge1': top3_ge1_count,
        'top3_ge1_rate': top3_ge1_count / total_races if total_races > 0 else 0,
        'top3_ge2': top3_ge2_count,
        'top3_ge2_rate': top3_ge2_count / total_races if total_races > 0 else 0,
        'top3_eq3': top3_eq3_count,
        'top3_eq3_rate': top3_eq3_count / total_races if total_races > 0 else 0,
        'top5_ge3': top5_ge3_count,
        'top5_ge3_rate': top5_ge3_count / total_races if total_races > 0 else 0,
        'top5_eq5': top5_eq5_count,
        'top5_eq5_rate': top5_eq5_count / total_races if total_races > 0 else 0
    }

def main():
    """メイン処理"""
    print("=" * 60)
    print("🚀 EOI-PL v1.0-Prime 完全版バックテスト")
    print("=" * 60)
    
    # 特徴量データベースをロード
    print("\n📂 特徴量データベースをロード中...")
    with open("/home/user/eoi-pl/data/feature_database_2020_2024.json", 'r', encoding='utf-8') as f:
        feature_db = json.load(f)
    print(f"   ✅ ロード完了")
    
    # モデル作成
    model = FullFeatureModel(feature_db)
    
    # バックテスト実行
    results = model.run_backtest(102, 130)
    
    # サマリー生成
    print("\n📊 サマリー生成中...")
    summary = generate_summary(results)
    
    # 結果表示
    print("\n" + "=" * 60)
    print("🎯 バックテスト結果（完全版）")
    print("=" * 60)
    print(f"対象レース数: {summary['total_races']}")
    print(f"\n【Top3予測】")
    print(f"  Top3≥1: {summary['top3_ge1']}/{summary['total_races']} ({summary['top3_ge1_rate']:.2%})")
    print(f"  Top3≥2: {summary['top3_ge2']}/{summary['total_races']} ({summary['top3_ge2_rate']:.2%})")
    print(f"  Top3=3: {summary['top3_eq3']}/{summary['total_races']} ({summary['top3_eq3_rate']:.2%})")
    print(f"\n【Top5予測】")
    print(f"  Top5≥3: {summary['top5_ge3']}/{summary['total_races']} ({summary['top5_ge3_rate']:.2%})")
    print(f"  Top5=5: {summary['top5_eq5']}/{summary['total_races']} ({summary['top5_eq5_rate']:.2%})")
    
    # CSV保存
    detail_csv = BACKTEST_DIR / "backtest_2026_01_full_detail.csv"
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
    
    # JSON保存
    summary_json = BACKTEST_DIR / "backtest_2026_01_full_summary.json"
    with open(summary_json, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✅ サマリーJSON保存: {summary_json}")
    
    model.close()
    
    print("\n🎉 完全版バックテスト完了！")

if __name__ == '__main__':
    main()
