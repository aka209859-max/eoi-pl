#!/usr/bin/env python3
"""
CSVデータをPostgreSQLへインポート
- races_2020_2025.csv → races table
- entries_results_2020_2025.csv → entries table
- race_id生成（結合キー統一）
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm
import sys

def create_race_id(row):
    """race_id生成: YYYY_MMDD_venue_RR"""
    return f"{row['kaisai_nen']}_{str(row['kaisai_tsukihi']).zfill(4)}_{row['keibajo_code']}_{str(row['race_bango']).zfill(2)}"

def import_races(csv_path, conn):
    """races.csvをインポート"""
    print(f"\n📥 Importing races from {csv_path}...")
    
    # CSV読み込み（全データ）
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  Total rows: {len(df):,}")
    
    # race_id生成
    df['race_id'] = df.apply(create_race_id, axis=1)
    
    # データ準備
    records = df[[
        'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
        'race_bango', 'kyori', 'track_code', 'babajotai_code_dirt',
        'kyoso_joken_code', 'hassoujikoku', 'tosu'
    ]].to_dict('records')
    
    # バッチINSERT
    cursor = conn.cursor()
    insert_query = """
        INSERT INTO races (
            race_id, kaisai_nen, kaisai_tsukihi, keibajo_code, 
            race_bango, kyori, track_code, babajotai_code_dirt,
            kyoso_joken_code, hassoujikoku, tosu
        ) VALUES (
            %(race_id)s, %(kaisai_nen)s, %(kaisai_tsukihi)s, %(keibajo_code)s,
            %(race_bango)s, %(kyori)s, %(track_code)s, %(babajotai_code_dirt)s,
            %(kyoso_joken_code)s, %(hassoujikoku)s, %(tosu)s
        )
        ON CONFLICT (race_id) DO NOTHING
    """
    
    print("  Inserting rows...")
    execute_batch(cursor, insert_query, records, page_size=1000)
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM races")
    count = cursor.fetchone()[0]
    print(f"✅ Races imported: {count:,} rows")
    
    return count

def import_entries(csv_path, conn):
    """entries_results.csvをインポート"""
    print(f"\n📥 Importing entries from {csv_path}...")
    
    # CSV読み込み（チャンク処理 - メモリ節約）
    chunk_size = 50000
    total_imported = 0
    
    cursor = conn.cursor()
    insert_query = """
        INSERT INTO entries (
            race_id, umaban, bamei, wakuban, bataiju,
            kakutei_chakujun, soha_time, corner_1, corner_2,
            corner_3, corner_4, kohan_3f, ketto_toroku_bango,
            kishu_code, chokyoshi_code, fufu_ketto_toroku_bango
        ) VALUES (
            %(race_id)s, %(umaban)s, %(bamei)s, %(wakuban)s, %(bataiju)s,
            %(kakutei_chakujun)s, %(soha_time)s, %(corner_1)s, %(corner_2)s,
            %(corner_3)s, %(corner_4)s, %(kohan_3f)s, %(ketto_toroku_bango)s,
            %(kishu_code)s, %(chokyoshi_code)s, %(fufu_ketto_toroku_bango)s
        )
        ON CONFLICT (race_id, umaban) DO NOTHING
    """
    
    for chunk in tqdm(pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False)):
        # race_id生成
        chunk['race_id'] = chunk.apply(create_race_id, axis=1)
        
        # NaN を None に変換（PostgreSQL互換）
        chunk = chunk.where(pd.notnull(chunk), None)
        
        records = chunk[[
            'race_id', 'umaban', 'bamei', 'wakuban', 'bataiju',
            'kakutei_chakujun', 'soha_time', 'corner_1', 'corner_2',
            'corner_3', 'corner_4', 'kohan_3f', 'ketto_toroku_bango',
            'kishu_code', 'chokyoshi_code', 'fufu_ketto_toroku_bango'
        ]].to_dict('records')
        
        execute_batch(cursor, insert_query, records, page_size=1000)
        total_imported += len(records)
        conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM entries")
    count = cursor.fetchone()[0]
    print(f"\n✅ Entries imported: {count:,} rows")
    
    return count

def verify_data(conn):
    """データ検証"""
    print(f"\n{'='*60}")
    print("🔍 Data Verification")
    print(f"{'='*60}")
    
    cursor = conn.cursor()
    
    # レース数
    cursor.execute("SELECT COUNT(*) FROM races")
    races_count = cursor.fetchone()[0]
    print(f"  Total races: {races_count:,}")
    
    # エントリー数
    cursor.execute("SELECT COUNT(*) FROM entries")
    entries_count = cursor.fetchone()[0]
    print(f"  Total entries: {entries_count:,}")
    
    # 平均出走数
    cursor.execute("SELECT AVG(tosu) FROM races")
    avg_tosu = cursor.fetchone()[0]
    print(f"  Average horses per race: {avg_tosu:.2f}")
    
    # 期間
    cursor.execute("SELECT MIN(kaisai_nen), MAX(kaisai_nen) FROM races")
    min_year, max_year = cursor.fetchone()
    print(f"  Date range: {min_year} - {max_year}")
    
    # サンプルレース表示
    cursor.execute("""
        SELECT r.race_id, r.kyori, r.tosu, COUNT(e.entry_id) as actual_entries
        FROM races r
        LEFT JOIN entries e ON r.race_id = e.race_id
        GROUP BY r.race_id, r.kyori, r.tosu
        LIMIT 3
    """)
    
    print("\n  Sample races:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}m, expected={row[2]}, actual={row[3]}")
    
    print(f"\n✅ Data verification completed")

if __name__ == "__main__":
    # データベース接続
    conn = psycopg2.connect(
        host="localhost",
        database="eoi_pl",
        user="postgres",
        password="eoi_pl_dev"
    )
    
    try:
        # インポート実行
        races_path = "/home/user/uploaded_files/races_2020_2025.csv"
        entries_path = "/home/user/uploaded_files/entries_results_2020_2025.csv"
        
        import_races(races_path, conn)
        import_entries(entries_path, conn)
        
        # 検証
        verify_data(conn)
        
        print(f"\n{'='*60}")
        print("✅ ALL DATA IMPORTED SUCCESSFULLY")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        conn.rollback()
        raise
    finally:
        conn.close()
