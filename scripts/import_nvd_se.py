#!/usr/bin/env python3
"""
nvd_se テーブル統合スクリプト
- PC-KEIBA の nvd_se_export.sql をインポート
- データ検証（レコード数、文字化け確認）
- entries テーブルとの結合テスト
"""

import psycopg2
import sys
import subprocess

def create_nvd_se_table(conn):
    """nvd_se テーブル作成（最小限のカラム）"""
    print("\n" + "="*60)
    print("STEP 1: nvd_se テーブル作成")
    print("="*60)
    
    cursor = conn.cursor()
    
    # 既存テーブル削除（クリーンインポート）
    cursor.execute("DROP TABLE IF EXISTS nvd_se CASCADE")
    conn.commit()
    
    # テーブル作成（必要最小限 + その他カラム）
    create_sql = """
    CREATE TABLE nvd_se (
        record_id INTEGER,
        data_kubun VARCHAR(10),
        data_sakusei_nengappi VARCHAR(8),
        kaisai_nen VARCHAR(4) NOT NULL,
        kaisai_tsukihi VARCHAR(4) NOT NULL,
        keibajo_code VARCHAR(2) NOT NULL,
        kaisai_kai VARCHAR(2),
        kaisai_nichime VARCHAR(1),
        race_bango VARCHAR(2) NOT NULL,
        wakuban VARCHAR(2),
        umaban VARCHAR(2) NOT NULL,
        ketto_toroku_bango VARCHAR(10) NOT NULL,
        bamei VARCHAR(36) NOT NULL,
        umakigo_code VARCHAR(4),
        seibetsu_code VARCHAR(1),
        hinshu_code VARCHAR(1),
        moshoku_code VARCHAR(2),
        barei VARCHAR(2),
        tozai_shozoku_code VARCHAR(1),
        chokyoshi_code VARCHAR(5),
        chokyoshimei_ryakusho VARCHAR(10),
        banushi_code VARCHAR(6),
        banushimei VARCHAR(64),
        fukushoku_hyoji VARCHAR(2),
        yobi_1 VARCHAR(3),
        futan_juryo NUMERIC(3,1),
        futan_juryo_henkomae NUMERIC(3,1),
        blinker_shiyo_kubun VARCHAR(1),
        yobi_2 VARCHAR(3),
        kishu_code VARCHAR(5),
        kishu_code_henkomae VARCHAR(5),
        kishumei_ryakusho VARCHAR(10),
        kishumei_ryakusho_henkomae VARCHAR(10),
        kishu_minarai_code VARCHAR(1),
        kishu_minarai_code_henkomae VARCHAR(1),
        bataiju NUMERIC(3,0),
        zogen_fugo VARCHAR(1),
        zogen_sa NUMERIC(2,0),
        ijo_kubun_code VARCHAR(1),
        nyusen_juni VARCHAR(2),
        kakutei_chakujun VARCHAR(2),
        dochaku_kubun VARCHAR(1),
        dochaku_tosu VARCHAR(2),
        soha_time VARCHAR(7),
        chakusa_code_1 VARCHAR(3),
        chakusa_code_2 VARCHAR(3),
        chakusa_code_3 VARCHAR(3),
        corner_1 VARCHAR(2),
        corner_2 VARCHAR(2),
        corner_3 VARCHAR(2),
        corner_4 VARCHAR(2),
        tansho_odds NUMERIC(6,1),
        tansho_ninkijun VARCHAR(2),
        kakutoku_honshokin BIGINT,
        kakutoku_fukashokin BIGINT,
        yobi_3 VARCHAR(9),
        yobi_4 VARCHAR(9),
        kohan_4f VARCHAR(5),
        kohan_3f VARCHAR(5),
        aiteuma_joho_1 VARCHAR(70),
        aiteuma_joho_2 VARCHAR(70),
        aiteuma_joho_3 VARCHAR(70),
        time_sa VARCHAR(5),
        record_koshin_kubun VARCHAR(1),
        mining_kubun VARCHAR(1),
        yoso_soha_time VARCHAR(7),
        yoso_gosa_plus VARCHAR(4),
        yoso_gosa_minus VARCHAR(4),
        yoso_juni VARCHAR(2),
        kyakushitsu_hantei VARCHAR(1),
        PRIMARY KEY (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, umaban)
    )
    """
    
    cursor.execute(create_sql)
    conn.commit()
    
    # インデックス作成
    cursor.execute("CREATE INDEX idx_nvd_se_ketto ON nvd_se(ketto_toroku_bango)")
    conn.commit()
    
    print("✅ nvd_se テーブル作成完了")

def import_sql_dump(conn, sql_file):
    """SQL ダンプをインポート"""
    print("\n" + "="*60)
    print("STEP 2: SQL ダンプ インポート")
    print("="*60)
    
    print(f"  ファイル: {sql_file}")
    print("  インポート中... (数分かかります)")
    
    # psql コマンドで直接インポート（高速）
    cmd = [
        "psql",
        "-h", "localhost",
        "-U", "postgres",
        "-d", "eoi_pl",
        "-f", sql_file,
        "-v", "ON_ERROR_STOP=1"
    ]
    
    env = {"PGPASSWORD": "postgres123"}
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10分タイムアウト
        )
        
        if result.returncode != 0:
            print(f"\n❌ インポート失敗:")
            print(result.stderr)
            return False
        
        print("✅ SQL ダンプ インポート完了")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ タイムアウト（10分経過）")
        return False

def verify_data(conn):
    """データ検証"""
    print("\n" + "="*60)
    print("STEP 3: データ検証")
    print("="*60)
    
    cursor = conn.cursor()
    
    # レコード数
    cursor.execute("SELECT COUNT(*) FROM nvd_se")
    count = cursor.fetchone()[0]
    print(f"  総レコード数: {count:,}件")
    
    if count != 9551:
        print(f"  ⚠️ 警告: 期待値9,551件と異なります")
    
    # ユニーク馬数
    cursor.execute("SELECT COUNT(DISTINCT ketto_toroku_bango) FROM nvd_se")
    unique_horses = cursor.fetchone()[0]
    print(f"  ユニーク馬数: {unique_horses:,}頭")
    
    # レース数
    cursor.execute("""
        SELECT COUNT(DISTINCT (kaisai_nen || kaisai_tsukihi || keibajo_code || race_bango))
        FROM nvd_se
    """)
    unique_races = cursor.fetchone()[0]
    print(f"  ユニークレース数: {unique_races:,}レース")
    
    # 文字化け確認（サンプル10件）
    print("\n  馬名サンプル（文字化け確認）:")
    cursor.execute("""
        SELECT DISTINCT bamei
        FROM nvd_se
        ORDER BY bamei
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"    {row[0]}")
    
    print("\n✅ データ検証完了")

def test_join_with_entries(conn):
    """entries テーブルとの結合テスト"""
    print("\n" + "="*60)
    print("STEP 4: entries テーブルとの結合テスト")
    print("="*60)
    
    cursor = conn.cursor()
    
    # nvd_se の総レコード数
    cursor.execute("SELECT COUNT(*) FROM nvd_se")
    nvd_count = cursor.fetchone()[0]
    
    # entries テーブルの総レコード数
    cursor.execute("SELECT COUNT(*) FROM entries")
    entries_count = cursor.fetchone()[0]
    
    print(f"  nvd_se レコード数: {nvd_count:,}件")
    print(f"  entries レコード数: {entries_count:,}件")
    
    # ketto_toroku_bango で JOIN
    cursor.execute("""
        SELECT COUNT(*)
        FROM nvd_se n
        INNER JOIN entries e
        ON n.ketto_toroku_bango = e.ketto_toroku_bango
    """)
    
    join_count = cursor.fetchone()[0]
    match_rate = (join_count / nvd_count * 100) if nvd_count > 0 else 0
    
    print(f"\n  JOIN 成功数: {join_count:,}件")
    print(f"  照合成功率: {match_rate:.2f}%")
    
    # サンプル表示（照合成功例）
    print("\n  照合成功例（サンプル5件）:")
    cursor.execute("""
        SELECT 
            n.bamei,
            n.ketto_toroku_bango,
            e.bamei as entries_bamei,
            n.kaisai_nen,
            n.kaisai_tsukihi,
            n.keibajo_code,
            n.race_bango
        FROM nvd_se n
        INNER JOIN entries e
        ON n.ketto_toroku_bango = e.ketto_toroku_bango
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"    {row[0]} ({row[1]}) ⇔ {row[2]} | {row[3]}/{row[4]} {row[5]}-{row[6]}R")
    
    print("\n✅ 結合テスト完了")

if __name__ == "__main__":
    # データベース接続
    conn = psycopg2.connect(
        host="localhost",
        database="eoi_pl",
        user="postgres",
        password="postgres123"
    )
    
    try:
        # STEP 1: テーブル作成
        create_nvd_se_table(conn)
        
        # STEP 2: SQL ダンプ インポート
        sql_file = "/home/user/uploaded_files/nvd_se_export.sql"
        if not import_sql_dump(conn, sql_file):
            sys.exit(1)
        
        # STEP 3: データ検証
        verify_data(conn)
        
        # STEP 4: entries テーブルとの結合テスト
        test_join_with_entries(conn)
        
        print("\n" + "="*60)
        print("✅ nvd_se テーブル統合完了")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        conn.rollback()
        raise
    finally:
        conn.close()
