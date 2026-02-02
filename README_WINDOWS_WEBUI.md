# EOI-PL v1.0-Prime Windows PC用 Web UI完全ガイド

**最終更新**: 2026-02-01  
**対象環境**: Windows 10/11  
**所要時間**: 初回セットアップ 5分、日次運用 1分

---

## 🎯 このガイドの目的

**画像と同じWeb UIをWindows PC上で動かす**

```
Windows PC 上で:
1. start_api_windows.bat をダブルクリック
2. http://localhost:8001 が自動的に開く
3. 「更新ボタン」で最新データを自動検出
4. 予想が画面に表示される
```

---

## 📋 前提条件

### 必須環境
- ✅ Windows 10 または Windows 11
- ✅ Python 3.8以上（インストール済み）
- ✅ PostgreSQL 15以上（インストール済み、eoi-sike データベース作成済み）
- ✅ PC-KEIBA（UmaConn設定済み、データ取得済み）

### 必須ファイル
- ✅ `E:\eoi-pl\` ディレクトリ（Git リポジトリ）
- ✅ `E:\eoi-pl\data\feature_database_2020_2025.json`（27MB）
- ✅ PostgreSQL の eoi-sike データベース

---

## 🚀 初回セットアップ（5分）

### Step 1: GitHubから最新版を取得

Windows PowerShellを開き、以下を実行：

```powershell
# E:\eoi-pl に移動
cd E:\eoi-pl

# 最新版を取得
git pull origin main
```

### Step 2: 必要なPythonパッケージをインストール

```powershell
# 仮想環境を作成（初回のみ）
python -m venv venv

# 仮想環境を有効化
venv\Scripts\activate

# パッケージをインストール
pip install fastapi uvicorn psycopg2-binary numpy pandas
```

### Step 3: データベース接続テスト

```powershell
# 設定ファイルのテスト
python api\config_windows.py
```

**期待される出力例**:
```
=====================================================================
EOI-PL v1.0-Prime Windows PC用 設定確認
=====================================================================

1. PostgreSQL 接続テスト...
✅ 接続成功！2026年のレース数: 1,019件
✅ 最新データ日: 2026-01-30

2. 特徴量データベース確認...
✅ ファイル存在: E:\eoi-pl\data\feature_database_2020_2025.json
✅ ファイルサイズ: 27.0 MB

=====================================================================
設定確認完了！
=====================================================================
```

### Step 4: Web UIを起動

```powershell
# start_api_windows.bat をダブルクリック
# または PowerShell から実行
.\start_api_windows.bat
```

**起動確認**:
- ブラウザが自動的に開き、`http://localhost:8001` にアクセス
- 画面に「EOI-PL 予想配信センター v1.0-Prime」が表示

---

## 📖 日次運用ワークフロー（1分/日）

### 完全なワークフロー

```
【時刻: 朝 8:00】

1. PC-KEIBAでデータ取得（CEO作業、3分）
   - UmaConnを起動
   - 最新データをダウンロード
   - PostgreSQL eoi-sike に自動インポート

2. Web UIを起動（1クリック）
   - E:\eoi-pl\start_api_windows.bat をダブルクリック
   - http://localhost:8001 が自動的に開く

3. 最新データを更新（1クリック）
   - 画面上の「nohinbi更新（全レース）」ボタンをクリック
   - 最新日（例: 2026-02-01）が自動検出される
   - 予想が自動生成される

4. 予想を確認（30秒）
   - 画面に全レースの予想が表示
   - ★★★★★/★★★★☆ のレースを確認

5. Discordに投稿（30秒）
   - 各レースの「Discordにコピー」ボタンをクリック
   - Discord に貼り付け

【合計所要時間: 約5分】
```

---

## 🎨 Web UI の使い方

### 画面構成

```
┌─────────────────────────────────────────────┐
│  EOI-PL 予想配信センター v1.0-Prime         │
│  地方競馬AI予想                              │
├─────────────────────────────────────────────┤
│  📅 予想日を選択: [2026/01/04 ▼]            │
│  ✏️ [予想を生成]                            │
├─────────────────────────────────────────────┤
│  🔄 [nohinbi更新（全レース）]  ← NEW！     │
│     ⚠️ Discord用とはレースごとにコピーして  │
│        ください（★4以上のみ表示）           │
├─────────────────────────────────────────────┤
│  📊 2026/01/04 の予想                       │
│  ┌─────────────────────────────────────┐   │
│  │ 【川崎 1R】 ★★★★☆ 成績Rate: 65.4   │   │
│  │ Top3予想: 11-8-1                      │   │
│  │ Top5予想: 11-8-1-2-7                  │   │
│  │ 三連単: 11-8-1, 11-8-7, ...           │   │
│  │                                        │   │
│  │ 順位 | 馬番 | 馬名       | 偏差値     │   │
│  │  1   |  11  | ヤマヨシイチオー | 65.4  │   │
│  │  2   |   8  | アイノテンリュウ | 62.6  │   │
│  │  3   |   1  | シャプロンマヤン | 56.8  │   │
│  │  4   |   2  | ポルトフーリー   | 56.0  │   │
│  │  5   |   7  | マチノラインベッキア| 50.7│   │
│  │                                        │   │
│  │ [Discordにコピー]                      │   │
│  └─────────────────────────────────────┘   │
│  ... （全レース表示）                        │
└─────────────────────────────────────────────┘
```

### 主な機能

#### 1. 「nohinbi更新（全レース）」ボタン（緑色）
- 最新データを PostgreSQL から自動検出
- 最新日の予想を自動生成
- 完了メッセージ表示

#### 2. 「予想を生成」ボタン（青色）
- 選択した日付の予想を生成
- 全レースの詳細を表示

#### 3. 「Discordにコピー」ボタン
- ★★★★★/★★★★☆ のレースのみ表示
- クリックでクリップボードにコピー
- Discord に直接貼り付け可能

---

## 🔧 トラブルシューティング

### Q1: `start_api_windows.bat` をダブルクリックしてもエラーが出る

**原因1**: Python が見つからない
```
対処法:
1. Python 3.8以上をインストール
2. 環境変数 PATH に Python を追加
```

**原因2**: PostgreSQL が起動していない
```
対処法:
1. サービス一覧を開く（services.msc）
2. "postgresql-x64-15" を起動
3. 再度 start_api_windows.bat を実行
```

**原因3**: データベース接続エラー
```
対処法:
1. api\config_windows.py を開く
2. DB_CONFIG の内容を確認:
   - database: 'eoi-sike'
   - password: 'uwwlqzxqd125'
3. PostgreSQL の設定と一致しているか確認
```

### Q2: 「更新ボタン」を押しても最新データが表示されない

**原因1**: PC-KEIBA でデータを取得していない
```
対処法:
1. UmaConn を起動
2. 最新データをダウンロード
3. PostgreSQL への自動インポートを確認
```

**原因2**: PostgreSQL にデータがインポートされていない
```
対処法:
1. PowerShell で確認:
   & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h 127.0.0.1 -U postgres -d eoi-sike
   パスワード: uwwlqzxqd125
   
2. SQL実行:
   SELECT MAX(kaisai_tsukihi) FROM races WHERE kaisai_nen = 2026;
   
3. 期待値: 201（2026-02-01）または 202（2026-02-02）
```

### Q3: ブラウザが自動的に開かない

```
対処法:
手動でブラウザを開き、以下にアクセス:
http://localhost:8001
```

### Q4: 「特徴量データベースが見つかりません」エラー

```
対処法:
1. E:\eoi-pl\data\feature_database_2020_2025.json の存在確認
2. ファイルが無い場合:
   cd E:\eoi-pl
   git pull origin main
```

---

## 📊 パフォーマンス指標

### システム精度
- **Top3≥1**: 90.06%（軸馬的中率）
- **Top5≥3**: 28.23%（複勝的中率）

### 日次運用コスト
- **時間**: 1分/日（データ取得を除く）
- **費用**: 0円/日

### 月次メンテナンス
- **特徴量更新**: 1回/月（CEOの指示後）
- **費用**: 50クレジット/月

---

## 🎯 よくある質問（FAQ）

### Q: サンドボックス版とWindows版の違いは？

**サンドボックス版**:
- URL: `http://8001-ip441p2fec9c31j8sdwgf-5c13a017.sandbox.novita.ai`
- DB: `eoi_pl`（サンドボックスのPostgreSQL）
- データ: 2026-01-30まで

**Windows版**:
- URL: `http://localhost:8001`
- DB: `eoi-sike`（Windows PCのPostgreSQL）
- データ: PC-KEIBAで取得した最新データ

### Q: 毎日 `start_api_windows.bat` を実行する必要がある？

**いいえ、1回起動すれば終了するまで使い続けられます。**

```
朝8:00に起動 → 夜まで使用可能
終了する場合: PowerShell画面で Ctrl+C
```

### Q: 他のPCからアクセスできる？

**はい、同一ネットワーク内であれば可能です。**

```
1. Windows ファイアウォールでポート 8001 を開放
2. 他のPCから以下にアクセス:
   http://[Windows PCのIPアドレス]:8001
```

---

## 📝 クイックリファレンス

### 起動コマンド
```powershell
cd E:\eoi-pl
.\start_api_windows.bat
```

### 終了方法
```
PowerShell画面で Ctrl+C を押す
```

### 設定ファイル
- **DB設定**: `E:\eoi-pl\api\config_windows.py`
- **特徴量DB**: `E:\eoi-pl\data\feature_database_2020_2025.json`
- **起動スクリプト**: `E:\eoi-pl\start_api_windows.bat`

### データベース接続テスト
```powershell
python api\config_windows.py
```

### ログ確認
```
PowerShell画面に表示される
```

---

## 🚀 まとめ

### 初回セットアップ（5分）
```powershell
cd E:\eoi-pl
git pull origin main
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn psycopg2-binary numpy pandas
python api\config_windows.py
```

### 日次運用（1分）
```
1. start_api_windows.bat をダブルクリック
2. 「更新ボタン」をクリック
3. 予想を確認
4. Discordに投稿
```

---

**Play to Win！完全自動化の理想的なワークフローが完成しました！** 🎯
