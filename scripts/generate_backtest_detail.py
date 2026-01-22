#!/usr/bin/env python3
"""
Generate backtest_detail.csv from predictions_*_flat.csv
1レース1行で pred_top3/top5 と actual_top3/top5 を出力
"""

import os
import glob
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path("/home/user/eoi-pl")
BACKTEST_DIR = PROJECT_ROOT / "backtest"

def main():
    print("=" * 70)
    print("Generate backtest_detail.csv")
    print("=" * 70)
    
    # 全predictions_*_flat.csv を読み込み
    flat_files = sorted(glob.glob(str(BACKTEST_DIR / "predictions_*_flat.csv")))
    
    print(f"\nFound {len(flat_files)} flat CSV files")
    
    all_races = []
    
    for flat_file in flat_files:
        df = pd.read_csv(flat_file)
        
        # date列から日付取得
        if 'date' in df.columns:
            date = df['date'].iloc[0]
        else:
            # ファイル名から抽出
            date = os.path.basename(flat_file).replace('predictions_', '').replace('_flat.csv', '')
        
        # race_id でグループ化
        for race_id, group in df.groupby('race_id'):
            # Top5のみ（rank_pred <= 5）
            top5 = group[group['rank_pred'] <= 5].sort_values('rank_pred')
            
            if len(top5) == 0:
                continue
            
            # pred_top3/top5
            pred_top3 = top5[top5['rank_pred'] <= 3]['umaban'].tolist()
            pred_top5 = top5['umaban'].tolist()
            
            # actual_top3/top5（actual_rank が有効なもの）
            actual = group[group['actual_rank'].notna() & (group['actual_rank'] > 0)].sort_values('actual_rank')
            actual_top3 = actual[actual['actual_rank'] <= 3]['umaban'].tolist()
            actual_top5 = actual[actual['actual_rank'] <= 5]['umaban'].tolist()
            
            # P_win top5（文字列化）
            pred_pwin_top5 = top5['P_win'].tolist()
            
            all_races.append({
                'date': date,
                'race_id': race_id,
                'pred_top3': '|'.join(map(str, pred_top3)),
                'pred_top5': '|'.join(map(str, pred_top5)),
                'actual_top3': '|'.join(map(str, actual_top3)),
                'actual_top5': '|'.join(map(str, actual_top5)),
                'pred_pwin_top5': '|'.join(f"{x:.6f}" for x in pred_pwin_top5)
            })
    
    # DataFrame化
    detail_df = pd.DataFrame(all_races)
    
    # 保存
    output_path = BACKTEST_DIR / "backtest_detail.csv"
    detail_df.to_csv(output_path, index=False)
    
    print(f"\n✅ Generated: {output_path}")
    print(f"   Total races: {len(detail_df)}")
    print(f"\n【Sample (first 5 rows)】")
    print(detail_df.head(5).to_string(index=False))
    
    return 0

if __name__ == "__main__":
    exit(main())
