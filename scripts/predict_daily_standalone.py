#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime 日次予想スクリプト（スタンドアロン版）

【使い方】
  # 特定のレースを予想
  python predict_daily_standalone.py --race-id 202602014501
  
  # 特定日の全レースを予想
  python predict_daily_standalone.py --date 20260201
  
  # 予想結果をCSVで保存
  python predict_daily_standalone.py --date 20260201 --output predictions_20260201.csv

【前提条件】
  1. PostgreSQL (eoi_pl) が起動していること
  2. 特徴量データベース (feature_database_latest.json) が存在すること
  3. Python 3.8+ がインストールされていること
  4. 必要なライブラリ: psycopg2, numpy, pandas

【インストール】
  pip install psycopg2 numpy pandas
"""

import psycopg2
import json
import numpy as np
import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime

# =====================================================================
# 設定
# =====================================================================

# データベース接続設定
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

# 特徴量の重み（正規化済み: 合計=1.00）
WEIGHTS = {
    'avg_rank': 0.30,    # 平均順位
    'jockey': 0.15,      # 騎手
    'trainer': 0.10,     # 調教師
    'corner': 0.15,      # コーナー
    'time': 0.15,        # タイム（距離別基準使用）
    'distance': 0.10,    # 距離
    'track': 0.05        # 馬場
}

# NAR競馬場コード
NAR_VENUES = [30, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55]

# 競馬場名マッピング
VENUE_NAMES = {
    30: '門別', 35: '盛岡', 36: '水沢', 42: '浦和', 43: '船橋', 44: '大井', 45: '川崎',
    46: '金沢', 47: '笠松', 48: '名古屋', 50: '園田', 51: '姫路', 54: '高知', 55: '佐賀'
}

# 距離別基準タイム（2020-2025年、地方競馬、1着馬の平均）
# 単位: 0.1秒
DISTANCE_BENCHMARKS = {
    800: (492.0, 13.9), 820: (510.6, 7.4), 850: (516.1, 8.9),
    900: (553.1, 10.1), 920: (567.8, 10.0), 1000: (982.5, 119.3),
    1100: (1087.1, 9.9), 1200: (1147.3, 14.1), 1230: (1206.8, 13.3),
    1300: (1249.1, 15.8), 1400: (1313.8, 20.9), 1500: (1374.6, 15.5),
    1600: (1436.7, 24.6), 1650: (1457.6, 14.9), 1700: (1515.7, 29.0),
    1750: (1578.7, 74.0), 1800: (1655.5, 185.8), 1860: (2002.3, 117.5),
    1870: (2055.7, 56.0), 1900: (2049.1, 42.1), 2000: (2120.0, 34.7),
    2100: (2167.2, 25.9), 2200: (2279.0, 24.2), 2400: (2377.9, 55.9),
    2500: (2475.4, 30.8), 2600: (2505.0, 21.3),
}

# =====================================================================
# 予測モデル
# =====================================================================

class EOIPLPredictor:
    """EOI-PL v1.0-Prime 予測モデル"""
    
    def __init__(self, feature_db_path: str):
        """
        初期化
        
        Args:
            feature_db_path: 特徴量データベースのパス
        """
        print(f"📂 特徴量データベースをロード: {feature_db_path}")
        with open(feature_db_path, 'r', encoding='utf-8') as f:
            self.feature_db = json.load(f)
        print(f"   ✅ 馬: {len(self.feature_db['horses']):,}頭")
        print(f"   ✅ 騎手: {len(self.feature_db['jockeys']):,}人")
        print(f"   ✅ 調教師: {len(self.feature_db['trainers']):,}人\n")
    
    def calculate_horse_skill(self, ketto: str) -> float:
        """馬のスキル計算"""
        if ketto in self.feature_db['horses']:
            horse_data = self.feature_db['horses'][ketto]
            avg_rank = horse_data['avg_rank']
            return -np.log(max(avg_rank, 1.0))
        return -np.log(10.0)  # 未知馬
    
    def calculate_jockey_skill(self, kishu_code: int) -> float:
        """騎手スキル計算"""
        kishu_key = str(kishu_code)
        if kishu_key in self.feature_db['jockeys']:
            jockey_data = self.feature_db['jockeys'][kishu_key]
            avg_rank = jockey_data['avg_rank']
            return -np.log(max(avg_rank, 1.0))
        return -np.log(8.0)  # 未知騎手
    
    def calculate_trainer_skill(self, chokyoshi_code: int) -> float:
        """調教師スキル計算"""
        trainer_key = str(chokyoshi_code)
        if trainer_key in self.feature_db['trainers']:
            trainer_data = self.feature_db['trainers'][trainer_key]
            avg_rank = trainer_data['avg_rank']
            return -np.log(max(avg_rank, 1.0))
        return -np.log(8.0)  # 未知調教師
    
    def calculate_corner_skill(self, ketto: str) -> float:
        """コーナースキル計算"""
        if ketto in self.feature_db['horses']:
            horse_data = self.feature_db['horses'][ketto]
            avg_corner = horse_data.get('avg_corner')
            if avg_corner is not None:
                return -np.log(max(avg_corner, 1.0))
        return 0.0
    
    def calculate_time_skill(self, ketto: str, kyori: int) -> float:
        """タイムスキル計算（距離別基準タイム使用、0.1秒単位）"""
        if ketto not in self.feature_db['horses']:
            return 0.0
        
        horse_data = self.feature_db['horses'][ketto]
        avg_time = horse_data.get('avg_time')
        
        if avg_time is None or kyori is None or kyori == 0:
            return 0.0
        
        # 最も近い距離の基準値を使う
        if kyori in DISTANCE_BENCHMARKS:
            baseline, stddev = DISTANCE_BENCHMARKS[kyori]
        else:
            closest_kyori = min(DISTANCE_BENCHMARKS.keys(), key=lambda x: abs(x - kyori))
            baseline, stddev = DISTANCE_BENCHMARKS[closest_kyori]
        
        # 標準化スコア
        z_score = (baseline - avg_time) / stddev
        skill = max(min(z_score * 0.5, 2.0), -2.0)
        
        return skill
    
    def calculate_distance_adaptation(self, ketto: str, kyori: int) -> float:
        """距離適性計算"""
        if ketto not in self.feature_db.get('distance_adaptation', {}):
            return 0.0
        
        distance_data = self.feature_db['distance_adaptation'][ketto]
        kyori_key = str(kyori)
        
        if kyori_key in distance_data:
            return distance_data[kyori_key]
        
        # 近い距離を探す
        available_distances = [int(k) for k in distance_data.keys()]
        if not available_distances:
            return 0.0
        
        closest = min(available_distances, key=lambda x: abs(x - kyori))
        return distance_data[str(closest)]
    
    def calculate_track_adaptation(self, ketto: str, track_code: int) -> float:
        """馬場適性計算"""
        if ketto not in self.feature_db.get('track_adaptation', {}):
            return 0.0
        
        track_data = self.feature_db['track_adaptation'][ketto]
        track_key = str(track_code)
        
        if track_key in track_data:
            return track_data[track_key]
        
        return 0.0
    
    def predict_race(self, conn, race_id: str) -> pd.DataFrame:
        """
        レースの予想を実行
        
        Args:
            conn: PostgreSQL接続
            race_id: レースID（例: 202602014501）
        
        Returns:
            予想結果のDataFrame
        """
        cur = conn.cursor()
        
        # レース情報を取得
        cur.execute("""
            SELECT kyori, track_code, keibajo_code
            FROM races
            WHERE race_id = %s
        """, (race_id,))
        
        race_info = cur.fetchone()
        if not race_info:
            print(f"⚠️  レース {race_id} が見つかりません")
            return pd.DataFrame()
        
        kyori, track_code, keibajo_code = race_info
        
        # 出走馬情報を取得
        cur.execute("""
            SELECT 
                umaban, bamei, ketto_toroku_bango,
                kishu_code, chokyoshi_code
            FROM entries
            WHERE race_id = %s
            ORDER BY umaban
        """, (race_id,))
        
        entries = cur.fetchall()
        if not entries:
            print(f"⚠️  レース {race_id} の出走馬が見つかりません")
            return pd.DataFrame()
        
        # 各馬のスキルを計算
        predictions = []
        for umaban, bamei, ketto, kishu, chokyoshi in entries:
            # 各特徴量を計算
            horse_skill = self.calculate_horse_skill(ketto)
            jockey_skill = self.calculate_jockey_skill(kishu) if kishu else -np.log(8.0)
            trainer_skill = self.calculate_trainer_skill(chokyoshi) if chokyoshi else -np.log(8.0)
            corner_skill = self.calculate_corner_skill(ketto)
            time_skill = self.calculate_time_skill(ketto, kyori) if kyori else 0.0
            distance_skill = self.calculate_distance_adaptation(ketto, kyori) if kyori else 0.0
            track_skill = self.calculate_track_adaptation(ketto, track_code) if track_code else 0.0
            
            # 総合スキル
            total_skill = (
                WEIGHTS['avg_rank'] * horse_skill +
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
                'ketto_toroku_bango': ketto,
                'total_skill': total_skill,
                'horse_skill': horse_skill,
                'jockey_skill': jockey_skill,
                'trainer_skill': trainer_skill,
                'corner_skill': corner_skill,
                'time_skill': time_skill,
                'distance_skill': distance_skill,
                'track_skill': track_skill
            })
        
        # DataFrameに変換してスキル順にソート
        df = pd.DataFrame(predictions)
        df = df.sort_values('total_skill', ascending=False).reset_index(drop=True)
        df['rank_pred'] = range(1, len(df) + 1)
        
        cur.close()
        return df

# =====================================================================
# メイン処理
# =====================================================================

def predict_single_race(race_id: str, feature_db_path: str):
    """単一レースの予想"""
    print(f"\n{'='*60}")
    print(f"🏇 レース予想: {race_id}")
    print(f"{'='*60}\n")
    
    # 予測モデルを初期化
    predictor = EOIPLPredictor(feature_db_path)
    
    # PostgreSQLに接続
    conn = psycopg2.connect(**DB_CONFIG)
    
    # 予想を実行
    predictions = predictor.predict_race(conn, race_id)
    
    if predictions.empty:
        conn.close()
        return
    
    # 結果を表示
    print(f"\n📊 予想結果:\n")
    print(predictions[['rank_pred', 'umaban', 'bamei', 'total_skill']].to_string(index=False))
    
    print(f"\n🎯 推奨買い目:")
    print(f"  Top3: {', '.join(map(str, predictions.head(3)['umaban'].tolist()))}")
    print(f"  Top5: {', '.join(map(str, predictions.head(5)['umaban'].tolist()))}")
    
    conn.close()
    print(f"\n✅ 予想完了！\n")

def predict_daily_races(date: str, feature_db_path: str, output_path: str = None):
    """指定日の全レース予想"""
    print(f"\n{'='*60}")
    print(f"📅 日次予想: {date}")
    print(f"{'='*60}\n")
    
    # 予測モデルを初期化
    predictor = EOIPLPredictor(feature_db_path)
    
    # PostgreSQLに接続
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 指定日のレースIDを取得
    year = int(date[:4])
    month_day = int(date[4:8])
    
    cur.execute("""
        SELECT race_id, keibajo_code, race_bango
        FROM races
        WHERE kaisai_nen = %s AND kaisai_tsukihi = %s
        ORDER BY keibajo_code, race_bango
    """, (year, month_day))
    
    races = cur.fetchall()
    
    if not races:
        print(f"⚠️  {date} のレースが見つかりません")
        cur.close()
        conn.close()
        return
    
    print(f"🏇 対象レース: {len(races)}レース\n")
    
    all_predictions = []
    
    for race_id, keibajo_code, race_bango in races:
        venue_name = VENUE_NAMES.get(keibajo_code, str(keibajo_code))
        print(f"予想中: {venue_name} {race_bango}R ({race_id})...")
        
        predictions = predictor.predict_race(conn, race_id)
        
        if not predictions.empty:
            predictions['race_id'] = race_id
            predictions['keibajo_code'] = keibajo_code
            predictions['race_bango'] = race_bango
            predictions['venue_name'] = venue_name
            all_predictions.append(predictions)
    
    if not all_predictions:
        print(f"\n⚠️  予想結果がありません")
        cur.close()
        conn.close()
        return
    
    # 全予想を結合
    all_df = pd.concat(all_predictions, ignore_index=True)
    
    # CSV保存
    if output_path:
        all_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n💾 予想結果を保存: {output_path}")
    
    # サマリー表示
    print(f"\n📊 予想サマリー:")
    print(f"  対象レース: {len(races)}レース")
    print(f"  予想馬数: {len(all_df)}頭")
    
    cur.close()
    conn.close()
    print(f"\n✅ 日次予想完了！\n")

def main():
    parser = argparse.ArgumentParser(
        description='EOI-PL v1.0-Prime 日次予想スクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単一レースの予想
  python predict_daily_standalone.py --race-id 202602014501
  
  # 指定日の全レース予想
  python predict_daily_standalone.py --date 20260201
  
  # 予想結果をCSV保存
  python predict_daily_standalone.py --date 20260201 --output predictions_20260201.csv
        """
    )
    
    parser.add_argument('--race-id', type=str, help='レースID（例: 202602014501）')
    parser.add_argument('--date', type=str, help='予想日（例: 20260201）')
    parser.add_argument('--output', type=str, help='出力CSVファイル名')
    parser.add_argument('--db', type=str, 
                       default='E:/eoi-pl/data/feature_database_latest.json',
                       help='特徴量データベースのパス')
    
    args = parser.parse_args()
    
    # 特徴量データベースの存在確認
    if not Path(args.db).exists():
        print(f"❌ 特徴量データベースが見つかりません: {args.db}")
        print(f"\n推奨パス: E:/eoi-pl/data/feature_database_latest.json")
        sys.exit(1)
    
    # 予想実行
    if args.race_id:
        predict_single_race(args.race_id, args.db)
    elif args.date:
        predict_daily_races(args.date, args.db, args.output)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
