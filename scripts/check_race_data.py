#!/usr/bin/env python3
"""
データ確認スクリプト
2026/02/04のレースデータを確認
"""
import sys
import psycopg2
sys.path.append('E:/eoi-pl')

from api.config_windows import DB_CONFIG

def check_race_data():
    """2026/02/04のレースデータを確認"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("=" * 60)
    print("2026/02/04 のレースデータ確認")
    print("=" * 60)
    print()
    
    # 競馬場別レース数
    print("【競馬場別レース数】")
    cur.execute("""
        SELECT keibajo_code, COUNT(*) as race_count
        FROM races
        WHERE kaisai_nen = 2026 AND kaisai_tsukihi = 204
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
    
    print()
    print("-" * 60)
    print()
    
    # 詳細データ
    print("【詳細データ】")
    cur.execute("""
        SELECT kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, kyori, track_code
        FROM races
        WHERE kaisai_nen = 2026 AND kaisai_tsukihi = 204
        ORDER BY keibajo_code, race_bango
    """)
    
    rows = cur.fetchall()
    if rows:
        current_keibajo = None
        for row in rows:
            kaisai_nen, kaisai_tsukihi, keibajo, race_no, kyori, track = row
            if keibajo != current_keibajo:
                print(f"\n  🏇 {keibajo}")
                current_keibajo = keibajo
            print(f"    {race_no}R: {kyori}m ({track})")
    else:
        print("  ⚠️ データなし")
    
    print()
    print("=" * 60)
    print()
    
    # 出走馬データ確認
    print("【出走馬データ確認】")
    cur.execute("""
        SELECT r.keibajo_code, COUNT(DISTINCT e.race_id) as race_count, COUNT(*) as entry_count
        FROM races r
        LEFT JOIN entries e ON r.race_id = e.race_id
        WHERE r.kaisai_nen = 2026 AND r.kaisai_tsukihi = 204
        GROUP BY r.keibajo_code
        ORDER BY r.keibajo_code
    """)
    
    rows = cur.fetchall()
    if rows:
        for keibajo, race_count, entry_count in rows:
            print(f"  {keibajo}: {race_count}レース, {entry_count}頭")
    else:
        print("  ⚠️ データなし")
    
    print()
    print("=" * 60)
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    try:
        check_race_data()
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
