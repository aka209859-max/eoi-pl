#!/usr/bin/env python3
"""
pckeiba → eoi_pl データインポートスクリプト

pckeiba データベースの NAR データ（地方競馬）を
eoi_pl データベースの races と entries テーブルにインポートします。

使用方法:
    python scripts/import_from_pckeiba_to_eoi_pl.py
"""

import psycopg2
from datetime import datetime

# =====================================================================
# 設定
# =====================================================================

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres123'
}

# =====================================================================
# データインポート
# =====================================================================

def import_races():
    """pckeiba の nvd_ra テーブルから races テーブルにインポート"""
    print("=" * 60)
    print("pckeiba → eoi_pl データインポート")
    print("=" * 60)
    
    # pckeiba データベースに接続
    print("\n1. pckeiba データベースに接続中...")
    conn_pckeiba = psycopg2.connect(**DB_CONFIG, database='pckeiba')
    cur_pckeiba = conn_pckeiba.cursor()
    
    # eoi_pl データベースに接続
    print("2. eoi_pl データベースに接続中...")
    conn_eoi = psycopg2.connect(**DB_CONFIG, database='eoi_pl')
    cur_eoi = conn_eoi.cursor()
    
    try:
        # 既存データを削除
        print("\n3. 既存データを削除中...")
        cur_eoi.execute("DELETE FROM entries")
        cur_eoi.execute("DELETE FROM races")
        conn_eoi.commit()
        print("✅ 既存データを削除しました")
        
        # nvd_ra から races データを取得
        print("\n4. pckeiba から NAR レースデータを取得中...")
        cur_pckeiba.execute("""
            SELECT 
                年 || LPAD(月日::TEXT, 4, '0') || LPAD(場コード::TEXT, 2, '0') || LPAD(Ｒ::TEXT, 2, '0') as race_id,
                年 as kaisai_nen,
                月日 as kaisai_tsukihi,
                場コード as keibajo_code,
                Ｒ as race_bango,
                距離 as kyori,
                トラックコード as track_code
            FROM nvd_ra
            WHERE 年 >= 2020 AND 年 <= 2026
            ORDER BY 年, 月日, 場コード, Ｒ
        """)
        
        races_data = cur_pckeiba.fetchall()
        print(f"✅ {len(races_data):,}件のレースデータを取得")
        
        # races テーブルに挿入
        print("\n5. eoi_pl の races テーブルに挿入中...")
        cur_eoi.executemany("""
            INSERT INTO races (race_id, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, kyori, track_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (race_id) DO NOTHING
        """, races_data)
        conn_eoi.commit()
        print(f"✅ {cur_eoi.rowcount:,}件のレースデータを挿入")
        
        # nvd_se から entries データを取得
        print("\n6. pckeiba から NAR 出走馬データを取得中...")
        cur_pckeiba.execute("""
            SELECT 
                年 || LPAD(月日::TEXT, 4, '0') || LPAD(場コード::TEXT, 2, '0') || LPAD(Ｒ::TEXT, 2, '0') as race_id,
                馬番 as umaban,
                馬名 as bamei,
                血統登録番号 as ketto_toroku_bango,
                騎手コード as kishu_code,
                調教師コード as chokyoshi_code,
                CASE WHEN 確定着順 ~ '^[0-9]+$' THEN 確定着順::INTEGER ELSE NULL END as kakutei_chakujun,
                タイム_秒 as time_seconds
            FROM nvd_se
            WHERE 年 >= 2020 AND 年 <= 2026
            ORDER BY 年, 月日, 場コード, Ｒ, 馬番
        """)
        
        entries_data = cur_pckeiba.fetchall()
        print(f"✅ {len(entries_data):,}件の出走馬データを取得")
        
        # entries テーブルに挿入
        print("\n7. eoi_pl の entries テーブルに挿入中...")
        cur_eoi.executemany("""
            INSERT INTO entries (race_id, umaban, bamei, ketto_toroku_bango, kishu_code, chokyoshi_code, kakutei_chakujun, time_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, entries_data)
        conn_eoi.commit()
        print(f"✅ {cur_eoi.rowcount:,}件の出走馬データを挿入")
        
        # 2026年のデータ確認
        print("\n8. 2026年データを確認中...")
        cur_eoi.execute("SELECT COUNT(*) FROM races WHERE kaisai_nen = 2026")
        count_2026 = cur_eoi.fetchone()[0]
        print(f"✅ 2026年のレース数: {count_2026:,}件")
        
        # 最新日付を確認
        cur_eoi.execute("SELECT MAX(kaisai_tsukihi) FROM races WHERE kaisai_nen = 2026")
        latest = cur_eoi.fetchone()[0]
        if latest:
            print(f"✅ 最新データ日: 2026-{str(latest).zfill(4)[:2]}-{str(latest).zfill(4)[2:]}")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        conn_eoi.rollback()
        raise
    
    finally:
        cur_pckeiba.close()
        conn_pckeiba.close()
        cur_eoi.close()
        conn_eoi.close()
    
    print("\n" + "=" * 60)
    print("✅ インポート完了！")
    print("=" * 60)

# =====================================================================
# メイン処理
# =====================================================================

if __name__ == '__main__':
    import_races()
