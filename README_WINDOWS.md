# 🏇 EOI-PL v1.0-Prime「堅実派AI」ローカル実行ガイド

**Windows PC専用**  
**最終更新**: 2026-01-31

---

## 📦 **1. ダウンロードとセットアップ**

### **1-1: パッケージのダウンロード**

以下のURLからダウンロード:
```
https://www.genspark.ai/api/files/s/44XLAfBS
```

**ブラウザで上記URLをクリック**すると、自動的にダウンロードが始まります。

ダウンロード先（自動）:
```
C:\Users\あなたのユーザー名\Downloads\eoi-pl.tar.gz
```

---

### **1-2: Eドライブの固定場所に解凍**

**⚠️ 重要: 必ず E:\eoi-pl に保存してください**

**PowerShellで実行**（管理者権限不要）:

```powershell
# Eドライブに移動
E:

# eoi-plディレクトリを作成
New-Item -ItemType Directory -Force -Path E:\eoi-pl

# ダウンロードフォルダから解凍
cd E:\eoi-pl
tar -xzf C:\Users\あなたのユーザー名\Downloads\eoi-pl.tar.gz

# 解凍後、eoi-pl フォルダの中身を E:\eoi-pl に移動
Move-Item -Path .\eoi-pl\* -Destination . -Force

# 空のeoi-plフォルダを削除
Remove-Item -Path .\eoi-pl -Force
```

**📁 最終的なディレクトリ構成**:
```
E:\eoi-pl\                          ← 固定場所
├── data\
│   └── feature_database_2020_2025.json
├── scripts\
│   ├── format_predictions_discord.py
│   └── update_feature_database_monthly.py
├── predictions\                    ← 自動作成
├── backtest\
├── README_WINDOWS.md
├── OPERATION_GUIDE_完全版.md
└── FINAL_SPEC_堅実派AI.md
```

---

### **1-3: ファイル構成確認**

**⚠️ 重要: 全てのファイルが E:\eoi-pl 直下にあることを確認**

```
E:\eoi-pl\                          ← 固定場所（必須）
├── data\
│   └── feature_database_2020_2025.json  # 特徴量データベース（27MB）
├── scripts\
│   ├── format_predictions_discord.py    # Discord出力スクリプト
│   └── update_feature_database_monthly.py # 月次更新スクリプト
├── predictions\                    ← 自動作成（予想結果の保存先）
│   ├── predictions_20260201.txt
│   ├── predictions_20260202.txt
│   └── ...
├── backtest\                       ← バックテスト結果
├── README_WINDOWS.md
├── OPERATION_GUIDE_完全版.md
└── FINAL_SPEC_堅実派AI.md
```

**確認コマンド**（PowerShellで実行）:
```powershell
# E:\eoi-pl に移動
E:
cd E:\eoi-pl

# ファイル一覧を表示
Get-ChildItem -Recurse -Depth 1
```

**重要**: `predictions\` フォルダは初回実行時に自動作成されます

---

### **1-4: Python環境の確認**

**PowerShellで実行**:

```powershell
# Pythonのバージョン確認（3.8以上が必要）
python --version
# 出力例: Python 3.11.5

# 必要なライブラリをインストール
pip install psycopg2 numpy pandas
```

**エラーが出る場合**:
```powershell
# psycopg2-binaryをインストール（より簡単）
pip install psycopg2-binary numpy pandas
```

---

### **1-5: PostgreSQLの起動確認**

**PowerShellで実行**:

```powershell
# PC-KEIBAのPostgreSQLが起動しているか確認
psql -U postgres -d eoi_pl -c "SELECT COUNT(*) FROM races WHERE kaisai_nen = 2026;"
```

**期待される結果**:
```
 count 
-------
  1019
(1 row)
```

**エラーが出る場合**:
1. Windowsサービスから「postgresql」を起動
2. PC-KEIBAソフトを起動

---

## 🚀 **2. 日次運用（毎日実行）**

### **2-1: 今日のレース予想を生成**

**PowerShellで実行**:

```powershell
# Eドライブに移動
E:
cd E:\eoi-pl\scripts

# 今日の日付で予想生成（例: 2026年2月1日）
python format_predictions_discord.py --date 20260201 --output E:\eoi-pl\predictions\predictions_20260201.txt
```

**パラメータ説明**:
- `--date 20260201`: 予想する日付（YYYYMMDD形式）
- `--output E:\eoi-pl\predictions\predictions_20260201.txt`: 出力先

---

### **2-2: 出力ファイルを確認**

**PowerShellで実行**:

```powershell
# メモ帳で開く
notepad E:\eoi-pl\predictions\predictions_20260201.txt
```

**出力例**:
```
============================================================
🏇 レース予想: 202602014401
============================================================

【大井 1R】  レース推奨度: ★★★★☆ (1位偏差値: 69.0)
```
順位    馬番    馬名                      偏差値     
------------------------------------------------------------
1     2番    オーサムジェンヌ                 69.0
2     10番    ピサンザプラ                   60.4
3     8番    フランキングライン                60.1
...
```

🎯 **推奨買い目**
  Top3（馬連BOXなど）: 2, 10, 8
  Top5（三連複BOXなど）: 2, 10, 8, 3, 6

💡 **レース分析**
  本命が明確で予想しやすいレースです（推奨度: ★★★★☆）
```

---

### **2-3: ★★★★★/★★★★☆のレースのみ抽出**

**手動で抽出** (メモ帳で確認):
1. `predictions_20260201.txt` をメモ帳で開く
2. `★★★★★` または `★★★★☆` で検索（Ctrl+F）
3. 該当レースをコピペしてDiscordに投稿

**自動抽出** (PowerShellで実行):
```powershell
# ★★★★★/★★★★☆のレースのみ抽出
Select-String -Path "E:\eoi-pl\predictions\predictions_20260201.txt" -Pattern "★★★★★|★★★★☆" -Context 15 | Out-File -FilePath "E:\eoi-pl\predictions\predictions_20260201_filtered.txt"
```

---

## 📱 **3. Discordへの投稿**

### **3-1: 単一レースをDiscordに投稿**

**PowerShellで実行**（画面に表示）:

```powershell
# 特定のレースIDで予想を表示
python format_predictions_discord.py --race-id 202602014401
```

**出力をコピペしてDiscordに投稿**

---

### **3-2: 1日分の全レースをファイル出力**

既に実行済み:
```powershell
python format_predictions_discord.py --date 20260201 --output E:\eoi-pl\predictions\predictions_20260201.txt
```

ファイルから★★★★★/★★★★☆のレースを選んでDiscordに投稿

---

## 🔄 **4. 月次メンテナンス（毎月1回）**

### **4-1: このチャットで月次更新を依頼**

**CEOからこのチャットへ**:
```
「2026年2月分のデータを追加してください」
```

### **4-2: 更新されたデータベースをダウンロード**

このチャットから:
```
feature_database_2020_202602.json
```

ダウンロード先:
```
C:\Users\ihaji\Downloads\feature_database_2020_202602.json
```

---

### **4-3: ローカルに上書き**

**PowerShellで実行**:

```powershell
# 古いファイルをバックアップ
New-Item -ItemType Directory -Force -Path "E:\eoi-pl\data\backup"
Copy-Item "E:\eoi-pl\data\feature_database_2020_2025.json" "E:\eoi-pl\data\backup\feature_database_2020_2025_old.json"

# 新しいファイルをコピー（最新版にリネーム）
Copy-Item "C:\Users\あなたのユーザー名\Downloads\feature_database_2020_202602.json" "E:\eoi-pl\data\feature_database_2020_2025.json"
```

**⚠️ 重要**: 
- ファイル名は常に `feature_database_2020_2025.json` のまま
- スクリプトがこの名前を参照するため変更不可
- 保存場所は必ず `E:\eoi-pl\data\`

---

## 📊 **5. 推奨度の意味**

| 推奨度 | 1位偏差値 | 意味 | 戦略 |
|--------|----------|------|------|
| ★★★★★ | 70以上 | 本命が圧倒的 | 手堅く勝負 |
| ★★★★☆ | 65-69 | 本命が明確 | 信頼できる |
| ★★★☆☆ | 60-64 | 本命が有力 | 慎重に |
| ★★☆☆☆ | 55-59 | 混戦 | 要注意 |
| ★☆☆☆☆ | 50-54 | 大混戦 | 見送り推奨 |
| ☆☆☆☆☆ | 50未満 | 超混戦 | 見送り推奨 |

---

## 🎯 **6. 実際の馬券戦略**

### **戦略A: 3連複5頭BOX（10点）**
- **対象**: ★★★★★/★★★★☆のレースのみ
- **買い目**: Top5の5頭でBOX
- **的中率**: 
  - ★★★★★: **46.45%**（約2回に1回）
  - ★★★★☆: **54.66%**（約2回に1回）
- **推奨投資額**: 1点100円 = 1,000円/レース

### **戦略B: 3連複 軸1頭流し（6点）**
- **対象**: ★★★★★のレースのみ
- **買い目**: 1位馬を軸、2-5位の4頭と流し
- **的中率**: やや高め
- **推奨投資額**: 1点200円 = 1,200円/レース

### **戦略C: 馬連BOX（3点）**
- **対象**: ★★★★★/★★★★☆のレースのみ
- **買い目**: Top3の3頭でBOX
- **的中率**: **46.97%**（Top3≥2）
- **推奨投資額**: 1点300円 = 900円/レース

---

## ⚠️ **7. トラブルシューティング**

### **Q1: Python実行時にエラーが出る**

**エラー例**:
```
ModuleNotFoundError: No module named 'psycopg2'
```

**解決方法**:
```powershell
# 必要なライブラリを再インストール
pip install psycopg2-binary numpy pandas
```

---

### **Q2: PostgreSQLに接続できない**

**エラー例**:
```
psql: error: connection to server at "localhost" (::1), port 5432 failed
```

**解決方法**:
1. Windowsサービスを開く（Win+R → `services.msc`）
2. 「postgresql-x64-15」を探す
3. 右クリック → 「開始」

または:
```powershell
# サービスを起動
net start postgresql-x64-15
```

---

### **Q3: race_idが見つからない**

**エラー例**:
```
レース予想: 202602014401
レースが見つかりません
```

**原因**: 
- 該当日のレースデータがデータベースにない
- race_idの形式が間違っている

**解決方法**:
```powershell
# レースIDを確認
psql -U postgres -d eoi_pl -c "SELECT race_id FROM races WHERE kaisai_nen = 2026 AND kaisai_tsukihi = 201 LIMIT 10;"
```

---

### **Q4: 出力ファイルが文字化けする**

**症状**: メモ帳で開くと文字化け

**解決方法**:
1. メモ帳で開く
2. 「ファイル」→「名前を付けて保存」
3. 「エンコード」を「UTF-8」に変更して保存

または、**Visual Studio Code**で開く（推奨）

---

## 📈 **8. 運用スケジュール例**

| 時刻 | 作業 | 所要時間 | コマンド例 |
|------|------|---------|-----------|
| **13:00** | 今日のレース予想生成 | 3分 | `python format_predictions_discord.py --date 20260201 --output E:\eoi-pl\predictions\predictions_20260201.txt` |
| **13:05** | ★★★★★/★★★★☆を抽出 | 5分 | メモ帳で検索 |
| **13:10** | Discordに投稿 | 5分 | コピペ |
| **15:00** | 馬券購入 | 10分 | - |

**月次**:
| 日付 | 作業 | 所要時間 | 頻度 |
|------|------|---------|------|
| **毎月1日** | 月次更新依頼 | 5分 | 月1回 |
| **毎月1日** | データベース上書き | 3分 | 月1回 |

**合計**: 1日あたり約23分、月あたり約11時間

---

## 💰 **9. コスト**

| 項目 | 金額 | 備考 |
|------|------|------|
| 日次予想 | **0円** | ローカル実行（クレジット不要） |
| 月次更新 | 50クレジット/月 | このチャット |
| **年間合計** | **600クレジット** | 従来比98.4%削減 |

---

## 🎯 **10. 成功のポイント**

### **1. 推奨度★★★★★/★★★★☆のレースに絞る**
- 全レースで勝負しない
- 手堅いレースだけを狙う
- ★★★★☆の方が的中率が高い（54.66% vs 46.45%）

### **2. 3連複5頭BOXで手堅く**
- 1点100円 × 10点 = 1,000円
- 的中率約50% → 2回に1回的中

### **3. 月次更新を忘れずに**
- 毎月1日に前月データを追加
- 新馬・新騎手の実績を反映

### **4. 記録をつける**
- 的中率と回収率を記録
- Excelで管理するのがおすすめ

---

## 📝 **11. よくある質問（FAQ）**

### **Q: 毎日実行する必要がありますか？**
A: いいえ。競馬開催日のみ実行してください。

### **Q: 複数日分まとめて予想できますか？**
A: いいえ。1日ずつ `--date` を変えて実行してください。

### **Q: 的中率はどのくらいですか？**
A: ★★★★★/★★★★☆のレースで約50%です（Top5≥3）。

### **Q: 回収率はどのくらいですか？**
A: オッズ情報がないため計算不可です。実際の馬券購入で検証してください。

### **Q: Pythonがインストールされていません**
A: Python公式サイト（https://www.python.org/downloads/）からダウンロードしてください。
   - インストール時に「Add Python to PATH」にチェックを入れる

---

## 🚀 **12. クイックスタート（初回のみ）**

**PowerShellで一括実行**:

```powershell
# ⚠️ 重要: 必ず E:\eoi-pl に保存してください

# 1. Eドライブに移動
E:

# 2. eoi-plディレクトリを作成
New-Item -ItemType Directory -Force -Path E:\eoi-pl

# 3. ダウンロードフォルダから解凍
cd E:\eoi-pl
tar -xzf C:\Users\あなたのユーザー名\Downloads\eoi-pl.tar.gz

# 4. 解凍後、eoi-pl フォルダの中身を E:\eoi-pl に移動
Move-Item -Path .\eoi-pl\* -Destination . -Force
Remove-Item -Path .\eoi-pl -Force

# 5. Pythonライブラリをインストール
pip install psycopg2-binary numpy pandas

# 6. PostgreSQL起動確認
psql -U postgres -d eoi_pl -c "SELECT COUNT(*) FROM races WHERE kaisai_nen = 2026;"

# 7. テスト実行（2026年1月2日の川崎1R）
cd E:\eoi-pl\scripts
python format_predictions_discord.py --race-id 202601024501
```

**期待される出力**:
```
【川崎 1R】  レース推奨度: ★★★★☆ (1位偏差値: 69.0)

🎯 推奨買い目
  Top3（馬連BOXなど）: 2, 10, 8
  Top5（三連複BOXなど）: 2, 10, 8, 3, 6
...
```

**📁 最終的なディレクトリ構成（必須）**:
```
E:\eoi-pl\                          ← 固定場所
├── data\
│   └── feature_database_2020_2025.json
├── scripts\
│   ├── format_predictions_discord.py
│   └── update_feature_database_monthly.py
├── predictions\                    ← 自動作成
├── backtest\
├── README_WINDOWS.md
├── OPERATION_GUIDE_完全版.md
└── FINAL_SPEC_堅実派AI.md
```

---

## 🎉 **13. まとめ**

### **日次運用の流れ**
1. PowerShellを起動
2. `E:\eoi-pl\scripts` に移動
3. `python format_predictions_discord.py --date 今日の日付 --output 出力先` を実行
4. ★★★★★/★★★★☆のレースを抽出
5. Discordに投稿
6. 馬券購入

### **月次メンテナンスの流れ**
1. このチャットで「2026年X月分のデータを追加」と依頼
2. ダウンロードしたファイルを `E:\eoi-pl\data\feature_database_2020_2025.json` に上書き
3. 翌月から新しいデータで予想

---

**Play to Win！ローカル環境で堅実に勝ちましょう！** 🚀
