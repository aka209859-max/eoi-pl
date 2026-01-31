import os
import re
import csv
from pathlib import Path
from collections import Counter

# 設定
TARGET_DIR = r'E:\UmaConn\data'  # .nvd ファイルのディレクトリ
OUTPUT_CSV = r'C:\Users\ihaji\recovered_horse_names_v2.csv'
SOURCE_ENCODING = 'cp932'  # Shift_JIS (Windows)

def is_valid_horse_name(text):
    """
    馬名の妥当性チェック（厳格版）
    - 長さ: 3~18文字（通常の馬名の範囲）
    - カタカナ: 90%以上
    - 小文字（ァィゥェォ等）で始まらない
    - 末尾が長音記号（ー）や中黒（・）でない
    """
    # 長さチェック
    if not (3 <= len(text) <= 18):
        return False
    
    # 小文字カタカナで始まる場合は除外
    if text[0] in 'ァィゥェォヵヶッャュョヮ':
        return False
    
    # 末尾チェック
    if text[-1] in 'ー・':
        return False
    
    # カタカナの割合が90%以上
    katakana_count = sum(1 for c in text if '\u30A0' <= c <= '\u30FF')
    if (katakana_count / len(text)) < 0.9:
        return False
    
    # 同じ文字の連続が3回以上ある場合は除外
    if re.search(r'(.)\1{2,}', text):
        return False
    
    return True

def extract_horse_names_from_nvd(file_path):
    """
    .nvd ファイルからバイナリ読み取り → Shift_JIS でデコード → 馬名抽出
    """
    horse_names = []
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Shift_JIS でデコード試行
        try:
            decoded = data.decode(SOURCE_ENCODING, errors='ignore')
        except:
            return horse_names
        
        # カタカナ連続パターンを抽出（3~18文字）
        pattern = r'[\u30A0-\u30FF]{3,18}'
        matches = re.findall(pattern, decoded)
        
        for match in matches:
            if is_valid_horse_name(match):
                horse_names.append(match)
    
    except Exception as e:
        pass  # エラーは無視
    
    return horse_names

def main():
    all_horse_names = []
    
    # .nvd ファイルを再帰的に検索
    nvd_files = list(Path(TARGET_DIR).rglob('*.nvd'))
    
    print(f"Found {len(nvd_files)} .nvd files")
    print("Extracting horse names...")
    
    for i, file_path in enumerate(nvd_files, 1):
        if i % 100 == 0:
            print(f"  Processing {i}/{len(nvd_files)}...")
        
        names = extract_horse_names_from_nvd(file_path)
        all_horse_names.extend(names)
    
    # 出現回数でフィルタリング（2回以上出現した馬名のみ抽出）
    name_counts = Counter(all_horse_names)
    filtered_names = {name for name, count in name_counts.items() if count >= 2}
    
    print(f"\n✅ Extracted {len(all_horse_names)} total occurrences")
    print(f"✅ Unique names (appeared 2+ times): {len(filtered_names)}")
    
    # CSV 出力（出現回数順）
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:  # UTF-8 BOM
        writer = csv.writer(f)
        writer.writerow(['bamei', 'count'])
        
        # 出現回数の多い順にソート
        for name, count in name_counts.most_common():
            if count >= 2:  # 2回以上出現した馬名のみ
                writer.writerow([name, count])
    
    print(f"✅ Saved to: {OUTPUT_CSV}")
    
    # サンプル表示（上位10件）
    print("\n📊 Top 10 most frequent horse names:")
    for i, (name, count) in enumerate(name_counts.most_common(10), 1):
        print(f"  {i}. {name} ({count} times)")

if __name__ == '__main__':
    main()
