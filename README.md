# EOI-PL v1.0-Prime

**48時間で"勘"を"確信"に変える — 地方競馬AI予想エンジン**

## Project Status

- **Version**: v1.0-Prime (MVP)
- **Status**: 🚧 In Development
- **Target**: 48-hour delivery cycle
- **Last Updated**: 2026-01-21

## Core Principles (絶対遵守)

### 1. 当日オッズ・人気禁止（完全禁止）
- 学習・推論・出力のすべてで使用禁止
- ログにも記録しない
- コードレビューで保証

### 2. 公開予想の凍結配信
- 前日夜 or 当日朝に1回生成
- 以後変更禁止（freeze=true）
- タイムスタンプ記録必須

### 3. 全レース全馬配信
- ファンは待たない
- 推奨度で制御（S/A/B/C/N）

### 4. 推奨度は複勝確率のみで決定
- P_place_cal（校正済み複勝確率）を基準
- Coverage固定A方式採用

### 5. 確率校正必須
- reliability diagram相当の評価
- 未校正版は過渡期のみ

## 推奨度定義（Coverage固定A）

各レース内でP_place_calを降順に並べ、上位割合で付与：

| Grade | Coverage | 説明 |
|-------|----------|------|
| S | 上位10% | 最高推奨 |
| A | 次15%（累計25%） | 高推奨 |
| B | 次25%（累計50%） | 中推奨 |
| C | 次30%（累計80%） | 低推奨 |
| N | 残り20% | 非推奨 |

**Tie処理**: 同率の場合は馬番昇順で決定（再現性保証）

## データソース

- **元データ**: 地方競馬DATA（公式） via UmaConn
- **受信方法**: PC-KEIBA Database（PostgreSQL）
- **必須テーブル**: race, entry, result, past_performance

## Output Format (MVP)

1レース単位のJSON（全レース分生成）:

```json
{
  "race_id": "20260122_11_01",
  "race_meta": {
    "venue": "川崎",
    "date": "2026-01-22",
    "race_num": 1,
    "distance": 1400,
    "surface": "ダート",
    "weather": "晴",
    "condition": "良"
  },
  "generated_at": "2026-01-21T22:00:00Z",
  "horses": [
    {
      "horse_id": "2021105678",
      "umaban": 1,
      "name": "サンプルホース",
      "P_win_cal": 0.15,
      "P_place_cal": 0.42,
      "grade": "A",
      "rank_pred": 2,
      "explain_top3": ["前走1着", "距離適性○", "騎手実績◎"]
    }
  ],
  "policy": {
    "odds_used": false,
    "freeze": true,
    "coverage_scheme": "A",
    "thresholds": {"S": 0.10, "A": 0.25, "B": 0.50, "C": 0.80}
  }
}
```

## Tech Stack

- **Language**: Python 3.11+
- **Database**: PostgreSQL (local via PC-KEIBA)
- **ML**: scikit-learn, LightGBM
- **Calibration**: isotonic / sigmoid
- **Deployment**: JSON output → 既存配信導線へ接続

## Project Structure

```
eoi-pl/
├── claude/              # everything-claude-code essentials
│   ├── agents/          # AI委任用エージェント定義
│   ├── rules/           # コーディング規律
│   ├── commands/        # ショートカットコマンド
│   └── skills/          # 設計パターン
├── src/
│   ├── data/            # データ取得・前処理
│   ├── features/        # 特徴量エンジニアリング
│   ├── models/          # 学習・推論
│   ├── calibration/     # 確率校正
│   ├── grading/         # 推奨度付与
│   └── output/          # JSON生成
├── tests/               # TDD用テスト
├── config/              # 設定ファイル（.env含む）
├── scripts/             # 実行スクリプト
└── data/                # ローカルデータ（.gitignore済）
```

## Done Definition (48時間ゴール)

- [ ] ローカルPostgreSQLから読み込み成功
- [ ] 明日分の全レースでJSON生成可能
- [ ] gradeがCoverage固定Aで正しく付与
- [ ] 公開凍結（前夜/朝1回生成）を保証
- [ ] 当日オッズ・人気を一切使用していない保証
- [ ] 校正済み確率の出力成功
- [ ] 既存配信導線への接続テスト完了

## Development Philosophy

- **10x Mindset**: 10%改善ではなく10倍成長
- **Be Resourceful**: リソース不足を知恵とAIで突破
- **Play to Win**: 負けないためではなく、勝つためにプレイ
- **Buy Back Time**: 時間を金（AI）で買い、戦略に投資

## Notes

- NAR-SI4.0の既存資産（ETL/配信導線）は最大限温存
- v1.0はMVP = JSON出力まで
- v1.1以降でフロントエンド・リアルタイム配信等を拡張

---

**Status**: 🚀 Ready for rapid development
