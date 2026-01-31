# 🚀 EOI-PL v1.0-Prime クイックセットアップガイド

**所要時間**: 10分  
**対象**: Windows PC  
**保存先**: **E:\eoi-pl（固定）**

---

## 📥 **Step 1: ダウンロード（1分）**

### **ダウンロードURL**
```
https://www.genspark.ai/api/files/s/44XLAfBS
```

1. 上記URLをクリック
2. ブラウザでダウンロード（25.1MB）
3. `C:\Users\あなたのユーザー名\Downloads\eoi-pl.tar.gz` に保存される

---

## 📁 **Step 2: 解凍して E:\eoi-pl に保存（3分）**

### **PowerShellで実行**

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
Remove-Item -Path .\eoi-pl -Force
```

### **⚠️ 重要: 必ず E:\eoi-pl に保存**

```
E:\eoi-pl\                          ← 固定場所（必須）
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

## 🐍 **Step 3: Pythonライブラリインストール（3分）**

```powershell
pip install psycopg2-binary numpy pandas
```

**エラーが出る場合**:
```powershell
# Python公式サイトからインストール
# https://www.python.org/downloads/
# インストール時に「Add Python to PATH」にチェック
```

---

## 🗄️ **Step 4: PostgreSQL起動確認（2分）**

```powershell
# PostgreSQLが起動しているか確認
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
```powershell
# Windowsサービスを開く（Win+R → services.msc）
# 「postgresql-x64-15」を右クリック → 開始

# または
net start postgresql-x64-15
```

---

## 🎯 **Step 5: テスト実行（1分）**

```powershell
# E:\eoi-pl\scripts に移動
cd E:\eoi-pl\scripts

# テスト実行（2026年1月2日の川崎1R）
python format_predictions_discord.py --race-id 202601024501
```

**期待される出力**:
```
============================================================
🏇 レース予想: 202601024501
============================================================

【川崎 1R】  レース推奨度: ★★★★☆ (1位偏差値: 69.0)
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

## ✅ **セットアップ完了！**

### **日次運用（毎日実行）**

```powershell
# 今日の日付で予想生成（例: 2026年2月1日）
cd E:\eoi-pl\scripts
python format_predictions_discord.py --date 20260201 --output E:\eoi-pl\predictions\predictions_20260201.txt
```

### **出力ファイルを確認**

```powershell
# メモ帳で開く
notepad E:\eoi-pl\predictions\predictions_20260201.txt

# ★★★★★/★★★★☆を検索（Ctrl+F）
# 該当レースをコピペしてDiscordに投稿
```

---

## 📊 **的中率（確定版）**

### **全レース（2026年1月）**
- Top3≥1: **90.06%** (788/875)
- Top3≥2: **46.97%** (411/875)
- Top5≥3: **28.23%** (247/875)

### **★★★★★/★★★★☆のみ（2025年11月）**
- ★★★★★: **46.45%** (275/592)
- ★★★★☆: **54.66%** (217/397)
- 合計: **49.75%** (492/989) ← 約2回に1回的中

---

## 💡 **重要ポイント**

### **1. 保存先は必ず E:\eoi-pl**
- スクリプトがこのパスを参照
- 変更すると動作しません

### **2. ファイル名は変更不可**
- `feature_database_2020_2025.json`（固定）
- `format_predictions_discord.py`（固定）

### **3. predictions フォルダは自動作成**
- 初回実行時に自動作成されます
- 手動で作成する必要はありません

---

## 🎉 **配信開始準備完了！**

**Play to Win！堅実派AIで勝ちましょう！** 🚀

---

## 📝 **詳細ドキュメント**

- **詳細セットアップ**: `README_WINDOWS.md`
- **運用ガイド**: `OPERATION_GUIDE_完全版.md`
- **仕様書**: `FINAL_SPEC_堅実派AI.md`
