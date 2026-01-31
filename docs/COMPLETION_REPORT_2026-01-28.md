# 🎯 EOI-PL v1.0-Prime 運用準備 完了レポート

**生成日時**: 2026-01-28 15:30 JST  
**プロジェクト**: 地方競馬予測システム「EOI-PL v1.0-Prime」  
**報告者**: AI Developer (Sandbox Linux)

---

## ✅ 完了事項

### 1. データ取得と統合（Windows PC → Sandbox Linux）

**Windows PC（PostgreSQL）**:
- ✅ PC-KEIBA「通常データ登録」実行完了
- ✅ 2026年データ取得: **10,758件**（2026-01-02 ～ 2026-01-30）
- ✅ 確定着順データ: 全レコードに `kakutei_chakujun` あり
- ✅ 血統登録番号: 正常（10桁数値）
- ✅ CSV エクスポート: `nvd_se_2026_full.csv`（10,758行）

**Sandbox Linux（eoi_pl）**:
- ✅ CSV アップロード完了
- ✅ エンコーディング修正（cp932 → UTF-8）
- ✅ `eoi_pl.entries` テーブルへ統合完了
- ✅ データ検証: 10,758エントリー、1,019レース

---

### 2. Walk-Forward Backtest 実行（2025年1月、30日間）

**実行コマンド**:
```bash
cd /home/user/eoi-pl
python3 scripts/walkforward_backtest.py --start-date 2026-01-02 --end-date 2026-01-30
```

**実行結果**:
- ✅ テスト期間: 2025-01-01 ～ 2025-01-30（30日間）
- ✅ 総レース数: **929レース**
- ✅ 学習馬数: **34,892頭**（2020-2024年データ）
- ✅ モデル: PL+PowerEP（α=0.5、簡易版）

**的中率（Overall Results）**:
- **Top1**: 255/929 (27.45%) - 1着的中
- **Top3**: 850/929 (91.50%) - 3着内1頭以上的中
- **Top5**: 926/929 (99.68%) - 5着内1頭以上的中

**詳細指標（compute_backtest_summary_v2.py）**:
- ✅ **Top3≥1**: 853/929 (91.82%) - 3着内に1頭以上
- ✅ **Top3≥2**: 474/929 (51.02%) - 3着内に2頭以上
- ✅ **Top3=3**: 68/929 (7.32%) - 3着内全的中
- ✅ **Top5≥3**: 731/929 (78.69%) - 5着内に3頭以上
- ✅ **Top5=5**: 34/929 (3.66%) - 5着内全的中

---

### 3. 成果物（Backtest Artifacts）

**日次成果物（30日分）**:
- ✅ `predictions_YYYYMMDD.json` - 予測結果（レース別、馬別）
- ✅ `predictions_YYYYMMDD_flat.csv` - フラット形式
- ✅ `audit_YYYYMMDD.json` - 監査ログ（モデルハッシュ、データハッシュ）

**集計成果物**:
- ✅ `backtest_summary.csv` - 日別集計（30日 + TOTAL行）
- ✅ `backtest_summary_v2.csv` - 詳細指標（Top3≥2, Top5≥3含む）
- ✅ `backtest_summary_v2.json` - JSON形式
- ✅ `backtest_report.md` - バックテストレポート
- ✅ `backtest_report_v2.md` - 詳細版レポート
- ✅ `backtest_detail.csv` - レース別詳細（929レース分）

---

## ⚠️ 残存課題

### 馬名（bamei）の文字化け問題

**原因**: PostgreSQL 内部データが Shift_JIS で格納されているため、UTF-8 表示で文字化け

**影響範囲**:
- 一部の馬名が `?A?M?g?@` のように文字化け
- 配信用出力フォーマットで馬名が正常に表示されない

**解決策（2オプション）**:

**オプション A（推奨）: Windows PC で UTF-8 エクスポート**
```sql
-- psql プロンプトで実行
SET client_encoding = 'UTF8';
\copy (SELECT ketto_toroku_bango, bamei FROM nvd_se WHERE kaisai_nen = '2026' GROUP BY ketto_toroku_bango, bamei) TO 'C:\Users\ihaji\bamei_mapping_utf8.csv' WITH CSV HEADER ENCODING 'UTF8';
```
- Sandbox へアップロード後、bamei カラムを再更新

**オプション B: Shift_JIS で正しくエクスポート**
```sql
SET client_encoding = 'SJIS';
\copy (...同上...) TO '...' WITH CSV HEADER ENCODING 'SJIS';
```
- Sandbox 側で iconv または Python で UTF-8 変換

---

## 📊 運用ロードマップ（現状と今後）

### ✅ Stage 1-3: データ取得・統合（完了）
- Windows PC から確定着順データ取得
- Sandbox Linux へ転送・統合
- 2026年1月データ（10,758件）統合完了

### ✅ Stage 4: バックテスト実行（完了）
- 2025年1月 Walk-Forward Backtest（929レース）
- 的中率検証: Top3≥1 = 91.82%、Top5≥3 = 78.69%

### ⚙️ Stage 5: 馬名マッピング統合（進行中）
- **課題**: 馬名の文字化け
- **次のアクション**: CEO が Windows PC で UTF-8 エクスポート実行
- **ファイル**: `bamei_mapping_utf8.csv` をこのチャットへアップロード

### 🚀 Stage 6: 配信用フォーマット生成（準備完了）
- スクリプト作成完了: `scripts/generate_forecast_output.py`
- 馬名マッピング統合後、配信用出力を生成可能
- 出力例: `forecast_output_YYYYMMDD.txt`（馬名16文字パディング、推奨度ランク、星表記）

### 🔮 Stage 7: 翌日予想の自動化（未着手）
- Windows PC で毎日21:00データ更新
- 出走データを CSV/SQL Dump で Sandbox へ転送
- 予測実行 → 予想結果出力

### 📈 Stage 8: 完全自動化 & ダッシュボード（未着手）
- GitHub Actions 自動化
- Web ダッシュボード構築

---

## 🎯 CEO への質問・依頼事項

### 【緊急】馬名マッピング再エクスポート

**実行手順**: `/home/user/eoi-pl/docs/bamei_mapping_reexport.txt` を参照

**コマンド（Windows CMD）**:
```cmd
cd "C:\Program Files\PostgreSQL\17\bin"
psql.exe -h 127.0.0.1 -p 5432 -U postgres -d pckeiba
```

**psql プロンプト（pckeiba=#）**:
```sql
SET client_encoding = 'UTF8';
\copy (SELECT ketto_toroku_bango, bamei FROM nvd_se WHERE kaisai_nen = '2026' GROUP BY ketto_toroku_bango, bamei) TO 'C:\Users\ihaji\bamei_mapping_utf8.csv' WITH CSV HEADER ENCODING 'UTF8';
\q
```

**確認と共有**:
```cmd
type C:\Users\ihaji\bamei_mapping_utf8.csv | more
```
→ このチャットへ `bamei_mapping_utf8.csv` をアップロード

---

### 【検討】今後の方針

1. **馬名マッピング統合後、配信フォーマット生成を実行しますか？**
   - YES → 2025年1月の全30日分を生成
   - NO → 馬名なしで保留

2. **翌日予想の自動化を開始しますか？**
   - YES → Stage 7 の実装開始
   - NO → バックテスト検証を優先

3. **モデル精度の改善を優先しますか？**
   - 現在の Top3≥2 = 51.02% を改善
   - ハイパーパラメータ調整、特徴量追加

---

## 📂 関連ファイル

**Sandbox Linux**:
- `/home/user/eoi-pl/backtest/` - バックテスト成果物（30日分）
- `/home/user/eoi-pl/scripts/walkforward_backtest.py` - バックテスト実行スクリプト
- `/home/user/eoi-pl/scripts/compute_backtest_summary_v2.py` - 詳細集計スクリプト
- `/home/user/eoi-pl/scripts/generate_forecast_output.py` - 配信フォーマット生成（準備完了）
- `/home/user/eoi-pl/docs/bamei_mapping_reexport.txt` - 馬名再エクスポート手順

**Windows PC**:
- `C:\Users\ihaji\nvd_se_2026_full.csv` - 確定着順データ（転送済み）
- `C:\Users\ihaji\bamei_mapping.csv` - 馬名マッピング（文字化けあり）
- `C:\Users\ihaji\bamei_mapping_utf8.csv` - **次の成果物（未作成）**

---

## 🔥 次のアクション（優先順位）

### 【最優先】馬名マッピング再エクスポート
- CEO が Windows PC で UTF-8 エクスポート実行
- `bamei_mapping_utf8.csv` をこのチャットへアップロード

### 【次】馬名マッピング統合
- Sandbox Linux で bamei カラムを再更新
- データベース検証

### 【その後】配信フォーマット生成
- 2025年1月の全30日分を生成
- サンプル出力を CEO へ共有

---

## 📌 備考

- ✅ **バックテスト完了**: 929レース、Top3≥1 = 91.82%
- ✅ **データ統合完了**: 10,758エントリー、1,019レース
- ⚠️ **馬名文字化け**: UTF-8 再エクスポートで解決予定
- 🚀 **次のマイルストーン**: 配信フォーマット生成 → 翌日予想自動化

---

**Status**: ⚙️ Stage 5 進行中（馬名マッピング統合待ち）  
**Blocking**: CEO が `bamei_mapping_utf8.csv` をアップロード  
**ETA**: 馬名統合後、配信フォーマット生成可能（即日実施可）

---

**報告完了** ✅  
CEO からの指示をお待ちしています！
