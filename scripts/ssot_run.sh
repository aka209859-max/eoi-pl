#!/bin/bash
# ==============================================================================
# SSOT Runner - EOI-PL v1.0-Prime (PL+PowerEP)
# ==============================================================================
# Purpose: ワンコマンド実行で学習 → 予測 → 3点セット生成を再現
# Usage: bash scripts/ssot_run.sh
# Outputs:
#   - data/predictions_v1.0.json (84KB)
#   - data/predictions_flat_v1.0.csv (6.4KB)
#   - data/audit_log.json (35KB)
# ==============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="/home/user/eoi-pl"
cd "$PROJECT_ROOT"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  SSOT Runner - EOI-PL v1.0-Prime${NC}"
echo -e "${BLUE}  Model: PL+PowerEP (α=0.5)${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ==============================================================================
# Phase 2A: PL+PowerEP Training
# ==============================================================================
echo -e "${YELLOW}[Phase 2A] PL+PowerEP Training...${NC}"
python3 src/models/pl_powerep_minimal.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Phase 2A Complete${NC}"
else
    echo -e "${RED}❌ Phase 2A Failed${NC}"
    exit 1
fi
echo ""

# ==============================================================================
# Phase 2D: Prediction Generation
# ==============================================================================
echo -e "${YELLOW}[Phase 2D] Prediction Generation...${NC}"
python3 src/output/prediction_generator.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Phase 2D Complete${NC}"
else
    echo -e "${RED}❌ Phase 2D Failed${NC}"
    exit 1
fi
echo ""

# ==============================================================================
# Audit Generation
# ==============================================================================
echo -e "${YELLOW}[Audit] Generating audit_log.json...${NC}"
python3 src/audit/complete_audit_generator.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Audit Complete${NC}"
else
    echo -e "${RED}❌ Audit Failed${NC}"
    exit 1
fi
echo ""

# ==============================================================================
# Verify Outputs
# ==============================================================================
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Deliverables (3点セット)${NC}"
echo -e "${BLUE}============================================${NC}"

PREDICTIONS_JSON="data/predictions_v1.0.json"
PREDICTIONS_CSV="data/predictions_flat_v1.0.csv"
AUDIT_LOG="data/audit_log.json"

if [ -f "$PREDICTIONS_JSON" ]; then
    SIZE=$(du -h "$PREDICTIONS_JSON" | awk '{print $1}')
    SHA256=$(sha256sum "$PREDICTIONS_JSON" | awk '{print $1}')
    echo -e "${GREEN}✅ predictions_v1.0.json${NC} (${SIZE})"
    echo "   SHA256: ${SHA256:0:16}..."
else
    echo -e "${RED}❌ predictions_v1.0.json NOT FOUND${NC}"
    exit 1
fi

if [ -f "$PREDICTIONS_CSV" ]; then
    SIZE=$(du -h "$PREDICTIONS_CSV" | awk '{print $1}')
    SHA256=$(sha256sum "$PREDICTIONS_CSV" | awk '{print $1}')
    echo -e "${GREEN}✅ predictions_flat_v1.0.csv${NC} (${SIZE})"
    echo "   SHA256: ${SHA256:0:16}..."
else
    echo -e "${RED}❌ predictions_flat_v1.0.csv NOT FOUND${NC}"
    exit 1
fi

if [ -f "$AUDIT_LOG" ]; then
    SIZE=$(du -h "$AUDIT_LOG" | awk '{print $1}')
    SHA256=$(sha256sum "$AUDIT_LOG" | awk '{print $1}')
    echo -e "${GREEN}✅ audit_log.json${NC} (${SIZE})"
    echo "   SHA256: ${SHA256:0:16}..."
else
    echo -e "${RED}❌ audit_log.json NOT FOUND${NC}"
    exit 1
fi

echo ""

# ==============================================================================
# Summary
# ==============================================================================
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  SSOT Run Complete ✅${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e "Model: ${GREEN}v1.0-PL-PowerEP${NC}"
echo -e "Alpha: ${GREEN}0.5${NC}"
echo -e "Training Horses: ${GREEN}6,179頭${NC}"
echo -e "Deliverables: ${GREEN}3点セット生成済み${NC}"
echo ""
echo -e "${YELLOW}📊 View outputs:${NC}"
echo -e "  predictions: ${PREDICTIONS_JSON}"
echo -e "  flat CSV:    ${PREDICTIONS_CSV}"
echo -e "  audit log:   ${AUDIT_LOG}"
echo ""
echo -e "${GREEN}🚀 SSOT証明完了${NC}"
