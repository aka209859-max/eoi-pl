#!/usr/bin/env python3
"""
特徴量エンジニアリング - EOI-PL v1.0-Prime 完全版

全特徴量を計算:
- 馬の実績（平均順位、平均タイム、平均コーナー順位）
- 騎手スキル
- 調教師スキル
- 距離適性
- 馬場適性
"""

import psycopg2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import json

# データベース設定
DB_CONFIG = {
    'host': 'localhost',
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

# 地方競馬場コード（帯広ばんえいを除く）
NAR_VENUES = [30, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55]

class FeatureEngineer:
    """特徴量エンジニアリング"""
    
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        
    def calculate_horse_features(self, train_years: Tuple[int, int]) -> Dict:
        """馬の特徴量を計算"""
        print(f"📊 馬の特徴量計算中... ({train_years[0]}-{train_years[1]}年)")
        
        self.cur.execute("""
            SELECT 
                e.ketto_toroku_bango,
                AVG(e.kakutei_chakujun) as avg_rank,
                AVG(e.soha_time) as avg_time,
                AVG(e.corner_1) as avg_corner_1,
                AVG(e.corner_2) as avg_corner_2,
                AVG(e.corner_3) as avg_corner_3,
                AVG(e.corner_4) as avg_corner_4,
                COUNT(*) as race_count,
                SUM(CASE WHEN e.kakutei_chakujun = 1 THEN 1 ELSE 0 END) as win_count,
                SUM(CASE WHEN e.kakutei_chakujun <= 2 THEN 1 ELSE 0 END) as place2_count,
                SUM(CASE WHEN e.kakutei_chakujun <= 3 THEN 1 ELSE 0 END) as place3_count
            FROM entries e
            JOIN races r ON e.race_id = r.race_id
            WHERE r.kaisai_nen >= %s AND r.kaisai_nen <= %s
              AND r.keibajo_code = ANY(%s)
              AND e.kakutei_chakujun IS NOT NULL
              AND e.kakutei_chakujun > 0
              AND e.ketto_toroku_bango IS NOT NULL
            GROUP BY e.ketto_toroku_bango
            HAVING COUNT(*) >= 1
        """, (train_years[0], train_years[1], NAR_VENUES))
        
        horse_features = {}
        for row in self.cur.fetchall():
            ketto, avg_rank, avg_time, c1, c2, c3, c4, races, wins, p2, p3 = row
            
            # 平均コーナー順位（NULLを除外）
            corners = [float(c) for c in [c1, c2, c3, c4] if c is not None]
            avg_corner = np.mean(corners) if corners else None
            
            horse_features[ketto] = {
                'avg_rank': float(avg_rank) if avg_rank else 10.0,
                'avg_time': float(avg_time) if avg_time else None,
                'avg_corner': avg_corner,
                'race_count': races,
                'win_rate': wins / races if races > 0 else 0.0,
                'place2_rate': p2 / races if races > 0 else 0.0,
                'place3_rate': p3 / races if races > 0 else 0.0
            }
        
        print(f"   ✅ {len(horse_features)}頭の馬の特徴量を計算")
        return horse_features
    
    def calculate_jockey_features(self, train_years: Tuple[int, int]) -> Dict:
        """騎手の特徴量を計算"""
        print(f"🏇 騎手の特徴量計算中... ({train_years[0]}-{train_years[1]}年)")
        
        self.cur.execute("""
            SELECT 
                e.kishu_code,
                AVG(e.kakutei_chakujun) as avg_rank,
                COUNT(*) as race_count,
                SUM(CASE WHEN e.kakutei_chakujun = 1 THEN 1 ELSE 0 END) as win_count,
                SUM(CASE WHEN e.kakutei_chakujun <= 2 THEN 1 ELSE 0 END) as place2_count,
                SUM(CASE WHEN e.kakutei_chakujun <= 3 THEN 1 ELSE 0 END) as place3_count
            FROM entries e
            JOIN races r ON e.race_id = r.race_id
            WHERE r.kaisai_nen >= %s AND r.kaisai_nen <= %s
              AND r.keibajo_code = ANY(%s)
              AND e.kakutei_chakujun IS NOT NULL
              AND e.kakutei_chakujun > 0
              AND e.kishu_code IS NOT NULL
            GROUP BY e.kishu_code
            HAVING COUNT(*) >= 5
        """, (train_years[0], train_years[1], NAR_VENUES))
        
        jockey_features = {}
        for row in self.cur.fetchall():
            kishu_code, avg_rank, races, wins, p2, p3 = row
            jockey_features[kishu_code] = {
                'avg_rank': float(avg_rank) if avg_rank else 8.0,
                'race_count': races,
                'win_rate': wins / races if races > 0 else 0.0,
                'place2_rate': p2 / races if races > 0 else 0.0,
                'place3_rate': p3 / races if races > 0 else 0.0
            }
        
        print(f"   ✅ {len(jockey_features)}人の騎手の特徴量を計算")
        return jockey_features
    
    def calculate_trainer_features(self, train_years: Tuple[int, int]) -> Dict:
        """調教師の特徴量を計算"""
        print(f"👨‍🏫 調教師の特徴量計算中... ({train_years[0]}-{train_years[1]}年)")
        
        self.cur.execute("""
            SELECT 
                e.chokyoshi_code,
                AVG(e.kakutei_chakujun) as avg_rank,
                COUNT(*) as race_count,
                SUM(CASE WHEN e.kakutei_chakujun = 1 THEN 1 ELSE 0 END) as win_count,
                SUM(CASE WHEN e.kakutei_chakujun <= 2 THEN 1 ELSE 0 END) as place2_count,
                SUM(CASE WHEN e.kakutei_chakujun <= 3 THEN 1 ELSE 0 END) as place3_count
            FROM entries e
            JOIN races r ON e.race_id = r.race_id
            WHERE r.kaisai_nen >= %s AND r.kaisai_nen <= %s
              AND r.keibajo_code = ANY(%s)
              AND e.kakutei_chakujun IS NOT NULL
              AND e.kakutei_chakujun > 0
              AND e.chokyoshi_code IS NOT NULL
            GROUP BY e.chokyoshi_code
            HAVING COUNT(*) >= 5
        """, (train_years[0], train_years[1], NAR_VENUES))
        
        trainer_features = {}
        for row in self.cur.fetchall():
            chokyoshi_code, avg_rank, races, wins, p2, p3 = row
            trainer_features[chokyoshi_code] = {
                'avg_rank': float(avg_rank) if avg_rank else 8.0,
                'race_count': races,
                'win_rate': wins / races if races > 0 else 0.0,
                'place2_rate': p2 / races if races > 0 else 0.0,
                'place3_rate': p3 / races if races > 0 else 0.0
            }
        
        print(f"   ✅ {len(trainer_features)}人の調教師の特徴量を計算")
        return trainer_features
    
    def calculate_distance_adaptation(self, train_years: Tuple[int, int]) -> Dict:
        """距離適性を計算"""
        print(f"📏 距離適性計算中... ({train_years[0]}-{train_years[1]}年)")
        
        self.cur.execute("""
            SELECT 
                e.ketto_toroku_bango,
                r.kyori,
                AVG(e.kakutei_chakujun) as avg_rank,
                COUNT(*) as race_count
            FROM entries e
            JOIN races r ON e.race_id = r.race_id
            WHERE r.kaisai_nen >= %s AND r.kaisai_nen <= %s
              AND r.keibajo_code = ANY(%s)
              AND e.kakutei_chakujun IS NOT NULL
              AND e.kakutei_chakujun > 0
              AND e.ketto_toroku_bango IS NOT NULL
              AND r.kyori IS NOT NULL
            GROUP BY e.ketto_toroku_bango, r.kyori
            HAVING COUNT(*) >= 1
        """, (train_years[0], train_years[1], NAR_VENUES))
        
        distance_adaptation = {}
        for row in self.cur.fetchall():
            ketto, kyori, avg_rank, races = row
            if ketto not in distance_adaptation:
                distance_adaptation[ketto] = {}
            distance_adaptation[ketto][kyori] = {
                'avg_rank': float(avg_rank),
                'race_count': races
            }
        
        print(f"   ✅ {len(distance_adaptation)}頭の馬の距離適性を計算")
        return distance_adaptation
    
    def calculate_track_adaptation(self, train_years: Tuple[int, int]) -> Dict:
        """馬場適性を計算"""
        print(f"🏇 馬場適性計算中... ({train_years[0]}-{train_years[1]}年)")
        
        self.cur.execute("""
            SELECT 
                e.ketto_toroku_bango,
                r.track_code,
                AVG(e.kakutei_chakujun) as avg_rank,
                COUNT(*) as race_count
            FROM entries e
            JOIN races r ON e.race_id = r.race_id
            WHERE r.kaisai_nen >= %s AND r.kaisai_nen <= %s
              AND r.keibajo_code = ANY(%s)
              AND e.kakutei_chakujun IS NOT NULL
              AND e.kakutei_chakujun > 0
              AND e.ketto_toroku_bango IS NOT NULL
              AND r.track_code IS NOT NULL
            GROUP BY e.ketto_toroku_bango, r.track_code
            HAVING COUNT(*) >= 1
        """, (train_years[0], train_years[1], NAR_VENUES))
        
        track_adaptation = {}
        for row in self.cur.fetchall():
            ketto, track_code, avg_rank, races = row
            if ketto not in track_adaptation:
                track_adaptation[ketto] = {}
            track_adaptation[ketto][track_code] = {
                'avg_rank': float(avg_rank),
                'race_count': races
            }
        
        print(f"   ✅ {len(track_adaptation)}頭の馬の馬場適性を計算")
        return track_adaptation
    
    def build_feature_database(self, train_years: Tuple[int, int]) -> Dict:
        """全特徴量データベースを構築"""
        print("\n" + "=" * 60)
        print("🚀 特徴量データベース構築開始")
        print("=" * 60)
        
        feature_db = {
            'horses': self.calculate_horse_features(train_years),
            'jockeys': self.calculate_jockey_features(train_years),
            'trainers': self.calculate_trainer_features(train_years),
            'distance_adaptation': self.calculate_distance_adaptation(train_years),
            'track_adaptation': self.calculate_track_adaptation(train_years),
            'train_years': train_years,
            'nar_venues': NAR_VENUES
        }
        
        print("\n" + "=" * 60)
        print("✅ 特徴量データベース構築完了")
        print("=" * 60)
        print(f"   - 馬: {len(feature_db['horses'])}頭")
        print(f"   - 騎手: {len(feature_db['jockeys'])}人")
        print(f"   - 調教師: {len(feature_db['trainers'])}人")
        print(f"   - 距離適性: {len(feature_db['distance_adaptation'])}頭")
        print(f"   - 馬場適性: {len(feature_db['track_adaptation'])}頭")
        
        return feature_db
    
    def save_feature_database(self, feature_db: Dict, output_path: str):
        """特徴量データベースを保存"""
        # JSONシリアライズ可能な形式に変換
        serializable_db = {
            'horses': {k: v for k, v in feature_db['horses'].items()},
            'jockeys': {str(k): v for k, v in feature_db['jockeys'].items()},
            'trainers': {str(k): v for k, v in feature_db['trainers'].items()},
            'distance_adaptation': {
                k: {str(kyori): v for kyori, v in dist.items()} 
                for k, dist in feature_db['distance_adaptation'].items()
            },
            'track_adaptation': {
                k: {str(track): v for track, v in tracks.items()} 
                for k, tracks in feature_db['track_adaptation'].items()
            },
            'train_years': feature_db['train_years'],
            'nar_venues': feature_db['nar_venues']
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_db, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 特徴量データベース保存: {output_path}")
    
    def close(self):
        """データベース接続を閉じる"""
        self.cur.close()
        self.conn.close()

def main():
    """メイン処理"""
    # 特徴量エンジニア作成
    engineer = FeatureEngineer()
    
    # 2020-2024年のデータで特徴量を計算
    feature_db = engineer.build_feature_database((2020, 2024))
    
    # 保存
    output_path = "/home/user/eoi-pl/data/feature_database_2020_2024.json"
    engineer.save_feature_database(feature_db, output_path)
    
    # クローズ
    engineer.close()
    
    print("\n🎉 特徴量エンジニアリング完了！")

if __name__ == '__main__':
    main()
