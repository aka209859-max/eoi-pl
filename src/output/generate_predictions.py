#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: 予想生成エンジン（統合版）
- DB読み込み → 特徴量生成 → 予測 → 推奨度付与 → JSON出力
"""

import pandas as pd
import numpy as np
import psycopg2
import pickle
import json
from datetime import datetime
import sys

sys.path.append('/home/user/eoi-pl/src/features')
sys.path.append('/home/user/eoi-pl/src/grading')

from mvp_features import get_feature_columns
from grading_engine import GradingEngine

class PredictionEngine:
    """予想生成エンジン"""
    
    def __init__(self, model_path, calibrator_path, conn):
        # モデル読み込み
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(calibrator_path, 'rb') as f:
            self.calibrator = pickle.load(f)
        
        self.conn = conn
        self.feature_cols = get_feature_columns()
        self.grading_engine = GradingEngine()
        
        print(f"✅ Model loaded: {model_path}")
        print(f"✅ Calibrator loaded: {calibrator_path}")
    
    def load_target_races(self, target_date):
        """
        予想対象レースを読み込み
        target_date: YYYYMMDD形式
        """
        query = f"""
            SELECT 
                r.race_id,
                r.kaisai_nen,
                r.kaisai_tsukihi,
                r.keibajo_code,
                r.race_bango,
                r.kyori,
                r.track_code,
                r.babajotai_code_dirt,
                r.tosu,
                e.umaban,
                e.wakuban,
                e.bataiju,
                e.ketto_toroku_bango,
                e.kishu_code,
                e.chokyoshi_code,
                e.bamei
            FROM races r
            INNER JOIN entries e ON r.race_id = e.race_id
            WHERE r.kaisai_tsukihi = {target_date}
            ORDER BY r.keibajo_code, r.race_bango, e.umaban
        """
        
        df = pd.read_sql(query, self.conn)
        
        if len(df) == 0:
            raise ValueError(f"No races found for date {target_date}")
        
        n_races = df['race_id'].nunique()
        print(f"✅ Loaded {len(df)} entries from {n_races} races")
        return df
    
    def create_features_for_prediction(self, df):
        """予測用特徴量生成（簡易版）"""
        # 基本特徴量
        df['kyori_short'] = (df['kyori'] < 1400).astype(int)
        df['kyori_long'] = (df['kyori'] > 1800).astype(int)
        df['baba_good'] = (df['babajotai_code_dirt'] == 1).astype(int)
        df['tosu_many'] = (df['tosu'] >= 12).astype(int)
        
        # 馬体重（欠損値は中央値）
        df['bataiju'] = df['bataiju'].fillna(475.0)
        
        # 過去成績（簡易版: 全体統計で代用）
        df['horse_win_rate'] = 0.30  # デフォルト値
        df['jockey_win_rate'] = 0.30
        df['trainer_win_rate'] = 0.30
        df['wakuban_win_rate'] = 0.30
        df['umaban_win_rate'] = 0.30
        
        return df
    
    def predict_place_probabilities(self, df):
        """複勝確率予測"""
        X = df[self.feature_cols]
        
        # 未校正確率
        P_place_raw = self.model.predict(X)
        
        # 校正
        P_place_cal = self.calibrator.transform(P_place_raw)
        P_place_cal = np.clip(P_place_cal, 0.001, 0.999)
        
        df['P_place_raw'] = P_place_raw
        df['P_place_cal'] = P_place_cal
        
        # 単勝確率（簡易計算: 複勝確率の2乗）
        df['P_win_cal'] = df['P_place_cal'] ** 1.5
        
        # レース内で正規化
        for race_id in df['race_id'].unique():
            mask = df['race_id'] == race_id
            df.loc[mask, 'P_win_cal'] = df.loc[mask, 'P_win_cal'] / df.loc[mask, 'P_win_cal'].sum()
        
        return df
    
    def assign_grades_all_races(self, df):
        """全レースに推奨度を付与"""
        result_dfs = []
        
        for race_id in df['race_id'].unique():
            race_df = df[df['race_id'] == race_id].copy()
            race_df = self.grading_engine.assign_grades(race_df)
            result_dfs.append(race_df)
        
        return pd.concat(result_dfs, ignore_index=True)
    
    def generate_json_output(self, df, target_date):
        """JSON出力生成"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'target_date': target_date,
            'policy': {
                'odds_used': False,
                'freeze': True,
                'coverage_scheme': 'A',
                'thresholds': self.grading_engine.THRESHOLDS
            },
            'races': []
        }
        
        for race_id in sorted(df['race_id'].unique()):
            race_df = df[df['race_id'] == race_id]
            
            race_info = race_df.iloc[0]
            
            race_output = {
                'race_id': race_id,
                'race_meta': {
                    'kaisai_nen': int(race_info['kaisai_nen']),
                    'kaisai_tsukihi': int(race_info['kaisai_tsukihi']),
                    'keibajo_code': int(race_info['keibajo_code']),
                    'race_bango': int(race_info['race_bango']),
                    'kyori': int(race_info['kyori']),
                    'tosu': int(race_info['tosu'])
                },
                'horses': []
            }
            
            for _, horse in race_df.iterrows():
                horse_output = {
                    'umaban': int(horse['umaban']),
                    'bamei': str(horse['bamei']).strip(),
                    'P_win_cal': round(float(horse['P_win_cal']), 4),
                    'P_place_cal': round(float(horse['P_place_cal']), 4),
                    'grade': horse['grade'],
                    'ketto_toroku_bango': str(horse['ketto_toroku_bango']),
                    'kishu_code': int(horse['kishu_code']),
                    'chokyoshi_code': int(horse['chokyoshi_code'])
                }
                race_output['horses'].append(horse_output)
            
            # 馬番順にソート
            race_output['horses'] = sorted(race_output['horses'], key=lambda x: x['umaban'])
            
            output['races'].append(race_output)
        
        return output

def main(target_date):
    """メイン実行"""
    print(f"\n{'='*60}")
    print(f"🏇 EOI-PL v1.0-Prime: 予想生成")
    print(f"   Target Date: {target_date}")
    print(f"{'='*60}\n")
    
    # DB接続
    conn = psycopg2.connect(
        host="localhost",
        database="eoi_pl",
        user="postgres",
        password="eoi_pl_dev"
    )
    
    try:
        # エンジン初期化
        engine = PredictionEngine(
            model_path="/home/user/eoi-pl/models/lgbm_place_model.pkl",
            calibrator_path="/home/user/eoi-pl/models/calibrator.pkl",
            conn=conn
        )
        
        # レース読み込み
        df = engine.load_target_races(target_date)
        
        # 特徴量生成
        print("\n🔧 Creating features...")
        df = engine.create_features_for_prediction(df)
        
        # 予測
        print("🔮 Predicting place probabilities...")
        df = engine.predict_place_probabilities(df)
        
        # 推奨度付与
        print("📊 Assigning grades (Coverage A)...")
        df = engine.assign_grades_all_races(df)
        
        # JSON生成
        print("📝 Generating JSON output...")
        output = engine.generate_json_output(df, target_date)
        
        # 保存
        output_path = f"/home/user/eoi-pl/data/predictions_{target_date}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Predictions saved to {output_path}")
        
        # サマリー表示
        print(f"\n📊 Summary:")
        print(f"   Total races: {len(output['races'])}")
        print(f"   Total horses: {sum(len(r['horses']) for r in output['races'])}")
        
        # グレード分布
        all_grades = [h['grade'] for r in output['races'] for h in r['horses']]
        grade_dist = pd.Series(all_grades).value_counts().sort_index()
        print(f"\n   Grade Distribution:")
        for grade, count in grade_dist.items():
            pct = count / len(all_grades) * 100
            print(f"     {grade}: {count} ({pct:.1f}%)")
        
        print(f"\n{'='*60}")
        print("✅ PREDICTION COMPLETED")
        print(f"{'='*60}\n")
        
    finally:
        conn.close()

if __name__ == "__main__":
    # デフォルト: 2025年1月1日
    target_date = 20250101
    
    if len(sys.argv) > 1:
        target_date = int(sys.argv[1])
    
    main(target_date)
