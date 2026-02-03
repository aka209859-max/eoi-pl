#!/usr/bin/env python3
"""
PC-KEIBA nvd_raテーブルのカラム確認スクリプト
作成日: 2026-02-04
"""

import psycopg2

# PC-KEIBAデータベース接続設定
PCKEIBA_DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

def check_nvd_ra_columns():
    """nvd_raテーブルのカラム情報を確認"""
    
    print("\n" + "="*80)
    print("nvd_ra テーブルのカラム確認")
    print("="*80 + "\n")
    
    try:
        conn = psycopg2.connect(**PCKEIBA_DB_CONFIG)
        cursor = conn.cursor()
        
        # カラム情報を取得
        query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'nvd_ra'
        ORDER BY ordinal_position;
        """
        
        cursor.execute(query)
        columns = cursor.fetchall()
        
        print("カラム一覧:")
        print("-" * 80)
        for col_name, data_type, max_length in columns:
            if max_length:
                print(f"  {col_name:<30} {data_type}({max_length})")
            else:
                print(f"  {col_name:<30} {data_type}")
        
        print("\n" + "-" * 80)
        
        # サンプルデータを取得（最新5件）
        print("\nサンプルデータ（最新5件）:")
        print("-" * 80)
        
        cursor.execute("SELECT * FROM nvd_ra ORDER BY id DESC LIMIT 5;")
        rows = cursor.fetchall()
        
        # カラム名を取得
        col_names = [desc[0] for desc in cursor.description]
        
        for row in rows:
            print("\n")
            for col_name, value in zip(col_names, row):
                print(f"  {col_name}: {value}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_nvd_ra_columns()
