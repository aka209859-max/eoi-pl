# 🚀 EOI-PL ローカル実行環境セットアップガイド

**目的:** Windows PCで毎日の予想をローカル実行（クレジット消費ゼロ）

---

## 📋 **セットアップ手順**

### **Step 1: Eドライブにディレクトリを作成**

```cmd
# Eドライブに eoi-pl ディレクトリを作成
E:
mkdir E:\eoi-pl
mkdir E:\eoi-pl\data
mkdir E:\eoi-pl\scripts
mkdir E:\eoi-pl\predictions
```

### **Step 2: 必要なファイルをコピー**

**From Linux Sandbox → To Windows PC (Eドライブ):**

| ソース（Linux） | コピー先（Windows） | サイズ | 説明 |
|----------------|-------------------|--------|------|
| `/home/user/eoi-pl/data/feature_database_2020_2025.json` | `E:\eoi-pl\data\feature_database_latest.json` | 27MB | 特徴量データベース |
| `/home/user/eoi-pl/scripts/predict_daily_standalone.py` | `E:\eoi-pl\scripts\predict_daily_standalone.py` | 14KB | 予想スクリプト |
| `/home/user/eoi-pl/scripts/update_feature_database_monthly.py` | `E:\eoi-pl\scripts\update_feature_database_monthly.py` | 5KB | 月次更新スクリプト |

**コピー方法（このチャットで）:**

```bash
# 1. チャット上で「ダウンロードリンクを生成」依頼
# 2. ブラウザでダウンロード
# 3. Eドライブにコピー
```

### **Step 3: Python環境のセットアップ**

```cmd
# 必要なライブラリをインストール
pip install psycopg2 numpy pandas

# インストール確認
python -c "import psycopg2, numpy, pandas; print('✅ OK')"
```

### **Step 4: PostgreSQL接続確認**

```cmd
# PostgreSQL (eoi_pl) が起動しているか確認
psql -U postgres -d eoi_pl -c "SELECT COUNT(*) FROM races WHERE kaisai_nen = 2026;"

# 期待結果: 1019
```

---

## 🏇 **日次予想の実行方法**

### **使い方1: 特定レースの予想**

```cmd
# Eドライブに移動
E:
cd E:\eoi-pl\scripts

# 2026年2月1日、大井1Rを予想
python predict_daily_standalone.py --race-id 202602014401
```

**出力例:**
```
============================================================
🏇 レース予想: 202602014401
============================================================

📂 特徴量データベースをロード: E:/eoi-pl/data/feature_database_latest.json
   ✅ 馬: 40,366頭
   ✅ 騎手: 516人
   ✅ 調教師: 690人

📊 予想結果:

 rank_pred  umaban            bamei  total_skill
         1       5      サンプル馬A         2.145
         2       3      サンプル馬B         1.987
         3       7      サンプル馬C         1.856
         4       1      サンプル馬D         1.745
         5       2      サンプル馬E         1.632

🎯 推奨買い目:
  Top3: 5, 3, 7
  Top5: 5, 3, 7, 1, 2

✅ 予想完了！
```

### **使い方2: 1日分の全レース予想（推奨）**

```cmd
# 2026年2月1日の全レースを予想
python predict_daily_standalone.py --date 20260201 --output E:\eoi-pl\predictions\predictions_20260201.csv
```

**出力例:**
```
============================================================
📅 日次予想: 20260201
============================================================

📂 特徴量データベースをロード: E:/eoi-pl/data/feature_database_latest.json
   ✅ 馬: 40,366頭
   ✅ 騎手: 516人
   ✅ 調教師: 690人

🏇 対象レース: 48レース

予想中: 大井 1R (202602014401)...
予想中: 大井 2R (202602014402)...
予想中: 大井 3R (202602014403)...
...

💾 予想結果を保存: E:\eoi-pl\predictions\predictions_20260201.csv

📊 予想サマリー:
  対象レース: 48レース
  予想馬数: 537頭

✅ 日次予想完了！
```

### **生成されるCSVファイルの形式:**

| 列名 | 説明 | 例 |
|------|------|-----|
| race_id | レースID | 202602014401 |
| venue_name | 競馬場名 | 大井 |
| race_bango | レース番号 | 1 |
| rank_pred | 予想順位 | 1 |
| umaban | 馬番 | 5 |
| bamei | 馬名 | サンプル馬A |
| total_skill | 総合スキル | 2.145 |

---

## 📅 **月次メンテナンス（月1回、このチャットで実行）**

### **手順:**

1. **このチャットに戻る（月1回）**

2. **月次更新コマンドを実行:**

```bash
# 例: 2026年1月分のデータを学習データに追加
cd /home/user/eoi-pl
python3 scripts/update_feature_database_monthly.py --year 2026 --month 1
```

3. **更新されたデータベースをダウンロード:**

```bash
# 更新されたデータベースのダウンロードリンクを生成
# feature_database_latest.json をダウンロード
```

4. **Windows PCのEドライブに上書き保存:**

```cmd
# ダウンロードしたファイルを E:\eoi-pl\data\ にコピー
copy Downloads\feature_database_latest.json E:\eoi-pl\data\
```

5. **翌月からは更新されたデータで予想実行**

---

## 📊 **運用スケジュール例**

| 日付 | 作業 | 場所 | クレジット消費 |
|------|------|------|---------------|
| **2026/02/01 〜 02/28** | 毎日の予想実行 | ローカル（Windows PC） | **ゼロ** |
| **2026/03/01** | 月次更新（2月分を追加） | このチャット | 少量 |
| **2026/03/02 〜 03/31** | 毎日の予想実行 | ローカル（Windows PC） | **ゼロ** |
| **2026/04/01** | 月次更新（3月分を追加） | このチャット | 少量 |
| **2026/04/02 〜 04/30** | 毎日の予想実行 | ローカル（Windows PC） | **ゼロ** |

---

## 💰 **コスト削減効果**

### **従来（毎日このチャットで予想）:**
- 1日あたり: 約100クレジット
- 1ヶ月（30日）: **3,000クレジット**
- 1年間（365日）: **36,500クレジット**

### **新方式（ローカル実行 + 月次更新）:**
- 1日あたり: **0クレジット**（ローカル実行）
- 1ヶ月（30日）: **0クレジット**
- 月次更新: 約50クレジット
- **1年間合計: 600クレジット** ← **98.4%削減！**

---

## 🔧 **トラブルシューティング**

### **Q1: PostgreSQLに接続できない**
```cmd
# PostgreSQLが起動しているか確認
sc query postgresql-x64-16

# 起動していない場合
net start postgresql-x64-16
```

### **Q2: 特徴量データベースが見つからない**
```cmd
# ファイルの存在確認
dir E:\eoi-pl\data\feature_database_latest.json

# 存在しない場合: このチャットでダウンロードリンクを生成
```

### **Q3: 予想結果が空になる**
```cmd
# レースデータが登録されているか確認
psql -U postgres -d eoi_pl -c "SELECT COUNT(*) FROM races WHERE race_id = '202602014401';"

# 0件の場合: PC-KEIBAで「通常データ登録」を実行
```

### **Q4: 未知馬が多すぎる**
```cmd
# 月次更新を実行して新馬データを追加
# このチャットで update_feature_database_monthly.py を実行
```

---

## 📂 **最終的なディレクトリ構成**

```
E:\eoi-pl\
├── data\
│   ├── feature_database_latest.json       (27MB) ← 月次更新で上書き
│   └── feature_database_2020_2025.json    (27MB) ← バックアップ
├── scripts\
│   ├── predict_daily_standalone.py        (14KB)
│   └── update_feature_database_monthly.py (5KB)
└── predictions\
    ├── predictions_20260201.csv
    ├── predictions_20260202.csv
    └── ...
```

---

## 🎉 **完了！**

これで毎日の予想をローカルで実行でき、クレジット消費を**98.4%削減**できます！

月1回だけこのチャットで月次更新を実行してください。

**Play to Win！🚀**
