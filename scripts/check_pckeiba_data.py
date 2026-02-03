#!/usr/bin/env python3
"""
PC-KEIBAデータベース確認スクリプト
2026/02/04のレースデータを確認
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

def check_pckeiba_data():
    """PC-KEIBAデータベースを確認"""
    conn = psycopg2.connect(**PCKEIBA_CONFIG)
    cur = conn.cursor()
    
    print("=" * 60)
    print("PC-KEIBA データベース確認（2026/02/04）")
    print("=" * 60)
    print()
    
    # 競馬場別レース数
    print("【PC-KEIBAデータベース】")
    cur.execute("""
        SELECT keibajo_code, COUNT(*) as race_count
        FROM races
        WHERE year = 2026 AND month = 2 AND day = 4
        GROUP BY keibajo_code
        ORDER BY keibajo_code
    """)
    
    rows = cur.fetchall()
    if rows:
        total = 0
        for keibajo, count in rows:
            print(f"  {keibajo}: {count}R")
            total += count
        print(f"\n  合計: {total}R")
    else:
        print("  ⚠️ データなし")
        print("\n  【原因】")
        print("  1. PC-KEIBAでデータ取得されていない")
        print("  2. UmaConnでデータ取得を実行してください")
    
    print()
    print("=" * 60)
    print()
    
    # eoi_plとの比較
    print("【eoi_plデータベース】")
    conn2 = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='eoi_pl',
        user='postgres',
        password='postgres123'
    )
    cur2 = conn2.cursor()
    
    cur2.execute("""
        SELECT keibajo_code, COUNT(*) as race_count
        FROM races
        WHERE kaisai_nen = 2026 AND kaisai_tsukihi = 204
        GROUP BY keibajo_code
        ORDER BY keibajo_code
    """)
    
    rows2 = cur2.fetchall()
    if rows2:
        total2 = 0
        for keibajo, count in rows2:
            print(f"  {keibajo}: {count}R")
            total2 += count
        print(f"\n  合計: {total2}R")
    else:
        print("  ⚠️ データなし")
    
    print()
    print("=" * 60)
    print()
    
    # 比較結果
    if rows and rows2:
        pckeiba_total = sum([r[1] for r in rows])
        eoipl_total = sum([r[1] for r in rows2])
        
        if pckeiba_total == eoipl_total:
            print("✅ データ同期完了")
        else:
            print(f"⚠️ データ不一致")
            print(f"  PC-KEIBA: {pckeiba_total}R")
            print(f"  eoi_pl:   {eoipl_total}R")
            print()
            print("【対処法】")
            print("  python scripts\\import_from_pckeiba_to_eoi_pl.py")
    elif rows and not rows2:
        print("⚠️ eoi_plにデータなし")
        print()
        print("【対処法】")
        print("  python scripts\\import_from_pckeiba_to_eoi_pl.py")
    elif not rows:
        print("⚠️ PC-KEIBAにデータなし")
        print()
        print("【対処法】")
        print("  1. PC-KEIBAを起動")
        print("  2. UmaConnでデータ取得")
        print("  3. python scripts\\import_from_pckeiba_to_eoi_pl.py")
    
    print()
    print("=" * 60)
    
    cur.close()
    conn.close()
    cur2.close()
    conn2.close()

if __name__ == '__main__':
    try:
        check_pckeiba_data()
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
