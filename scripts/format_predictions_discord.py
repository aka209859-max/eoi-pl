#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime Discord & TXT出力スクリプト

【使い方】
  # 単一レースをDiscord形式で出力
  python format_predictions_discord.py --race-id 202602014501
  
  # 単一レースをTXTファイルに保存
  python format_predictions_discord.py --race-id 202602014501 --output predictions_202602014501.txt
  
  # 1日分の全レースをDiscord形式で出力
  python format_predictions_discord.py --date 20260201
  
  # 1日分の全レースをTXTファイルに保存
  python format_predictions_discord.py --date 20260201 --output predictions_20260201.txt
"""

import psycopg2
import json
import numpy as np
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# =====================================================================
# 設定（predict_daily_standalone.py と同じ）
# =====================================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

WEIGHTS = {
    'avg_rank': 0.30, 'jockey': 0.15, 'trainer': 0.10,
    'corner': 0.15, 'time': 0.15, 'distance': 0.10, 'track': 0.05
}

NAR_VENUES = [30, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55]

VENUE_NAMES = {
    30: '門別', 35: '盛岡', 36: '水沢', 42: '浦和', 43: '船橋', 44: '大井', 45: '川崎',
    46: '金沢', 47: '笠松', 48: '名古屋', 50: '園田', 51: '姫路', 54: '高知', 55: '佐賀'
}

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
# 偏差値計算と推奨度
# =====================================================================

def calculate_deviation_score(skills: List[float]) -> List[float]:
    """
    スキル値を偏差値に変換
    
    偏差値 = 50 + 10 * (スキル - 平均) / 標準偏差
    
    Args:
        skills: スキル値のリスト
    
    Returns:
        偏差値のリスト
    """
    skills_array = np.array(skills)
    mean = np.mean(skills_array)
    std = np.std(skills_array)
    
    if std == 0:
        # 標準偏差が0の場合（全馬同じスキル）
        return [50.0] * len(skills)
    
    deviations = 50.0 + 10.0 * (skills_array - mean) / std
    return deviations.tolist()

def get_race_recommendation(top_deviation: float) -> tuple:
    """
    1位馬の偏差値からレース全体の推奨度を取得（★5段階評価）
    
    Args:
        top_deviation: 1位馬の偏差値
    
    Returns:
        (推奨度, 説明文) のタプル
    """
    if top_deviation >= 70:
        return '★★★★★', '本命が圧倒的で非常に予想しやすいレースです'
    elif top_deviation >= 65:
        return '★★★★☆', '本命が明確で予想しやすいレースです'
    elif top_deviation >= 60:
        return '★★★☆☆', '本命が有力で信頼できるレースです'
    elif top_deviation >= 55:
        return '★★☆☆☆', '混戦模様ですが予想可能なレースです'
    elif top_deviation >= 50:
        return '★☆☆☆☆', '大混戦で予想が難しいレースです'
    else:
        return '☆☆☆☆☆', '超混戦で要注意のレースです'

# =====================================================================
# 予測モデル（predict_daily_standalone.py と同じ）
# =====================================================================

class EOIPLPredictor:
    """EOI-PL v1.0-Prime 予測モデル"""
    
    def __init__(self, feature_db_path: str):
        with open(feature_db_path, 'r', encoding='utf-8') as f:
            self.feature_db = json.load(f)
    
    def calculate_horse_skill(self, ketto: str) -> float:
        if ketto in self.feature_db['horses']:
            return -np.log(max(self.feature_db['horses'][ketto]['avg_rank'], 1.0))
        return -np.log(10.0)
    
    def calculate_jockey_skill(self, kishu_code: int) -> float:
        kishu_key = str(kishu_code)
        if kishu_key in self.feature_db['jockeys']:
            return -np.log(max(self.feature_db['jockeys'][kishu_key]['avg_rank'], 1.0))
        return -np.log(8.0)
    
    def calculate_trainer_skill(self, chokyoshi_code: int) -> float:
        trainer_key = str(chokyoshi_code)
        if trainer_key in self.feature_db['trainers']:
            return -np.log(max(self.feature_db['trainers'][trainer_key]['avg_rank'], 1.0))
        return -np.log(8.0)
    
    def calculate_corner_skill(self, ketto: str) -> float:
        if ketto in self.feature_db['horses']:
            avg_corner = self.feature_db['horses'][ketto].get('avg_corner')
            if avg_corner is not None:
                return -np.log(max(avg_corner, 1.0))
        return 0.0
    
    def calculate_time_skill(self, ketto: str, kyori: int) -> float:
        if ketto not in self.feature_db['horses']:
            return 0.0
        avg_time = self.feature_db['horses'][ketto].get('avg_time')
        if avg_time is None or kyori is None or kyori == 0:
            return 0.0
        if kyori in DISTANCE_BENCHMARKS:
            baseline, stddev = DISTANCE_BENCHMARKS[kyori]
        else:
            closest = min(DISTANCE_BENCHMARKS.keys(), key=lambda x: abs(x - kyori))
            baseline, stddev = DISTANCE_BENCHMARKS[closest]
        z_score = (baseline - avg_time) / stddev
        return max(min(z_score * 0.5, 2.0), -2.0)
    
    def calculate_distance_adaptation(self, ketto: str, kyori: int) -> float:
        if ketto not in self.feature_db.get('distance_adaptation', {}):
            return 0.0
        distance_data = self.feature_db['distance_adaptation'][ketto]
        kyori_key = str(kyori)
        if kyori_key in distance_data:
            return distance_data[kyori_key]
        available = [int(k) for k in distance_data.keys()]
        if not available:
            return 0.0
        closest = min(available, key=lambda x: abs(x - kyori))
        return distance_data[str(closest)]
    
    def calculate_track_adaptation(self, ketto: str, track_code: int) -> float:
        if ketto not in self.feature_db.get('track_adaptation', {}):
            return 0.0
        track_data = self.feature_db['track_adaptation'][ketto]
        track_key = str(track_code)
        return track_data.get(track_key, 0.0)
    
    def predict_race(self, conn, race_id: str) -> List[Dict]:
        """レース予想を実行して全頭のデータを返す"""
        cur = conn.cursor()
        
        # レース情報を取得
        cur.execute("""
            SELECT kyori, track_code, keibajo_code, race_bango
            FROM races
            WHERE race_id = %s
        """, (race_id,))
        
        race_info = cur.fetchone()
        if not race_info:
            cur.close()
            return []
        
        kyori, track_code, keibajo_code, race_bango = race_info
        
        # 出走馬情報を取得
        cur.execute("""
            SELECT umaban, bamei, ketto_toroku_bango, kishu_code, chokyoshi_code
            FROM entries
            WHERE race_id = %s
            ORDER BY umaban
        """, (race_id,))
        
        entries = cur.fetchall()
        cur.close()
        
        if not entries:
            return []
        
        # 各馬のスキルを計算
        predictions = []
        for umaban, bamei, ketto, kishu, chokyoshi in entries:
            horse_skill = self.calculate_horse_skill(ketto)
            jockey_skill = self.calculate_jockey_skill(kishu) if kishu else -np.log(8.0)
            trainer_skill = self.calculate_trainer_skill(chokyoshi) if chokyoshi else -np.log(8.0)
            corner_skill = self.calculate_corner_skill(ketto)
            time_skill = self.calculate_time_skill(ketto, kyori) if kyori else 0.0
            distance_skill = self.calculate_distance_adaptation(ketto, kyori) if kyori else 0.0
            track_skill = self.calculate_track_adaptation(ketto, track_code) if track_code else 0.0
            
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
                'total_skill': total_skill,
                'keibajo_code': keibajo_code,
                'race_bango': race_bango
            })
        
        # 偏差値を計算
        skills = [p['total_skill'] for p in predictions]
        deviations = calculate_deviation_score(skills)
        
        # 偏差値を追加してスキル順にソート
        for i, pred in enumerate(predictions):
            pred['deviation'] = deviations[i]
        
        # スキル順（偏差値降順）にソート
        predictions.sort(key=lambda x: x['total_skill'], reverse=True)
        
        # 順位を追加
        for rank, pred in enumerate(predictions, 1):
            pred['rank'] = rank
        
        return predictions

# =====================================================================
# Discord & TXT フォーマット出力
# =====================================================================

def format_race_discord(predictions: List[Dict], race_id: str) -> str:
    """
    Discord形式で予想結果をフォーマット
    
    Args:
        predictions: 予想結果のリスト
        race_id: レースID
    
    Returns:
        Discord形式のテキスト
    """
    if not predictions:
        return f"⚠️ レース {race_id} の予想結果がありません"
    
    # ヘッダー情報
    keibajo_code = predictions[0]['keibajo_code']
    race_bango = predictions[0]['race_bango']
    venue_name = VENUE_NAMES.get(keibajo_code, str(keibajo_code))
    
    # 1位馬の偏差値からレース推奨度を取得
    top_deviation = predictions[0]['deviation']
    race_recommendation, race_comment = get_race_recommendation(top_deviation)
    
    # タイトル
    output = f"【{venue_name} {race_bango}R】  レース推奨度: {race_recommendation} (1位偏差値: {top_deviation:.1f})\n"
    output += "```\n"
    
    # テーブルヘッダー
    output += f"{'順位':<6}{'馬番':<6}{'馬名':<24}{'偏差値':<8}\n"
    output += "-" * 60 + "\n"
    
    # 各馬のデータ
    for pred in predictions:
        rank = pred['rank']
        umaban = pred['umaban']
        bamei = pred['bamei'][:20]  # 馬名は20文字まで
        deviation = pred['deviation']
        
        output += f"{rank:<6}{umaban}番{'':<4}{bamei:<24}{deviation:>5.1f}\n"
    
    output += "```\n"
    
    # 推奨買い目
    top3 = [str(p['umaban']) for p in predictions[:3]]
    top5 = [str(p['umaban']) for p in predictions[:5]]
    
    output += f"\n🎯 **推奨買い目**\n"
    output += f"  Top3: {', '.join(top3)}\n"
    output += f"  Top5: {', '.join(top5)}\n"
    
    # レース分析コメント
    output += f"\n💡 **レース分析**\n"
    output += f"  {race_comment}（推奨度: {race_recommendation}）\n"
    
    return output

def save_to_txt(content: str, output_path: str):
    """TXTファイルに保存（親ディレクトリを自動作成）"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 保存完了: {output_path}")

# =====================================================================
# メイン処理
# =====================================================================

def format_single_race(race_id: str, feature_db_path: str, output_path: str = None):
    """単一レースをフォーマット"""
    print(f"\n{'='*60}")
    print(f"🏇 レース予想: {race_id}")
    print(f"{'='*60}\n")
    
    predictor = EOIPLPredictor(feature_db_path)
    conn = psycopg2.connect(**DB_CONFIG)
    
    predictions = predictor.predict_race(conn, race_id)
    conn.close()
    
    if not predictions:
        print(f"⚠️ レース {race_id} が見つかりません")
        return
    
    # Discord形式で出力
    output_text = format_race_discord(predictions, race_id)
    
    # 画面に表示
    print(output_text)
    
    # TXTファイルに保存
    if output_path:
        save_to_txt(output_text, output_path)

def format_daily_races(date: str, feature_db_path: str, output_path: str = None):
    """1日分の全レースをフォーマット"""
    print(f"\n{'='*60}")
    print(f"📅 日次予想: {date}")
    print(f"{'='*60}\n")
    
    predictor = EOIPLPredictor(feature_db_path)
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    year = int(date[:4])
    month_day = int(date[4:8])
    
    cur.execute("""
        SELECT race_id
        FROM races
        WHERE kaisai_nen = %s AND kaisai_tsukihi = %s
        ORDER BY keibajo_code, race_bango
    """, (year, month_day))
    
    race_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    
    if not race_ids:
        print(f"⚠️ {date} のレースが見つかりません")
        conn.close()
        return
    
    print(f"🏇 対象レース: {len(race_ids)}レース\n")
    
    all_output = f"NAR AI予想 {date[:4]}/{date[4:6]}/{date[6:8]}\n\n"
    
    for race_id in race_ids:
        predictions = predictor.predict_race(conn, race_id)
        if predictions:
            all_output += format_race_discord(predictions, race_id)
            all_output += "\n" + "="*60 + "\n\n"
    
    conn.close()
    
    # 画面に表示
    print(all_output)
    
    # TXTファイルに保存
    if output_path:
        save_to_txt(all_output, output_path)

def main():
    parser = argparse.ArgumentParser(
        description='EOI-PL v1.0-Prime Discord & TXT出力',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--race-id', type=str, help='レースID（例: 202602014501）')
    parser.add_argument('--date', type=str, help='予想日（例: 20260201）')
    parser.add_argument('--output', type=str, help='出力TXTファイル名')
    parser.add_argument('--db', type=str, 
                       default='E:/eoi-pl/data/feature_database_2020_2025.json',
                       help='特徴量データベースのパス')
    
    args = parser.parse_args()
    
    if not Path(args.db).exists():
        print(f"❌ 特徴量データベースが見つかりません: {args.db}")
        sys.exit(1)
    
    if args.race_id:
        format_single_race(args.race_id, args.db, args.output)
    elif args.date:
        format_daily_races(args.date, args.db, args.output)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
