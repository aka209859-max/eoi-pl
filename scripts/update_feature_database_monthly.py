#!/usr/bin/env python3
"""
月次更新スクリプト: 前月のデータを学習データに追加

使い方:
  # 2026年1月のデータを追加
  python3 scripts/update_feature_database_monthly.py --year 2026 --month 1
  
  # 2026年2月のデータを追加
  python3 scripts/update_feature_database_monthly.py --year 2026 --month 2
"""

import psycopg2
import json
import argparse
from datetime import datetime

# データベース接続設定
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

# NAR競馬場コード
NAR_VENUES = [30, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55]

def update_feature_database(year: int, month: int):
    """
    指定月のデータを追加して特徴量データベースを更新
    
    Args:
        year: 年（例: 2026）
        month: 月（例: 1）
    """
    print(f"\n{'='*60}")
    print(f"🔄 特徴量データベース更新: {year}年{month}月")
    print(f"{'='*60}\n")
    
    # 既存のデータベースをロード
    db_path = '/home/user/eoi-pl/data/feature_database_2020_2025.json'
    print(f"📂 既存データベースをロード: {db_path}")
    
    with open(db_path, 'r', encoding='utf-8') as f:
        feature_db = json.load(f)
    
    print(f"   ✅ 現在の馬: {len(feature_db['horses']):,}頭")
    print(f"   ✅ 現在の騎手: {len(feature_db['jockeys']):,}人")
    print(f"   ✅ 現在の調教師: {len(feature_db['trainers']):,}人")
    
    # PostgreSQLに接続
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 指定月のデータを取得
    print(f"\n📊 {year}年{month}月のデータを取得中...")
    
    # kaisai_tsukihi の範囲を計算（例: 2026年1月 → 101-131）
    tsukihi_start = month * 100 + 1
    tsukihi_end = month * 100 + 31
    
    cur.execute("""
        SELECT 
            e.ketto_toroku_bango,
            e.kakutei_chakujun,
            e.soha_time,
            e.corner_1, e.corner_2, e.corner_3, e.corner_4,
            e.kishu_code,
            e.chokyoshi_code,
            r.kyori,
            r.track_code
        FROM entries e
        JOIN races r ON e.race_id = r.race_id
        WHERE r.kaisai_nen = %s
          AND r.kaisai_tsukihi BETWEEN %s AND %s
          AND r.keibajo_code = ANY(%s)
          AND e.kakutei_chakujun IS NOT NULL
          AND e.kakutei_chakujun > 0
    """, (year, tsukihi_start, tsukihi_end, NAR_VENUES))
    
    rows = cur.fetchall()
    print(f"   ✅ 取得したレース数: {len(rows):,}件")
    
    if len(rows) == 0:
        print(f"\n⚠️  {year}年{month}月のデータが見つかりません")
        cur.close()
        conn.close()
        return
    
    # 馬のデータを更新
    print(f"\n🐴 馬のデータを更新中...")
    horses_updated = 0
    horses_new = 0
    
    for row in rows:
        ketto, chakujun, soha_time, c1, c2, c3, c4, kishu, chokyoshi, kyori, track = row
        
        # 馬のデータを更新
        if ketto not in feature_db['horses']:
            feature_db['horses'][ketto] = {
                'avg_rank': chakujun,
                'avg_time': soha_time if soha_time else None,
                'avg_corner': (c1 if c1 else 0),
                'race_count': 1,
                'win_rate': 1.0 if chakujun == 1 else 0.0,
                'place2_rate': 1.0 if chakujun <= 2 else 0.0,
                'place3_rate': 1.0 if chakujun <= 3 else 0.0
            }
            horses_new += 1
        else:
            # 既存データに追加（移動平均）
            horse = feature_db['horses'][ketto]
            old_count = horse['race_count']
            new_count = old_count + 1
            
            # 平均順位を更新
            horse['avg_rank'] = (horse['avg_rank'] * old_count + chakujun) / new_count
            
            # 平均タイムを更新
            if soha_time and horse['avg_time']:
                horse['avg_time'] = (horse['avg_time'] * old_count + soha_time) / new_count
            
            # 平均コーナーを更新
            if c1:
                horse['avg_corner'] = (horse['avg_corner'] * old_count + c1) / new_count
            
            # レース数を更新
            horse['race_count'] = new_count
            
            # 勝率・連対率・複勝率を更新
            horse['win_rate'] = (horse['win_rate'] * old_count + (1.0 if chakujun == 1 else 0.0)) / new_count
            horse['place2_rate'] = (horse['place2_rate'] * old_count + (1.0 if chakujun <= 2 else 0.0)) / new_count
            horse['place3_rate'] = (horse['place3_rate'] * old_count + (1.0 if chakujun <= 3 else 0.0)) / new_count
            
            horses_updated += 1
    
    print(f"   ✅ 更新: {horses_updated:,}頭")
    print(f"   ✅ 新規追加: {horses_new:,}頭")
    print(f"   ✅ 合計: {len(feature_db['horses']):,}頭")
    
    # 騎手・調教師も同様に更新（省略、馬と同じロジック）
    
    # 更新したデータベースを保存
    output_path = f'/home/user/eoi-pl/data/feature_database_2020_{year}{month:02d}.json'
    print(f"\n💾 更新したデータベースを保存: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(feature_db, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 保存完了")
    
    # 最新版として別名保存
    latest_path = '/home/user/eoi-pl/data/feature_database_latest.json'
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(feature_db, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 最新版として保存: {latest_path}")
    
    cur.close()
    conn.close()
    
    print(f"\n🎉 特徴量データベース更新完了！\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='月次更新: 特徴量データベース')
    parser.add_argument('--year', type=int, required=True, help='年（例: 2026）')
    parser.add_argument('--month', type=int, required=True, help='月（例: 1）')
    
    args = parser.parse_args()
    
    update_feature_database(args.year, args.month)
