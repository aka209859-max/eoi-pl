#!/usr/bin/env python3
"""
PC-KEIBA 最近取得したデータ確認スクリプト
作成日: 2026-02-04
目的: PC-KEIBAデータベースで最近取得したデータを確認
"""

import psycopg2
from datetime import datetime

# PC-KEIBAデータベース接続設定
PCKEIBA_DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

# 競馬場コード
VENUE_NAMES = {
    '30': '門別', '35': '盛岡', '36': '水沢',
    '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
    '46': '金沢', '47': '笠松', '48': '名古屋',
    '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
}

def check_recent_data():
    """PC-KEIBAで最近取得したデータを確認"""
    
    print("\n" + "="*80)
    print("PC-KEIBA 最近取得したデータ確認")
    print("="*80 + "\n")
    
    try:
        conn = psycopg2.connect(**PCKEIBA_DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. nvd_raテーブルの最新データを確認
        print("【1】nvd_ra (レース基本情報) の最新データ\n")
        
        query = """
        SELECT 
            kaisai_nen,
            kaisai_tsukihi,
            keibajo_code,
            COUNT(*) as race_count
        FROM nvd_ra
        WHERE kaisai_nen = '2026'
        GROUP BY kaisai_nen, kaisai_tsukihi, keibajo_code
        ORDER BY kaisai_tsukihi DESC, keibajo_code
        LIMIT 50;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if results:
            print("最近のレースデータ:")
            print("-" * 80)
            current_date = None
            for kaisai_nen, kaisai_tsukihi, keibajo_code, race_count in results:
                date_str = f"{kaisai_nen}/{kaisai_tsukihi}"
                venue_name = VENUE_NAMES.get(keibajo_code, f"不明({keibajo_code})")
                
                if current_date != date_str:
                    print(f"\n{date_str}")
                    current_date = date_str
                
                print(f"  {venue_name} ({keibajo_code}): {race_count}R")
        else:
            print("❌ 2026年のデータが見つかりません")
        
        print("\n" + "-" * 80)
        
        # 2. 2026年2月のデータを全て表示
        print("\n【2】2026年2月の全開催データ\n")
        
        query = """
        SELECT 
            kaisai_tsukihi,
            keibajo_code,
            COUNT(*) as race_count
        FROM nvd_ra
        WHERE kaisai_nen = '2026' 
          AND kaisai_tsukihi LIKE '02%'
        GROUP BY kaisai_tsukihi, keibajo_code
        ORDER BY kaisai_tsukihi, keibajo_code;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if results:
            print("2026年2月の開催:")
            print("-" * 80)
            current_date = None
            for kaisai_tsukihi, keibajo_code, race_count in results:
                date_str = f"2026/{kaisai_tsukihi}"
                venue_name = VENUE_NAMES.get(keibajo_code, f"不明({keibajo_code})")
                
                if current_date != date_str:
                    print(f"\n{date_str}")
                    current_date = date_str
                
                print(f"  {venue_name} ({keibajo_code}): {race_count}R")
        else:
            print("❌ 2026年2月のデータが見つかりません")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        
        # 判定
        has_kawasaki = any(row[1] == '45' and row[0] == '0204' for row in results if len(row) >= 2)
        has_kasamatsu = any(row[1] == '47' and row[0] == '0204' for row in results if len(row) >= 2)
        
        if has_kawasaki and has_kasamatsu:
            print("\n✅ 川崎・笠松のデータがあります！")
        elif has_kawasaki:
            print("\n⚠️ 川崎のデータはありますが、笠松がありません")
        elif has_kasamatsu:
            print("\n⚠️ 笠松のデータはありますが、川崎がありません")
        else:
            print("\n❌ 川崎・笠松のデータがありません")
            print("\n【対処法】")
            print("1. PC-KEIBAを起動")
            print("2. データ取得が正常に完了したか確認")
            print("3. 地方競馬DATAの設定を確認")
            print("   - 競馬場: 全場選択されているか")
            print("   - 日付: 2026/02/04が含まれているか")
            print("4. 再度データ取得を実行")
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recent_data()
