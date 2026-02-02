#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime Windows PC用 データベース設定
Windows PC上でWeb UIを動かす場合の設定ファイル

使用方法:
1. E:\\eoi-pl\\api\\config_windows.py として保存
2. start_api_windows.bat で自動的に読み込まれる
3. Windows PC の PostgreSQL eoi-sike に接続

作成日: 2026-02-01
最終更新: 2026-02-02
"""

# =====================================================================
# Windows PC用 PostgreSQL設定
# =====================================================================

# Windows PC のローカル PostgreSQL（eoi_pl）への接続設定
DB_CONFIG = {
    'host': '127.0.0.1',      # ローカルホスト
    'port': 5432,              # PostgreSQL標準ポート
    'database': 'eoi_pl',     # ← EOI-PL用データベース
    'user': 'postgres',        # PostgreSQLユーザー
    'password': 'postgres123'  # ← 正しいパスワード
}

# 特徴量データベースのパス（Windows PC用）
FEATURE_DB_PATH = r"E:\eoi-pl\data\feature_database_2020_2025.json"

# =====================================================================
# その他の設定（変更不要）
# =====================================================================

WEIGHTS = {
    'avg_rank': 0.30,
    'jockey': 0.15,
    'trainer': 0.10,
    'corner': 0.15,
    'time': 0.15,
    'distance': 0.10,
    'track': 0.05
}

VENUE_NAMES = {
    30: '門別', 35: '盛岡', 36: '水沢', 42: '浦和', 43: '船橋', 44: '大井', 45: '川崎',
    46: '金沢', 47: '笠松', 48: '名古屋', 50: '園田', 51: '姫路', 54: '高知', 55: '佐賀'
}

NAR_VENUES = [30, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55]

# =====================================================================
# 動作確認
# =====================================================================

if __name__ == '__main__':
    import psycopg2
    from pathlib import Path
    
    print("=" * 60)
    print("EOI-PL v1.0-Prime Windows PC用 設定確認")
    print("=" * 60)
    
    # DB接続テスト
    print("\n1. PostgreSQL 接続テスト...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM races WHERE kaisai_nen = 2026;")
        count = cursor.fetchone()[0]
        print(f"✅ 接続成功！2026年のレース数: {count:,}件")
        
        # 最新日付を取得
        cursor.execute("SELECT MAX(kaisai_tsukihi) FROM races WHERE kaisai_nen = 2026;")
        latest = cursor.fetchone()[0]
        print(f"✅ 最新データ日: 2026-{str(latest).zfill(4)[:2]}-{str(latest).zfill(4)[2:]}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ 接続失敗: {e}")
        print("\n対処法:")
        print("1. PostgreSQL が起動しているか確認")
        print("2. データベース名が 'eoi-sike' か確認")
        print("3. パスワードが正しいか確認")
    
    # 特徴量DBテスト
    print("\n2. 特徴量データベース確認...")
    if Path(FEATURE_DB_PATH).exists():
        size_mb = Path(FEATURE_DB_PATH).stat().st_size / 1024 / 1024
        print(f"✅ ファイル存在: {FEATURE_DB_PATH}")
        print(f"✅ ファイルサイズ: {size_mb:.1f} MB")
    else:
        print(f"❌ ファイル未検出: {FEATURE_DB_PATH}")
        print("\n対処法:")
        print(r"1. E:\eoi-pl\data\feature_database_2020_2025.json が存在するか確認")
        print("2. git pull origin main で最新版を取得")
    
    print("\n" + "=" * 60)
    print("設定確認完了！")
    print("=" * 60)
