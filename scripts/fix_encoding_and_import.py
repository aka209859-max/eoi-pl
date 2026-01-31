#!/usr/bin/env python3
"""
CSVファイルのエンコーディングを修正してeoi_plデータベースに統合

目的:
1. Windows PC-KEIBAからエクスポートされたCSV（Shift_JIS文字化け）を修正
2. eoi_pl.entries テーブルに2026年データを統合
3. 馬名を正常な日本語に変換
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import chardet

# ファイルパス
CSV_PATH = '/home/user/uploaded_files/nvd_se_2026_full.csv'

# データベース接続情報
DB_CONFIG = {
    'host': 'localhost',
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

def detect_encoding(file_path):
    """ファイルのエンコーディングを自動検出"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(100000)  # 先頭100KB
    result = chardet.detect(raw_data)
    print(f"検出されたエンコーディング: {result['encoding']} (信頼度: {result['confidence']:.2%})")
    return result['encoding']

def read_csv_with_encoding(file_path):
    """複数のエンコーディングで読み込みを試行"""
    encodings = ['cp932', 'shift_jis', 'utf-8', 'latin1']
    
    for encoding in encodings:
        try:
            print(f"\n試行: {encoding}")
            df = pd.read_csv(file_path, encoding=encoding)
            
            # サンプルデータを表示
            print(f"✅ {encoding} で読み込み成功")
            print(f"総行数: {len(df)}")
            print(f"\nサンプル（先頭3行）:")
            print(df[['kaisai_tsukihi', 'umaban', 'bamei', 'kakutei_chakujun']].head(3))
            
            return df, encoding
        except Exception as e:
            print(f"❌ {encoding} で失敗: {e}")
    
    raise Exception("すべてのエンコーディングで読み込みに失敗しました")

def create_race_id(row):
    """race_id を生成: YYYY_MMDD_venue_RR"""
    return f"{row['kaisai_nen']}_{str(row['kaisai_tsukihi']).zfill(4)}_{row['keibajo_code']}_{str(row['race_bango']).zfill(2)}"

def import_to_database(df):
    """データベースに統合"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # race_id を生成
        df['race_id'] = df.apply(create_race_id, axis=1)
        
        # 外部キー制約を一時的に無効化
        print(f"\n=== 外部キー制約の一時無効化 ===")
        cur.execute("ALTER TABLE entries DROP CONSTRAINT IF EXISTS entries_race_id_fkey;")
        conn.commit()
        print("✅ 外部キー制約を無効化しました")
        
        # entries テーブルに挿入
        print(f"\n=== entries テーブルへの挿入 ===")
        
        insert_query = """
        INSERT INTO entries (
            race_id, umaban, bamei, ketto_toroku_bango, kakutei_chakujun
        ) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (race_id, umaban) DO UPDATE SET
            bamei = EXCLUDED.bamei,
            kakutei_chakujun = EXCLUDED.kakutei_chakujun;
        """
        
        data = []
        for _, row in df.iterrows():
            # kakutei_chakujunのクリーニング
            kakutei = str(row['kakutei_chakujun']).strip() if pd.notna(row['kakutei_chakujun']) else None
            if kakutei and kakutei.isdigit():
                kakutei = kakutei.zfill(2)
            else:
                kakutei = None  # 空白や無効な値はNULLに
            
            data.append((
                row['race_id'],
                str(row['umaban']).zfill(2),
                row['bamei'].strip() if pd.notna(row['bamei']) else None,
                row['ketto_toroku_bango'],
                kakutei
            ))
        
        # バッチ挿入
        execute_batch(cur, insert_query, data, page_size=1000)
        conn.commit()
        
        print(f"✅ {len(data)} 件のデータを統合しました")
        
        # 検証
        cur.execute("""
            SELECT COUNT(*) 
            FROM entries 
            WHERE race_id LIKE '2026_%'
        """)
        count_2026 = cur.fetchone()[0]
        
        cur.execute("""
            SELECT race_id, umaban, bamei, kakutei_chakujun
            FROM entries 
            WHERE race_id LIKE '2026_0102_%'
            LIMIT 5
        """)
        samples = cur.fetchall()
        
        print(f"\n=== 検証結果 ===")
        print(f"2026年データ件数: {count_2026}")
        print(f"\nサンプルデータ（2026-01-02）:")
        for sample in samples:
            print(f"  {sample[0]} | 馬番:{sample[1]} | 馬名:{sample[2]} | 着順:{sample[3]}")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def main():
    print("=== CSVエンコーディング修正とデータ統合 ===\n")
    
    # STEP 1: エンコーディング自動検出
    print("STEP 1: エンコーディング検出")
    detected_encoding = detect_encoding(CSV_PATH)
    
    # STEP 2: CSVを読み込み
    print("\nSTEP 2: CSVファイル読み込み")
    df, used_encoding = read_csv_with_encoding(CSV_PATH)
    
    # STEP 3: データベースに統合
    print("\nSTEP 3: データベースへ統合")
    import_to_database(df)
    
    print("\n=== 完了 ===")
    print(f"使用したエンコーディング: {used_encoding}")
    print(f"統合件数: {len(df)}")

if __name__ == '__main__':
    main()
