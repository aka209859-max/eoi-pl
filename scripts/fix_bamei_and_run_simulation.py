#!/usr/bin/env python3
"""
馬名マッピングの文字化け修正とシミュレーション実行

1. bamei_mapping.csv を Shift_JIS で読み込み
2. bamei カラムを UTF-8 に変換
3. entries テーブルの bamei を更新
4. 2026年1月のバックテスト実行
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# ファイルパス
BAMEI_CSV = '/home/user/uploaded_files/bamei_mapping.csv'

# データベース接続情報
DB_CONFIG = {
    'host': 'localhost',
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

def load_bamei_mapping():
    """馬名マッピングを読み込み"""
    print("=== 馬名マッピング読み込み ===")
    
    # Shift_JIS で読み込み
    df = pd.read_csv(BAMEI_CSV, encoding='cp932')
    
    print(f"総件数: {len(df)}")
    print(f"\nサンプル（先頭5件）:")
    print(df.head())
    
    return df

def update_bamei_in_database(df):
    """データベースの bamei カラムを更新"""
    print("\n=== bamei カラムの更新 ===")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        update_query = """
        UPDATE entries 
        SET bamei = %s
        WHERE ketto_toroku_bango = %s
        """
        
        data = [(row['bamei'].strip(), str(row['ketto_toroku_bango'])) 
                for _, row in df.iterrows()]
        
        execute_batch(cur, update_query, data, page_size=1000)
        conn.commit()
        
        print(f"✅ {len(data)} 件の馬名を更新しました")
        
        # 検証
        cur.execute("""
            SELECT ketto_toroku_bango, bamei 
            FROM entries 
            WHERE race_id LIKE '2026_0102_%'
            LIMIT 10
        """)
        samples = cur.fetchall()
        
        print(f"\n検証サンプル（2026-01-02）:")
        for sample in samples:
            print(f"  血統番号: {sample[0]} | 馬名: {sample[1]}")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def verify_data():
    """データ完全性を検証"""
    print("\n=== データ検証 ===")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # 2026年データ統計
        cur.execute("""
            SELECT 
                COUNT(*) as total_entries,
                COUNT(DISTINCT race_id) as unique_races,
                MIN(race_id) as earliest,
                MAX(race_id) as latest,
                COUNT(CASE WHEN kakutei_chakujun IS NOT NULL THEN 1 END) as with_result,
                COUNT(CASE WHEN bamei IS NOT NULL THEN 1 END) as with_bamei
            FROM entries 
            WHERE race_id LIKE '2026_%'
        """)
        stats = cur.fetchone()
        
        print(f"総エントリー数: {stats[0]}")
        print(f"ユニークレース数: {stats[1]}")
        print(f"期間: {stats[2]} ～ {stats[3]}")
        print(f"確定着順あり: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
        print(f"馬名あり: {stats[5]} ({stats[5]/stats[0]*100:.1f}%)")
        
        return stats[0], stats[1]
        
    finally:
        cur.close()
        conn.close()

def main():
    print("=" * 60)
    print("馬名文字化け修正とデータ検証")
    print("=" * 60)
    
    # STEP 1: 馬名マッピング読み込み
    df = load_bamei_mapping()
    
    # STEP 2: データベース更新
    update_bamei_in_database(df)
    
    # STEP 3: データ検証
    total_entries, unique_races = verify_data()
    
    print("\n" + "=" * 60)
    print("完了")
    print("=" * 60)
    print(f"馬名更新: {len(df)} 件")
    print(f"2026年データ: {total_entries} エントリー, {unique_races} レース")
    print("\n次のステップ: シミュレーション実行")
    print("  cd /home/user/eoi-pl")
    print("  python3 scripts/walkforward_backtest.py --start-date 2026-01-02 --end-date 2026-01-30")

if __name__ == '__main__':
    main()
