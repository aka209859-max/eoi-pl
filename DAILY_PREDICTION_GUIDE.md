# 🏇 EOI-PL 毎日の予想出力ガイド

**最終更新**: 2026-02-01  
**対象環境**: Windows PC + PostgreSQL + Python

---

## 📋 **前提条件**

✅ **必須環境**:
- Windows PC
- Python 3.8以上
- PostgreSQL 15（PC-KEIBA）
- E:\eoi-pl にプロジェクトが配置済み

✅ **必須ファイル**:
```
E:\eoi-pl\
├── data\
│   └── feature_database_2020_2025.json  ← 特徴量データベース
├── scripts\
│   ├── format_predictions_discord.py    ← Discord出力スクリプト
│   └── daily_prediction.py              ← 日次予想スクリプト（NEW！）
├── predictions\                         ← 予想結果の保存先（自動作成）
└── daily_prediction.bat                 ← ワンクリック実行用（NEW！）
```

---

## 🚀 **方法1: ワンクリック実行（推奨）**

### **手順1: バッチファイルをダブルクリック**

```
E:\eoi-pl\daily_prediction.bat
```

をダブルクリックするだけ！

### **実行結果**

PowerShellウィンドウが開き、以下のように表示されます:

```
============================================================
 EOI-PL v1.0-Prime 日次予想生成
============================================================

📅 日次予想生成: 20260202
📂 出力先: E:\eoi-pl\predictions\predictions_20260202.txt
💾 データベース: E:/eoi-pl/data/feature_database_2020_2025.json

🏇 対象レース: 48レース

============================================================
✅ 予想生成完了！
============================================================

【次のステップ】
1. E:\eoi-pl\predictions フォルダを開く
2. 生成されたファイルをメモ帳で開く
3. ★★★★★/★★★★☆ のレースを検索
4. Discordに投稿

続行するには何かキーを押してください . . .
```

### **出力ファイル**

```
E:\eoi-pl\predictions\predictions_20260202.txt
```

が自動生成されます。

---

## 🖥️ **方法2: PowerShellで実行**

### **手順1: PowerShellを起動**

1. Windowsキー + R
2. `powershell` と入力してEnter

### **手順2: コマンド実行**

```powershell
# Eドライブに移動
E:
cd E:\eoi-pl\scripts

# 今日の予想を生成
python daily_prediction.py
```

### **特定の日付を指定する場合**

```powershell
# 2026年2月3日の予想
python daily_prediction.py --date 20260203
```

### **出力先を指定する場合**

```powershell
# デスクトップに出力
python daily_prediction.py --output C:\Users\あなたのユーザー名\Desktop\predictions_today.txt
```

---

## 📱 **方法3: 旧スクリプトを直接実行（上級者向け）**

### **単一レースをDiscord形式で出力**

```powershell
E:
cd E:\eoi-pl\scripts

# 特定のレースID（例: 202602024401）
python format_predictions_discord.py --race-id 202602024401
```

### **1日分の全レースをファイル出力**

```powershell
# 2026年2月2日の全レース
python format_predictions_discord.py --date 20260202 --output E:\eoi-pl\predictions\predictions_20260202.txt
```

---

## 📊 **出力ファイルの見方**

### **ファイル構造**

```
NAR AI予想 2026/02/02

【大井 1R】  レース推奨度: ★★★★★ (1位偏差値: 71.3)
```
順位    馬番    馬名                      偏差値     
------------------------------------------------------------
1     5番    アウスラフラッグ                 71.3
2     3番    ポンペルモ                    67.8
3     7番    ベンハー                     56.5
...
```

🎯 **推奨買い目**
  Top3（馬連BOXなど）: 5, 3, 7
  Top5（三連複BOXなど）: 5, 3, 7, 6, 12

💡 **レース分析**
  本命が圧倒的で非常に予想しやすいレースです（推奨度: ★★★★★）

============================================================
```

### **推奨度の意味**

| 推奨度 | 1位偏差値 | 意味 | 戦略 |
|--------|----------|------|------|
| ★★★★★ | 70以上 | 本命が圧倒的 | 手堅く勝負 |
| ★★★★☆ | 65-69 | 本命が明確 | 信頼できる |
| ★★★☆☆ | 60-64 | 本命が有力 | 慎重に |
| ★★☆☆☆ | 55-59 | 混戦 | 要注意 |
| ★☆☆☆☆ | 50-54 | 大混戦 | 見送り推奨 |

---

## 🎯 **Discordへの投稿手順**

### **Step 1: ★4以上のレースを検索**

1. `E:\eoi-pl\predictions\predictions_20260202.txt` をメモ帳で開く
2. Ctrl+F で検索
3. `★★★★` を検索

### **Step 2: レース情報をコピー**

1レースの情報をコピー:

```
【大井 1R】  レース推奨度: ★★★★★ (1位偏差値: 71.3)
```
順位    馬番    馬名                      偏差値     
------------------------------------------------------------
1     5番    アウスラフラッグ                 71.3
2     3番    ポンペルモ                    67.8
3     7番    ベンハー                     56.5
...
```

🎯 **推奨買い目**
  Top3（馬連BOXなど）: 5, 3, 7
  Top5（三連複BOXなど）: 5, 3, 7, 6, 12

💡 **レース分析**
  本命が圧倒的で非常に予想しやすいレースです（推奨度: ★★★★★）
```

### **Step 3: Discordに投稿**

Discordのチャンネルにペースト

---

## 📅 **日次運用スケジュール**

### **推奨タイミング**

| 時刻 | 作業 | 所要時間 |
|------|------|---------|
| **13:00** | 今日のレース予想生成 | 3分 |
| **13:05** | ★★★★★/★★★★☆を抽出 | 5分 |
| **13:10** | Discordに投稿 | 5分 |
| **15:00** | 馬券購入 | 10分 |

**合計**: 約23分/日

---

## ⚠️ **トラブルシューティング**

### **Q1: "❌ 特徴量データベースが見つかりません"**

**原因**: 
- `E:\eoi-pl\data\feature_database_2020_2025.json` が存在しない

**解決方法**:
```powershell
# ファイルの存在確認
Test-Path E:\eoi-pl\data\feature_database_2020_2025.json
```

### **Q2: "⚠️ YYYYMMDD のレースが見つかりません"**

**原因**: 
- 該当日のレースデータがデータベースにない
- 未来の日付を指定している

**解決方法**:
```powershell
# データベースで開催日を確認
psql -U postgres -d eoi_pl -c "SELECT DISTINCT kaisai_nen, kaisai_tsukihi FROM races WHERE kaisai_nen = 2026 ORDER BY kaisai_tsukihi DESC LIMIT 10;"
```

### **Q3: PostgreSQL接続エラー**

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

## 🔄 **月次メンテナンス（毎月1回）**

### **1. このチャットで月次更新を依頼**

**CEOからこのチャットへ**:
```
「2026年2月分のデータを追加してください」
```

### **2. 更新されたデータベースをダウンロード**

このチャットから:
```
feature_database_2020_202602.json
```

ダウンロード先:
```
C:\Users\あなたのユーザー名\Downloads\feature_database_2020_202602.json
```

### **3. ローカルに上書き**

```powershell
# 古いファイルをバックアップ
New-Item -ItemType Directory -Force -Path "E:\eoi-pl\data\backup"
Copy-Item "E:\eoi-pl\data\feature_database_2020_2025.json" "E:\eoi-pl\data\backup\feature_database_2020_2025_old.json"

# 新しいファイルをコピー（最新版にリネーム）
Copy-Item "C:\Users\あなたのユーザー名\Downloads\feature_database_2020_202602.json" "E:\eoi-pl\data\feature_database_2020_2025.json"
```

---

## 💰 **コスト**

| 項目 | 金額 | 備考 |
|------|------|------|
| 日次予想 | **0円** | ローカル実行（クレジット不要） |
| 月次更新 | 50クレジット/月 | このチャット |
| **年間合計** | **600クレジット** | 従来比98.4%削減 |

---

## 🎯 **成功のポイント**

1. **毎日13:00に実行**
   - `daily_prediction.bat` をダブルクリック
   
2. **★★★★★/★★★★☆のレースに絞る**
   - 全レースで勝負しない
   - 手堅いレースだけを狙う
   
3. **記録をつける**
   - 的中率と回収率を記録
   - Excelで管理するのがおすすめ

---

## 📝 **よくある質問（FAQ）**

### **Q: 複数日分まとめて予想できますか？**

A: はい。PowerShellで以下のようにループ実行:

```powershell
# 2026年2月1日～3日の予想を一括生成
foreach ($day in 1..3) {
    $date = "202602" + $day.ToString("00")
    python daily_prediction.py --date $date
}
```

### **Q: 自動で毎日実行できますか？**

A: はい。Windowsタスクスケジューラを使用:

1. タスクスケジューラを開く（Win+R → `taskschd.msc`）
2. 「基本タスクの作成」を選択
3. トリガー: 毎日13:00
4. 操作: `E:\eoi-pl\daily_prediction.bat` を実行

---

## 🚀 **まとめ**

### **日次運用の流れ**

1. `E:\eoi-pl\daily_prediction.bat` をダブルクリック
2. ★★★★★/★★★★☆のレースを抽出
3. Discordに投稿
4. 馬券購入

**所要時間**: 約23分/日  
**コスト**: 0円/日（ローカル実行）

---

**Play to Win！ローカル環境で堅実に勝ちましょう！** 🚀
