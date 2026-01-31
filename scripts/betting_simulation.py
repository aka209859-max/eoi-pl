#!/usr/bin/env python3
"""
馬券シミュレーション - ★★★★★/★★★★☆レースのみ
"""

import psycopg2
import numpy as np
import pandas as pd
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

# 特徴量の重み
WEIGHTS = {
    'avg_rank': 0.30,
    'jockey': 0.15,
    'trainer': 0.10,
    'corner': 0.15,
    'time': 0.15,
    'distance': 0.10,
    'track': 0.05
}

class BettingSimulator:
    def __init__(self, feature_db: Dict):
        self.feature_db = feature_db
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
    
    def calculate_horse_skill(self, ketto: str, race_conditions: Dict) -> float:
        if ketto not in self.feature_db['horses']:
            return -np.log(8.0)
        
        horse_data = self.feature_db['horses'][ketto]
        avg_rank = horse_data.get('avg_rank', 8.0)
        return -np.log(max(avg_rank, 1.0))
    
    def calculate_jockey_skill(self, kishu_code: str) -> float:
        if kishu_code not in self.feature_db['jockeys']:
            return -np.log(8.0)
        
        jockey_data = self.feature_db['jockeys'][kishu_code]
        avg_rank = jockey_data.get('avg_rank', 8.0)
        return -np.log(max(avg_rank, 1.0))
    
    def calculate_trainer_skill(self, chokyoshi_code: str) -> float:
        if chokyoshi_code not in self.feature_db['trainers']:
            return -np.log(8.0)
        
        trainer_data = self.feature_db['trainers'][chokyoshi_code]
        avg_rank = trainer_data.get('avg_rank', 8.0)
        return -np.log(max(avg_rank, 1.0))
    
    def calculate_corner_skill(self, ketto: str) -> float:
        if ketto not in self.feature_db['horses']:
            return 0.0
        
        horse_data = self.feature_db['horses'][ketto]
        avg_corner = horse_data.get('avg_corner')
        if avg_corner is None:
            return 0.0
        
        return -np.log(max(avg_corner, 1.0))
    
    def calculate_time_skill(self, ketto: str, kyori: int) -> float:
        return 0.0  # 簡略化
    
    def calculate_distance_adaptation(self, ketto: str, kyori: int) -> float:
        return 0.0  # 簡略化
    
    def calculate_track_adaptation(self, ketto: str, track_code: int) -> float:
        return 0.0  # 簡略化
    
    def predict_race(self, race_id: str) -> List[Dict]:
        # レース情報取得
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
        
        # 出走馬取得
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
            horse_skill = self.calculate_horse_skill(ketto, race_conditions)
            jockey_skill = self.calculate_jockey_skill(kishu)
            trainer_skill = self.calculate_trainer_skill(chokyoshi)
            corner_skill = self.calculate_corner_skill(ketto)
            time_skill = self.calculate_time_skill(ketto, kyori) if kyori else 0.0
            distance_skill = self.calculate_distance_adaptation(ketto, kyori) if kyori else 0.0
            track_skill = self.calculate_track_adaptation(ketto, track_code) if track_code else 0.0
            
            total_skill = (
                horse_skill +
                WEIGHTS['jockey'] * jockey_skill +
                WEIGHTS['trainer'] * trainer_skill +
                WEIGHTS['corner'] * corner_skill +
                WEIGHTS['time'] * time_skill +
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
        
        total_exp_skill = sum(np.exp(p['skill']) for p in predictions)
        for p in predictions:
            p['p_win'] = np.exp(p['skill']) / total_exp_skill if total_exp_skill > 0 else 1.0 / len(predictions)
        
        predictions.sort(key=lambda x: x['p_win'], reverse=True)
        
        for i, p in enumerate(predictions, 1):
            p['predicted_rank'] = i
        
        return predictions
    
    def calculate_recommendation(self, predictions: List[Dict]) -> tuple:
        """偏差値から推奨度を計算"""
        skills = [p['skill'] for p in predictions]
        if len(skills) < 2:
            return None, None
        
        mean_skill = np.mean(skills)
        std_skill = np.std(skills)
        
        if std_skill == 0:
            deviations = [50.0] * len(skills)
        else:
            deviations = [50 + 10 * (skill - mean_skill) / std_skill for skill in skills]
        
        for i, p in enumerate(predictions):
            p['deviation'] = deviations[i]
        
        top1_deviation = deviations[0]
        
        if top1_deviation >= 70:
            return "★★★★★", top1_deviation
        elif top1_deviation >= 65:
            return "★★★★☆", top1_deviation
        else:
            return None, top1_deviation
    
    def simulate_betting(self, start_date: int, end_date: int, year: int):
        """馬券シミュレーション"""
        # レース取得
        self.cur.execute("""
            SELECT 
                r.race_id,
                r.kaisai_nen,
                r.kaisai_tsukihi,
                r.keibajo_code,
                r.race_bango
            FROM races r
            WHERE r.kaisai_nen = %s
              AND r.kaisai_tsukihi BETWEEN %s AND %s
              AND r.keibajo_code = ANY(%s)
            ORDER BY r.kaisai_tsukihi, r.keibajo_code, r.race_bango
        """, (year, start_date, end_date, NAR_VENUES))
        
        races = self.cur.fetchall()
        
        results = []
        
        print(f"\n🔍 {year}年{start_date:04d}〜{end_date:04d}のレースを分析中...")
        print(f"   総レース数: {len(races)}")
        
        for race_id, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango in races:
            predictions = self.predict_race(race_id)
            
            if not predictions:
                continue
            
            # 推奨度を計算
            recommendation, top1_deviation = self.calculate_recommendation(predictions)
            
            # ★★★★★/★★★★☆のみ
            if recommendation not in ["★★★★★", "★★★★☆"]:
                continue
            
            # Top5予想
            top5_predicted = [p['umaban'] for p in predictions[:5]]
            
            # 実際のTop3
            top3_actual = sorted(
                [p for p in predictions if p['kakutei_chakujun'] and p['kakutei_chakujun'] <= 3],
                key=lambda x: x['kakutei_chakujun']
            )
            top3_actual_umaban = [p['umaban'] for p in top3_actual]
            
            # 的中判定（正しい: Top5予想 vs Top3実際）
            hit_count = len(set(top5_predicted) & set(top3_actual_umaban))
            is_hit = hit_count >= 3
            
            results.append({
                'race_id': race_id,
                'kaisai_tsukihi': kaisai_tsukihi,
                'keibajo_code': keibajo_code,
                'race_bango': race_bango,
                'recommendation': recommendation,
                'top1_deviation': top1_deviation,
                'top5_predicted': top5_predicted,
                'top3_actual': top3_actual_umaban,
                'hit_count': hit_count,
                'is_hit': is_hit
            })
        
        print(f"   ★★★★★/★★★★☆レース: {len(results)}レース\n")
        
        return results
    
    def close(self):
        self.cur.close()
        self.conn.close()

def main():
    print("=" * 60)
    print("🎯 馬券シミュレーション（★★★★★/★★★★☆レースのみ）")
    print("=" * 60)
    
    # 特徴量DBをロード
    print("\n📂 特徴量データベースをロード中...")
    with open("/home/user/eoi-pl/data/feature_database_2020_2025.json", 'r', encoding='utf-8') as f:
        feature_db = json.load(f)
    print("   ✅ ロード完了")
    
    # シミュレーター作成
    simulator = BettingSimulator(feature_db)
    
    # 2025年11月のシミュレーション
    results = simulator.simulate_betting(1101, 1130, 2025)
    
    # 統計計算
    print("=" * 60)
    print("📊 馬券シミュレーション結果")
    print("=" * 60)
    
    total_races = len(results)
    star5_races = [r for r in results if r['recommendation'] == "★★★★★"]
    star4_races = [r for r in results if r['recommendation'] == "★★★★☆"]
    
    hit_races = [r for r in results if r['is_hit']]
    star5_hit = [r for r in star5_races if r['is_hit']]
    star4_hit = [r for r in star4_races if r['is_hit']]
    
    print(f"\n【推奨度別レース数】")
    print(f"  ★★★★★: {len(star5_races)}レース")
    print(f"  ★★★★☆: {len(star4_races)}レース")
    print(f"  合計: {total_races}レース")
    
    print(f"\n【的中率（Top5≥3）】")
    print(f"  ★★★★★: {len(star5_hit)}/{len(star5_races)} ({len(star5_hit)/len(star5_races)*100:.2f}%)") if len(star5_races) > 0 else print(f"  ★★★★★: 0/0 (N/A)")
    print(f"  ★★★★☆: {len(star4_hit)}/{len(star4_races)} ({len(star4_hit)/len(star4_races)*100:.2f}%)") if len(star4_races) > 0 else print(f"  ★★★★☆: 0/0 (N/A)")
    print(f"  合計: {len(hit_races)}/{total_races} ({len(hit_races)/total_races*100:.2f}%)") if total_races > 0 else print(f"  合計: 0/0 (N/A)")
    
    print(f"\n【3連複5頭BOX（10点）のシミュレーション】")
    bet_per_race = 1000  # 1点100円 × 10点
    total_bet = total_races * bet_per_race
    
    # 回収率は計算できない（オッズ情報がないため）
    print(f"  総レース数: {total_races}レース")
    print(f"  総投資額: {total_bet:,}円")
    print(f"  的中レース数: {len(hit_races)}レース")
    print(f"  的中率: {len(hit_races)/total_races*100:.2f}%") if total_races > 0 else print(f"  的中率: N/A")
    print(f"\n  ⚠️ 回収率: 計算不可（オッズ情報なし）")
    
    # CSV保存
    output_csv = "/home/user/eoi-pl/backtest/betting_simulation_2025_11.csv"
    df = pd.DataFrame([{
        'kaisai_tsukihi': r['kaisai_tsukihi'],
        'keibajo_code': r['keibajo_code'],
        'race_bango': r['race_bango'],
        'recommendation': r['recommendation'],
        'top1_deviation': f"{r['top1_deviation']:.1f}",
        'top5_predicted': ','.join(map(str, r['top5_predicted'])),
        'top3_actual': ','.join(map(str, r['top3_actual'])),
        'hit_count': r['hit_count'],
        'is_hit': '○' if r['is_hit'] else '×'
    } for r in results])
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n✅ 詳細CSV保存: {output_csv}")
    
    simulator.close()
    
    print("\n🎉 馬券シミュレーション完了！\n")

if __name__ == "__main__":
    main()
