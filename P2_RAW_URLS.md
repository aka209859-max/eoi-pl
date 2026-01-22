# P2 監査実証 - GitHub Raw URLs

**Repository**: https://github.com/aka209859-max/eoi-pl  
**Commit**: cf86d81 (pending push)  
**Branch**: main

---

## 📂 成果物の raw URL（外部検証用）

### 1. backtest_summary.csv
**GitHub blob**: https://github.com/aka209859-max/eoi-pl/blob/main/backtest/backtest_summary.csv  
**GitHub raw**: https://raw.githubusercontent.com/aka209859-max/eoi-pl/main/backtest/backtest_summary.csv

### 2. backtest_report.md
**GitHub blob**: https://github.com/aka209859-max/eoi-pl/blob/main/backtest/backtest_report.md  
**GitHub raw**: https://raw.githubusercontent.com/aka209859-max/eoi-pl/main/backtest/backtest_report.md

### 3. walkforward_backtest.py
**GitHub blob**: https://github.com/aka209859-max/eoi-pl/blob/main/scripts/walkforward_backtest.py  
**GitHub raw**: https://raw.githubusercontent.com/aka209859-max/eoi-pl/main/scripts/walkforward_backtest.py

---

## 🔍 外部検証手順

### ステップ1: Summary CSVをダウンロード
```bash
wget https://raw.githubusercontent.com/aka209859-max/eoi-pl/main/backtest/backtest_summary.csv
```

### ステップ2: 手計算で検証
```python
import pandas as pd
df = pd.read_csv('backtest_summary.csv')
total = df[df['date'] == 'TOTAL'].iloc[0]

print(f"Top1: {total['top1_hits']} / {total['races']} = {total['top1_rate']:.4f}")
print(f"Top3: {total['top3_hits']} / {total['races']} = {total['top3_rate']:.4f}")
print(f"Top5: {total['top5_hits']} / {total['races']} = {total['top5_rate']:.4f}")
```

### ステップ3: スクリプトをダウンロード＆実行
```bash
wget https://raw.githubusercontent.com/aka209859-max/eoi-pl/main/scripts/walkforward_backtest.py
python3 walkforward_backtest.py
```

---

## ✅ raw URL の利点

1. **直接ダウンロード可能**: `wget`, `curl` で即取得
2. **コード実行可能**: Pythonで直接実行可能
3. **外部検証可能**: GitHub外からでも検証可能
4. **バージョン固定**: コミットハッシュで固定化

---

**Status**: raw URL準備完了（Push後に有効化）
