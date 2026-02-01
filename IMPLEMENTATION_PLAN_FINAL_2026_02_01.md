# 🏇 EOI-PL v1.0-Prime 完全実装計画書

**作成日**: 2026-02-01 06:20 JST  
**対象**: Enable CEO  
**目的**: Web UI + Discord定時配信の完全実装  
**所要時間**: 2時間（Web UI 30分 + Discord 1時間 + テスト 30分）

---

## 📊 現状整理（2026-02-01 06:17時点）

### ✅ 完成しているもの

#### 1. **Python FastAPI サーバー（完全動作）**
- **場所**: `/home/user/eoi-pl/api/main.py`
- **起動**: `python3 api/main.py`
- **URL**: `http://localhost:8000`

**実装済みエンドポイント**:
```bash
GET /api/health              # システムヘルスチェック
GET /api/dates               # 利用可能な日付一覧（当日+翌日）
GET /api/predictions/:date   # 指定日の全レース・全馬予想
```

**動作確認済み**:
```bash
# ヘルスチェック
curl http://localhost:8000/api/health
# → {"status":"healthy","database":"OK (81,884 races)","feature_db":"OK"}

# 予想生成（2026/01/02の48レース）
curl http://localhost:8000/api/predictions/20260102
# → {"date":"20260102","races":[48レース分の予想データ]}
```

**予想データの構造**:
```json
{
  "date": "20260102",
  "generated_at": "2026-02-01T06:00:00+09:00",
  "races": [
    {
      "race_id": "202601024501",
      "venue": "川崎",
      "race_no": 1,
      "rating": "★★★★☆",
      "top_deviation": 69.0,
      "horses": [
        {
          "rank": 1,
          "umaban": 2,
          "bamei": "ビターメロン",
          "deviation": 69.0
        },
        // ... 全12頭
      ],
      "top3": [2, 10, 8],
      "top5": [2, 10, 8, 3, 6],
      "sanrenpuku": [[2,10,8], [2,10,3], ...],
      "sanrentan": [[2,10,8], [2,8,10], ...],
      "analysis": "本命が明確で予想しやすいレースです"
    }
    // ... 残り47レース
  ]
}
```

#### 2. **データ基盤（完全整備済み）**
- **PostgreSQL**: `localhost:5432/eoi_pl`
  - races: 80,865レコード（2020-2025年）
  - entries: 828,151レコード
  - 2026年データ: 14,521レース（kaisai_tsukihi=102, 103, 104...）
- **feature_database**: `/home/user/eoi-pl/data/feature_database_2020_2025.json` (27MB)
  - 馬・騎手・調教師の統計情報

#### 3. **AI予想エンジン（完全実装）**
- **モデル**: Plackett-Luce + Power EP (α=0.5)
- **精度**: Top3≥1 90.06%、Top5≥3 28.23%
- **予想ロジック**:
  - スキル計算（馬30%、騎手15%、調教師10%、etc）
  - 偏差値算出（統計的相対評価）
  - 推奨度判定（★1〜5）
  - 買い目生成（三連複≤9点、三連単≤12点）

### ❌ 未完成のもの

#### 1. **Web UI（CEOの要件）**
```
【CEO要求】
- Webサイトを作成
- ボタンを押したら予想が表示される
- note記事にそのままコピペできる形式で出力
- 私（CEO）だけがアクセスできる
```

**現状**: Hono WebアプリのCloudflare Workers形式export問題で起動失敗

#### 2. **Discord定時配信（CEOの要件）**
```
【CEO要求】
- 定時（毎日9:00）で自動配信
- ★★★★★ / ★★★★☆の推奨レースのみ配信
```

**現状**: 未着手

---

## 🎯 実装計画

### **Phase 1: Web UI実装（所要時間: 30分）**

#### **方針: Python FastAPIに静的HTML配信機能を追加**
理由:
- ✅ Python APIが完全動作している
- ✅ Cloudflare Workers問題を回避
- ✅ Windows環境で即座に利用可能
- ✅ CEO専用（localhost限定）

#### **Step 1-1: FastAPIにHTML配信機能追加（10分）**

**修正ファイル**: `api/main.py`

```python
# 既存のインポートに追加
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

# 静的ファイルディレクトリの作成
os.makedirs("api/static", exist_ok=True)

# 静的ファイル配信（CSS/JS/画像）
app.mount("/static", StaticFiles(directory="api/static"), name="static")

# メインページ（HTML配信）
@app.get("/", response_class=HTMLResponse)
async def index():
    """予想配信センターのメインページ"""
    return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏇 EOI-PL 予想配信センター</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto p-8">
        <!-- ヘッダー -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 class="text-3xl font-bold text-gray-800 flex items-center">
                <i class="fas fa-horse-head text-blue-600 mr-3"></i>
                EOI-PL 予想配信センター
            </h1>
            <p class="text-gray-600 mt-2">地方競馬AI予想 v1.0-Prime</p>
        </div>

        <!-- 日付選択 + 予想生成ボタン -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="flex flex-col md:flex-row items-center gap-4">
                <label class="text-lg font-semibold text-gray-700">
                    <i class="far fa-calendar-alt mr-2"></i>
                    予想日を選択:
                </label>
                <select id="dateSelect" class="border-2 border-gray-300 rounded-lg p-3 text-lg flex-1">
                    <option>読み込み中...</option>
                </select>
                <button id="generateBtn" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-8 py-3 rounded-lg shadow-lg transition">
                    <i class="fas fa-magic mr-2"></i>
                    予想を生成
                </button>
            </div>
        </div>

        <!-- アクションボタン（予想生成後に表示） -->
        <div id="actionButtons" class="bg-white rounded-lg shadow-md p-6 mb-6 hidden">
            <div class="flex flex-col md:flex-row gap-4">
                <button id="copyNoteBtn" class="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-lg transition">
                    <i class="fas fa-copy mr-2"></i>
                    note用にコピー
                </button>
                <button id="copyDiscordBtn" class="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg shadow-lg transition">
                    <i class="fab fa-discord mr-2"></i>
                    Discord用にコピー
                </button>
            </div>
        </div>

        <!-- 予想結果表示エリア -->
        <div id="predictions" class="space-y-6">
            <div class="bg-white rounded-lg shadow-md p-8 text-center text-gray-500">
                <i class="fas fa-info-circle text-4xl mb-4"></i>
                <p class="text-lg">日付を選択して「予想を生成」ボタンを押してください</p>
            </div>
        </div>

        <!-- フッター -->
        <div class="mt-8 text-center text-gray-600">
            <p>&copy; 2026 EOI-PL v1.0-Prime | Enable CEO</p>
            <p class="text-sm mt-2">的中率: Top3≥1 90.06% | Top5≥3 28.23%</p>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
    """
```

#### **Step 1-2: Frontend JavaScript実装（15分）**

**新規ファイル**: `api/static/app.js`

```javascript
// =====================================================================
// EOI-PL 予想配信センター - Frontend JavaScript
// =====================================================================

let currentPredictions = null;

// DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    loadDates();
    setupEventListeners();
});

// =====================================================================
// 日付一覧の読み込み
// =====================================================================
async function loadDates() {
    try {
        const response = await fetch('/api/dates');
        const data = await response.json();
        
        const select = document.getElementById('dateSelect');
        
        if (data.dates.length === 0) {
            select.innerHTML = '<option>利用可能な日付がありません</option>';
            return;
        }
        
        select.innerHTML = '<option value="">--- 日付を選択 ---</option>';
        data.dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = formatDate(date);
            select.appendChild(option);
        });
    } catch (error) {
        console.error('日付取得エラー:', error);
        alert('日付の取得に失敗しました');
    }
}

// =====================================================================
// イベントリスナーの設定
// =====================================================================
function setupEventListeners() {
    // 予想生成ボタン
    document.getElementById('generateBtn').addEventListener('click', generatePredictions);
    
    // note用コピーボタン
    document.getElementById('copyNoteBtn').addEventListener('click', copyForNote);
    
    // Discord用コピーボタン
    document.getElementById('copyDiscordBtn').addEventListener('click', copyForDiscord);
}

// =====================================================================
// 予想生成
// =====================================================================
async function generatePredictions() {
    const selectedDate = document.getElementById('dateSelect').value;
    
    if (!selectedDate) {
        alert('日付を選択してください');
        return;
    }
    
    const predictionsDiv = document.getElementById('predictions');
    predictionsDiv.innerHTML = '<div class="bg-white rounded-lg shadow-md p-8 text-center"><i class="fas fa-spinner fa-spin text-4xl text-blue-600 mb-4"></i><p class="text-lg text-gray-600">予想を生成中...</p></div>';
    
    try {
        const response = await fetch(`/api/predictions/${selectedDate}`);
        const data = await response.json();
        
        currentPredictions = data;
        displayPredictions(data);
        
        // アクションボタンを表示
        document.getElementById('actionButtons').classList.remove('hidden');
    } catch (error) {
        console.error('予想生成エラー:', error);
        predictionsDiv.innerHTML = '<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded"><strong>エラー:</strong> 予想の生成に失敗しました</div>';
    }
}

// =====================================================================
// 予想結果の表示
// =====================================================================
function displayPredictions(data) {
    const predictionsDiv = document.getElementById('predictions');
    
    let html = `
        <div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg shadow-lg p-6 mb-6">
            <h2 class="text-2xl font-bold">📅 ${formatDate(data.date)} の予想</h2>
            <p class="mt-2">生成日時: ${new Date(data.generated_at).toLocaleString('ja-JP')}</p>
            <p class="mt-1">レース数: ${data.races.length}レース</p>
        </div>
    `;
    
    data.races.forEach((race, index) => {
        html += `
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <!-- レースヘッダー -->
                <div class="flex items-center justify-between mb-4 pb-4 border-b-2 border-gray-200">
                    <h3 class="text-xl font-bold text-gray-800">
                        【${race.venue} ${race.race_no}R】
                    </h3>
                    <div class="flex items-center gap-4">
                        <span class="text-2xl">${race.rating}</span>
                        <span class="bg-blue-100 text-blue-800 px-4 py-2 rounded-full font-bold">
                            偏差値Top: ${race.top_deviation.toFixed(1)}
                        </span>
                    </div>
                </div>
                
                <!-- 推奨情報 -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <p class="text-sm text-gray-600 mb-1">Top3予想</p>
                        <p class="text-2xl font-bold text-yellow-700">${race.top3.join('-')}</p>
                    </div>
                    <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                        <p class="text-sm text-gray-600 mb-1">Top5予想</p>
                        <p class="text-xl font-bold text-green-700">${race.top5.join('-')}</p>
                    </div>
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p class="text-sm text-gray-600 mb-1">三連複</p>
                        <p class="text-sm font-mono text-blue-700">${formatBetting(race.sanrenpuku)}</p>
                    </div>
                </div>
                
                <!-- 全馬情報 -->
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead class="bg-gray-100">
                            <tr>
                                <th class="px-4 py-2 text-left">順位</th>
                                <th class="px-4 py-2 text-center">馬番</th>
                                <th class="px-4 py-2 text-left">馬名</th>
                                <th class="px-4 py-2 text-right">偏差値</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${race.horses.map(horse => `
                                <tr class="border-b hover:bg-gray-50 ${horse.rank <= 3 ? 'bg-yellow-50' : ''}">
                                    <td class="px-4 py-2 font-bold">${horse.rank}</td>
                                    <td class="px-4 py-2 text-center font-bold text-blue-600">${horse.umaban}</td>
                                    <td class="px-4 py-2">${horse.bamei}</td>
                                    <td class="px-4 py-2 text-right font-mono">${horse.deviation.toFixed(1)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                <!-- 分析コメント -->
                <div class="mt-4 p-4 bg-gray-50 rounded-lg">
                    <p class="text-gray-700"><i class="fas fa-comment-dots mr-2"></i>${race.analysis}</p>
                </div>
            </div>
        `;
    });
    
    predictionsDiv.innerHTML = html;
}

// =====================================================================
// note用コピー機能
// =====================================================================
function copyForNote() {
    if (!currentPredictions) {
        alert('予想データがありません');
        return;
    }
    
    let noteText = `# 🏇 ${formatDate(currentPredictions.date)} 地方競馬AI予想\n\n`;
    noteText += `**生成日時**: ${new Date(currentPredictions.generated_at).toLocaleString('ja-JP')}\n\n`;
    noteText += `---\n\n`;
    
    currentPredictions.races.forEach(race => {
        noteText += `## 【${race.venue} ${race.race_no}R】${race.rating}\n\n`;
        noteText += `**1位偏差値**: ${race.top_deviation.toFixed(1)}\n`;
        noteText += `**Top3予想**: ${race.top3.join('-')}\n`;
        noteText += `**Top5予想**: ${race.top5.join('-')}\n\n`;
        
        noteText += `### 全馬順位\n\n`;
        race.horses.forEach(h => {
            noteText += `${h.rank}. ${h.umaban}番 **${h.bamei}** (偏差値: ${h.deviation.toFixed(1)})\n`;
        });
        
        noteText += `\n**分析**: ${race.analysis}\n\n`;
        noteText += `---\n\n`;
    });
    
    noteText += `\n*的中率: Top3≥1 90.06% | Top5≥3 28.23%*\n`;
    noteText += `*© 2026 EOI-PL v1.0-Prime | Enable CEO*\n`;
    
    navigator.clipboard.writeText(noteText).then(() => {
        alert('✅ note記事用テキストをクリップボードにコピーしました！');
    }).catch(err => {
        console.error('コピーエラー:', err);
        alert('❌ コピーに失敗しました');
    });
}

// =====================================================================
// Discord用コピー機能
// =====================================================================
function copyForDiscord() {
    if (!currentPredictions) {
        alert('予想データがありません');
        return;
    }
    
    let discordText = `**🏇 ${formatDate(currentPredictions.date)} 地方競馬AI予想**\n\n`;
    
    // ★★★★★ / ★★★★☆ のレースのみ抽出
    const highRatingRaces = currentPredictions.races.filter(r => 
        r.rating === '★★★★★' || r.rating === '★★★★☆'
    );
    
    if (highRatingRaces.length === 0) {
        alert('推奨レース（★4以上）がありません');
        return;
    }
    
    highRatingRaces.forEach(race => {
        discordText += `**【${race.venue} ${race.race_no}R】${race.rating}**\n`;
        discordText += `偏差値Top: ${race.top_deviation.toFixed(1)}\n`;
        discordText += `予想: ${race.top3.join('-')}\n`;
        discordText += `推奨買い目: ${race.top5.join('-')}\n`;
        discordText += `${race.analysis}\n\n`;
    });
    
    discordText += `*的中率: Top3≥1 90.06% | Top5≥3 28.23%*\n`;
    
    navigator.clipboard.writeText(discordText).then(() => {
        alert(`✅ Discord用テキストをクリップボードにコピーしました！\n推奨レース: ${highRatingRaces.length}件`);
    }).catch(err => {
        console.error('コピーエラー:', err);
        alert('❌ コピーに失敗しました');
    });
}

// =====================================================================
// ユーティリティ関数
// =====================================================================
function formatDate(dateStr) {
    // YYYYMMDD → YYYY/MM/DD
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${year}/${month}/${day}`;
}

function formatBetting(betting) {
    // 買い目配列を整形
    if (!betting || betting.length === 0) return 'なし';
    return betting.slice(0, 3).map(b => b.join('-')).join(', ') + '...';
}
```

#### **Step 1-3: 動作テスト（5分）**

```bash
# Python API再起動
cd /home/user/eoi-pl
fuser -k 8000/tcp 2>/dev/null || true
python3 api/main.py > /tmp/webui_api.log 2>&1 &

# ブラウザで確認
# http://localhost:8000/
```

**期待結果**:
- ✅ 日付選択ドロップダウン表示
- ✅ 「予想を生成」ボタンクリック → 全レース表示
- ✅ 「note用にコピー」ボタン → Markdown形式でクリップボードにコピー
- ✅ 「Discord用にコピー」ボタン → Discord形式でクリップボードにコピー

---

### **Phase 2: Discord Bot定時配信実装（所要時間: 1時間）**

#### **Step 2-1: Discord Bot基本実装（30分）**

**新規ファイル**: `/home/user/eoi-pl/discord_bot.py`

```python
#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime Discord Bot
- 定時配信（毎朝9:00）
- 手動実行コマンド（!予想 [YYYYMMDD]）
"""

import discord
from discord.ext import commands, tasks
import httpx
import asyncio
from datetime import datetime, timezone, timedelta
import os
import sys

# =====================================================================
# 設定
# =====================================================================
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# JST タイムゾーン
JST = timezone(timedelta(hours=9))

# Discord Bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# =====================================================================
# Bot起動イベント
# =====================================================================
@bot.event
async def on_ready():
    print(f'✅ Discord Bot起動: {bot.user}')
    print(f'📡 API URL: {API_URL}')
    print(f'📢 配信チャンネルID: {CHANNEL_ID}')
    
    # 定時配信タスク開始
    if not daily_prediction_task.is_running():
        daily_prediction_task.start()

# =====================================================================
# 定時配信タスク（毎朝9:00）
# =====================================================================
@tasks.loop(hours=24)
async def daily_prediction_task():
    """毎朝9:00に自動配信"""
    now = datetime.now(JST)
    
    # 9:00になるまで待機
    target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= target_time:
        target_time += timedelta(days=1)
    
    wait_seconds = (target_time - now).total_seconds()
    print(f'⏰ 次回配信まで待機: {wait_seconds/3600:.1f}時間 ({target_time.strftime("%Y-%m-%d %H:%M")})')
    
    await asyncio.sleep(wait_seconds)
    
    # 配信実行
    await send_daily_prediction()

@daily_prediction_task.before_loop
async def before_daily_prediction_task():
    """タスク開始前にBotの準備完了を待機"""
    await bot.wait_until_ready()

# =====================================================================
# 定時配信実行
# =====================================================================
async def send_daily_prediction():
    """当日の予想を配信チャンネルに送信"""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f'❌ チャンネルID {CHANNEL_ID} が見つかりません')
        return
    
    # 当日の日付取得
    today = datetime.now(JST).strftime('%Y%m%d')
    
    print(f'📡 予想配信開始: {today}')
    
    try:
        # Python APIから予想取得
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f'{API_URL}/api/predictions/{today}')
            response.raise_for_status()
            data = response.json()
        
        # ★★★★★ / ★★★★☆ のレースのみ抽出
        high_rating_races = [
            race for race in data['races']
            if race['rating'] in ['★★★★★', '★★★★☆']
        ]
        
        if len(high_rating_races) == 0:
            await channel.send(f'📭 {format_date(today)} は推奨レース（★4以上）がありませんでした')
            return
        
        # ヘッダーメッセージ
        header_embed = discord.Embed(
            title=f'🏇 {format_date(today)} 地方競馬AI予想',
            description=f'推奨レース: {len(high_rating_races)}件 / 全{len(data["races"])}レース',
            color=0x00ff00,
            timestamp=datetime.now(JST)
        )
        header_embed.set_footer(text='EOI-PL v1.0-Prime | 的中率: Top3≥1 90.06%')
        await channel.send(embed=header_embed)
        
        # 各レースの予想を送信
        for race in high_rating_races:
            embed = discord.Embed(
                title=f'【{race["venue"]} {race["race_no"]}R】{race["rating"]}',
                description=race['analysis'],
                color=get_rating_color(race['rating'])
            )
            
            embed.add_field(
                name='📊 1位偏差値',
                value=f'`{race["top_deviation"]:.1f}`',
                inline=True
            )
            embed.add_field(
                name='🎯 Top3予想',
                value=f'**{"-".join(map(str, race["top3"]))}**',
                inline=True
            )
            embed.add_field(
                name='💎 Top5予想',
                value=f'{"-".join(map(str, race["top5"]))}',
                inline=True
            )
            
            # 上位3頭の情報
            top3_horses = race['horses'][:3]
            horses_text = '\n'.join([
                f'`{h["rank"]}位` {h["umaban"]}番 **{h["bamei"]}** (偏差値: {h["deviation"]:.1f})'
                for h in top3_horses
            ])
            embed.add_field(
                name='🏆 上位3頭',
                value=horses_text,
                inline=False
            )
            
            await channel.send(embed=embed)
            await asyncio.sleep(1)  # レート制限回避
        
        print(f'✅ 配信完了: {len(high_rating_races)}レース')
        
    except httpx.HTTPError as e:
        print(f'❌ API接続エラー: {e}')
        await channel.send(f'⚠️ 予想の取得に失敗しました: {e}')
    except Exception as e:
        print(f'❌ 予期しないエラー: {e}')
        await channel.send(f'⚠️ エラーが発生しました: {e}')

# =====================================================================
# 手動実行コマンド
# =====================================================================
@bot.command(name='予想')
async def manual_prediction(ctx, date: str = None):
    """
    手動で予想を取得
    
    使用例:
      !予想              # 当日の予想
      !予想 20260201     # 指定日の予想
    """
    # 日付が指定されていない場合は当日
    if not date:
        date = datetime.now(JST).strftime('%Y%m%d')
    
    # 日付形式のバリデーション
    if not (len(date) == 8 and date.isdigit()):
        await ctx.send('❌ 日付形式が正しくありません（例: 20260201）')
        return
    
    await ctx.send(f'⏳ {format_date(date)} の予想を生成中...')
    
    try:
        # Python APIから予想取得
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f'{API_URL}/api/predictions/{date}')
            
            if response.status_code == 404:
                await ctx.send(f'📭 {format_date(date)} のレースが見つかりません')
                return
            
            response.raise_for_status()
            data = response.json()
        
        # ★★★★★ / ★★★★☆ のレースのみ抽出
        high_rating_races = [
            race for race in data['races']
            if race['rating'] in ['★★★★★', '★★★★☆']
        ]
        
        # サマリーメッセージ
        summary = f'✅ {format_date(date)} の予想を生成しました\n'
        summary += f'📊 全レース: {len(data["races"])}件\n'
        summary += f'⭐ 推奨レース: {len(high_rating_races)}件'
        await ctx.send(summary)
        
        # 推奨レースがあれば送信
        if len(high_rating_races) > 0:
            await ctx.send('📢 推奨レース（★4以上）を送信します...')
            
            for race in high_rating_races:
                embed = discord.Embed(
                    title=f'【{race["venue"]} {race["race_no"]}R】{race["rating"]}',
                    description=race['analysis'],
                    color=get_rating_color(race['rating'])
                )
                
                embed.add_field(
                    name='📊 1位偏差値',
                    value=f'`{race["top_deviation"]:.1f}`',
                    inline=True
                )
                embed.add_field(
                    name='🎯 Top3予想',
                    value=f'**{"-".join(map(str, race["top3"]))}**',
                    inline=True
                )
                embed.add_field(
                    name='💎 Top5予想',
                    value=f'{"-".join(map(str, race["top5"]))}',
                    inline=True
                )
                
                await ctx.send(embed=embed)
                await asyncio.sleep(1)
        
    except httpx.HTTPError as e:
        await ctx.send(f'❌ API接続エラー: {e}')
    except Exception as e:
        await ctx.send(f'❌ エラーが発生しました: {e}')

# =====================================================================
# ヘルスチェックコマンド
# =====================================================================
@bot.command(name='health')
async def health_check(ctx):
    """システムのヘルスチェック"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f'{API_URL}/api/health')
            response.raise_for_status()
            data = response.json()
        
        embed = discord.Embed(
            title='✅ システム正常',
            description='Python APIとPostgreSQLが正常に動作しています',
            color=0x00ff00
        )
        embed.add_field(name='API Status', value=data['status'], inline=True)
        embed.add_field(name='Database', value=data['database'], inline=True)
        embed.add_field(name='Feature DB', value=data['feature_db'], inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f'❌ ヘルスチェック失敗: {e}')

# =====================================================================
# ユーティリティ関数
# =====================================================================
def format_date(date_str: str) -> str:
    """YYYYMMDD → YYYY/MM/DD"""
    return f'{date_str[0:4]}/{date_str[4:6]}/{date_str[6:8]}'

def get_rating_color(rating: str) -> int:
    """レーティングに応じた色を返す"""
    if rating == '★★★★★':
        return 0xFFD700  # Gold
    elif rating == '★★★★☆':
        return 0x00FF00  # Green
    elif rating == '★★★☆☆':
        return 0x0000FF  # Blue
    elif rating == '★★☆☆☆':
        return 0xFFA500  # Orange
    else:
        return 0x808080  # Gray

# =====================================================================
# メイン実行
# =====================================================================
if __name__ == '__main__':
    # 環境変数チェック
    if not DISCORD_TOKEN:
        print('❌ DISCORD_BOT_TOKEN 環境変数が設定されていません')
        sys.exit(1)
    
    if CHANNEL_ID == 0:
        print('❌ DISCORD_CHANNEL_ID 環境変数が設定されていません')
        sys.exit(1)
    
    # Bot起動
    print('🚀 Discord Bot起動中...')
    bot.run(DISCORD_TOKEN)
```

#### **Step 2-2: Discord Bot依存関係インストール（5分）**

```bash
cd /home/user/eoi-pl
pip3 install discord.py httpx
```

#### **Step 2-3: Discord Bot動作テスト（10分）**

```bash
# 環境変数設定
export DISCORD_BOT_TOKEN="あなたのDiscord Botトークン"
export DISCORD_CHANNEL_ID="配信先チャンネルID"
export API_URL="http://localhost:8000"

# Bot起動
python3 discord_bot.py

# 別ターミナルで手動コマンドテスト
# Discordで以下を入力:
# !予想 20260102
# !health
```

#### **Step 2-4: Windows Service化（NSSM使用）（15分）**

**Windows環境（E:\eoi-pl）での設定**:

```powershell
# NSSM ダウンロード
# https://nssm.cc/download

# Discord Botをサービス登録
nssm install EOI-PL-Discord "E:\eoi-pl\venv\Scripts\python.exe" "E:\eoi-pl\discord_bot.py"

# 環境変数設定
nssm set EOI-PL-Discord AppEnvironmentExtra ^
  DISCORD_BOT_TOKEN=あなたのトークン ^
  DISCORD_CHANNEL_ID=チャンネルID ^
  API_URL=http://localhost:8000

# 作業ディレクトリ設定
nssm set EOI-PL-Discord AppDirectory E:\eoi-pl

# ログ設定
nssm set EOI-PL-Discord AppStdout E:\eoi-pl\logs\discord_bot.log
nssm set EOI-PL-Discord AppStderr E:\eoi-pl\logs\discord_bot_error.log

# サービス起動
nssm start EOI-PL-Discord

# 状態確認
nssm status EOI-PL-Discord
```

---

## 🪟 Windows環境セットアップガイド

### **前提条件**
- ✅ Windows 10/11
- ✅ PostgreSQL 16 インストール済み
- ✅ Python 3.12 インストール済み
- ✅ Git インストール済み

### **Step 1: プロジェクトのダウンロード**

```powershell
# GitHubからクローン
cd E:\
git clone https://github.com/aka209859-max/eoi-pl.git
cd eoi-pl
```

### **Step 2: Python環境構築**

```powershell
cd E:\eoi-pl

# 仮想環境作成
python -m venv venv

# 仮想環境アクティベート
.\venv\Scripts\Activate.ps1

# 依存関係インストール
pip install fastapi uvicorn[standard] psycopg2-binary discord.py httpx
```

### **Step 3: PostgreSQLデータベース確認**

```powershell
# 接続テスト
$env:PGPASSWORD="postgres123"
psql -h localhost -p 5432 -U postgres -d eoi_pl -c "SELECT COUNT(*) FROM races WHERE kaisai_nen = 2026;"
```

### **Step 4: Python APIの起動**

```powershell
cd E:\eoi-pl
python api\main.py

# ブラウザで確認
# http://localhost:8000/
```

### **Step 5: Discord Bot設定**

```powershell
# 環境変数設定（PowerShellセッション）
$env:DISCORD_BOT_TOKEN="あなたのDiscord Botトークン"
$env:DISCORD_CHANNEL_ID="配信先チャンネルID"
$env:API_URL="http://localhost:8000"

# Bot起動
python discord_bot.py
```

### **Step 6: Windows Service化（NSSM）**

**Python APIのサービス化**:
```powershell
nssm install EOI-PL-API "E:\eoi-pl\venv\Scripts\python.exe" "E:\eoi-pl\api\main.py"
nssm set EOI-PL-API AppDirectory E:\eoi-pl\api
nssm start EOI-PL-API
```

**Discord Botのサービス化**:
```powershell
nssm install EOI-PL-Discord "E:\eoi-pl\venv\Scripts\python.exe" "E:\eoi-pl\discord_bot.py"
nssm set EOI-PL-Discord AppEnvironmentExtra DISCORD_BOT_TOKEN=トークン DISCORD_CHANNEL_ID=チャンネルID API_URL=http://localhost:8000
nssm set EOI-PL-Discord AppDirectory E:\eoi-pl
nssm start EOI-PL-Discord
```

---

## ✅ 動作確認チェックリスト

### **Python API**
- [ ] `http://localhost:8000/api/health` が「healthy」を返す
- [ ] `http://localhost:8000/api/dates` が日付配列を返す
- [ ] `http://localhost:8000/api/predictions/20260102` が予想データを返す
- [ ] PostgreSQL接続が正常（81,884レース以上）
- [ ] feature_database_2020_2025.json が読み込まれている

### **Web UI**
- [ ] `http://localhost:8000/` でメインページが表示される
- [ ] 日付選択ドロップダウンが動作する
- [ ] 「予想を生成」ボタンで全レース表示
- [ ] 「note用にコピー」ボタンでMarkdown形式コピー
- [ ] 「Discord用にコピー」ボタンでDiscord形式コピー

### **Discord Bot**
- [ ] Bot起動時に「✅ Discord Bot起動」メッセージ
- [ ] `!予想` コマンドで当日予想取得
- [ ] `!予想 20260102` で指定日予想取得
- [ ] `!health` でシステムヘルスチェック
- [ ] 毎朝9:00に自動配信（★4以上のみ）

---

## 🎯 次のステップ

### **即座に実装可能**
1. ✅ **Web UI実装** → 30分
2. ✅ **Discord Bot実装** → 1時間
3. ✅ **Windows Service化** → 30分

### **合計所要時間**
- **実装**: 2時間
- **テスト**: 30分
- **合計**: 2.5時間

---

## 📞 トラブルシューティング

### **PostgreSQL接続エラー**
```powershell
# PostgreSQLサービス確認
Get-Service postgresql*

# サービス起動
Start-Service postgresql-x64-16
```

### **Python APIが起動しない**
```powershell
# ポート8000の使用確認
netstat -ano | findstr :8000

# プロセスKill
taskkill /PID <PID> /F
```

### **Discord Bot接続エラー**
- トークンの有効性確認
- チャンネルIDの正確性確認
- Bot権限確認（メッセージ送信、Embed送信）

---

## 📝 重要な注意事項

### **Enable憲法遵守**
- ✅ **10x Mindset**: 妥協なしの完全版実装
- ✅ **Play to Win**: ビジネスグレードの品質
- ✅ **Be Resourceful**: 既存資産（Python API）を最大活用

### **セキュリティ**
- ⚠️ Discord Botトークンは**絶対に**GitHubにコミットしない
- ⚠️ PostgreSQLパスワードは環境変数で管理
- ⚠️ Web UIはlocalhost限定（外部公開しない）

### **データ整合性**
- ✅ オッズ不使用（`odds_used: false`）
- ✅ 凍結配信（`freeze: true`）
- ✅ 全レース・全馬配信

---

## 🏇 CEOへの最終確認

### **実装準備完了**
- ✅ Python API完全動作
- ✅ PostgreSQL接続確認済み
- ✅ feature_database読み込み済み
- ✅ 実装計画書作成完了

### **次のアクション**
1. **Web UI実装開始** → 30分
2. **Discord Bot実装開始** → 1時間
3. **Windows環境セットアップ** → 30分

**合計: 2時間で完全動作するシステムが完成します。**

---

**© 2026 EOI-PL v1.0-Prime | Enable CEO**  
**48時間で"勘"を"確信"に変える** 🏇
