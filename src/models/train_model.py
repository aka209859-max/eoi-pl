#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: モデル学習 + 確率校正
- LightGBM: 複勝確率予測
- Isotonic Regression: 確率校正
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, log_loss
import pickle
import json
import sys

sys.path.append('/home/user/eoi-pl/src/features')
from mvp_features import get_feature_columns

def train_model(df, feature_cols):
    """LightGBMモデル学習"""
    print("\n🚂 Training LightGBM model...")
    
    # データ分割（時系列考慮）
    X = df[feature_cols]
    y = df['target_place']
    
    # 2024年=Train, 2025年=Test
    train_mask = df['kaisai_nen'] == 2024
    test_mask = df['kaisai_nen'] == 2025
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    print(f"  Train: {len(X_train):,} samples")
    print(f"  Test:  {len(X_test):,} samples")
    
    # LightGBMパラメータ（複勝確率予測用）
    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'max_depth': 6,
        'min_data_in_leaf': 50,
        'verbose': -1
    }
    
    # Dataset作成
    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_test = lgb.Dataset(X_test, y_test, reference=lgb_train)
    
    # 学習
    model = lgb.train(
        params,
        lgb_train,
        num_boost_round=500,
        valid_sets=[lgb_train, lgb_test],
        valid_names=['train', 'test'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50, verbose=False),
            lgb.log_evaluation(period=100)
        ]
    )
    
    # 予測（未校正確率）
    y_pred_train_raw = model.predict(X_train, num_iteration=model.best_iteration)
    y_pred_test_raw = model.predict(X_test, num_iteration=model.best_iteration)
    
    # 評価
    train_auc = roc_auc_score(y_train, y_pred_train_raw)
    test_auc = roc_auc_score(y_test, y_pred_test_raw)
    train_logloss = log_loss(y_train, y_pred_train_raw)
    test_logloss = log_loss(y_test, y_pred_test_raw)
    
    print(f"\n📊 Model Performance (Uncalibrated):")
    print(f"  Train AUC: {train_auc:.4f}, LogLoss: {train_logloss:.4f}")
    print(f"  Test  AUC: {test_auc:.4f}, LogLoss: {test_logloss:.4f}")
    
    return model, X_train, y_train, X_test, y_test, y_pred_train_raw, y_pred_test_raw

def calibrate_probabilities(model, X_train, y_train, X_test, y_test):
    """確率校正（Isotonic Regression）"""
    print("\n🔧 Calibrating probabilities (Isotonic Regression)...")
    
    # LightGBMをsklearn互換のWrapperに
    from sklearn.base import BaseEstimator, ClassifierMixin
    
    class LGBMWrapper(BaseEstimator, ClassifierMixin):
        def __init__(self, model):
            self.model = model
            self.classes_ = np.array([0, 1])
        
        def fit(self, X, y):
            # Already fitted
            return self
        
        def predict_proba(self, X):
            preds = self.model.predict(X)
            return np.vstack([1 - preds, preds]).T
        
        def predict(self, X):
            return (self.predict_proba(X)[:, 1] > 0.5).astype(int)
    
    lgbm_wrapper = LGBMWrapper(model)
    
    # Isotonic校正
    calibrated_model = CalibratedClassifierCV(
        lgbm_wrapper,
        method='isotonic',
        cv='prefit'
    )
    calibrated_model.fit(X_train, y_train)
    
    # 校正後確率
    y_pred_train_cal = calibrated_model.predict_proba(X_train)[:, 1]
    y_pred_test_cal = calibrated_model.predict_proba(X_test)[:, 1]
    
    # 校正後評価
    train_auc_cal = roc_auc_score(y_train, y_pred_train_cal)
    test_auc_cal = roc_auc_score(y_test, y_pred_test_cal)
    train_logloss_cal = log_loss(y_train, y_pred_train_cal)
    test_logloss_cal = log_loss(y_test, y_pred_test_cal)
    
    print(f"\n📊 Model Performance (Calibrated):")
    print(f"  Train AUC: {train_auc_cal:.4f}, LogLoss: {train_logloss_cal:.4f}")
    print(f"  Test  AUC: {test_auc_cal:.4f}, LogLoss: {test_logloss_cal:.4f}")
    
    return calibrated_model, y_pred_train_cal, y_pred_test_cal

def analyze_calibration(y_true, y_pred_raw, y_pred_cal, name="Test"):
    """校正効果の分析"""
    print(f"\n📊 Calibration Analysis ({name}):")
    
    # 確率を10分位に分割して実際の複勝率と比較
    bins = np.linspace(0, 1, 11)
    
    print("  Predicted vs Actual (Uncalibrated):")
    for i in range(10):
        mask = (y_pred_raw >= bins[i]) & (y_pred_raw < bins[i+1])
        if mask.sum() > 0:
            actual_rate = y_true[mask].mean()
            pred_mean = y_pred_raw[mask].mean()
            print(f"    [{bins[i]:.1f}-{bins[i+1]:.1f}]: Pred={pred_mean:.3f}, Actual={actual_rate:.3f}, N={mask.sum():,}")
    
    print("\n  Predicted vs Actual (Calibrated):")
    for i in range(10):
        mask = (y_pred_cal >= bins[i]) & (y_pred_cal < bins[i+1])
        if mask.sum() > 0:
            actual_rate = y_true[mask].mean()
            pred_mean = y_pred_cal[mask].mean()
            print(f"    [{bins[i]:.1f}-{bins[i+1]:.1f}]: Pred={pred_mean:.3f}, Actual={actual_rate:.3f}, N={mask.sum():,}")

if __name__ == "__main__":
    # 特徴量読み込み
    print("📥 Loading features...")
    df = pd.read_parquet("/home/user/eoi-pl/data/training_features.parquet")
    feature_cols = get_feature_columns()
    
    print(f"  Shape: {df.shape}")
    print(f"  Features: {len(feature_cols)}")
    
    # モデル学習
    model, X_train, y_train, X_test, y_test, y_pred_train_raw, y_pred_test_raw = train_model(df, feature_cols)
    
    # 確率校正
    calibrated_model, y_pred_train_cal, y_pred_test_cal = calibrate_probabilities(
        model, X_train, y_train, X_test, y_test
    )
    
    # 校正効果の分析
    analyze_calibration(y_test.values, y_pred_test_raw, y_pred_test_cal, name="Test")
    
    # モデル保存
    model_path = "/home/user/eoi-pl/models/lgbm_place_model.pkl"
    calibrated_model_path = "/home/user/eoi-pl/models/calibrated_place_model.pkl"
    
    import os
    os.makedirs("/home/user/eoi-pl/models", exist_ok=True)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(calibrated_model_path, 'wb') as f:
        pickle.dump(calibrated_model, f)
    
    # メタデータ保存
    metadata = {
        'model_type': 'LightGBM + Isotonic Calibration',
        'target': 'place (1-3rd)',
        'features': feature_cols,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'train_auc': float(roc_auc_score(y_train, y_pred_train_cal)),
        'test_auc': float(roc_auc_score(y_test, y_pred_test_cal)),
        'train_logloss': float(log_loss(y_train, y_pred_train_cal)),
        'test_logloss': float(log_loss(y_test, y_pred_test_cal)),
        'created_at': pd.Timestamp.now().isoformat()
    }
    
    with open("/home/user/eoi-pl/models/model_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'='*60}")
    print("✅ MODEL TRAINING COMPLETED")
    print(f"{'='*60}")
    print(f"  Uncalibrated model: {model_path}")
    print(f"  Calibrated model:   {calibrated_model_path}")
    print(f"  Metadata:           /home/user/eoi-pl/models/model_metadata.json")
    print(f"{'='*60}\n")
