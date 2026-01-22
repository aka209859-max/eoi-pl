#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: MVP特徴量エンジニアリング（簡易版）
- メモリ効率重視: 最新1年分のデータのみ使用
- 禁止事項: 当日オッズ/人気は一切使用しない
"""

import pandas as pd
import numpy as np
import psycopg2

def create_mvp_features(conn):
    """MVP用の最小特徴量セット"""
    print("🔧 Creating MVP features (2024-2025 data only)...")
    
    # 最新1年分のみ（メモリ節約）
    query = """
        SELECT 
            r.race_id,
            r.kaisai_nen,
            r.kaisai_tsukihi,
            r.keibajo_code,
            r.kyori,
            r.babajotai_code_dirt,
            r.tosu,
            e.umaban,
            e.wakuban,
            e.bataiju,
            e.kakutei_chakujun,
            e.ketto_toroku_bango,
            e.kishu_code,
            e.chokyoshi_code
        FROM races r
        INNER JOIN entries e ON r.race_id = e.race_id
        WHERE r.kaisai_nen >= 2024
        AND e.kakutei_chakujun > 0
        ORDER BY r.kaisai_nen, r.kaisai_tsukihi, r.race_id, e.umaban
    """
    
    df = pd.read_sql(query, conn)
    print(f"✅ Loaded {len(df):,} entries (2024-2025)")
    
    # 禁止カラムチェック
    forbidden = ['odds', 'オッズ', '人気', 'ninki', 'popularity']
    for col in df.columns:
        if any(kw.lower() in col.lower() for kw in forbidden):
            raise ValueError(f"🚨 FORBIDDEN COLUMN: {col}")
    print("✅ No forbidden columns detected")
    
    # 目的変数: 複勝フラグ
    df['target_place'] = (df['kakutei_chakujun'] <= 3).astype(int)
    
    # 基本特徴量
    df['kyori_short'] = (df['kyori'] < 1400).astype(int)
    df['kyori_long'] = (df['kyori'] > 1800).astype(int)
    df['baba_good'] = (df['babajotai_code_dirt'] == 1).astype(int)
    df['tosu_many'] = (df['tosu'] >= 12).astype(int)
    
    # 馬体重（欠損値は中央値）
    df['bataiju'] = df['bataiju'].fillna(df['bataiju'].median())
    
    # 過去成績（簡易版）
    df['horse_race_count'] = df.groupby('ketto_toroku_bango').cumcount()
    df['horse_win_count'] = df.groupby('ketto_toroku_bango')['target_place'].cumsum()
    df['horse_win_rate'] = np.where(
        df['horse_race_count'] > 0,
        df['horse_win_count'] / df['horse_race_count'],
        0.3  # デフォルト値
    )
    
    # 騎手・調教師の勝率（集計ベース）
    jockey_win_rate = df.groupby('kishu_code')['target_place'].mean()
    df['jockey_win_rate'] = df['kishu_code'].map(jockey_win_rate).fillna(0.3)
    
    trainer_win_rate = df.groupby('chokyoshi_code')['target_place'].mean()
    df['trainer_win_rate'] = df['chokyoshi_code'].map(trainer_win_rate).fillna(0.3)
    
    # 枠・馬番の勝率
    wakuban_win_rate = df.groupby('wakuban')['target_place'].mean()
    df['wakuban_win_rate'] = df['wakuban'].map(wakuban_win_rate).fillna(0.3)
    
    umaban_win_rate = df.groupby('umaban')['target_place'].mean()
    df['umaban_win_rate'] = df['umaban'].map(umaban_win_rate).fillna(0.3)
    
    print(f"✅ Features created: {len(df.columns)} columns")
    return df

def get_feature_columns():
    """学習用特徴量カラム"""
    return [
        'kyori', 'tosu', 'wakuban', 'umaban', 'bataiju',
        'kyori_short', 'kyori_long', 'baba_good', 'tosu_many',
        'horse_win_rate', 'jockey_win_rate', 'trainer_win_rate',
        'wakuban_win_rate', 'umaban_win_rate'
    ]

if __name__ == "__main__":
    conn = psycopg2.connect(
        host="localhost",
        database="eoi_pl",
        user="postgres",
        password="eoi_pl_dev"
    )
    
    try:
        df = create_mvp_features(conn)
        
        # サンプル表示
        feature_cols = get_feature_columns()
        print("\n📋 Feature Sample:")
        print(df[feature_cols + ['target_place']].head(10))
        
        # 欠損値確認
        print("\n📊 Missing Values:")
        missing = df[feature_cols].isnull().sum()
        print(missing[missing > 0] if missing.sum() > 0 else "No missing values")
        
        # Target distribution
        print("\n📊 Target Distribution:")
        print(df['target_place'].value_counts())
        print(f"Place rate: {df['target_place'].mean():.3f}")
        
        # 保存
        output_path = "/home/user/eoi-pl/data/training_features.parquet"
        df.to_parquet(output_path, index=False)
        print(f"\n✅ Features saved to {output_path}")
        print(f"   Shape: {df.shape}")
        
    finally:
        conn.close()
