# 🏇 EOI-PL Web配信システム + Discord Bot 実装計画書

**作成日**: 2026-01-31  
**プロジェクト**: EOI-PL v1.0-Prime 配信システム  
**CEO**: Enable CEO  
**目標**: Webアプリ + Discord自動配信の完全自動化

---

## 🎯 **プロジェクト目標**

### **Phase 1: Webアプリケーション**
- ボタン1つで地方競馬予想を生成
- note記事用テキストをワンクリックコピー
- 過去の予想を閲覧可能
- スマホ・PCからアクセス可能

### **Phase 2: Discord Bot**
- 毎朝9:00に自動配信
- 手動コマンドでも実行可能
- 推奨度フィルタリング機能

---

## 📊 **技術スタック**

### **Webアプリ**
- **Backend**: Hono (TypeScript)
- **Frontend**: TailwindCSS + Vanilla JavaScript
- **Database**: PostgreSQL (既存の eoi_pl)
- **Deployment**: Cloudflare Pages (無料)
- **開発環境**: PM2 (sandbox) → wrangler pages dev

### **Discord Bot**
- **Language**: Python 3.12
- **Library**: discord.py
- **Scheduler**: Windows Task Scheduler or Cloudflare Workers Cron
- **Database**: PostgreSQL (eoi_pl)

---

## 🚀 **Phase 1: Webアプリ実装（推定時間: 2時間）**

### **Step 1-1: プロジェクト構造作成（10分）**

```
E:\eoi-pl\webapp\
├── src\
│   └── index.tsx           # Hono メインアプリ
├── public\
│   ├── static\
│   │   ├── app.js          # フロントエンド JavaScript
│   │   └── styles.css      # カスタムCSS
│   └── index.html          # (必要に応じて)
├── wrangler.jsonc          # Cloudflare設定
├── package.json
├── tsconfig.json
├── vite.config.ts
└── ecosystem.config.cjs    # PM2設定
```

### **Step 1-2: Hono Backend実装（30分）**

**API エンドポイント:**

```typescript
// GET /api/dates - 利用可能な日付一覧を取得
// GET /api/predictions/:date - 指定日の予想を取得
// GET /api/race/:race_id - 単一レース予想を取得
// POST /api/generate/:date - 予想を生成（未生成の場合）
```

**主要機能:**
1. PostgreSQL (eoi_pl) からレースデータ取得
2. feature_database_2020_2025.json を使用して予想計算
3. 推奨度（★1〜5）の算出
4. JSON形式でフロントエンドに返却

**予想生成ロジック:**
- 既存の `format_predictions_discord.py` のロジックを TypeScript に移植
- `EOIPLPredictor` クラスを TypeScript で再実装
- 偏差値計算、推奨度計算を実装

### **Step 1-3: Frontend実装（40分）**

**画面構成:**

```
┌─────────────────────────────────────────────┐
│  🏇 EOI-PL 予想配信センター                  │
├─────────────────────────────────────────────┤
│                                             │
│  📅 日付選択: [2026/02/01 ▼] [予想生成]    │
│                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  【高知 1R】★★★★★ (1位偏差値: 72.6)       │
│  ┌─────────────────────────────────────┐  │
│  │ 順位  馬番  馬名           偏差値   │  │
│  ├─────────────────────────────────────┤  │
│  │ 1    7番   シーザソング      72.6   │  │
│  │ 2    9番   ランギロア        54.2   │  │
│  │ 3    8番   カンタベリー      53.5   │  │
│  └─────────────────────────────────────┘  │
│  🎯 推奨買い目: Top3（馬連BOX）: 7,9,8      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                             │
│  📋 [note用にコピー] 📤 [Discordに送信]    │
│                                             │
└─────────────────────────────────────────────┘
```

**実装機能:**
1. 日付選択（カレンダーUI or ドロップダウン）
2. 予想生成ボタン（APIコール）
3. レース一覧表示（全馬表示）
4. note用フォーマット生成
5. クリップボードへコピー機能
6. レスポンシブデザイン（スマホ対応）

**note用フォーマット例:**

```markdown
# 2026/02/01 地方競馬AI予想

## 高知 1R ★★★★★

**本命:** 7番 シーザソング (偏差値: 72.6)  
**対抗:** 9番 ランギロア (54.2)  
**単穴:** 8番 カンタベリービーム (53.5)

**推奨買い目:**
- 馬連BOX: 7-9-8
- 三連複BOX: 7-9-8-4-6

**分析:** 本命が圧倒的で非常に予想しやすいレースです

---
```

### **Step 1-4: データベース連携（20分）**

**接続設定:**
- 開発環境: localhost PostgreSQL (eoi_pl)
- 本番環境: Cloudflare D1 (PostgreSQLからマイグレーション)

**マイグレーション戦略:**
1. 開発: PostgreSQL (E:\eoi-pl\scripts\import_csv_to_postgres.py)
2. 本番: Cloudflare D1 (wrangler d1 migrations)

### **Step 1-5: デプロイ準備（20分）**

**Cloudflare Pages設定:**
```jsonc
// wrangler.jsonc
{
  "name": "eoi-pl-webapp",
  "compatibility_date": "2024-01-01",
  "pages_build_output_dir": "./dist"
}
```

**デプロイコマンド:**
```bash
npm run build
npx wrangler pages deploy dist --project-name eoi-pl-webapp
```

---

## 🤖 **Phase 2: Discord Bot実装（推定時間: 1時間）**

### **Step 2-1: Discord Bot基本構造（20分）**

```
E:\eoi-pl\discord-bot\
├── bot.py                  # メインBot
├── config.py               # 設定（トークン等）
├── predictor.py            # 予想ロジック
├── formatter.py            # Discord用フォーマット
├── scheduler.py            # 定時実行
└── requirements.txt
```

**Discord Bot機能:**
1. `/predict <日付>` - 手動で予想を生成
2. `/today` - 今日の予想を表示
3. 毎朝9:00に自動配信

### **Step 2-2: 予想ロジック統合（20分）**

```python
# predictor.py
import psycopg2
import json
from format_predictions_discord import EOIPLPredictor

class DiscordPredictor:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'eoi_pl',
            'user': 'postgres',
            'password': 'postgres123'
        }
        self.predictor = EOIPLPredictor('E:/eoi-pl/data/feature_database_2020_2025.json')
    
    def predict_date(self, date: str):
        """日付を指定して全レース予想"""
        # 既存のformat_predictions_discord.pyを活用
        pass
```

### **Step 2-3: Discord用フォーマット（10分）**

```python
# formatter.py
def format_for_discord(predictions):
    """Discord Embed形式で整形"""
    embed = discord.Embed(
        title=f"🏇 {date} NAR AI予想",
        color=0x00ff00
    )
    
    for race in predictions:
        embed.add_field(
            name=f"【{race['venue']} {race['race_no']}R】{race['rating']}",
            value=f"本命: {race['top1']}\n推奨: {race['top3']}",
            inline=False
        )
    
    return embed
```

### **Step 2-4: 定時実行設定（10分）**

**Option A: Windows Task Scheduler**
```powershell
# 毎朝9:00に実行
$action = New-ScheduledTaskAction -Execute "py" -Argument "-3.12 E:\eoi-pl\discord-bot\bot.py --daily"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "EOI-PL Discord配信"
```

**Option B: Cloudflare Workers Cron**
```toml
# wrangler.toml
[triggers]
crons = ["0 9 * * *"]  # 毎日9:00 UTC (18:00 JST)
```

---

## 📋 **実装チェックリスト**

### **Phase 1: Webアプリ**
- [ ] Step 1-1: プロジェクト構造作成
- [ ] Step 1-2: Hono Backend実装
  - [ ] API /api/dates
  - [ ] API /api/predictions/:date
  - [ ] API /api/race/:race_id
  - [ ] 予想生成ロジック
- [ ] Step 1-3: Frontend実装
  - [ ] 日付選択UI
  - [ ] レース表示
  - [ ] note用コピー機能
  - [ ] レスポンシブデザイン
- [ ] Step 1-4: データベース連携
- [ ] Step 1-5: ローカルテスト
- [ ] Step 1-6: Cloudflare Pagesデプロイ

### **Phase 2: Discord Bot**
- [ ] Step 2-1: Bot基本構造
- [ ] Step 2-2: 予想ロジック統合
- [ ] Step 2-3: Discord用フォーマット
- [ ] Step 2-4: 定時実行設定
- [ ] Step 2-5: テスト配信
- [ ] Step 2-6: 本番運用開始

---

## 🎯 **成功基準**

### **Webアプリ**
✅ ボタン1つで予想生成成功  
✅ note用テキストが正しくコピーされる  
✅ スマホからアクセス可能  
✅ 過去の予想が閲覧可能  
✅ Cloudflare Pagesで公開

### **Discord Bot**
✅ 毎朝9:00に自動配信成功  
✅ `/predict` コマンドで手動実行可能  
✅ 推奨度フィルタリング機能動作  
✅ エラーハンドリング実装

---

## ⚠️ **リスクと対策**

### **リスク1: Cloudflare D1への移行**
- **問題**: PostgreSQLとの互換性
- **対策**: ローカルはPostgreSQL、本番はD1で --local開発

### **リスク2: Discord Bot認証**
- **問題**: Bot トークンの管理
- **対策**: .env ファイルで管理、.gitignoreに追加

### **リスク3: 定時実行の信頼性**
- **問題**: Windows PCがスリープ中は実行されない
- **対策**: Cloudflare Workers Cronに移行

---

## 📅 **実装スケジュール**

| Phase | タスク | 推定時間 | 実施日 |
|-------|--------|---------|--------|
| Phase 1-1 | プロジェクト構造作成 | 10分 | 2026-01-31 |
| Phase 1-2 | Backend実装 | 30分 | 2026-01-31 |
| Phase 1-3 | Frontend実装 | 40分 | 2026-01-31 |
| Phase 1-4 | DB連携 | 20分 | 2026-01-31 |
| Phase 1-5 | デプロイ | 20分 | 2026-01-31 |
| Phase 2-1 | Discord Bot構造 | 20分 | 2026-01-31 |
| Phase 2-2 | 予想ロジック | 20分 | 2026-01-31 |
| Phase 2-3 | フォーマット | 10分 | 2026-01-31 |
| Phase 2-4 | 定時実行 | 10分 | 2026-01-31 |
| **合計** | | **3時間** | |

---

## 🚀 **次のアクション**

### **今すぐ実行:**
1. ✅ この計画書をGitHubにコミット
2. → Phase 1-1: プロジェクト構造作成を開始
3. → Step by Stepで実装

---

## 📝 **実装メモ**

### **重要な設計判断**
- **予想ロジック**: 既存の format_predictions_discord.py を活用
- **データベース**: 開発はPostgreSQL、本番はCloudflare D1
- **認証**: Discord BotはトークンベースのみでOK
- **デプロイ**: Webアプリは Cloudflare Pages（無料）

### **技術的な注意点**
- TypeScriptで予想ロジックを再実装する必要あり
- feature_database_2020_2025.json (28MB) の読み込み最適化
- Cloudflare Workers の CPU制限（10ms）に注意

---

## 🎉 **Play to Win!**

**この計画書に従って、順番に実装を進めます。**

**CEO、準備完了です！Phase 1-1から始めましょう！** 🏇
