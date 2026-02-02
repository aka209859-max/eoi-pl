# EOI-PL v1.0-Prime Windows PC版 実装状況レポート

**作成日**: 2026-02-02  
**最終更新**: 2026-02-02 19:30  
**GitHub**: https://github.com/aka209859-max/eoi-pl  
**最新コミット**: cf3b818

---

## 🎯 目標

**画像と同じWeb UIをWindows PC上で動かす**

```
Windows PC 上で:
1. start_api_windows.bat をダブルクリック
2. http://localhost:8001 が自動的に開く
3. 「更新ボタン」で最新データを自動検出
4. 予想が画面に表示される
```

---

## ✅ 完了した作業

### 1. Windows PC環境の調査
- **PostgreSQL バージョン**: 16
- **データディレクトリ**: `E:\PostgreSQL\data`
- **サービス名**: `postgresql-x64-16`
- **状態**: Running

### 2. データベース構成の確認

#### データベース一覧
```
1. pckeiba   - PC-KEIBA の生データ
2. eoi_pl    - EOI-PL 用のデータベース
3. postgres  - デフォルト
4. template0 - テンプレート
5. template1 - テンプレート
```

#### pckeiba データベース（PC-KEIBA用）
- **94テーブル存在**
- **JVD テーブル**: JRA（中央競馬）データ
  - `jvd_ra`: レース情報
  - `jvd_se`: 出走馬情報
  - `jvd_um`: 馬マスタ
  - など
- **NVD テーブル**: NAR（地方競馬）データ
  - `nvd_ra`: レース情報
  - `nvd_se`: 出走馬情報
  - `nvd_um`: 馬マスタ
  - など

#### eoi_pl データベース（EOI-PL用）
- **2テーブル存在**
  - `races`: EOI-PL が使用する統合レースデータ
  - `entries`: EOI-PL が使用する出走馬データ
- **現状**: テーブルは存在するが、データは空（0件）

### 3. UmaConn の設定確認

UmaConnの設定画面から確認した情報：

| 項目 | 値 |
|------|-----|
| **サーバー名** | 127.0.0.1 |
| **ポート番号** | 5432 |
| **データベース名** | pckeiba |
| **ユーザー名** | postgres |
| **パスワード** | postgres123 |

### 4. 作成したファイル

#### api/config_windows.py (3,808 bytes)
Windows PC用のデータベース設定ファイル

**現在の設定**:
```python
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'eoi_pl',     # ← EOI-PL用データベース
    'user': 'postgres',
    'password': 'postgres123'
}

FEATURE_DB_PATH = r"E:\eoi-pl\data\feature_database_2020_2025.json"
```

#### start_api_windows.bat (2,947 bytes)
ダブルクリックでWeb UIを起動するバッチファイル

**実行内容**:
1. E:\eoi-pl に移動
2. Python仮想環境を有効化
3. 必要なパッケージを自動インストール
4. データベース接続テスト
5. FastAPI サーバーを起動（ポート 8001）
6. ブラウザを自動的に開く

#### README_WINDOWS_WEBUI.md (11,055 bytes)
完全なセットアップガイド

#### scripts/import_from_pckeiba_to_eoi_pl.py (4,706 bytes)
pckeiba → eoi_pl データインポートスクリプト

**目的**:
- pckeiba の `nvd_ra` → eoi_pl の `races`
- pckeiba の `nvd_se` → eoi_pl の `entries`

---

## ❌ 現在の問題

### 問題1: カラム名が日本語である

**エラー内容**:
```
psycopg2.errors.UndefinedColumn: column "年" does not exist
```

**原因**:
- `nvd_ra` テーブルのカラム名が日本語ではなく、英語またはローマ字の可能性
- SQL文で日本語カラム名を使用しているが、実際のカラム名が異なる

**必要な作業**:
1. `nvd_ra` テーブルの実際のカラム名を確認
2. `nvd_se` テーブルの実際のカラム名を確認
3. インポートスクリプトを修正

---

## 📋 次のステップ

### Step 1: テーブルスキーマを確認（CEO作業）

Windows PowerShell で以下を実行：

```powershell
# nvd_ra テーブルのカラム名を確認
$env:PGPASSWORD = "postgres123"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h 127.0.0.1 -U postgres -d pckeiba -c "\d nvd_ra"

# nvd_se テーブルのカラム名を確認
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h 127.0.0.1 -U postgres -d pckeiba -c "\d nvd_se"

# サンプルデータを確認
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h 127.0.0.1 -U postgres -d pckeiba -c "SELECT * FROM nvd_ra LIMIT 1;"
```

### Step 2: インポートスクリプトを修正

実際のカラム名に基づいてスクリプトを修正する。

### Step 3: データインポートを実行

```powershell
python scripts\import_from_pckeiba_to_eoi_pl.py
```

### Step 4: Web UIを起動

```powershell
.\start_api_windows.bat
```

---

## 🔍 調査が必要な情報

### nvd_ra テーブルの実際のカラム名

必要なカラム：
- 年（kaisai_nen）
- 月日（kaisai_tsukihi）
- 場コード（keibajo_code）
- Ｒ（race_bango）
- 距離（kyori）
- トラックコード（track_code）

### nvd_se テーブルの実際のカラム名

必要なカラム：
- 年
- 月日
- 場コード
- Ｒ
- 馬番（umaban）
- 馬名（bamei）
- 血統登録番号（ketto_toroku_bango）
- 騎手コード（kishu_code）
- 調教師コード（chokyoshi_code）
- 確定着順（kakutei_chakujun）
- タイム_秒（time_seconds）

---

## 📊 データフロー図

```
PC-KEIBA (UmaConn)
    ↓
【pckeiba データベース】
    ├─ nvd_ra (NAR レース情報)
    └─ nvd_se (NAR 出走馬情報)
    ↓
【import_from_pckeiba_to_eoi_pl.py】← ここで問題発生
    ↓
【eoi_pl データベース】
    ├─ races (統合レースデータ)
    └─ entries (統合出走馬データ)
    ↓
【Web UI (api/main.py)】
    ↓
http://localhost:8001
```

---

## 🎯 完成までの残りタスク

1. ✅ Windows PC環境の調査
2. ✅ PostgreSQL バージョン確認
3. ✅ データベース構成の確認
4. ✅ 設定ファイルの作成
5. ✅ 起動スクリプトの作成
6. ⏳ **テーブルスキーマの確認** ← 現在ここ
7. ⏳ インポートスクリプトの修正
8. ⏳ データインポートの実行
9. ⏳ Web UIの起動テスト
10. ⏳ 予想生成の動作確認

---

## 📝 重要な発見

### 発見1: データベース名の変遷
- 最初: `eoi-sike` と予想 → 存在しなかった
- 次: `pckeiba` と確認 → PC-KEIBAの生データ用だった
- 最終: `eoi_pl` が正解 → EOI-PL用のデータベース

### 発見2: データの分離
- **pckeiba**: PC-KEIBAの生データ（94テーブル）
- **eoi_pl**: EOI-PLの統合データ（2テーブル）
- データは別々に管理されている

### 発見3: PostgreSQL 16 を使用
- バージョン15ではなく16
- データディレクトリは `E:\PostgreSQL\data`
- パスワードは `postgres123`

---

## 🔗 関連ファイル

### GitHub リポジトリ
- **URL**: https://github.com/aka209859-max/eoi-pl
- **最新コミット**: cf3b818

### ローカルファイル
- **プロジェクトディレクトリ**: `E:\eoi-pl`
- **データディレクトリ**: `E:\eoi-pl\data`
- **特徴量DB**: `E:\eoi-pl\data\feature_database_2020_2025.json` (26.9 MB)

### ドキュメント
- `README_WINDOWS_WEBUI.md`: Windows PC用完全ガイド
- `STATUS_WINDOWS_WEBUI_2026_02_01.md`: 完成報告書（途中）
- `api/config_windows.py`: 設定ファイル

---

## 🚀 次回の作業開始時に実行すること

### 1. テーブルスキーマを確認

```powershell
$env:PGPASSWORD = "postgres123"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h 127.0.0.1 -U postgres -d pckeiba -c "\d nvd_ra"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h 127.0.0.1 -U postgres -d pckeiba -c "\d nvd_se"
```

### 2. 結果を基にスクリプト修正

実際のカラム名に合わせて `scripts/import_from_pckeiba_to_eoi_pl.py` を修正

### 3. データインポート実行

```powershell
cd E:\eoi-pl
python scripts\import_from_pckeiba_to_eoi_pl.py
```

---

**Play to Win！あと一歩で完成です！** 🎯
