# Auditable Backtest Report v2 - EOI-PL v1.0-Prime

**Generated**: 2026-01-22 09:36:55 JST

## Overview

- **Period**: 2025-01 (30 days)
- **Model**: PL+PowerEP (α=0.5)
- **SSOT**: v1.0-ssot
- **Repository**: https://github.com/aka209859-max/eoi-pl
- **Prohibition**: odds_used=false, popularity not used
- **Reproducibility**: One-command `python scripts/compute_backtest_summary_v2.py`

## Metric Definitions

- **Top3≥1**: |Pred ∩ Actual| ≥ 1 (any 1 hit in top3)
- **Top3≥2**: |Pred ∩ Actual| ≥ 2 (at least 2 shared)
- **Top3=3**: |Pred ∩ Actual| = 3 (exact unordered match)
- **Top5≥3**: |Pred ∩ Actual| ≥ 3 (at least 3 shared in top5)
- **Top5=5**: |Pred ∩ Actual| = 5 (full unordered match)

Example: pred_top3='8|5|2', actual_top3='8|7|9' → overlap={8} → Top3≥1=1, Top3≥2=0, Top3=3=0

## Overall Results (929 races)

- **Top3≥1**: 853/929 (91.82%)
- **Top3≥2**: 476/929 (51.24%)
- **Top3=3**: 68/929 (7.32%)
- **Top5≥3**: 731/929 (78.69%)
- **Top5=5**: 36/929 (3.88%)

**Verification**: Top3≥1 and Top5≥1 match existing backtest_summary.csv ✅

## Daily Examples (First 5 days)

- **20250101**: 33 races; Top3≥1 30 (90.91%); Top3≥2 19 (57.58%); Top3=3 2 (6.06%)
- **20250102**: 36 races; Top3≥1 34 (94.44%); Top3≥2 23 (63.89%); Top3=3 0 (0.00%)
- **20250103**: 36 races; Top3≥1 33 (91.67%); Top3≥2 17 (47.22%); Top3=3 2 (5.56%)
- **20250104**: 48 races; Top3≥1 46 (95.83%); Top3≥2 22 (45.83%); Top3=3 3 (6.25%)
- **20250105**: 22 races; Top3≥1 22 (100.00%); Top3≥2 9 (40.91%); Top3=3 2 (9.09%)

*(Remaining days in backtest_summary_v2.csv)*

## Artifacts

- `backtest/backtest_detail.csv`: Per-race detail (929 rows)
- `backtest/backtest_summary_v2.csv`: Daily + TOTAL rows
- `backtest/backtest_summary_v2.json`: Audit-friendly format
- `backtest/backtest_report_v2.md`: This file

## Reproducibility

```bash
python scripts/compute_backtest_summary_v2.py
```

## Limitations

- Simplified PL model (features: avg_rank only)
- No betting verification
- No calibration applied

## Future Improvements

- Complete PL+PowerEP implementation (all features)
- Betting optimization
- External audit
