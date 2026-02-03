#!/usr/bin/env python3
"""
PC-KEIBAデータベーススキーマ確認
テーブル一覧とカラム情報を確認
"""
import psycopg2

# pckeiba データベース接続設定
PCKEIBA_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

def check_pckeiba_schema():
    """PC-KEIBAデータベースのスキーマを確認"""
    try:
        conn = psycopg2.connect(**PCKEIBA_CONFIG)
        cur = conn.cursor()
        
        print("=" * 60)
        print("PC-KEIBA データベーススキーマ確認")
        print("=" * 60)
        print()
        
        # テーブル一覧
        print("【テーブル一覧】")
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        if tables:
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("  ⚠️ テーブルなし")
        
        print()
        print("=" * 60)
        print()
        
        # 各テーブルのカラム情報
        for table in tables:
            table_name = table[0]
            print(f"【{table_name} テーブル】")
            
            # カラム一覧
            cur.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            
            columns = cur.fetchall()
            for col_name, col_type in columns:
                print(f"  {col_name}: {col_type}")
            
            # レコード数
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"\n  レコード数: {count:,}件")
            
            print()
            print("-" * 60)
            print()
        
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"❌ データベース接続エラー: {e}")
        print()
        print("【考えられる原因】")
        print("1. PostgreSQLが起動していない")
        print("2. データベース名が間違っている")
        print("3. パスワードが間違っている")
        print()
        print("【確認方法】")
        print("  psql -U postgres -l")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_pckeiba_schema()
