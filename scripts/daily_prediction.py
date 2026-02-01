#!/usr/bin/env python3
"""
EOI-PL 日次予想生成スクリプト（Windows用）

【使い方】
  # 今日の予想を自動生成
  python daily_prediction.py
  
  # 特定の日付を指定
  python daily_prediction.py --date 20260202
  
  # 出力先を指定
  python daily_prediction.py --output E:\eoi-pl\predictions\predictions_today.txt
"""

import psycopg2
import json
import numpy as np
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

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

# 特徴量データベースのデフォルトパス（Windows環境）
DEFAULT_FEATURE_DB_PATH = 'E:/eoi-pl/data/feature_database_2020_2025.json'

# 予想結果のデフォルト出力先（Windows環境）
DEFAULT_OUTPUT_DIR = 'E:/eoi-pl/predictions'

# 重み付け設定
WEIGHTS = {
    'avg_rank': 0.30, 'jockey': 0.15, 'trainer': 0.10,
    'corner': 0.15, 'time': 0.15, 'distance': 0.10, 'track': 0.05
}

# NAR競馬場コード（地方競馬）
NAR_VENUES = [30, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55]

# 競馬場名マッピング
VENUE_NAMES = {
    30: '門別', 35: '盛岡', 36: '水沢', 42: '浦和', 43: '船橋', 44: '大井', 45: '川崎',
    46: '金沢', 47: '笠松', 48: '名古屋', 50: '園田', 51: '姫路', 54: '高知', 55: '佐賀'
}

# =====================================================================
# 今日の日付を取得
# =====================================================================

def get_today_date() -> str:
    """
    今日の日付を YYYYMMDD 形式で取得
    
    Returns:
        今日の日付文字列（例: '20260202'）
    """
    today = datetime.now()
    return today.strftime('%Y%m%d')

# =====================================================================
# メイン処理
# =====================================================================

def main():
    """
    メイン処理
    """
    parser = argparse.ArgumentParser(
        description='EOI-PL 日次予想生成スクリプト（Windows用）',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--date', type=str, 
                       help='予想日（例: 20260202）省略時は今日の日付')
    parser.add_argument('--output', type=str, 
                       help='出力ファイルパス（省略時は自動生成）')
    parser.add_argument('--db', type=str, 
                       default=DEFAULT_FEATURE_DB_PATH,
                       help=f'特徴量データベースのパス（デフォルト: {DEFAULT_FEATURE_DB_PATH}）')
    
    args = parser.parse_args()
    
    # 日付の決定（省略時は今日）
    target_date = args.date if args.date else get_today_date()
    
    # 出力先の決定
    if args.output:
        output_path = args.output
    else:
        # デフォルト: E:\eoi-pl\predictions\predictions_YYYYMMDD.txt
        output_dir = Path(DEFAULT_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"predictions_{target_date}.txt"
    
    # 特徴量データベースの存在確認
    if not Path(args.db).exists():
        print(f"❌ 特徴量データベースが見つかりません: {args.db}")
        print(f"")
        print(f"【対処方法】")
        print(f"1. E:\\eoi-pl\\data\\feature_database_2020_2025.json が存在するか確認")
        print(f"2. --db オプションで正しいパスを指定")
        sys.exit(1)
    
    # format_predictions_discord.py を呼び出し
    print(f"")
    print(f"=" * 60)
    print(f"📅 日次予想生成: {target_date}")
    print(f"=" * 60)
    print(f"")
    print(f"📂 出力先: {output_path}")
    print(f"💾 データベース: {args.db}")
    print(f"")
    
    # format_predictions_discord.py のインポートと実行
    import format_predictions_discord as fpd
    
    try:
        # 予想生成
        fpd.format_daily_races(target_date, args.db, str(output_path))
        
        print(f"")
        print(f"=" * 60)
        print(f"✅ 予想生成完了！")
        print(f"=" * 60)
        print(f"")
        print(f"📄 予想ファイル: {output_path}")
        print(f"")
        print(f"【次のステップ】")
        print(f"1. メモ帳で {output_path} を開く")
        print(f"2. ★★★★★/★★★★☆ のレースを検索（Ctrl+F）")
        print(f"3. 該当レースをDiscordに投稿")
        print(f"")
        
    except Exception as e:
        print(f"")
        print(f"❌ 予想生成エラー: {e}")
        print(f"")
        print(f"【トラブルシューティング】")
        print(f"1. PostgreSQLが起動しているか確認")
        print(f"   - Windowsサービスで 'postgresql-x64-15' を確認")
        print(f"2. データベース接続設定を確認")
        print(f"   - ホスト: {DB_CONFIG['host']}")
        print(f"   - ポート: {DB_CONFIG['port']}")
        print(f"   - データベース: {DB_CONFIG['database']}")
        print(f"3. {target_date} のレースがデータベースに存在するか確認")
        print(f"")
        sys.exit(1)

if __name__ == '__main__':
    main()
