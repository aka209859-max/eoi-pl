# 🔍 PostgreSQL Shift_JIS 文字化け問題 - ディープサーチ用プロンプト

---

## 📋 調査依頼内容

Windows環境のPostgreSQL 17データベースから、地方競馬の馬名（bamei）データをCSVエクスポートする際に発生する文字化け問題の解決策を調査してください。

---

## 🏗️ システム構成

### Windows PC 環境
- **OS**: Windows 10/11
- **PostgreSQL**: 17.7
- **データベース**: `pckeiba`
- **ソフトウェア**: PC-KEIBA（地方競馬データ管理ソフト）
- **データソース**: UmaConn（地方競馬DATA自動取得サービス）
- **データ形式**: .nvd ファイル（地方競馬DATAのバイナリ形式）

### データ特性
- **データ内容**: 日本の地方競馬の馬名（例: "ドンクロノス"、"ビリーヴサンライズ"）
- **文字種**: 全角カタカナ、全角ひらがな、漢字、記号を含む日本語
- **格納テーブル**: `nvd_se` テーブルの `bamei` カラム (TEXT型)
- **データ量**: 約10,000レコード

---

## ❌ 問題の詳細

### 現象
PostgreSQLから以下のコマンドでCSVエクスポートすると、馬名が文字化けする：

```sql
-- psql プロンプト (pckeiba=#) で実行
\copy (SELECT ketto_toroku_bango, bamei FROM nvd_se WHERE kaisai_nen = '2026' GROUP BY ketto_toroku_bango, bamei) TO 'C:\Users\ihaji\bamei_mapping.csv' WITH CSV HEADER ENCODING 'UTF8';
```

### 文字化けの例
- **正常な馬名**: "ドンクロノス"、"ビリーヴサンライズ"
- **文字化け後**: `?W?[?e?B?[?????o?C?@?@?@?@?@?@?@?@?@`、`?G?X?V?[???}?g?@?@?@?@?@?@?@?@?@?@?@`

### エクスポートしたCSVの実例
```csv
ketto_toroku_bango,bamei
2022110071,?W?[?e?B?[?????o?C?@?@?@?@?@?@?@?@?@
2021100845,?G?X?V?[???}?g?@?@?@?@?@?@?@?@?@?@?@
2120250331,?T?J?m?V?b?v?[?@?@?@?@?@?@?@?@?@?@?@
```

---

## 🔧 既に試した対策（全て失敗）

### 試行1: UTF-8エンコーディング指定
```sql
SET client_encoding = 'UTF8';
\copy (...) TO '...' WITH CSV HEADER ENCODING 'UTF8';
```
**結果**: 文字化け継続

### 試行2: 環境変数設定
```cmd
setx PGCLIENTENCODING UTF8
```
**結果**: 新しいCMDでも文字化け継続

### 試行3: Shift_JISエンコーディング指定
```sql
SET client_encoding = 'SJIS';
\copy (...) TO '...' WITH CSV HEADER ENCODING 'SJIS';
```
**結果**: 文字化け継続（同じパターン）

### 試行4: Windows CMDでの表示確認
```cmd
type C:\Users\ihaji\bamei_mapping.csv | more
```
**結果**: `?W?[?e?B?[?????o?C` のような文字化け

---

## 📊 データベース内部の状態

### サーバーエンコーディング確認
```sql
SHOW server_encoding;
-- 結果: UTF8
```

### クライアントエンコーディング確認
```sql
SHOW client_encoding;
-- 初期状態: SJIS
-- SET後: UTF8（設定したエンコーディングに変化）
```

### psqlでのデータ表示（Windows CMD）
```sql
SELECT bamei FROM nvd_se WHERE kaisai_nen = '2026' LIMIT 5;
```
**結果**: 全て文字化け（`?W?[?e?B?[?????o?C` など）

### データベース内のbameiカラムの実データ確認
Linuxサンドボックス（UTF-8環境）から接続した場合：
```sql
SELECT bamei FROM entries WHERE race_id = '2025_0101_54_01';
```
**結果**: 
- 一部の馬名は正常表示（例: "ドンクロノス"、"ビリーヴサンライズ"）
- 一部は文字化け（例: `?A?M?g?@?@?@?@?@`）

---

## 🤔 推定される原因

### 仮説1: データベース内部にShift_JISで格納されている
- PC-KEIBAソフトが.nvdファイルからデータをインポートする際に、Shift_JISエンコーディングで格納
- PostgreSQLのサーバーエンコーディングはUTF8だが、実データはShift_JISのバイト列がそのまま格納されている可能性

### 仮説2: UmaConnの.nvdファイル自体がShift_JIS
- 元データ（.nvdファイル）がShift_JISエンコーディング
- PostgreSQLへのインポート時にエンコーディング変換が行われていない

### 仮説3: Windowsのコードページ問題
- Windows CMDのコードページが932（Shift_JIS）
- PostgreSQL psqlクライアントとの通信時にエンコーディング不一致が発生

---

## 🎯 調査してほしい事項

### 1. PostgreSQL内部の実データエンコーディング確認方法
- TEXTカラムに格納されているバイト列のエンコーディングを確認する方法
- `SELECT encode(bamei::bytea, 'hex')` のような方法で実バイト列を確認できるか？

### 2. Shift_JIS → UTF-8 変換の正しい手順
- PostgreSQL内部でShift_JISで格納されているデータをUTF-8に変換してエクスポートする方法
- `convert_from()` 関数や `CAST` を使った変換方法

### 3. CSVエクスポート時の正しいエンコーディング指定
- `\copy` コマンドで実データがShift_JISの場合の正しいエンコーディング指定方法
- `ENCODING 'SJIS'` と `ENCODING 'UTF8'` の挙動の違い

### 4. Windows環境特有の対処法
- Windows CMDのコードページ設定（`chcp 65001` など）
- psql.exeの起動オプション（`--encoding` など）

### 5. データ移行の最適解
- PostgreSQLでデータを正しくエクスポートする最も確実な方法
- pg_dump、COPY、\copy の使い分け

---

## 🔍 期待する調査結果

### 最優先
1. **文字化けの根本原因の特定**
   - データベース内部のエンコーディング状態を正確に把握する方法

2. **Windows PCでのCSVエクスポート成功手順**
   - psqlコマンドまたはSQL文で、正常な日本語馬名をCSVエクスポートする具体的な手順

### 副次的
3. **Linux環境での対処法**
   - 文字化けしたCSVをLinux側でShift_JIS → UTF-8変換する方法（iconvなど）

4. **PostgreSQL設定の最適化**
   - 将来のデータインポート時に文字化けを防ぐための設定

---

## 📚 参考情報

### PostgreSQL公式ドキュメント
- Character Set Support: https://www.postgresql.org/docs/17/multibyte.html
- COPY command: https://www.postgresql.org/docs/17/sql-copy.html

### 関連する日本語エンコーディング
- Shift_JIS (Windows-31J, CP932)
- UTF-8
- EUC-JP

### 使用中のツール
- psql 17.7 (PostgreSQL client)
- PC-KEIBA (Windows地方競馬データ管理ソフト)
- UmaConn (地方競馬DATA自動取得サービス)

---

## 🎯 最終ゴール

**Windows PCのPostgreSQLから、日本語の馬名が正常に表示されるCSVファイル（UTF-8エンコーディング）をエクスポートする具体的な手順を確立する。**

エクスポート成功の判断基準：
```csv
ketto_toroku_bango,bamei
2022110071,ジーティービバーイ
2021100845,エスヴィーマト
2120250331,サカノシップー
```

上記のように、正常な日本語（カタカナ）が表示されるCSVファイルが得られること。

---

## 💡 調査のヒント

- PostgreSQLの `pg_client_encoding()` 関数
- `SELECT encode(bamei::bytea, 'hex')` でバイト列確認
- `convert_from(bamei::bytea, 'SJIS')` でShift_JIS → UTF-8変換
- Windows CMDの `chcp 65001` (UTF-8コードページ)
- psql起動時の `--encoding` オプション

---

**調査期限**: できるだけ早く  
**優先度**: 🔥 最優先（システム運用のブロッカー）

---

以上、よろしくお願いいたします！
