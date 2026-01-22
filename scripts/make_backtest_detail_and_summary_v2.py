#!/usr/bin/env python3
"""
Generate backtest_summary_v2 with extended metrics
Top3@1/2/3, Top5@1/3 を監査可能な形で算出
"""

import os
import hashlib
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import pytz

JST = pytz.timezone('Asia/Tokyo')
PROJECT_ROOT = Path("/home/user/eoi-pl")
BACKTEST_DIR = PROJECT_ROOT / "backtest"

# ---- utilities ----
def sha256_file(path):
    """ファイルのSHA256ハッシュを計算"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_set(s):
    """'8|5|2' → {8, 5, 2}"""
    if pd.isna(s) or str(s).strip() == "":
        return set()
    return set(int(x) for x in str(s).split("|") if x != "")

def inter_k(a, b):
    """交集合のサイズ"""
    return len(parse_set(a) & parse_set(b))

def main():
    print("=" * 70)
    print("Generate backtest_summary_v2 (Extended Metrics)")
    print("=" * 70)
    
    # ---- 1) load backtest_detail.csv ----
    detail_path = BACKTEST_DIR / "backtest_detail.csv"
    if not detail_path.exists():
        raise SystemExit(
            f"❌ {detail_path} が見つかりません。"
            "まず scripts/generate_backtest_detail.py を実行してください。"
        )
    
    df = pd.read_csv(detail_path)
    print(f"\n✅ Loaded: {detail_path}")
    print(f"   Total races: {len(df)}")
    
    # ---- 2) compute ks ----
    print("\n📊 Computing intersection sizes...")
    df["top3_k"] = df.apply(lambda r: inter_k(r["pred_top3"], r["actual_top3"]), axis=1)
    df["top5_k"] = df.apply(lambda r: inter_k(r["pred_top5"], r["actual_top5"]), axis=1)
    
    # ---- 3) daily aggregation ----
    def agg_day(g):
        races = len(g)
        return pd.Series({
            "races": races,
            "top3_at1_hits": int((g["top3_k"] >= 1).sum()),
            "top3_at2_hits": int((g["top3_k"] >= 2).sum()),
            "top3_at3_hits": int((g["top3_k"] >= 3).sum()),
            "top5_at1_hits": int((g["top5_k"] >= 1).sum()),
            "top5_at3_hits": int((g["top5_k"] >= 3).sum()),
            "top3_at1_rate": float((g["top3_k"] >= 1).mean()),
            "top3_at2_rate": float((g["top3_k"] >= 2).mean()),
            "top3_at3_rate": float((g["top3_k"] >= 3).mean()),
            "top5_at1_rate": float((g["top5_k"] >= 1).mean()),
            "top5_at3_rate": float((g["top5_k"] >= 3).mean()),
        })
    
    print("📊 Aggregating by date...")
    daily = df.groupby("date", as_index=False).apply(agg_day).reset_index(drop=True)
    
    # ---- 4) total row ----
    total = agg_day(df)
    total_row = pd.DataFrame([{
        "date": "TOTAL",
        **total.to_dict()
    }])
    
    out = pd.concat([daily, total_row], ignore_index=True)
    
    # ---- 5) attach data_hash ----
    detail_hash = sha256_file(detail_path)
    out["data_hash"] = detail_hash[:16]  # 短縮版
    
    # ---- 6) save CSV ----
    out_csv = BACKTEST_DIR / "backtest_summary_v2.csv"
    out.to_csv(out_csv, index=False)
    print(f"\n✅ Saved: {out_csv}")
    
    # ---- 7) verification against backtest_summary.csv ----
    print("\n" + "=" * 70)
    print("Verification against backtest_summary.csv")
    print("=" * 70)
    
    old_csv = BACKTEST_DIR / "backtest_summary.csv"
    if old_csv.exists():
        old_df = pd.read_csv(old_csv)
        old_total = old_df[old_df['date'] == 'TOTAL'].iloc[0]
        new_total = out[out['date'] == 'TOTAL'].iloc[0]
        
        # Top3@1 should equal old top3_hits
        old_top3_hits = int(old_total['top3_hits'])
        new_top3_at1_hits = int(new_total['top3_at1_hits'])
        
        # Top5@1 should equal old top5_hits
        old_top5_hits = int(old_total['top5_hits'])
        new_top5_at1_hits = int(new_total['top5_at1_hits'])
        
        print(f"\nTop3@1 verification:")
        print(f"  Old top3_hits: {old_top3_hits}")
        print(f"  New top3_at1_hits: {new_top3_at1_hits}")
        if old_top3_hits == new_top3_at1_hits:
            print(f"  ✅ MATCH")
        else:
            raise SystemExit(f"  ❌ MISMATCH - Bug detected!")
        
        print(f"\nTop5@1 verification:")
        print(f"  Old top5_hits: {old_top5_hits}")
        print(f"  New top5_at1_hits: {new_top5_at1_hits}")
        if old_top5_hits == new_top5_at1_hits:
            print(f"  ✅ MATCH")
        else:
            raise SystemExit(f"  ❌ MISMATCH - Bug detected!")
    
    # ---- 8) save JSON ----
    out_json = BACKTEST_DIR / "backtest_summary_v2.json"
    json_data = {
        "meta": {
            "generated_at": datetime.now(JST).isoformat(),
            "model_version": "v1.0-PL-PowerEP",
            "detail_sha256": detail_hash,
            "total_races": int(new_total['races'])
        },
        "metrics": {
            "top3_at1": {
                "hits": int(new_total['top3_at1_hits']),
                "rate": float(new_total['top3_at1_rate']),
                "definition": "|PredTop3 ∩ ActualTop3| ≥ 1"
            },
            "top3_at2": {
                "hits": int(new_total['top3_at2_hits']),
                "rate": float(new_total['top3_at2_rate']),
                "definition": "|PredTop3 ∩ ActualTop3| ≥ 2"
            },
            "top3_at3": {
                "hits": int(new_total['top3_at3_hits']),
                "rate": float(new_total['top3_at3_rate']),
                "definition": "|PredTop3 ∩ ActualTop3| = 3 (完全一致)"
            },
            "top5_at1": {
                "hits": int(new_total['top5_at1_hits']),
                "rate": float(new_total['top5_at1_rate']),
                "definition": "|PredTop5 ∩ ActualTop5| ≥ 1"
            },
            "top5_at3": {
                "hits": int(new_total['top5_at3_hits']),
                "rate": float(new_total['top5_at3_rate']),
                "definition": "|PredTop5 ∩ ActualTop5| ≥ 3"
            }
        },
        "daily": out[out['date'] != 'TOTAL'].to_dict('records')
    }
    
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved: {out_json}")
    
    # ---- 9) save Markdown report ----
    out_md = BACKTEST_DIR / "backtest_report_v2.md"
    
    report = f"""# Backtest Report v2 - Extended Metrics

**Generated**: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')} JST  
**Model**: PL+PowerEP (α=0.5)  
**SSOT**: v1.0-ssot  
**Detail SHA256**: {detail_hash}

---

## 指標定義

### Top3@k: 予測Top3と実際Top3の交集合サイズ

- **Top3@1**: |PredTop3 ∩ ActualTop3| ≥ 1（少なくとも1頭一致）
- **Top3@2**: |PredTop3 ∩ ActualTop3| ≥ 2（少なくとも2頭一致）
- **Top3@3**: |PredTop3 ∩ ActualTop3| = 3（完全一致、順不同）

### Top5@k: 予測Top5と実際Top5の交集合サイズ

- **Top5@1**: |PredTop5 ∩ ActualTop5| ≥ 1（少なくとも1頭一致）
- **Top5@3**: |PredTop5 ∩ ActualTop5| ≥ 3（少なくとも3頭一致）

---

## 全体結果（TOTAL）

| 指標 | 命中数 | 命中率 | 定義 |
|------|--------|--------|------|
| **Top3@1** | {int(new_total['top3_at1_hits'])} / {int(new_total['races'])} | **{new_total['top3_at1_rate']*100:.1f}%** | 少なくとも1頭一致 |
| **Top3@2** | {int(new_total['top3_at2_hits'])} / {int(new_total['races'])} | **{new_total['top3_at2_rate']*100:.1f}%** | 少なくとも2頭一致 |
| **Top3@3** | {int(new_total['top3_at3_hits'])} / {int(new_total['races'])} | **{new_total['top3_at3_rate']*100:.1f}%** | 完全一致（順不同） |
| **Top5@1** | {int(new_total['top5_at1_hits'])} / {int(new_total['races'])} | **{new_total['top5_at1_rate']*100:.1f}%** | 少なくとも1頭一致 |
| **Top5@3** | {int(new_total['top5_at3_hits'])} / {int(new_total['races'])} | **{new_total['top5_at3_rate']*100:.1f}%** | 少なくとも3頭一致 |

---

## 検証結果

### 既存 backtest_summary.csv との突合

- ✅ **Top3@1 = old.top3_hits**: {old_top3_hits} = {new_top3_at1_hits} → MATCH
- ✅ **Top5@1 = old.top5_hits**: {old_top5_hits} = {new_top5_at1_hits} → MATCH

---

## 再現手順

### Step 1: 詳細データ生成
```bash
python3 scripts/generate_backtest_detail.py
```

### Step 2: 集計（本スクリプト）
```bash
python3 scripts/make_backtest_detail_and_summary_v2.py
```

### 成果物
- `backtest/backtest_detail.csv` ({len(df)}レース)
- `backtest/backtest_summary_v2.csv` (日別+TOTAL)
- `backtest/backtest_summary_v2.json` (監査用)
- `backtest/backtest_report_v2.md` (本レポート)

### SHA256
- detail.csv: `{detail_hash}`
- summary_v2.csv: `{sha256_file(out_csv)}`

---

## 外部検証

```bash
# ダウンロード
wget https://raw.githubusercontent.com/aka209859-max/eoi-pl/main/backtest/backtest_detail.csv
wget https://raw.githubusercontent.com/aka209859-max/eoi-pl/main/backtest/backtest_summary_v2.csv

# 検証
sha256sum backtest_detail.csv
sha256sum backtest_summary_v2.csv

# 手計算確認
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('backtest_detail.csv')
def parse_set(s):
    if pd.isna(s) or str(s).strip() == "":
        return set()
    return set(int(x) for x in str(s).split("|") if x != "")

df['top3_k'] = df.apply(lambda r: len(parse_set(r['pred_top3']) & parse_set(r['actual_top3'])), axis=1)
print(f"Top3@1: {{(df['top3_k'] >= 1).sum()}} / {{len(df)}} = {{(df['top3_k'] >= 1).mean():.4f}}")
print(f"Top3@2: {{(df['top3_k'] >= 2).sum()}} / {{len(df)}} = {{(df['top3_k'] >= 2).mean():.4f}}")
print(f"Top3@3: {{(df['top3_k'] >= 3).sum()}} / {{len(df)}} = {{(df['top3_k'] >= 3).mean():.4f}}")
EOF
```

---

**Status**: ✅ 完了  
**Generated**: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')} JST
"""
    
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Saved: {out_md}")
    
    # ---- 10) Final summary ----
    print("\n" + "=" * 70)
    print("TOTAL Results (backtest_summary_v2.csv)")
    print("=" * 70)
    print(out[out['date'] == 'TOTAL'].to_string(index=False))
    
    print("\n" + "=" * 70)
    print("SHA256 Hashes")
    print("=" * 70)
    print(f"backtest_detail.csv:     {detail_hash}")
    print(f"backtest_summary_v2.csv: {sha256_file(out_csv)}")
    print(f"backtest_summary_v2.json: {sha256_file(out_json)}")
    
    print("\n" + "=" * 70)
    print("✅ All tasks completed successfully")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    exit(main())
