#!/usr/bin/env python3
"""
============================================================
EOI-PL v1.0-Prime - 配信用予想出力生成
============================================================
Purpose: 2025年1月データから馬名付きの配信フォーマット生成

Input: backtest/predictions_YYYYMMDD.json
Output: backtest/forecast_output_YYYYMMDD.txt

仕様:
- 馬名を16文字にパディング（全角空白）
- 推奨度: p1 - p2 差分で A/B/C/N ランク判定
- 星表記: ★★★★☆
- レース別に出力

CEO Directive: 馬名必須（bamei_mapping.csv統合済み）
============================================================
"""

import json
import re
from pathlib import Path
from datetime import datetime
import pytz

JST = pytz.timezone('Asia/Tokyo')

# Project paths
PROJECT_ROOT = Path("/home/user/eoi-pl")
BACKTEST_DIR = PROJECT_ROOT / "backtest"

# 推奨度の星表記
REC_LABELS = {
    'S': '★★★★★',  # 最高推奨 (p1-p2 > 20%)
    'A': '★★★★☆',  # 高推奨 (p1-p2 > 10%)
    'B': '★★★☆☆',  # 中推奨 (p1-p2 > 5%)
    'C': '★★☆☆☆',  # 低推奨 (p1-p2 > 2%)
    'N': '★☆☆☆☆',  # 非推奨 (p1-p2 <= 2%)
}

# 競馬場コード → 名前マッピング
VENUE_NAMES = {
    '30': '帯広', '35': '門別', '36': '北見', '42': '盛岡', '43': '水沢',
    '44': '上山', '45': '浦和', '46': '船橋', '47': '大井', '48': '川崎',
    '50': '金沢', '51': '笠松', '54': '名古屋', '55': '紀三井寺',
    '58': '園田', '59': '姫路', '60': '益田', '61': '福山', '62': '高知',
    '63': '佐賀', '65': '荒尾', '66': '中津', '83': '旭川', '84': '札幌'
}

def get_recommendation_label(p1: float, p2: float) -> str:
    """推奨度ラベル判定"""
    diff = (p1 - p2) * 100  # パーセント差
    if diff > 20:
        return 'S'
    elif diff > 10:
        return 'A'
    elif diff > 5:
        return 'B'
    elif diff > 2:
        return 'C'
    else:
        return 'N'

def format_horse_name(bamei: str) -> str:
    """馬名を16文字にパディング（全角空白）"""
    # Unicode escapeをデコード（例: \u30c9 → ド）
    if '\\u' in bamei:
        try:
            bamei = bamei.encode('utf-8').decode('unicode-escape')
        except:
            pass
    
    # 末尾の全角空白を削除
    bamei = bamei.strip('　').strip()
    
    # 16文字になるまで全角空白で埋める
    while len(bamei) < 16:
        bamei += '　'
    
    # 16文字に切り詰め
    return bamei[:16]

def generate_forecast_output(date_str: str):
    """配信用フォーマット生成"""
    json_file = BACKTEST_DIR / f"predictions_{date_str}.json"
    
    if not json_file.exists():
        print(f"❌ {json_file} not found")
        return
    
    # JSON読み込み
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 出力ファイル
    output_file = BACKTEST_DIR / f"forecast_output_{date_str}.txt"
    
    # ヘッダー
    generated_at = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
    output_lines = [
        "【EOI-PL v1.0-Prime 地方競馬予想】",
        f"生成日時: {generated_at}",
        "",
        f"【{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}】",
        ""
    ]
    
    # レース別に処理
    for race in data['races']:
        race_id = race['race_id']
        horses = race['horses']
        
        # race_id から情報抽出: 2025_0101_54_01
        parts = race_id.split('_')
        year, mmdd, venue_code, race_no = parts[0], parts[1], parts[2], parts[3]
        venue_name = VENUE_NAMES.get(venue_code, f"場所{venue_code}")
        
        # Top5
        top5 = horses[:5]
        
        # 推奨度判定（p1 - p2）
        if len(top5) >= 2:
            p1 = top5[0]['P_win']
            p2 = top5[1]['P_win']
            rec_label = get_recommendation_label(p1, p2)
            rec_stars = REC_LABELS[rec_label]
        else:
            rec_label = 'N'
            rec_stars = REC_LABELS['N']
        
        # レースヘッダー
        output_lines.append(f"【{venue_name} {race_no}R】推奨度：{rec_label} {rec_stars}")
        output_lines.append("")
        output_lines.append("【Top5予想】")
        
        # 上位5頭
        for rank, horse in enumerate(top5, 1):
            bamei_padded = format_horse_name(horse['bamei'])
            umaban = horse['umaban']
            p_win_pct = horse['P_win'] * 100
            output_lines.append(f"{rank}. {bamei_padded} ({umaban:2d}番) 単勝率: {p_win_pct:5.1f}%")
        
        output_lines.append("")
        
        # 確率メモ
        if len(top5) >= 3:
            p1 = top5[0]['P_win'] * 100
            p2 = top5[1]['P_win'] * 100
            top3_sum = sum(h['P_win'] for h in top5[:3]) * 100
            output_lines.append("【確率メモ】")
            output_lines.append(f"p1 - p2 = {p1 - p2:5.1f}% (集中度)")
            output_lines.append(f"Top3合計 = {top3_sum:5.1f}%")
        
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
    
    # ファイル出力
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"✅ {output_file} 生成完了")
    
    # サンプル表示（先頭30行）
    print("\n【先頭30行サンプル】")
    for i, line in enumerate(output_lines[:30], 1):
        print(line)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 generate_forecast_output.py YYYYMMDD")
        print("Example: python3 generate_forecast_output.py 20250101")
        sys.exit(1)
    
    date_str = sys.argv[1]
    generate_forecast_output(date_str)
