#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: 特徴量エンジニアリング
-禁止事項: 当日オッズ/人気は一切使用しない（学習・推論・出力すべてで禁止）
- 目的変数: 複勝フラグ (kakutei_chakujun <= 3)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import psycopg2

class FeatureEngineering:
    """特徴量生成エンジン"""
    
    # 🚨 FORBIDDEN COLUMNS - 絶対に使用禁止
    FORBIDDEN_KEYWORDS = ['odds', 'オッズ', '人気', 'ninki', 'popularity']
    
    def __init__(self, conn):
        self.conn = conn
        
    def load_training_data(self, limit_date=None):
        """
        学習用データ読み込み
        limit_date: YYYYMMDD形式（この日付以前のデータを使用）
        """
        query = """
            SELECT 
                r.race_id,
                r.kaisai_nen,
                r.kaisai_tsukihi,
                r.keibajo_code,
                r.race_bango,
                r.kyori,
                r.track_code,
                r.babajotai_code_dirt,
                r.kyoso_joken_code,
                r.tosu,
                e.umaban,
                e.wakuban,
                e.bataiju,
                e.kakutei_chakujun,
                e.soha_time,
                e.corner_1,
                e.corner_2,
                e.corner_3,
                e.corner_4,
                e.kohan_3f,
                e.ketto_toroku_bango,
                e.kishu_code,
                e.chokyoshi_code
            FROM races r
            INNER JOIN entries e ON r.race_id = e.race_id
            WHERE e.kakutei_chakujun > 0  -- 結果確定済み
        """
        
        if limit_date:
            query += f" AND r.kaisai_tsukihi <= {limit_date}"
        
        query += " ORDER BY r.kaisai_nen, r.kaisai_tsukihi, r.keibajo_code, r.race_bango, e.umaban"
        
        df = pd.read_sql(query, self.conn)
        print(f"✅ Loaded {len(df):,} entries")
        
        # 禁止カラムチェック
        self._check_forbidden_columns(df)
        
        return df
    
    def _check_forbidden_columns(self, df):
        """禁止カラムの存在チェック"""
        forbidden = [col for col in df.columns 
                    if any(kw.lower() in col.lower() for kw in self.FORBIDDEN_KEYWORDS)]
        
        if forbidden:
            raise ValueError(f"🚨 FORBIDDEN COLUMNS DETECTED: {forbidden}")
        
        print("✅ No forbidden columns (odds/popularity) detected")
    
    def create_features(self, df):
        """
        特徴量生成
        - レース基本情報
        - 馬の過去成績
        - 騎手・調教師の実績
        - 枠・馬番の統計
        """
        print("\n🔧 Creating features...")
        
        # 目的変数: 複勝フラグ (1着〜3着)
        df['target_place'] = (df['kakutei_chakujun'] <= 3).astype(int)
        
        # 基本特徴量
        df = self._add_basic_features(df)
        
        # 過去成績特徴量（時系列順に処理）
        df = self._add_past_performance_features(df)
        
        # 騎手・調教師の実績
        df = self._add_jockey_trainer_features(df)
        
        # 枠・馬番の統計
        df = self._add_position_features(df)
        
        print(f"✅ Features created: {len(df.columns)} columns")
        return df
    
    def _add_basic_features(self, df):
        """基本特徴量"""
        # 距離カテゴリ
        df['kyori_category'] = pd.cut(df['kyori'], 
                                      bins=[0, 1200, 1600, 2000, 3000], 
                                      labels=['短距離', '中距離', '中長距離', '長距離'])
        
        # 馬場状態（ダミー変数化）
        df['baba_良'] = (df['babajotai_code_dirt'] == 1).astype(int)
        df['baba_稍重'] = (df['babajotai_code_dirt'] == 2).astype(int)
        df['baba_重'] = (df['babajotai_code_dirt'] == 3).astype(int)
        df['baba_不良'] = (df['babajotai_code_dirt'] == 4).astype(int)
        
        # 出走頭数
        df['tosu_少'] = (df['tosu'] <= 8).astype(int)
        df['tosu_多'] = (df['tosu'] >= 12).astype(int)
        
        return df
    
    def _add_past_performance_features(self, df):
        """過去成績特徴量（時系列考慮）"""
        # 日付順にソート
        df = df.sort_values(['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango'])
        
        # 馬ごとの過去成績集計
        df['horse_past_races'] = df.groupby('ketto_toroku_bango').cumcount()
        df['horse_past_wins'] = df.groupby('ketto_toroku_bango')['target_place'].cumsum()
        
        # 過去勝率（0除算回避）
        df['horse_win_rate'] = np.where(
            df['horse_past_races'] > 0,
            df['horse_past_wins'] / df['horse_past_races'],
            0.0
        )
        
        # 直近3走の成績
        df['horse_recent_3_avg_rank'] = (
            df.groupby('ketto_toroku_bango')['kakutei_chakujun']
            .transform(lambda x: x.rolling(3, min_periods=1).mean().shift(1))
        )
        
        return df
    
    def _add_jockey_trainer_features(self, df):
        """騎手・調教師の実績特徴量"""
        # 騎手の過去勝率
        jockey_stats = df.groupby('kishu_code').agg({
            'target_place': ['count', 'sum']
        }).reset_index()
        jockey_stats.columns = ['kishu_code', 'jockey_races', 'jockey_wins']
        jockey_stats['jockey_win_rate'] = jockey_stats['jockey_wins'] / jockey_stats['jockey_races']
        
        df = df.merge(jockey_stats, on='kishu_code', how='left')
        
        # 調教師の過去勝率
        trainer_stats = df.groupby('chokyoshi_code').agg({
            'target_place': ['count', 'sum']
        }).reset_index()
        trainer_stats.columns = ['chokyoshi_code', 'trainer_races', 'trainer_wins']
        trainer_stats['trainer_win_rate'] = trainer_stats['trainer_wins'] / trainer_stats['trainer_races']
        
        df = df.merge(trainer_stats, on='chokyoshi_code', how='left')
        
        return df
    
    def _add_position_features(self, df):
        """枠・馬番の統計特徴量"""
        # 枠番別の複勝率
        wakuban_stats = df.groupby('wakuban').agg({
            'target_place': ['count', 'sum']
        }).reset_index()
        wakuban_stats.columns = ['wakuban', 'wakuban_races', 'wakuban_wins']
        wakuban_stats['wakuban_win_rate'] = wakuban_stats['wakuban_wins'] / wakuban_stats['wakuban_races']
        
        df = df.merge(wakuban_stats, on='wakuban', how='left')
        
        # 馬番別の複勝率
        umaban_stats = df.groupby('umaban').agg({
            'target_place': ['count', 'sum']
        }).reset_index()
        umaban_stats.columns = ['umaban', 'umaban_races', 'umaban_wins']
        umaban_stats['umaban_win_rate'] = umaban_stats['umaban_wins'] / umaban_stats['umaban_races']
        
        df = df.merge(umaban_stats, on='umaban', how='left')
        
        return df
    
    def get_feature_columns(self):
        """モデル学習に使用する特徴量カラム一覧"""
        return [
            # レース基本情報
            'kyori', 'tosu',
            'baba_良', 'baba_稍重', 'baba_重', 'baba_不良',
            'tosu_少', 'tosu_多',
            
            # 馬の過去成績
            'horse_past_races', 'horse_win_rate', 'horse_recent_3_avg_rank',
            
            # 騎手・調教師
            'jockey_win_rate', 'trainer_win_rate',
            
            # 枠・馬番
            'wakuban', 'umaban', 'wakuban_win_rate', 'umaban_win_rate',
            
            # 馬体重（欠損値は平均値で補完）
            'bataiju',
        ]


if __name__ == "__main__":
    # 接続
    conn = psycopg2.connect(
        host="localhost",
        database="eoi_pl",
        user="postgres",
        password="eoi_pl_dev"
    )
    
    # 特徴量エンジン初期化
    fe = FeatureEngineering(conn)
    
    # データ読み込み（2024年末まで＝学習用）
    df = fe.load_training_data(limit_date=20241231)
    
    # 特徴量生成
    df = fe.create_features(df)
    
    # サンプル表示
    print("\n📋 Feature Sample:")
    feature_cols = fe.get_feature_columns()
    print(df[feature_cols + ['target_place']].head(10))
    
    # 欠損値確認
    print("\n📊 Missing Values:")
    print(df[feature_cols].isnull().sum()[df[feature_cols].isnull().sum() > 0])
    
    # 保存
    output_path = "/home/user/eoi-pl/data/training_features.parquet"
    df.to_parquet(output_path, index=False)
    print(f"\n✅ Features saved to {output_path}")
    print(f"   Shape: {df.shape}")
    
    conn.close()
