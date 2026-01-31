# PC-KEIBA GUI 文字化け問題の徹底調査依頼

## 🚨 緊急度：HIGH

---

## 📊 問題の概要

**環境:**
- OS: Windows 10 (Build 26100.7623)
- ソフトウェア: PC-KEIBA Database
- データベース: PostgreSQL 17.7
- データソース: UmaConn (.nvd ファイル, Shift_JIS)

**問題:**
- PC-KEIBA の GUI 画面で**馬名、父名、母名、母父名などが全て文字化け**している
- PostgreSQL のデータベースでも同様に文字化け
- Windows の「Beta: Unicode UTF-8」設定が有効になっていた（現在は無効化済み）

**スクリーンショット:**
- 添付画像を参照: 馬名列が `??????` や `?C???X?g???C?J?[` のように表示されている

---

## 🔍 現状の詳細

### 1. PC-KEIBA GUI の表示状態

**馬名列（bamei）の例:**
```
??????
?C???X?g???C?J?[
?r???n?N?W???
?c?C???N???p???X
```

**期待される表示:**
```
ディープインパクト
サクラローレル
ジーティービバーイ
```

**その他の列も同様に文字化け:**
- 父名（父）
- 母名（母）
- 母父名（母父）
- 調教師名
- 馬主名

**正常に表示されている列:**
- 性別（牡、牝、せん）
- 毛色（鹿毛、栗毛、黒鹿毛）
- 所属（地方、中央）

---

### 2. データベース内部の状態

**PostgreSQL での確認結果:**

```sql
-- nvd_se テーブル（出走馬データ）
SELECT bamei FROM nvd_se WHERE kaisai_nen = '2026' LIMIT 5;
-- 結果: ???C???X?g???C?J?[?@?@?@...

-- nvd_um テーブル（馬マスタデータ）
SELECT bamei FROM nvd_um LIMIT 5;
-- 結果: �I�[�X�~���p�[�h�@�@�@...（16進数表記のようなノイズ）
```

**バイト列の確認:**
```sql
SELECT encode(bamei::bytea, 'hex') FROM nvd_se WHERE kaisai_nen = '2026' LIMIT 3;
-- 結果: 3f3f3f433f3f3f583f673f3f3f433f4a3f5b3f403f403f40...
--       (0x3F = '?', 0x40 = '@' の繰り返し)
```

**結論:**
- データは**不可逆的に破損**している
- Shift_JIS のバイナリデータが ASCII の `?` と `@` に置換されている

---

### 3. これまでの試行錯誤

#### ✅ 試したこと（全て失敗）

1. **PostgreSQL での convert_from() 関数:**
   ```sql
   SELECT convert_from(bamei::bytea, 'SJIS') FROM nvd_se;
   -- エラー: bytea型に対する不正な入力構文
   ```

2. **環境変数の設定:**
   ```cmd
   setx PGCLIENTENCODING SJIS /M
   -- 設定は成功したが、文字化けは継続
   ```

3. **データの再インポート:**
   - 環境変数 `PGCLIENTENCODING=SJIS` 設定後
   - PC-KEIBA で「通常データ登録」を再実行（2026年1月データ）
   - **結果: 文字化けは解消せず**

4. **.nvd ファイルからの直接抽出:**
   - Python スクリプトで `E:\UmaConn\data\*.nvd` から馬名を抽出
   - **結果: 有効な馬名が抽出されず（2文字の断片のみ）**

5. **Windows の「Beta: Unicode UTF-8」設定を無効化:**
   - コントロールパネル → 地域 → システムロケール変更
   - 「Beta: ワールドワイド言語サポートで Unicode UTF-8 を使用」を**無効化**
   - システム再起動
   - **結果: PC-KEIBA GUI の文字化けは継続**

---

## 🎯 調査してほしい内容

### 最優先（Critical）

1. **PC-KEIBA のデータベース接続設定の確認方法**
   - PC-KEIBA が PostgreSQL に接続する際の文字コード設定はどこで行うか？
   - 設定ファイル（.ini, .conf, .cfg）の場所は？
   - ODBC/JDBC の接続文字列の確認方法は？

2. **UmaConn のデータ取得時の文字コード設定**
   - UmaConn の .nvd ファイルは本当に Shift_JIS なのか？
   - UmaConn の環境設定で文字コードを変更できるか？
   - .nvd ファイルのバイナリ構造は？（仕様書はあるか？）

3. **PC-KEIBA のデータインポート処理の内部動作**
   - PC-KEIBA が .nvd → PostgreSQL へデータを転送する際の文字コード変換処理
   - どの時点で文字化けが発生しているのか？（.nvd 読み取り時 or PostgreSQL 書き込み時）

---

### 重要（High Priority）

4. **Windows のシステムロケールと PC-KEIBA の関係**
   - 「Beta: Unicode UTF-8」設定が有効だった期間にインポートされたデータは復旧可能か？
   - システムロケールを変更した後、既存データを修復する方法はあるか？

5. **PostgreSQL の client_encoding と server_encoding の整合性**
   - PostgreSQL 側で強制的に文字コード変換を行う方法は？
   - `sql_ascii` データベースに変更した方が良いか？

6. **PC-KEIBA の代替エクスポート機能**
   - PC-KEIBA に CSV エクスポート機能はあるか？
   - レポート機能で UTF-8 出力できるか？
   - クリップボード経由でデータを取り出せるか？

---

### 補足調査（Medium Priority）

7. **他のユーザーの事例**
   - PC-KEIBA ユーザーで同様の文字化け問題を経験した人はいるか？
   - 公式サポートフォーラムやマニュアルに記載はあるか？

8. **データ復旧の可能性**
   - .nvd ファイルが正常な場合、PostgreSQL のデータを完全に削除して再インポートする手順
   - バックアップからの復元方法

---

## 📋 期待する調査結果

### 最も知りたいこと（優先順位）

1. **PC-KEIBA の接続設定ファイルの場所と編集方法**
   - 例: `C:\Program Files\PC-KEIBA\config\database.ini`
   - 設定例: `ClientEncoding=SJIS` または `Encoding=UTF8`

2. **PC-KEIBA の正しいデータインポート手順**
   - ステップバイステップの手順書
   - 文字化けを防ぐための環境変数設定
   - データベース設定の推奨値

3. **UmaConn の .nvd ファイルから正しく馬名を抽出する方法**
   - .nvd ファイルのバイナリ構造解析
   - Python/Ruby/Perl などでのパーサー実装例
   - 既存のツールやライブラリの有無

---

## 🔗 参考情報

### 公式ドキュメント

- **PC-KEIBA 公式サイト:**
  - マニュアル: https://pc-keiba.com/wp/manual-menu/
  - 外部データ登録: https://pc-keiba.com/wp/gaibu-data/

- **PostgreSQL 公式ドキュメント:**
  - 文字セットサポート: https://www.postgresql.org/docs/17/multibyte.html
  - クライアントエンコーディング: https://www.postgresql.org/docs/17/libpq-envars.html

- **UmaConn:**
  - データ提供元: 地方競馬情報サイト（詳細不明）

---

### 技術情報

**Windows のコードページ:**
- Shift_JIS: CP932 (Windows-31J)
- UTF-8: CP65001

**PostgreSQL の設定:**
- Server Encoding: UTF8
- Client Encoding: SJIS → UTF8（自動変換されるはず）

**PC-KEIBA のバージョン情報:**
- 不明（スクリーンショットから推測: 最新版と思われる）

---

## 📸 添付資料

1. **PC-KEIBA GUI のスクリーンショット:**
   - 馬名列が全て文字化けしている状態
   - 列名は正常に表示（「馬名」「父」「母」等）

2. **PostgreSQL のクエリ結果:**
   - bamei 列のバイト列: `3f3f3f433f3f3f58...`（0x3F と 0x40 の繰り返し）

---

## 🎯 最終ゴール

**達成したいこと:**
1. PC-KEIBA の GUI で**馬名が正常に日本語表示される**状態にする
2. PostgreSQL のデータベースで**馬名が UTF-8 で正しく保存される**状態にする
3. CSV エクスポートで**正常な日本語馬名のリスト**を取得できる状態にする

**成功基準:**
- PC-KEIBA で「ディープインパクト」「サクラローレル」等が正常表示される
- PostgreSQL で `SELECT bamei FROM nvd_um LIMIT 10;` を実行すると日本語馬名が表示される
- CSV ファイルを Excel/Notepad で開いても文字化けしない

---

## ⏱️ 緊急性

**背景:**
- 競馬予測モデル（EOI-PL）の学習データとして馬名が必要
- 現状は馬番のみで運用しているが、ユーザー体験が著しく低下
- 2026年1月のデータ（10,758件）が全て文字化け状態

**タイムライン:**
- 理想: 24時間以内に解決策を特定
- 妥協: 72時間以内に暫定的な回避策を確立

---

## 📞 追加情報が必要な場合

以下の情報を追加で提供できます：
- PC-KEIBA のインストールディレクトリ構成
- PostgreSQL の設定ファイル（postgresql.conf, pg_hba.conf）
- UmaConn の .nvd ファイルのサンプル（一部抜粋）
- Windows のシステム情報（locale, code page）

---

## 🙏 調査依頼

この問題の解決策を徹底的に調査してください。

特に以下の点に注力してください：
1. **PC-KEIBA の接続設定ファイルの編集方法**
2. **UmaConn .nvd ファイルの正しい読み取り方法**
3. **データ再インポートの正しい手順**
4. **既存データの復旧可能性**

よろしくお願いします！🙇‍♂️
