# PC-KEIBA 完全復旧計画（確定版）

## 📋 前提条件の確認

- ✅ Windows の「Beta: Unicode UTF-8」設定は無効化済み
- ✅ システムのコードページは 932 (Shift_JIS)
- ❌ PostgreSQL 17.7 は非推奨 → 16.4 へダウングレード必須

---

## 🚀 Phase 1: 環境初期化（所要時間: 30分）

### Step 1-1: PostgreSQL 17.7 のアンインストール

```powershell
# コントロールパネルから PostgreSQL 17.7 をアンインストール
# または PowerShell で実行:
Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like "*PostgreSQL*"} | ForEach-Object {$_.Uninstall()}
```

### Step 1-2: データベースディレクトリの完全削除

```powershell
# PostgreSQL のデータディレクトリを削除
Remove-Item -Path "C:\Program Files\PostgreSQL\17" -Recurse -Force

# ProgramData も削除
Remove-Item -Path "C:\ProgramData\PostgreSQL" -Recurse -Force
```

### Step 1-3: PC-KEIBA の setupdata フォルダ削除

```powershell
# インポート待ちの破損データを削除
Remove-Item -Path "$env:APPDATA\PC-KEIBA Database\setupdata\*" -Recurse -Force

# ログも確認（削除は任意）
notepad "$env:APPDATA\PC-KEIBA Database\logs\latest.log"
```

---

## 🔧 Phase 2: システム修正（所要時間: 15分）

### Step 2-1: Windows コードページの最終確認

```cmd
# コマンドプロンプトで実行
chcp

# 期待される出力: "現在のコード ページ: 932"
```

**もし 65001 (UTF-8) の場合:**
- コントロールパネル → 時計と地域 → 地域 → 管理
- 「システムロケールの変更」
- 「Beta: ワールドワイド言語サポートで Unicode UTF-8 を使用」のチェックを**外す**
- **システム再起動**

### Step 2-2: 環境変数の設定（オプション）

```cmd
# PostgreSQL のクライアントエンコーディングを明示
setx PGCLIENTENCODING SJIS /M
```

---

## 🏗️ Phase 3: 基盤再構築（所要時間: 20分）

### Step 3-1: PostgreSQL 16.4 のインストール

1. **ダウンロード:**
   - URL: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
   - バージョン: **PostgreSQL 16.4 for Windows x86-64**

2. **インストール設定:**
   - インストール先: `C:\Program Files\PostgreSQL\16`
   - ポート: `5432`
   - ロケール: **C** または **Japanese_Japan.932**
   - 文字セット: **UTF8**（サーバー側）
   - パスワード: `postgres` または既存のものを使用

3. **サービスの起動確認:**
   ```powershell
   # PostgreSQL サービスが起動しているか確認
   Get-Service -Name "postgresql-x64-16"
   ```

### Step 3-2: PC-KEIBA の接続設定

1. **PC-KEIBA を起動**
2. **メニュー:** データ → データベース設定
3. **接続情報:**
   - ホスト: `127.0.0.1`
   - ポート: `5432`
   - データベース: `pckeiba`
   - ユーザー: `postgres`
   - パスワード: （インストール時に設定したもの）
4. **接続テスト** → 成功を確認

---

## 📥 Phase 4: データ再登録（所要時間: 30分）

### Step 4-1: セットアップデータ登録の実行

1. **PC-KEIBA を起動**
2. **メニュー:** データ → セットアップデータ登録
3. **設定:**
   - データ種別: 全て選択
   - 期間: 2020年1月1日 〜 2026年1月30日
4. **実行** → 完了まで待機（約30分）

### Step 4-2: 進行中のトラブル対応

**もしエラーが発生した場合:**
- ログを確認: `$env:APPDATA\PC-KEIBA Database\logs\`
- エラーメッセージをこのチャットで共有
- `setupdata` フォルダを削除して再実行

---

## ✅ Phase 5: 最終検証（所要時間: 10分）

### Step 5-1: PC-KEIBA GUI での確認

1. **PC-KEIBA を起動**
2. **メニュー:** データベース → 馬データ
3. **検索条件:** 開催年 = 2026
4. **確認項目:**
   - 馬名が**日本語で正常に表示**されているか
   - 例: `ディープインパクト`, `サクラローレル`

**期待される表示:**
```
馬名: ジーティービバーイ
父: ディープインパクト
母: サクラローレル
```

### Step 5-2: PostgreSQL での確認

```powershell
cd "C:\Program Files\PostgreSQL\16\bin"
psql.exe -h 127.0.0.1 -p 5432 -U postgres -d pckeiba
```

**SQL で確認:**
```sql
-- 馬名の確認
SELECT ketto_toroku_bango, bamei 
FROM nvd_um 
LIMIT 10;

-- バイト列の確認（UTF-8 の日本語になっているはず）
SELECT encode(bamei::bytea, 'hex') AS byte_hex
FROM nvd_um 
LIMIT 5;
```

**期待される結果:**
```
ketto_toroku_bango |        bamei
--------------------+---------------------
2022110071         | ジーティービバーイ
2021100845         | アルジュニース
...

byte_hex (先頭部分)
---------------------
e382b8e383bce38386... (UTF-8 の日本語)
```

**失敗パターン（再度文字化け）:**
```
3f3f3f433f3f3f58... (0x3F = '?' の繰り返し)
```

### Step 5-3: CSV エクスポート

```sql
\copy (SELECT ketto_toroku_bango, bamei FROM nvd_um WHERE bamei IS NOT NULL ORDER BY ketto_toroku_bango LIMIT 1000) TO 'C:\Users\ihaji\bamei_final_check.csv' WITH CSV HEADER ENCODING 'UTF8'
```

```powershell
# Windows で確認
type C:\Users\ihaji\bamei_final_check.csv | more
```

**正常な出力例:**
```
ketto_toroku_bango,bamei
2022110071,ジーティービバーイ
2021100845,アルジュニース
```

---

## 🔥 Phase 6: Linux Sandbox への統合

### Step 6-1: CSV のアップロード

1. `bamei_final_check.csv` をこのチャットにアップロード
2. AI Developer が Sandbox で受領

### Step 6-2: EOI-PL データベースの更新

```bash
cd /home/user/eoi-pl

# CSV を data/backup/ へ保存
cp /home/user/uploaded_files/bamei_final_check.csv data/backup/

# 更新スクリプトの実行（AI Developer が作成）
python3 scripts/update_bamei_from_csv.py
```

### Step 6-3: 配信フォーマットの生成

```bash
# 2025年1月1日のサンプル生成
python3 scripts/generate_forecast_output.py 20250101

# 馬名が正常に表示されるか確認
head -50 backtest/forecast_output_20250101.txt
```

---

## 📊 成功基準（達成目標）

| 項目 | 成功基準 | 検証方法 |
|------|----------|----------|
| **PC-KEIBA GUI** | 馬名が日本語で表示される | GUI で馬データを開いて目視確認 |
| **PostgreSQL** | bamei 列が UTF-8 の日本語バイト列 | `encode(bamei::bytea, 'hex')` で確認 |
| **CSV エクスポート** | Excel で開いても文字化けしない | Notepad/Excel で確認 |
| **EOI-PL 統合** | 配信フォーマットで馬名が正常表示 | `forecast_output_*.txt` を確認 |

---

## ⏱️ タイムライン

| Phase | 作業内容 | 所要時間 |
|-------|----------|----------|
| Phase 1 | 環境初期化 | 30分 |
| Phase 2 | システム修正 | 15分 |
| Phase 3 | 基盤再構築 | 20分 |
| Phase 4 | データ再登録 | 30分 |
| Phase 5 | 最終検証 | 10分 |
| **合計** | | **約 105分** |

---

## 🚨 トラブルシューティング

### 問題1: PostgreSQL 16.4 のインストールで競合

**症状:** インストール時に「既存のインスタンスが存在する」エラー

**対策:**
```powershell
# レジストリの残骸を削除
reg delete "HKLM\SOFTWARE\PostgreSQL" /f
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\postgresql-x64-17" /f
```

### 問題2: PC-KEIBA の接続テストで失敗

**症状:** 「データベースに接続できません」

**対策:**
1. PostgreSQL サービスが起動しているか確認
   ```powershell
   Get-Service -Name "postgresql-x64-16"
   # 停止している場合: Start-Service "postgresql-x64-16"
   ```
2. ファイアウォールの確認
3. pg_hba.conf の編集（必要に応じて）

### 問題3: データ再登録で文字化けが継続

**症状:** Phase 5 の検証でまだ `?` が表示される

**原因:**
- Windows のコードページが依然として UTF-8
- UmaConn のデータ自体が破損

**対策:**
1. `chcp` で 932 を確認
2. システム再起動
3. UmaConn のデータ再取得

---

## 📝 最終チェックリスト

- [ ] PostgreSQL 17.7 をアンインストール
- [ ] setupdata フォルダを削除
- [ ] Windows コードページが 932 であることを確認
- [ ] PostgreSQL 16.4 をインストール（ロケール: C または Japanese_Japan.932）
- [ ] PC-KEIBA の接続設定を変更
- [ ] セットアップデータ登録を実行
- [ ] PC-KEIBA GUI で馬名が日本語表示されることを確認
- [ ] PostgreSQL で `encode(bamei::bytea, 'hex')` が UTF-8 バイト列であることを確認
- [ ] CSV エクスポートで正常な日本語が出力されることを確認
- [ ] CSV をこのチャットにアップロード
- [ ] AI Developer が EOI-PL データベースを更新
- [ ] 配信フォーマットで馬名が正常表示されることを確認

---

## ✅ CEO、この計画で実行しますか？

**推定完了時間:** 約 2時間（105分 + トラブル対応の余裕）

**次のアクション:**
1. Phase 1 から順番に実行
2. 各 Phase の実行結果をこのチャットで報告
3. 問題が発生したら即座に報告

**準備はできています！実行指示をお願いします！** 🚀
