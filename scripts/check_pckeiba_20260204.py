#!/usr/bin/env python3
"""
PC-KEIBA 2026/02/04データ確認スクリプト
作成日: 2026-02-04
目的: PC-KEIBAデータベースから2026/02/04のレースデータを確認
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

def check_pckeiba_data():
    """PC-KEIBAデータベースから2026/02/04のデータを確認"""
    
    print("\n" + "="*80)
    print("PC-KEIBA 2026/02/04 データ確認")
    print("="*80 + "\n")
    
    try:
        # PC-KEIBAデータベースに接続
        conn = psycopg2.connect(**PCKEIBA_DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. nvd_raテーブルから2026/02/04のレース数を確認
        print("【1】nvd_ra (レース基本情報) を確認\n")
        
        query = """
        SELECT 
            keibajo_code,
            COUNT(*) as race_count
        FROM nvd_ra
        WHERE kaisai_nen = '2026' 
          AND kaisai_tsukihi = '0204'
        GROUP BY keibajo_code
        ORDER BY keibajo_code;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if results:
            print("競馬場別レース数:")
            total_races = 0
            for keibajo_code, race_count in results:
                venue_name = VENUE_NAMES.get(keibajo_code, f"不明({keibajo_code})")
                print(f"  {venue_name} ({keibajo_code}): {race_count}R")
                total_races += race_count
            print(f"\n合計: {total_races}R\n")
        else:
            print("❌ 2026/02/04のレースデータが見つかりません\n")
        
        # 2. nvd_seテーブルから出馬表を確認
        print("【2】nvd_se (出馬表) を確認\n")
        
        query = """
        SELECT 
            keibajo_code,
            COUNT(DISTINCT race_bango) as race_count,
            COUNT(*) as horse_count
        FROM nvd_se
        WHERE kaisai_nen = '2026' 
          AND kaisai_tsukihi = '0204'
        GROUP BY keibajo_code
        ORDER BY keibajo_code;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if results:
            print("競馬場別出馬表データ:")
            total_races = 0
            total_horses = 0
            for keibajo_code, race_count, horse_count in results:
                venue_name = VENUE_NAMES.get(keibajo_code, f"不明({keibajo_code})")
                print(f"  {venue_name} ({keibajo_code}): {race_count}レース, {horse_count}頭")
                total_races += race_count
                total_horses += horse_count
            print(f"\n合計: {total_races}レース, {total_horses}頭\n")
        else:
            print("❌ 2026/02/04の出馬表データが見つかりません\n")
        
        # 3. 詳細データを確認
        print("【3】詳細データ確認\n")
        
        query = """
        SELECT 
            r.keibajo_code,
            r.race_bango,
            r.kyosomei_hondai as race_name,
            r.kyori,
            r.track_code,
            COUNT(s.umaban) as horse_count
        FROM nvd_ra r
        LEFT JOIN nvd_se s ON 
            r.kaisai_nen = s.kaisai_nen AND 
            r.kaisai_tsukihi = s.kaisai_tsukihi AND 
            r.keibajo_code = s.keibajo_code AND 
            r.race_bango = s.race_bango
        WHERE r.kaisai_nen = '2026' 
          AND r.kaisai_tsukihi = '0204'
        GROUP BY 
            r.keibajo_code, 
            r.race_bango, 
            r.kyosomei_hondai, 
            r.kyori, 
            r.track_code
        ORDER BY 
            r.keibajo_code, 
            r.race_bango;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if results:
            current_venue = None
            for row in results:
                keibajo_code, race_bango, race_name, kyori, track_code, horse_count = row
                venue_name = VENUE_NAMES.get(keibajo_code, f"不明({keibajo_code})")
                
                if current_venue != keibajo_code:
                    print(f"\n{venue_name} ({keibajo_code})")
                    print("-" * 80)
                    current_venue = keibajo_code
                
                print(f"  {race_bango}R: {race_name} ({kyori}m, {track_code}) - {horse_count}頭")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        
        # 判定と対処法
        if not results:
            print("\n❌ 問題: PC-KEIBAに2026/02/04のデータがありません")
            print("\n【対処法】")
            print("1. PC-KEIBAを起動")
            print("2. UmaConnでデータを取得")
            print("   - メニュー: データ取得 → JRA-VAN データ取得")
            print("   - 対象日: 2026/02/04")
            print("   - 対象: 川崎・姫路・笠松")
            print("3. データ取得後、再度このスクリプトを実行")
            print("4. データ確認OK後、インポートスクリプトを実行:")
            print("   python scripts\\import_from_pckeiba_to_eoi_pl.py")
        else:
            print("\n✅ PC-KEIBAにデータがあります")
            print("\n【次のステップ】")
            print("インポートスクリプトを修正して実行してください。")
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_pckeiba_data()
