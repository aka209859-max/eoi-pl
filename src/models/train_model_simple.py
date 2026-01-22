#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime: モデル学習 + 確率校正（簡易版）
- LightGBM: 複勝確率予測
- IsotonicRegression: 直接校正
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score, log_loss
import pickle
import json
import sys

sys.path.append('/home/user/eoi-pl/src/features')
from mvp_features import get_feature_columns

def train_model(df, feature_cols):
    """LightGBMモデル学習"""
    print("\n🚂 Training LightGBM model...")
    
    X = df[feature_cols]
    y = df['target_place']
    
    # 2024年=Train, 2025年=Test
    train_mask = df['kaisai_nen'] == 2024
    test_mask = df['kaisai_nen'] == 2025
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    print(f"  Train: {len(X_train):,} samples")
    print(f"  Test:  {len(X_test):,} samples")
    
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
    
    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_test = lgb.Dataset(X_test, y_test, reference=lgb_train)
    
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
    
    y_pred_train_raw = model.predict(X_train, num_iteration=model.best_iteration)
    y_pred_test_raw = model.predict(X_test, num_iteration=model.best_iteration)
    
    train_auc = roc_auc_score(y_train, y_pred_train_raw)
    test_auc = roc_auc_score(y_test, y_pred_test_raw)
    train_logloss = log_loss(y_train, y_pred_train_raw)
    test_logloss = log_loss(y_test, y_pred_test_raw)
    
    print(f"\n📊 Model Performance (Uncalibrated):")
    print(f"  Train AUC: {train_auc:.4f}, LogLoss: {train_logloss:.4f}")
    print(f"  Test  AUC: {test_auc:.4f}, LogLoss: {test_logloss:.4f}")
    
    return model, X_train, y_train, X_test, y_test, y_pred_train_raw, y_pred_test_raw

def calibrate_probabilities(y_train, y_pred_train_raw, y_pred_test_raw):
    """確率校正（Isotonic Regression）"""
    print("\n🔧 Calibrating probabilities (Isotonic Regression)...")
    
    # Isotonic Regressionで校正
    calibrator = IsotonicRegression(out_of_bounds='clip')
    calibrator.fit(y_pred_train_raw, y_train)
    
    # 校正後確率
    y_pred_train_cal = calibrator.transform(y_pred_train_raw)
    y_pred_test_cal = calibrator.transform(y_pred_test_raw)
    
    # クリップ（0-1範囲に収める）
    y_pred_train_cal = np.clip(y_pred_train_cal, 0.001, 0.999)
    y_pred_test_cal = np.clip(y_pred_test_cal, 0.001, 0.999)
    
    return calibrator, y_pred_train_cal, y_pred_test_cal

def analyze_calibration(y_true, y_pred_raw, y_pred_cal, name="Test"):
    """校正効果の分析"""
    print(f"\n📊 Calibration Analysis ({name}):")
    
    bins = np.linspace(0, 1, 11)
    
    print("  Predicted vs Actual (Uncalibrated):")
    for i in range(10):
        mask = (y_pred_raw >= bins[i]) & (y_pred_raw < bins[i+1])
        if mask.sum() > 0:
            actual_rate = y_true[mask].mean()
            pred_mean = y_pred_raw[mask].mean()
            diff = abs(actual_rate - pred_mean)
            print(f"    [{bins[i]:.1f}-{bins[i+1]:.1f}]: Pred={pred_mean:.3f}, Actual={actual_rate:.3f}, Diff={diff:.3f}, N={mask.sum():,}")
    
    print("\n  Predicted vs Actual (Calibrated):")
    for i in range(10):
        mask = (y_pred_cal >= bins[i]) & (y_pred_cal < bins[i+1])
        if mask.sum() > 0:
            actual_rate = y_true[mask].mean()
            pred_mean = y_pred_cal[mask].mean()
            diff = abs(actual_rate - pred_mean)
            print(f"    [{bins[i]:.1f}-{bins[i+1]:.1f}]: Pred={pred_mean:.3f}, Actual={actual_rate:.3f}, Diff={diff:.3f}, N={mask.sum():,}")

if __name__ == "__main__":
    print("📥 Loading features...")
    df = pd.read_parquet("/home/user/eoi-pl/data/training_features.parquet")
    feature_cols = get_feature_columns()
    
    print(f"  Shape: {df.shape}")
    print(f"  Features: {len(feature_cols)}")
    
    # モデル学習
    model, X_train, y_train, X_test, y_test, y_pred_train_raw, y_pred_test_raw = train_model(df, feature_cols)
    
    # 確率校正
    calibrator, y_pred_train_cal, y_pred_test_cal = calibrate_probabilities(
        y_train.values, y_pred_train_raw, y_pred_test_raw
    )
    
    # 校正後評価
    train_auc_cal = roc_auc_score(y_train, y_pred_train_cal)
    test_auc_cal = roc_auc_score(y_test, y_pred_test_cal)
    train_logloss_cal = log_loss(y_train, y_pred_train_cal)
    test_logloss_cal = log_loss(y_test, y_pred_test_cal)
    
    print(f"\n📊 Model Performance (Calibrated):")
    print(f"  Train AUC: {train_auc_cal:.4f}, LogLoss: {train_logloss_cal:.4f}")
    print(f"  Test  AUC: {test_auc_cal:.4f}, LogLoss: {test_logloss_cal:.4f}")
    
    # 校正効果の分析
    analyze_calibration(y_test.values, y_pred_test_raw, y_pred_test_cal, name="Test")
    
    # モデル保存
    import os
    os.makedirs("/home/user/eoi-pl/models", exist_ok=True)
    
    with open("/home/user/eoi-pl/models/lgbm_place_model.pkl", 'wb') as f:
        pickle.dump(model, f)
    
    with open("/home/user/eoi-pl/models/calibrator.pkl", 'wb') as f:
        pickle.dump(calibrator, f)
    
    # メタデータ保存
    metadata = {
        'model_type': 'LightGBM + Isotonic Regression',
        'target': 'place (1-3rd)',
        'features': feature_cols,
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'train_auc': float(train_auc_cal),
        'test_auc': float(test_auc_cal),
        'train_logloss': float(train_logloss_cal),
        'test_logloss': float(test_logloss_cal),
        'created_at': pd.Timestamp.now().isoformat()
    }
    
    with open("/home/user/eoi-pl/models/model_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'='*60}")
    print("✅ MODEL TRAINING COMPLETED")
    print(f"{'='*60}")
    print(f"  LightGBM model: /home/user/eoi-pl/models/lgbm_place_model.pkl")
    print(f"  Calibrator:     /home/user/eoi-pl/models/calibrator.pkl")
    print(f"  Metadata:       /home/user/eoi-pl/models/model_metadata.json")
    print(f"{'='*60}\n")
