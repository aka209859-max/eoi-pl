# 🚀 PostgreSQL馬名データ文字化け問題 - 完全解決実行計画

**生成日時**: 2026-01-29 朝  
**実行者**: CEO（Windows PC） + AI Developer（Sandbox Linux）  
**所要時間**: 約55分

---

## 📋 **解決策サマリー**

### ✅ **採用する方法**
**オプションB: PostgreSQLへの再インポート（正しいエンコーディング設定）**

### 🔑 **成功の鍵**
- **環境変数**: `PGCLIENTENCODING=SJIS` を設定
- **PC-KEIBA**: 正しいエンコーディング設定で「通常データ登録」を再実行
- **検証**: バイト列が UTF-8 の日本語（`e382b8...`）になることを確認

---

## 📊 **Phase 1: 事前準備とバックアップ（CEO実行）**

### ⏱️ **所要時間**: 5分

### 📋 **手順1: 現在のデータをバックアップ**

```cmd
REM Windows PowerShellで実行
cd "C:\Program Files\PostgreSQL\17\bin"

REM バックアップディレクトリ作成
mkdir C:\backup

REM データベースバックアップ
pg_dump.exe -U postgres -d pckeiba -t nvd_se --data-only -f "C:\backup\nvd_se_backup_%date:~0,4%%date:~5,2%%date:~8,2%.sql"
```

**確認**:
```cmd
dir C:\backup\nvd_se_backup_*.sql
```

**期待結果**: バックアップファイルが作成される（例: `nvd_se_backup_20260129.sql`）

---

## 🔧 **Phase 2: 環境設定の変更（CEO実行）**

### ⏱️ **所要時間**: 10分

### 📋 **手順2: 環境変数を恒久的に設定**

```cmd
REM 管理者権限でコマンドプロンプトを開く
REM （スタートメニュー → cmd → 右クリック → 管理者として実行）

REM システム環境変数に設定
setx PGCLIENTENCODING SJIS /M
```

**確認**:
```cmd
REM 新しいコマンドプロンプトを開いて確認
echo %PGCLIENTENCODING%
```

**期待結果**: `SJIS` と表示される

### 📋 **手順3: PC-KEIBAの設定確認（オプション）**

1. PC-KEIBAソフトを起動
2. **環境設定** → **データベース設定** → **接続詳細**
3. PostgreSQL接続設定を確認
   - ホスト: 127.0.0.1
   - ポート: 5432
   - データベース: pckeiba
   - ユーザー: postgres

---

## 🗑️ **Phase 3: 破損データの削除（CEO実行）**

### ⏱️ **所要時間**: 2分

### 📋 **手順4: 2026年の破損データを削除**

```cmd
cd "C:\Program Files\PostgreSQL\17\bin"
psql.exe -h 127.0.0.1 -p 5432 -U postgres -d pckeiba
```

**psql プロンプト (pckeiba=#) で実行**:
```sql
-- 2026年データを削除
DELETE FROM nvd_se WHERE kaisai_nen = '2026';

-- 削除件数確認
SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026';
-- 期待結果: 0

-- 終了
\q
```

---

## 📥 **Phase 4: 正しいエンコーディングで再インポート（CEO実行）**

### ⏱️ **所要時間**: 30分

### 📋 **手順5: PC-KEIBAで「通常データ登録」を実行**

```cmd
REM 新しいコマンドプロンプトを開く（環境変数を反映）
set PGCLIENTENCODING=SJIS

REM PC-KEIBAを起動
start "" "C:\Program Files\PC-KEIBA\pckeiba.exe"
```

**PC-KEIBAソフト上での操作**:
1. メニュー → **データ** → **通常データ登録**
2. 読み出し開始ポイント: **2026年1月2日**
3. 読み出し終了ポイント: **2026年1月30日**
4. **開始** ボタンをクリック
5. 処理完了まで待機（進捗バーを確認）

**期待結果**: 「データ登録が完了しました」というメッセージ

---

## ✅ **Phase 5: データ検証（CEO実行）**

### ⏱️ **所要時間**: 3分

### 📋 **手順6: 馬名の文字化けが解消されたか確認**

```cmd
cd "C:\Program Files\PostgreSQL\17\bin"
psql.exe -h 127.0.0.1 -p 5432 -U postgres -d pckeiba
```

**psql プロンプト (pckeiba=#) で実行**:
```sql
-- 文字化けチェック
SELECT 
    ketto_toroku_bango,
    bamei,
    length(bamei) AS 文字数,
    encode(bamei::bytea, 'hex') AS バイト列
FROM nvd_se 
WHERE kaisai_nen = '2026'
LIMIT 5;
```

**期待結果**:
```
 ketto_toroku_bango |      bamei       | 文字数 |                    バイト列
--------------------+------------------+--------+--------------------------------------------------
 2022110071         | ジーティービバーイ |     11     | e382b8e383bce38386e382a3e383bce38393e38390e383bc...
```

**重要**: バイト列が `e382b8...` のように `e3` で始まる（UTF-8の日本語）

**もし文字化けが継続する場合**:
- バイト列が `3f3f3f...` → 環境変数設定が反映されていない
- 新しいコマンドプロンプトで `echo %PGCLIENTENCODING%` を確認
- PC-KEIBAソフトを再起動して再試行

---

## 📤 **Phase 6: UTF-8 CSVエクスポート（CEO実行）**

### ⏱️ **所要時間**: 5分

### 📋 **手順7: CSVエクスポート**

**psql プロンプト (pckeiba=#) で実行**:
```sql
-- UTF-8エンコーディングに設定
\encoding UTF8

-- CSVエクスポート
\copy (SELECT ketto_toroku_bango, bamei FROM nvd_se WHERE kaisai_nen = '2026' GROUP BY ketto_toroku_bango, bamei ORDER BY ketto_toroku_bango) TO 'C:\Users\ihaji\bamei_utf8_fixed.csv' WITH (FORMAT CSV, HEADER true);

-- 終了
\q
```

### 📋 **手順8: 確認とアップロード**

```cmd
REM メモ帳で確認
notepad C:\Users\ihaji\bamei_utf8_fixed.csv

REM 先頭10行を表示
type C:\Users\ihaji\bamei_utf8_fixed.csv | more
```

**期待結果**: 馬名が正常に表示される（例: "ジーティービバーイ"）

**このチャットへアップロード**: `C:\Users\ihaji\bamei_utf8_fixed.csv`

---

## 🔄 **Phase 7: Sandbox Linuxでのデータ統合（AI Developer実行）**

### ⏱️ **所要時間**: 10分

### 📋 **手順9: CSVアップロード後の処理**

```bash
cd /home/user/eoi-pl

# バックアップ作成
mkdir -p data/backup
cp /home/user/uploaded_files/bamei_utf8_fixed.csv data/backup/

# エンコーディング確認
file data/backup/bamei_utf8_fixed.csv

# 先頭確認
head -20 data/backup/bamei_utf8_fixed.csv
```

### 📋 **手順10: データベース更新スクリプト作成**

```python
# scripts/update_bamei_from_csv.py
#!/usr/bin/env python3
import csv
import psycopg2

print("🔄 馬名マッピング統合開始...")

# データベース接続
conn = psycopg2.connect(
    host="localhost",
    database="eoi_pl",
    user="postgres",
    password="postgres123"
)
cur = conn.cursor()

# CSV読み込み
csv_path = '/home/user/eoi-pl/data/backup/bamei_utf8_fixed.csv'
updates = []

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ketto = row['ketto_toroku_bango']
        bamei = row['bamei'].strip()
        updates.append((bamei, ketto))

print(f"📊 読み込み件数: {len(updates)}件")

# 一括更新
cur.executemany("""
    UPDATE entries 
    SET bamei = %s 
    WHERE ketto_toroku_bango = %s
""", updates)

conn.commit()
print(f"✅ {cur.rowcount} 件の馬名を更新")

# 検証
print("\n📋 更新後のサンプルデータ:")
cur.execute("""
    SELECT race_id, umaban, bamei, ketto_toroku_bango 
    FROM entries 
    WHERE race_id LIKE '2025_0101%'
    ORDER BY race_id, umaban
    LIMIT 10
""")

for row in cur.fetchall():
    print(f"  {row[0]} | 馬番{row[1]:2d} | {row[2]} | {row[3]}")

conn.close()
print("\n✅ 馬名マッピング統合完了")
```

### 📋 **手順11: 実行と検証**

```bash
cd /home/user/eoi-pl
python3 scripts/update_bamei_from_csv.py

# データベース直接確認
PGPASSWORD=postgres123 psql -h localhost -U postgres -d eoi_pl -c "SELECT bamei, umaban FROM entries WHERE race_id = '2025_0101_54_01' ORDER BY umaban LIMIT 10;"
```

**期待結果**: 馬名が正常に表示される

---

## 🎨 **Phase 8: 配信フォーマット生成（AI Developer実行）**

### ⏱️ **所要時間**: 5分

### 📋 **手順12: サンプル出力生成**

```bash
cd /home/user/eoi-pl
python3 scripts/generate_forecast_output.py 20250101

# 確認
cat backtest/forecast_output_20250101.txt | head -50
```

**期待結果**: 馬名が正常に表示される配信フォーマット

### 📋 **手順13: 全日程の生成（オプション）**

```bash
# 2025年1月全30日分
for date in $(seq -w 1 30); do
    python3 scripts/generate_forecast_output.py 202501$date
done

# 生成確認
ls -lh backtest/forecast_output_202501*.txt
```

---

## 🛡️ **Phase 9: 再発防止策（CEO実行）**

### 📋 **手順14: 自動検証スクリプト作成**

```sql
-- C:\Users\ihaji\validate_bamei.sql
-- データ取込後に毎回実行
SELECT 
    COUNT(*) AS 総件数,
    COUNT(CASE WHEN bamei LIKE '%?%' THEN 1 END) AS 文字化け件数,
    COUNT(CASE WHEN bamei ~ '[ァ-ヶー]+' THEN 1 END) AS 正常件数
FROM nvd_se 
WHERE kaisai_nen = '2026';

-- 文字化け件数が0であることを確認
```

**使用方法**:
```cmd
cd "C:\Program Files\PostgreSQL\17\bin"
psql.exe -U postgres -d pckeiba -f C:\Users\ihaji\validate_bamei.sql
```

---

## 📊 **実行チェックリスト**

### ✅ **CEO実行事項**
- [ ] Phase 1: バックアップ作成
- [ ] Phase 2: 環境変数設定（`PGCLIENTENCODING=SJIS`）
- [ ] Phase 3: 破損データ削除
- [ ] Phase 4: PC-KEIBAで再インポート
- [ ] Phase 5: データ検証（バイト列が `e382b8...`）
- [ ] Phase 6: UTF-8 CSVエクスポート
- [ ] Phase 6: `bamei_utf8_fixed.csv` をこのチャットへアップロード

### ✅ **AI Developer実行事項**
- [ ] Phase 7: CSVアップロード後の処理
- [ ] Phase 7: データベース更新スクリプト実行
- [ ] Phase 8: 配信フォーマット生成
- [ ] Phase 8: 全日程生成（オプション）

### ✅ **最終確認**
- [ ] 馬名が正常に表示される
- [ ] 配信フォーマットが正常に生成される
- [ ] 自動検証スクリプトで文字化け件数が0

---

## 🚨 **トラブルシューティング**

### 問題1: Phase 5で文字化けが継続
**症状**: バイト列が `3f3f3f...` のまま

**解決策**:
```cmd
REM 1. 環境変数確認
echo %PGCLIENTENCODING%

REM 2. システム再起動
shutdown /r /t 0

REM 3. 再起動後に環境変数再確認
echo %PGCLIENTENCODING%

REM 4. PC-KEIBAで再度「通常データ登録」実行
```

### 問題2: PC-KEIBAでインポートエラー
**症状**: 「データベース接続エラー」

**解決策**:
```cmd
REM PostgreSQLサービスの再起動
net stop postgresql-x64-17
net start postgresql-x64-17

REM 接続テスト
psql.exe -U postgres -d pckeiba -c "SELECT version();"
```

### 問題3: CSVエクスポート時にパスエラー
**症状**: `Permission denied`

**解決策**:
```cmd
REM ユーザーディレクトリに出力
\copy (...) TO 'C:\Users\ihaji\bamei_utf8_fixed.csv' WITH (FORMAT CSV, HEADER true);
```

---

## 📚 **参考資料**

- PostgreSQL Character Set Support: https://www.postgresql.org/docs/17/multibyte.html
- PostgreSQL COPY Command: https://www.postgresql.org/docs/17/sql-copy.html
- PostgreSQL Environment Variables: https://www.postgresql.org/docs/17/libpq-envars.html

---

## 🎯 **成功基準**

### ✅ **Phase 5（検証）**
- バイト列が `e382b8...` で始まる（UTF-8の日本語）
- 馬名が正常に表示される（例: "ジーティービバーイ"）

### ✅ **Phase 6（エクスポート）**
- CSV内の馬名が正常に表示される
- メモ帳で開いて文字化けがない

### ✅ **Phase 8（配信）**
- 配信フォーマットで馬名が正常に表示される
- 16文字パディング、推奨度ランク、星表記が正常

---

**実行準備完了です！Phase 1から順番に実行してください！** 🚀

**質問や問題が発生したら、すぐにこのチャットで報告してください！**
