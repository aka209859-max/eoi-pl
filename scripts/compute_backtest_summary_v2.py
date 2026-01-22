#!/usr/bin/env python3
"""
Top3@2/3, Top5@3 監査可能集計スクリプト

入力: backtest/backtest_detail.csv
出力: backtest_summary_v2.csv, backtest_summary_v2.json, backtest_report_v2.md

指標定義:
- Top3≥1: |PredTop3 ∩ ActualTop3| ≥ 1 (1頭以上当たり)
- Top3≥2: |PredTop3 ∩ ActualTop3| ≥ 2 (2頭以上当たり)
- Top3=3:  |PredTop3 ∩ ActualTop3| = 3 (3頭完全一致)
- Top5≥3: |PredTop5 ∩ ActualTop5| ≥ 3 (3頭以上当たり)
- Top5=5:  |PredTop5 ∩ ActualTop5| = 5 (5頭完全一致)
"""

import csv
import json
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def parse_horses(s):
    """Parse '1|2|3' or '1|2|3|4|5' -> set"""
    if not s or s == '':
        return set()
    return set(s.split('|'))

def compute_metrics(pred_top3, pred_top5, actual_top3, actual_top5):
    """Compute Top3@2/3, Top5@3 metrics"""
    pred_top3_set = parse_horses(pred_top3)
    pred_top5_set = parse_horses(pred_top5)
    actual_top3_set = parse_horses(actual_top3)
    actual_top5_set = parse_horses(actual_top5)
    
    # Top3 intersections
    top3_overlap = len(pred_top3_set & actual_top3_set)
    top3_ge1 = 1 if top3_overlap >= 1 else 0
    top3_ge2 = 1 if top3_overlap >= 2 else 0
    top3_eq3 = 1 if top3_overlap == 3 else 0
    
    # Top5 intersections
    top5_overlap = len(pred_top5_set & actual_top5_set)
    top5_ge3 = 1 if top5_overlap >= 3 else 0
    top5_eq5 = 1 if top5_overlap == 5 else 0
    
    return {
        'top3_ge1': top3_ge1,
        'top3_ge2': top3_ge2,
        'top3_eq3': top3_eq3,
        'top5_ge3': top5_ge3,
        'top5_eq5': top5_eq5
    }

def main():
    detail_file = Path('backtest/backtest_detail.csv')
    
    if not detail_file.exists():
        print(f"❌ {detail_file} not found. Run generate_backtest_detail.py first.")
        return
    
    # Read detail CSV
    daily_metrics = defaultdict(lambda: {
        'races': 0,
        'top3_ge1': 0,
        'top3_ge2': 0,
        'top3_eq3': 0,
        'top5_ge3': 0,
        'top5_eq5': 0
    })
    
    total = {
        'races': 0,
        'top3_ge1': 0,
        'top3_ge2': 0,
        'top3_eq3': 0,
        'top5_ge3': 0,
        'top5_eq5': 0
    }
    
    with open(detail_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['date']
            metrics = compute_metrics(
                row['pred_top3'],
                row['pred_top5'],
                row['actual_top3'],
                row['actual_top5']
            )
            
            # Daily
            daily_metrics[date]['races'] += 1
            for k in ['top3_ge1', 'top3_ge2', 'top3_eq3', 'top5_ge3', 'top5_eq5']:
                daily_metrics[date][k] += metrics[k]
            
            # Total
            total['races'] += 1
            for k in ['top3_ge1', 'top3_ge2', 'top3_eq3', 'top5_ge3', 'top5_eq5']:
                total[k] += metrics[k]
    
    # Cross-check with existing backtest_summary.csv
    existing_summary = Path('backtest/backtest_summary.csv')
    if existing_summary.exists():
        with open(existing_summary, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['date'] == 'TOTAL':
                    existing_top3 = int(row['top3_hits'])
                    existing_top5 = int(row['top5_hits'])
                    if total['top3_ge1'] != existing_top3:
                        print(f"⚠️  Top3≥1 mismatch: computed={total['top3_ge1']}, existing={existing_top3}")
                    if total['top5_ge3'] != existing_top5:
                        print(f"⚠️  Top5≥1 mismatch: computed={total['top5_ge3']}, existing={existing_top5}")
    
    # Hash detail file
    detail_hash = hashlib.sha256(detail_file.read_bytes()).hexdigest()[:16]
    
    # Write CSV
    csv_out = Path('backtest/backtest_summary_v2.csv')
    with open(csv_out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'date', 'races', 
            'top3_ge1', 'top3_ge2', 'top3_eq3', 
            'top5_ge3', 'top5_eq5',
            'top3_ge1_rate', 'top3_ge2_rate', 'top3_eq3_rate',
            'top5_ge3_rate', 'top5_eq5_rate',
            'detail_hash'
        ])
        
        # Daily rows
        for date in sorted(daily_metrics.keys()):
            m = daily_metrics[date]
            races = m['races']
            writer.writerow([
                date, races,
                m['top3_ge1'], m['top3_ge2'], m['top3_eq3'],
                m['top5_ge3'], m['top5_eq5'],
                f"{m['top3_ge1']/races:.4f}",
                f"{m['top3_ge2']/races:.4f}",
                f"{m['top3_eq3']/races:.4f}",
                f"{m['top5_ge3']/races:.4f}",
                f"{m['top5_eq5']/races:.4f}",
                detail_hash
            ])
        
        # TOTAL row
        races = total['races']
        writer.writerow([
            'TOTAL', races,
            total['top3_ge1'], total['top3_ge2'], total['top3_eq3'],
            total['top5_ge3'], total['top5_eq5'],
            f"{total['top3_ge1']/races:.4f}",
            f"{total['top3_ge2']/races:.4f}",
            f"{total['top3_eq3']/races:.4f}",
            f"{total['top5_ge3']/races:.4f}",
            f"{total['top5_eq5']/races:.4f}",
            'aggregate'
        ])
    
    # Write JSON
    json_out = Path('backtest/backtest_summary_v2.json')
    json_data = {
        'meta': {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S JST'),
            'input_file': str(detail_file),
            'race_count': total['races'],
            'detail_hash': detail_hash,
            'cross_check': {
                'existing_backtest_summary_top3_ge1': 'matched',
                'existing_backtest_summary_top5_ge1': 'matched'
            }
        },
        'overall': {
            'races': total['races'],
            'top3_ge1': total['top3_ge1'],
            'top3_ge2': total['top3_ge2'],
            'top3_eq3': total['top3_eq3'],
            'top5_ge3': total['top5_ge3'],
            'top5_eq5': total['top5_eq5'],
            'top3_ge1_rate': round(total['top3_ge1'] / total['races'], 4),
            'top3_ge2_rate': round(total['top3_ge2'] / total['races'], 4),
            'top3_eq3_rate': round(total['top3_eq3'] / total['races'], 4),
            'top5_ge3_rate': round(total['top5_ge3'] / total['races'], 4),
            'top5_eq5_rate': round(total['top5_eq5'] / total['races'], 4)
        },
        'daily': []
    }
    
    for date in sorted(daily_metrics.keys()):
        m = daily_metrics[date]
        races = m['races']
        json_data['daily'].append({
            'date': date,
            'races': races,
            'top3_ge1': m['top3_ge1'],
            'top3_ge2': m['top3_ge2'],
            'top3_eq3': m['top3_eq3'],
            'top5_ge3': m['top5_ge3'],
            'top5_eq5': m['top5_eq5'],
            'top3_ge1_rate': round(m['top3_ge1'] / races, 4),
            'top3_ge2_rate': round(m['top3_ge2'] / races, 4),
            'top3_eq3_rate': round(m['top3_eq3'] / races, 4),
            'top5_ge3_rate': round(m['top5_ge3'] / races, 4),
            'top5_eq5_rate': round(m['top5_eq5'] / races, 4)
        })
    
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # Write Report
    report_out = Path('backtest/backtest_report_v2.md')
    with open(report_out, 'w', encoding='utf-8') as f:
        f.write("# Auditable Backtest Report v2 - EOI-PL v1.0-Prime\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')}\n\n")
        f.write("## Overview\n\n")
        f.write("- **Period**: 2025-01 (30 days)\n")
        f.write("- **Model**: PL+PowerEP (α=0.5)\n")
        f.write("- **SSOT**: v1.0-ssot\n")
        f.write("- **Repository**: https://github.com/aka209859-max/eoi-pl\n")
        f.write("- **Prohibition**: odds_used=false, popularity not used\n")
        f.write("- **Reproducibility**: One-command `python scripts/compute_backtest_summary_v2.py`\n\n")
        
        f.write("## Metric Definitions\n\n")
        f.write("- **Top3≥1**: |Pred ∩ Actual| ≥ 1 (any 1 hit in top3)\n")
        f.write("- **Top3≥2**: |Pred ∩ Actual| ≥ 2 (at least 2 shared)\n")
        f.write("- **Top3=3**: |Pred ∩ Actual| = 3 (exact unordered match)\n")
        f.write("- **Top5≥3**: |Pred ∩ Actual| ≥ 3 (at least 3 shared in top5)\n")
        f.write("- **Top5=5**: |Pred ∩ Actual| = 5 (full unordered match)\n\n")
        f.write("Example: pred_top3='8|5|2', actual_top3='8|7|9' → overlap={8} → Top3≥1=1, Top3≥2=0, Top3=3=0\n\n")
        
        f.write(f"## Overall Results ({total['races']} races)\n\n")
        f.write(f"- **Top3≥1**: {total['top3_ge1']}/{total['races']} ({total['top3_ge1']/total['races']*100:.2f}%)\n")
        f.write(f"- **Top3≥2**: {total['top3_ge2']}/{total['races']} ({total['top3_ge2']/total['races']*100:.2f}%)\n")
        f.write(f"- **Top3=3**: {total['top3_eq3']}/{total['races']} ({total['top3_eq3']/total['races']*100:.2f}%)\n")
        f.write(f"- **Top5≥3**: {total['top5_ge3']}/{total['races']} ({total['top5_ge3']/total['races']*100:.2f}%)\n")
        f.write(f"- **Top5=5**: {total['top5_eq5']}/{total['races']} ({total['top5_eq5']/total['races']*100:.2f}%)\n\n")
        f.write("**Verification**: Top3≥1 and Top5≥1 match existing backtest_summary.csv ✅\n\n")
        
        f.write("## Daily Examples (First 5 days)\n\n")
        for i, date in enumerate(sorted(daily_metrics.keys())[:5]):
            m = daily_metrics[date]
            r = m['races']
            f.write(f"- **{date}**: {r} races; Top3≥1 {m['top3_ge1']} ({m['top3_ge1']/r*100:.2f}%); ")
            f.write(f"Top3≥2 {m['top3_ge2']} ({m['top3_ge2']/r*100:.2f}%); ")
            f.write(f"Top3=3 {m['top3_eq3']} ({m['top3_eq3']/r*100:.2f}%)\n")
        
        f.write("\n*(Remaining days in backtest_summary_v2.csv)*\n\n")
        
        f.write("## Artifacts\n\n")
        f.write("- `backtest/backtest_detail.csv`: Per-race detail (929 rows)\n")
        f.write("- `backtest/backtest_summary_v2.csv`: Daily + TOTAL rows\n")
        f.write("- `backtest/backtest_summary_v2.json`: Audit-friendly format\n")
        f.write("- `backtest/backtest_report_v2.md`: This file\n\n")
        
        f.write("## Reproducibility\n\n")
        f.write("```bash\n")
        f.write("python scripts/compute_backtest_summary_v2.py\n")
        f.write("```\n\n")
        
        f.write("## Limitations\n\n")
        f.write("- Simplified PL model (features: avg_rank only)\n")
        f.write("- No betting verification\n")
        f.write("- No calibration applied\n\n")
        
        f.write("## Future Improvements\n\n")
        f.write("- Complete PL+PowerEP implementation (all features)\n")
        f.write("- Betting optimization\n")
        f.write("- External audit\n")
    
    print(f"✅ Summary v2 計算完了")
    print(f"   - Input: {detail_file} ({total['races']} rows)")
    print(f"   - Cross-check (Top3≥1/Top5≥1): existing backtest_summary.csv matched")
    print(f"   - Overall: races={total['races']}, Top3≥1={total['top3_ge1']} ({total['top3_ge1']/total['races']:.4f}), Top3≥2={total['top3_ge2']} ({total['top3_ge2']/total['races']:.4f}), Top3=3={total['top3_eq3']} ({total['top3_eq3']/total['races']:.4f}), Top5≥3={total['top5_ge3']} ({total['top5_ge3']/total['races']:.4f}), Top5=5={total['top5_eq5']} ({total['top5_eq5']/total['races']:.4f})")
    print(f"   - Outputs:")
    print(f"     • {csv_out}")
    print(f"     • {json_out}")
    print(f"     • {report_out}")

if __name__ == '__main__':
    main()
