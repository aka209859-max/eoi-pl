#!/usr/bin/env python3
"""
PC-KEIBA CSV → PostgreSQL インポートスクリプト

CSVファイルをPostgreSQLデータベースにインポートします。
"""

import psycopg2
import pandas as pd
import sys
from pathlib import Path

# =====================================================================
# 設定
# =====================================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',  # 最初は postgres データベースに接続
    'user': 'postgres',
    'password': 'postgres123'
}

CSV_DIR = r"C:\Users\ihaji\OneDrive\デスクトップ\pc_keiba_2020_2025\pc_keiba_2020_2025"
RACES_CSV = "races_2020_2025.csv"
ENTRIES_CSV = "entries_results_2020_2025.csv"

# =====================================================================
# データベース作成
# =====================================================================

def create_database():
    """eoi_pl データベースを作成"""
    print("📊 データベース eoi_pl を作成中...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        
        # 既存のデータベースを削除（確認）
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'eoi_pl'")
        if cur.fetchone():
            print("⚠️ データベース eoi_pl が既に存在します")
            response = input("削除して再作成しますか？ (y/n): ")
            if response.lower() == 'y':
                cur.execute("DROP DATABASE eoi_pl")
                print("✅ 既存のデータベースを削除しました")
            else:
                print("❌ 処理を中止しました")
                sys.exit(1)
        
        # データベース作成
        cur.execute("CREATE DATABASE eoi_pl")
        print("✅ データベース eoi_pl を作成しました")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

# =====================================================================
# テーブル作成
# =====================================================================

def create_tables():
    """races と entries テーブルを作成"""
    print("📊 テーブルを作成中...")
    
    # eoi_pl データベースに接続
    db_config = DB_CONFIG.copy()
    db_config['database'] = 'eoi_pl'
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # races テーブル
        cur.execute("""
            CREATE TABLE IF NOT EXISTS races (
                race_id VARCHAR(20) PRIMARY KEY,
                kaisai_nen INTEGER,
                kaisai_tsukihi INTEGER,
                keibajo_code INTEGER,
                race_bango INTEGER,
                kyori INTEGER,
                track_code INTEGER
            )
        """)
        print("✅ races テーブルを作成しました")
        
        # entries テーブル
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                race_id VARCHAR(20),
                umaban INTEGER,
                bamei VARCHAR(100),
                ketto_toroku_bango VARCHAR(20),
                kishu_code INTEGER,
                chokyoshi_code INTEGER,
                kakutei_chakujun INTEGER,
                data_kubun VARCHAR(10),
                soha_time NUMERIC,
                corner_tsuuka_jun VARCHAR(100),
                PRIMARY KEY (race_id, umaban)
            )
        """)
        print("✅ entries テーブルを作成しました")
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

# =====================================================================
# CSVインポート
# =====================================================================

def import_races_csv():
    """races CSVをインポート"""
    print(f"📥 {RACES_CSV} をインポート中...")
    
    csv_path = Path(CSV_DIR) / RACES_CSV
    if not csv_path.exists():
        print(f"❌ ファイルが見つかりません: {csv_path}")
        sys.exit(1)
    
    # CSVを読み込み
    df = pd.read_csv(csv_path, encoding='utf-8')
    print(f"📊 レコード数: {len(df)}")
    
    # race_id を生成
    # race_id = kaisai_nen(4桁) + kaisai_tsukihi(4桁) + keibajo_code(2桁) + race_bango(2桁)
    df['race_id'] = (
        df['kaisai_nen'].astype(str) + 
        df['kaisai_tsukihi'].astype(str).str.zfill(4) + 
        df['keibajo_code'].astype(str).str.zfill(2) + 
        df['race_bango'].astype(str).str.zfill(2)
    )
    print(f"✅ race_id を生成しました（例: {df['race_id'].iloc[0]}）")
    
    # eoi_pl データベースに接続
    db_config = DB_CONFIG.copy()
    db_config['database'] = 'eoi_pl'
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # データを挿入
        for index, row in df.iterrows():
            cur.execute("""
                INSERT INTO races (race_id, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, kyori, track_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (race_id) DO NOTHING
            """, (
                row['race_id'],
                row['kaisai_nen'],
                row['kaisai_tsukihi'],
                row['keibajo_code'],
                row['race_bango'],
                row.get('kyori'),
                row.get('track_code')
            ))
            
            if (index + 1) % 1000 == 0:
                print(f"  {index + 1}/{len(df)} レコード処理完了...")
        
        conn.commit()
        print(f"✅ {len(df)} レコードをインポートしました")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

def import_entries_csv():
    """entries CSVをインポート"""
    print(f"📥 {ENTRIES_CSV} をインポート中...")
    
    csv_path = Path(CSV_DIR) / ENTRIES_CSV
    if not csv_path.exists():
        print(f"❌ ファイルが見つかりません: {csv_path}")
        sys.exit(1)
    
    # CSVを読み込み
    df = pd.read_csv(csv_path, encoding='utf-8')
    print(f"📊 レコード数: {len(df)}")
    
    # race_id を生成
    df['race_id'] = (
        df['kaisai_nen'].astype(str) + 
        df['kaisai_tsukihi'].astype(str).str.zfill(4) + 
        df['keibajo_code'].astype(str).str.zfill(2) + 
        df['race_bango'].astype(str).str.zfill(2)
    )
    print(f"✅ race_id を生成しました")
    
    # corner_tsuuka_jun を生成（corner_1, corner_2, corner_3, corner_4 を結合）
    # 例: corner_1=3, corner_2=4, corner_3=5, corner_4=6 → "3-4-5-6"
    def combine_corners(row):
        corners = []
        for i in range(1, 5):
            col = f'corner_{i}'
            if col in row and pd.notna(row[col]):
                corners.append(str(int(row[col])))
        return '-'.join(corners) if corners else None
    
    df['corner_tsuuka_jun'] = df.apply(combine_corners, axis=1)
    
    # data_kubun を設定（確定着順がある場合は '7'）
    df['data_kubun'] = df['kakutei_chakujun'].apply(lambda x: '7' if pd.notna(x) else None)
    
    # eoi_pl データベースに接続
    db_config = DB_CONFIG.copy()
    db_config['database'] = 'eoi_pl'
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # データを挿入
        for index, row in df.iterrows():
            cur.execute("""
                INSERT INTO entries (race_id, umaban, bamei, ketto_toroku_bango, kishu_code, chokyoshi_code, 
                                   kakutei_chakujun, data_kubun, soha_time, corner_tsuuka_jun)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (race_id, umaban) DO NOTHING
            """, (
                row['race_id'],
                row['umaban'],
                row['bamei'],
                row['ketto_toroku_bango'],
                row.get('kishu_code'),
                row.get('chokyoshi_code'),
                row.get('kakutei_chakujun'),
                row.get('data_kubun'),
                row.get('soha_time'),
                row.get('corner_tsuuka_jun')
            ))
            
            if (index + 1) % 5000 == 0:
                print(f"  {index + 1}/{len(df)} レコード処理完了...")
        
        conn.commit()
        print(f"✅ {len(df)} レコードをインポートしました")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

# =====================================================================
# メイン処理
# =====================================================================

def main():
    print("="*60)
    print("🏇 PC-KEIBA CSV → PostgreSQL インポート")
    print("="*60)
    print()
    
    # Step 1: データベース作成
    create_database()
    print()
    
    # Step 2: テーブル作成
    create_tables()
    print()
    
    # Step 3: races CSV をインポート
    import_races_csv()
    print()
    
    # Step 4: entries CSV をインポート
    import_entries_csv()
    print()
    
    print("="*60)
    print("🎉 インポート完了！")
    print("="*60)
    print()
    print("次のコマンドで確認:")
    print('  psql -U postgres -d eoi_pl -c "SELECT COUNT(*) FROM races;"')
    print('  psql -U postgres -d eoi_pl -c "SELECT COUNT(*) FROM entries;"')
    print()

if __name__ == '__main__':
    main()
