#!/usr/bin/env python3
"""
2026年1月のレース結果データをeoi_plデータベースにインポートするスクリプト

入力: race_results_2026_01.csv
出力: races, entries テーブルへの挿入
"""

import psycopg2
import csv
import sys
from datetime import datetime

# データベース接続設定
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

def connect_db():
    """データベースに接続"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        sys.exit(1)

def import_csv_data(csv_path):
    """CSVデータをインポート"""
    conn = connect_db()
    cur = conn.cursor()
    
    # トランザクション開始
    conn.autocommit = False
    
    try:
        # CSVファイルを読み込み
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            race_count = 0
            entry_count = 0
            race_cache = set()
            
            for row in reader:
                # データを整形
                kaisai_nen = int(row['kaisai_nen'])
                kaisai_tsukihi = int(row['kaisai_tsukihi'])
                keibajo_code = int(row['keibajo_code'])
                race_bango = int(row['race_bango'])
                umaban = int(row['umaban'])
                ketto_toroku_bango = row['ketto_toroku_bango']
                bamei = row['bamei'].strip()  # 馬名の空白を削除
                kakutei_chakujun = int(row['kakutei_chakujun']) if row['kakutei_chakujun'] and row['kakutei_chakujun'] != '00' else None
                
                # race_id を生成
                race_id = f"{kaisai_nen}{kaisai_tsukihi:04d}{keibajo_code:02d}{race_bango:02d}"
                
                # races テーブルに挿入（重複回避）
                if race_id not in race_cache:
                    cur.execute("""
                        INSERT INTO races (race_id, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (race_id) DO NOTHING
                    """, (race_id, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango))
                    race_cache.add(race_id)
                    race_count += 1
                
                # entries テーブルに挿入
                cur.execute("""
                    INSERT INTO entries (race_id, umaban, bamei, ketto_toroku_bango, kakutei_chakujun)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (race_id, umaban) DO UPDATE
                    SET kakutei_chakujun = EXCLUDED.kakutei_chakujun,
                        bamei = EXCLUDED.bamei,
                        ketto_toroku_bango = EXCLUDED.ketto_toroku_bango
                """, (race_id, umaban, bamei, ketto_toroku_bango, kakutei_chakujun))
                entry_count += 1
        
        # コミット
        conn.commit()
        
        print(f"✅ インポート完了:")
        print(f"   - レース数: {race_count}")
        print(f"   - エントリー数: {entry_count}")
        
        # 確認クエリ
        cur.execute("SELECT COUNT(*) FROM races WHERE kaisai_nen = 2026")
        race_total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM entries WHERE race_id LIKE '2026%'")
        entry_total = cur.fetchone()[0]
        
        print(f"\n📊 データベース確認:")
        print(f"   - 2026年レース総数: {race_total}")
        print(f"   - 2026年エントリー総数: {entry_total}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ インポートエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    csv_path = '/home/user/uploaded_files/race_results_2026_01.csv'
    print(f"📂 CSVファイル: {csv_path}")
    print(f"🔄 インポート開始...")
    import_csv_data(csv_path)
    print(f"🎉 完了！")
