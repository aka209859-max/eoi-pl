#!/usr/bin/env python3
"""
CSVスキーマ解析スクリプト
- カラム名、データ型、欠損値の確認
- 結合キーの検証
- オッズ/人気カラムの有無チェック（禁止事項確認）
"""

import pandas as pd
import sys

def analyze_csv(filepath, name, nrows=10000):
    """CSV基本情報を解析"""
    print(f"\n{'='*60}")
    print(f"📊 {name} Analysis")
    print(f"{'='*60}")
    
    # サンプル読み込み（大きいファイル対策）
    df = pd.read_csv(filepath, nrows=nrows, low_memory=False)
    
    print(f"\n✅ Shape: {df.shape}")
    print(f"✅ Columns ({len(df.columns)}): {list(df.columns)}")
    
    print("\n📋 Data Types:")
    print(df.dtypes)
    
    print("\n📋 Missing Values:")
    missing = df.isnull().sum()
    print(missing[missing > 0])
    
    print("\n📋 Sample Data (first 3 rows):")
    print(df.head(3))
    
    # オッズ/人気カラムチェック（禁止事項）
    forbidden_keywords = ['odds', 'オッズ', '人気', 'ninki', 'popularity']
    forbidden_cols = [col for col in df.columns 
                     if any(kw.lower() in col.lower() for kw in forbidden_keywords)]
    
    if forbidden_cols:
        print(f"\n⚠️  WARNING: Potential forbidden columns detected: {forbidden_cols}")
    else:
        print(f"\n✅ No obvious odds/popularity columns detected")
    
    return df

def verify_join_keys(races_df, entries_df):
    """結合キーの検証"""
    print(f"\n{'='*60}")
    print("🔗 Join Key Verification")
    print(f"{'='*60}")
    
    join_keys = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango']
    
    print(f"\n✅ Join keys: {join_keys}")
    
    # キーの存在確認
    for key in join_keys:
        in_races = key in races_df.columns
        in_entries = key in entries_df.columns
        print(f"  - {key}: races={in_races}, entries={in_entries}")
    
    # ユニークレース数
    races_df['race_id'] = (
        races_df['kaisai_nen'].astype(str) + '_' +
        races_df['kaisai_tsukihi'].astype(str).str.zfill(4) + '_' +
        races_df['keibajo_code'].astype(str) + '_' +
        races_df['race_bango'].astype(str).str.zfill(2)
    )
    
    entries_df['race_id'] = (
        entries_df['kaisai_nen'].astype(str) + '_' +
        entries_df['kaisai_tsukihi'].astype(str).str.zfill(4) + '_' +
        entries_df['keibajo_code'].astype(str) + '_' +
        entries_df['race_bango'].astype(str).str.zfill(2)
    )
    
    print(f"\n✅ Unique races in races.csv: {races_df['race_id'].nunique()}")
    print(f"✅ Unique races in entries.csv: {entries_df['race_id'].nunique()}")
    
    # 結合可能性チェック
    races_ids = set(races_df['race_id'])
    entries_ids = set(entries_df['race_id'])
    
    common_ids = races_ids & entries_ids
    only_races = races_ids - entries_ids
    only_entries = entries_ids - races_ids
    
    print(f"\n✅ Common races: {len(common_ids)}")
    print(f"⚠️  Only in races: {len(only_races)}")
    print(f"⚠️  Only in entries: {len(only_entries)}")
    
    # サンプル表示
    if len(common_ids) > 0:
        sample_id = list(common_ids)[0]
        print(f"\n📋 Sample race_id: {sample_id}")
        print("\nRaces data:")
        print(races_df[races_df['race_id'] == sample_id])
        print("\nEntries data:")
        print(entries_df[entries_df['race_id'] == sample_id].head(3))

if __name__ == "__main__":
    # ファイルパス
    races_path = "/home/user/uploaded_files/races_2020_2025.csv"
    entries_path = "/home/user/uploaded_files/entries_results_2020_2025.csv"
    
    # 解析実行
    races_df = analyze_csv(races_path, "races_2020_2025.csv", nrows=10000)
    entries_df = analyze_csv(entries_path, "entries_results_2020_2025.csv", nrows=10000)
    
    # 結合キー検証
    verify_join_keys(races_df, entries_df)
    
    print(f"\n{'='*60}")
    print("✅ Schema analysis completed")
    print(f"{'='*60}\n")
