#!/bin/bash
# EOI-PL v1.0-Prime: 完全自動予想生成スクリプト

set -e  # エラーで停止

echo "============================================================"
echo "🏇 EOI-PL v1.0-Prime: 全自動予想生成"
echo "============================================================"

# 引数チェック
if [ -z "$1" ]; then
    echo "使用方法: $0 <kaisai_tsukihi>"
    echo "例: $0 101 (2025年1月1日)"
    exit 1
fi

TARGET_DATE=$1
echo "📅 Target Date: $TARGET_DATE"
echo ""

# Step 1: PostgreSQL起動
echo "🔧 Step 1: Starting PostgreSQL..."
sudo service postgresql start || true
sleep 2
echo "✅ PostgreSQL started"
echo ""

# Step 2: 特徴量生成（初回のみ or データ更新時）
if [ ! -f "/home/user/eoi-pl/data/training_features.parquet" ]; then
    echo "🔧 Step 2: Creating features (first time)..."
    python3 /home/user/eoi-pl/src/features/mvp_features.py
    echo "✅ Features created"
    echo ""
fi

# Step 3: モデル学習（初回のみ or 再学習時）
if [ ! -f "/home/user/eoi-pl/models/lgbm_place_model.pkl" ]; then
    echo "🔧 Step 3: Training model (first time)..."
    python3 /home/user/eoi-pl/src/models/train_model_simple.py
    echo "✅ Model trained"
    echo ""
fi

# Step 4: 予想生成
echo "🔮 Step 4: Generating predictions..."
python3 /home/user/eoi-pl/src/output/generate_predictions.py $TARGET_DATE

OUTPUT_FILE="/home/user/eoi-pl/data/predictions_${TARGET_DATE}.json"

if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo "============================================================"
    echo "✅ PREDICTION GENERATION COMPLETED"
    echo "============================================================"
    echo "📁 Output file: $OUTPUT_FILE"
    echo ""
    echo "📊 Quick Stats:"
    python3 << EOF
import json
with open("$OUTPUT_FILE", 'r') as f:
    data = json.load(f)
print(f"  - Total races: {len(data['races'])}")
print(f"  - Total horses: {sum(len(r['horses']) for r in data['races'])}")
print(f"  - Generated at: {data['generated_at']}")
print(f"  - Odds used: {data['policy']['odds_used']}")
print(f"  - Freeze mode: {data['policy']['freeze']}")
EOF
    echo ""
    echo "🚀 Ready for delivery!"
    echo "============================================================"
else
    echo "❌ ERROR: Output file not found"
    exit 1
fi
