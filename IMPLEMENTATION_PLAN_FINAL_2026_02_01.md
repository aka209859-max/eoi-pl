# 🏇 EOI-PL v1.0-Prime 完全版実装計画書

**作成日**: 2026-02-01  
**対象**: Web UI + Discord Bot 完全実装  
**環境**: Windows (E:\eoi-pl)  
**Discord**: ronrq0581_10975

---

## 🎯 実装目標

### **Phase 1: Web UI（30分）**
- ✅ ボタン1つで予想生成
- ✅ note記事用にコピペ可能
- ✅ 全レース・全馬表示

### **Phase 2: Discord Bot定時配信（1時間）**
- ✅ 毎朝9:00自動配信
- ✅ 手動実行コマンド（!予想）
- ✅ 推奨度フィルタリング（★4以上）

---

## 📊 現在の完成状況

### ✅ **完成済み**
1. **Python FastAPI サーバー** (`E:\eoi-pl\api\main.py`)
   - ✅ GET /api/health - ヘルスチェック
   - ✅ GET /api/dates - 利用可能な日付一覧
   - ✅ GET /api/predictions/:date - 全レース・全馬予想
   - ✅ PostgreSQL接続（81,884レース）
   - ✅ feature_database_2020_2025.json（28MB）
   - ✅ EOIPLPredictor（完全版予想ロジック）

2. **データベース**
   - ✅ PostgreSQL (localhost:5432)
   - ✅ Database: eoi_pl
   - ✅ User: postgres / Password: postgres123
   - ✅ 2026年データあり（kaisai_tsukihi: 102, 103, 104, 105...）

3. **予想ロジック**
   - ✅ スキル計算（馬30%、騎手15%、調教師10%、他）
   - ✅ 偏差値算出（標準偏差ベース）
   - ✅ 推奨度判定（★5段階評価）
   - ✅ Top3/Top5買い目生成

### ❌ **未実装**
1. Web UI（HTML + JavaScript）
2. note用コピー機能
3. Discord Bot
4. 定時配信機能
5. Windows Service化

---

## 🔧 Phase 1: Web UI実装（30分）

### **Step 1-1: Python APIに静的ファイル配信機能を追加**

**ファイル**: `E:\eoi-pl\api\main.py`

**追加するコード（ファイル冒頭のimport文の後）**:

```python
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

# 静的ファイル配信
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
```

**追加するコード（最後の if __name__ == "__main__": の前）**:

```python
@app.get("/", response_class=HTMLResponse)
async def index():
    """メインページ"""
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
    <!-- ヘッダー -->
    <header class="bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
        <div class="container mx-auto px-4 py-6">
            <h1 class="text-3xl font-bold">
                <i class="fas fa-horse-head mr-2"></i>
                EOI-PL 予想配信センター
            </h1>
            <p class="text-blue-100 mt-2">地方競馬AI予想システム v1.0-Prime</p>
        </div>
    </header>

    <!-- メインコンテンツ -->
    <main class="container mx-auto px-4 py-8">
        <!-- 日付選択 -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="flex flex-col md:flex-row items-center gap-4">
                <label class="text-lg font-semibold text-gray-700">
                    <i class="fas fa-calendar-alt mr-2"></i>
                    予想日を選択:
                </label>
                <select id="dateSelect" class="flex-1 px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none">
                    <option value="">読み込み中...</option>
                </select>
                <button id="generateBtn" class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md transition">
                    <i class="fas fa-play mr-2"></i>
                    予想を生成
                </button>
            </div>
        </div>

        <!-- 予想結果エリア -->
        <div id="predictions" class="space-y-6">
            <div class="text-center text-gray-500 py-12">
                <i class="fas fa-info-circle text-4xl mb-4"></i>
                <p class="text-lg">日付を選択して「予想を生成」ボタンを押してください</p>
            </div>
        </div>

        <!-- アクションボタン -->
        <div id="actionButtons" class="hidden mt-6 flex gap-4">
            <button id="copyNoteBtn" class="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-md transition">
                <i class="fas fa-copy mr-2"></i>
                note用にコピー
            </button>
            <button id="copyDiscordBtn" class="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg shadow-md transition">
                <i class="fab fa-discord mr-2"></i>
                Discord用にコピー
            </button>
        </div>
    </main>

    <!-- フッター -->
    <footer class="bg-gray-800 text-white py-6 mt-12">
        <div class="container mx-auto px-4 text-center">
            <p>&copy; 2026 EOI-PL v1.0-Prime | Enable CEO</p>
            <p class="text-gray-400 text-sm mt-2">的中率: Top3≥1 90.06% | Top5≥3 28.23%</p>
        </div>
    </footer>

    <script src="/static/app.js"></script>
</body>
</html>
    """
```

### **Step 1-2: Frontend JavaScript実装**

**ファイル**: `E:\eoi-pl\api\static\app.js`

```javascript
// =====================================================================
// EOI-PL 予想配信センター - Frontend JavaScript
// =====================================================================

let currentPredictions = null;

// ページ読み込み時に日付一覧を取得
document.addEventListener('DOMContentLoaded', async () => {
    await loadDates();
    setupEventListeners();
});

// イベントリスナーの設定
function setupEventListeners() {
    const generateBtn = document.getElementById('generateBtn');
    const copyNoteBtn = document.getElementById('copyNoteBtn');
    const copyDiscordBtn = document.getElementById('copyDiscordBtn');

    generateBtn.addEventListener('click', generatePredictions);
    copyNoteBtn.addEventListener('click', () => copyToClipboard('note'));
    copyDiscordBtn.addEventListener('click', () => copyToClipboard('discord'));
}

// 日付一覧を読み込み
async function loadDates() {
    try {
        const response = await fetch('/api/dates');
        const data = await response.json();
        
        const select = document.getElementById('dateSelect');
        
        if (data.dates.length === 0) {
            select.innerHTML = '<option value="">利用可能な日付がありません</option>';
            return;
        }
        
        select.innerHTML = '<option value="">日付を選択してください</option>';
        
        data.dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = formatDate(date);
            select.appendChild(option);
        });
    } catch (error) {
        console.error('日付読み込みエラー:', error);
        alert('日付の読み込みに失敗しました');
    }
}

// 予想を生成
async function generatePredictions() {
    const dateSelect = document.getElementById('dateSelect');
    const selectedDate = dateSelect.value;
    
    if (!selectedDate) {
        alert('日付を選択してください');
        return;
    }
    
    const predictionsDiv = document.getElementById('predictions');
    predictionsDiv.innerHTML = `
        <div class="text-center py-12">
            <i class="fas fa-spinner fa-spin text-4xl text-blue-600 mb-4"></i>
            <p class="text-lg text-gray-700">予想を生成中...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`/api/predictions/${selectedDate}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        currentPredictions = await response.json();
        displayPredictions(currentPredictions);
        
        // アクションボタンを表示
        document.getElementById('actionButtons').classList.remove('hidden');
    } catch (error) {
        console.error('予想生成エラー:', error);
        predictionsDiv.innerHTML = `
            <div class="text-center py-12 text-red-600">
                <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                <p class="text-lg">予想の生成に失敗しました</p>
                <p class="text-sm mt-2">${error.message}</p>
            </div>
        `;
    }
}

// 予想を表示
function displayPredictions(data) {
    const predictionsDiv = document.getElementById('predictions');
    
    let html = `
        <div class="bg-blue-50 rounded-lg p-4 mb-6">
            <h2 class="text-2xl font-bold text-blue-900">
                <i class="fas fa-calendar-check mr-2"></i>
                ${formatDate(data.date)} の予想（${data.races.length}レース）
            </h2>
        </div>
    `;
    
    data.races.forEach(race => {
        html += `
            <div class="bg-white rounded-lg shadow-md p-6 mb-4">
                <!-- レースヘッダー -->
                <div class="flex items-center justify-between mb-4 pb-4 border-b-2 border-gray-200">
                    <h3 class="text-xl font-bold text-gray-800">
                        【${race.venue} ${race.race_no}R】
                    </h3>
                    <div class="flex items-center gap-4">
                        <span class="text-2xl">${race.rating}</span>
                        <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-bold">
                            1位偏差値: ${race.top_deviation.toFixed(1)}
                        </span>
                    </div>
                </div>
                
                <!-- 推奨買い目 -->
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="bg-yellow-50 p-4 rounded-lg">
                        <div class="text-sm text-gray-600 mb-1">Top3予想</div>
                        <div class="text-2xl font-bold text-yellow-700">
                            ${race.top3.join(' - ')}
                        </div>
                    </div>
                    <div class="bg-green-50 p-4 rounded-lg">
                        <div class="text-sm text-gray-600 mb-1">Top5予想</div>
                        <div class="text-2xl font-bold text-green-700">
                            ${race.top5.join(' - ')}
                        </div>
                    </div>
                </div>
                
                <!-- レース分析 -->
                <div class="bg-gray-50 p-4 rounded-lg mb-4">
                    <div class="text-sm text-gray-600 mb-1">
                        <i class="fas fa-lightbulb mr-2"></i>レース分析
                    </div>
                    <div class="text-gray-800">${race.analysis}</div>
                </div>
                
                <!-- 全馬リスト -->
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead class="bg-gray-100">
                            <tr>
                                <th class="px-4 py-2 text-left">順位</th>
                                <th class="px-4 py-2 text-left">馬番</th>
                                <th class="px-4 py-2 text-left">馬名</th>
                                <th class="px-4 py-2 text-right">偏差値</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${race.horses.map(horse => `
                                <tr class="border-b hover:bg-gray-50 ${horse.rank <= 3 ? 'bg-yellow-50' : ''}">
                                    <td class="px-4 py-2 font-bold">${horse.rank}</td>
                                    <td class="px-4 py-2">${horse.umaban}番</td>
                                    <td class="px-4 py-2">${horse.bamei}</td>
                                    <td class="px-4 py-2 text-right font-mono">${horse.deviation.toFixed(1)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });
    
    predictionsDiv.innerHTML = html;
}

// クリップボードにコピー
function copyToClipboard(format) {
    if (!currentPredictions) {
        alert('予想データがありません');
        return;
    }
    
    let text = '';
    
    if (format === 'note') {
        text = generateNoteFormat(currentPredictions);
    } else if (format === 'discord') {
        text = generateDiscordFormat(currentPredictions);
    }
    
    navigator.clipboard.writeText(text).then(() => {
        alert(`${format === 'note' ? 'note' : 'Discord'}用テキストをコピーしました！`);
    }).catch(err => {
        console.error('コピーエラー:', err);
        alert('コピーに失敗しました');
    });
}

// note用フォーマット生成
function generateNoteFormat(data) {
    let text = `# ${formatDate(data.date)} 地方競馬AI予想\n\n`;
    text += `**EOI-PL v1.0-Prime by Enable CEO**\n\n`;
    text += `全${data.races.length}レースの予想を掲載します。\n\n`;
    text += `---\n\n`;
    
    data.races.forEach(race => {
        text += `## 【${race.venue} ${race.race_no}R】${race.rating}\n\n`;
        text += `**1位偏差値**: ${race.top_deviation.toFixed(1)}\n\n`;
        text += `### 推奨買い目\n`;
        text += `- **Top3予想**: ${race.top3.join('-')}\n`;
        text += `- **Top5予想**: ${race.top5.join('-')}\n\n`;
        text += `### レース分析\n`;
        text += `${race.analysis}\n\n`;
        text += `### 全馬リスト\n\n`;
        
        race.horses.forEach(horse => {
            text += `${horse.rank}. ${horse.umaban}番 **${horse.bamei}** (偏差値: ${horse.deviation.toFixed(1)})\n`;
        });
        
        text += `\n---\n\n`;
    });
    
    text += `**的中率**: Top3≥1 90.06% | Top5≥3 28.23%\n`;
    text += `**システム**: EOI-PL v1.0-Prime (Plackett-Luce + Power EP)\n`;
    
    return text;
}

// Discord用フォーマット生成
function generateDiscordFormat(data) {
    let text = `**🏇 ${formatDate(data.date)} 地方競馬AI予想**\n`;
    text += `EOI-PL v1.0-Prime | Enable CEO\n\n`;
    
    // 推奨度★4以上のみ
    const recommendedRaces = data.races.filter(r => 
        r.rating === '★★★★★' || r.rating === '★★★★☆'
    );
    
    if (recommendedRaces.length === 0) {
        text += `本日は推奨レースがありません。\n`;
        return text;
    }
    
    text += `**推奨レース**: ${recommendedRaces.length}/${data.races.length}レース\n\n`;
    
    recommendedRaces.forEach(race => {
        text += `**【${race.venue} ${race.race_no}R】${race.rating}**\n`;
        text += `1位偏差値: ${race.top_deviation.toFixed(1)}\n`;
        text += `予想: ${race.top3.join('-')}\n`;
        text += `推奨: ${race.top5.join('-')}\n`;
        text += `分析: ${race.analysis}\n\n`;
    });
    
    text += `**的中率**: Top3≥1 90.06% | Top5≥3 28.23%\n`;
    
    return text;
}

// 日付フォーマット（YYYYMMDD → YYYY/MM/DD）
function formatDate(dateStr) {
    if (!dateStr || dateStr.length !== 8) return dateStr;
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${year}/${month}/${day}`;
}
```

---

## 🤖 Phase 2: Discord Bot実装（1時間）

### **Step 2-1: Discord Bot基本構造**

**ファイル**: `E:\eoi-pl\discord_bot.py`

```python
#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime Discord Bot
地方競馬AI予想自動配信システム

機能:
- 毎朝9:00に自動配信
- 手動実行コマンド（!予想）
- 推奨度フィルタリング（★4以上）
"""

import discord
from discord.ext import commands, tasks
import httpx
from datetime import datetime, time
import asyncio
from typing import List, Dict

# =====================================================================
# 設定
# =====================================================================

# Discord Bot Token（環境変数から取得することを推奨）
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"  # ← ここにトークンを設定

# 配信先チャンネルID
TARGET_CHANNEL_ID = 0  # ← ここにチャンネルIDを設定

# Python API URL
API_URL = "http://localhost:8000"

# 配信時刻（毎朝9:00）
BROADCAST_TIME = time(hour=9, minute=0)

# =====================================================================
# Discord Bot設定
# =====================================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# =====================================================================
# ヘルパー関数
# =====================================================================

def format_date(date_str: str) -> str:
    """日付フォーマット（YYYYMMDD → YYYY/MM/DD）"""
    if len(date_str) != 8:
        return date_str
    return f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"

def create_race_embed(race: Dict) -> discord.Embed:
    """レース情報のEmbedを作成"""
    embed = discord.Embed(
        title=f"【{race['venue']} {race['race_no']}R】{race['rating']}",
        description=race['analysis'],
        color=0xFFD700 if race['rating'] == '★★★★★' else 0x00FF00
    )
    
    embed.add_field(
        name="1位偏差値",
        value=f"{race['top_deviation']:.1f}",
        inline=True
    )
    
    embed.add_field(
        name="Top3予想",
        value=f"{race['top3'][0]}-{race['top3'][1]}-{race['top3'][2]}",
        inline=True
    )
    
    embed.add_field(
        name="Top5予想",
        value='-'.join(map(str, race['top5'])),
        inline=True
    )
    
    # 上位5頭の詳細
    top5_horses = race['horses'][:5]
    horses_text = '\n'.join([
        f"{h['rank']}. {h['umaban']}番 {h['bamei']} ({h['deviation']:.1f})"
        for h in top5_horses
    ])
    
    embed.add_field(
        name="上位5頭",
        value=horses_text,
        inline=False
    )
    
    embed.set_footer(text="EOI-PL v1.0-Prime | Enable CEO")
    
    return embed

async def fetch_predictions(date: str) -> Dict:
    """予想データを取得"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_URL}/api/predictions/{date}")
        response.raise_for_status()
        return response.json()

# =====================================================================
# Bot イベント
# =====================================================================

@bot.event
async def on_ready():
    """Bot起動時"""
    print(f'✅ Bot起動: {bot.user} (ID: {bot.user.id})')
    print(f'🏇 EOI-PL Discord Bot v1.0-Prime')
    print(f'📅 定時配信: 毎朝{BROADCAST_TIME.hour}:{BROADCAST_TIME.minute:02d}')
    
    # 定時配信タスク開始
    daily_broadcast.start()

@bot.event
async def on_command_error(ctx, error):
    """コマンドエラーハンドリング"""
    if isinstance(error, commands.CommandNotFound):
        return
    
    await ctx.send(f"❌ エラーが発生しました: {str(error)}")
    print(f"Error: {error}")

# =====================================================================
# 定時配信タスク
# =====================================================================

@tasks.loop(hours=24)
async def daily_broadcast():
    """毎朝9:00に予想を自動配信"""
    try:
        # 今日の日付
        today = datetime.now().strftime("%Y%m%d")
        
        print(f"📅 定時配信開始: {today}")
        
        # チャンネル取得
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if not channel:
            print(f"❌ チャンネルID {TARGET_CHANNEL_ID} が見つかりません")
            return
        
        # 予想取得
        try:
            data = await fetch_predictions(today)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                await channel.send(f"📅 {format_date(today)}\n本日はレース開催がありません。")
                return
            raise
        
        # ヘッダーメッセージ
        await channel.send(
            f"🏇 **{format_date(today)} 地方競馬AI予想**\n"
            f"EOI-PL v1.0-Prime | Enable CEO\n"
            f"全{len(data['races'])}レース中、推奨レースを配信します。"
        )
        
        # 推奨度★4以上のレースのみ配信
        recommended_races = [
            race for race in data['races']
            if race['rating'] in ['★★★★★', '★★★★☆']
        ]
        
        if not recommended_races:
            await channel.send("本日は推奨レースがありません。")
            return
        
        await channel.send(f"**推奨レース**: {len(recommended_races)}レース")
        
        # レースごとにEmbed送信
        for race in recommended_races:
            embed = create_race_embed(race)
            await channel.send(embed=embed)
            await asyncio.sleep(1)  # レート制限回避
        
        # フッター
        await channel.send(
            "**的中率**: Top3≥1 90.06% | Top5≥3 28.23%\n"
            "**システム**: EOI-PL v1.0-Prime (Plackett-Luce + Power EP)"
        )
        
        print(f"✅ 定時配信完了: {len(recommended_races)}レース")
        
    except Exception as e:
        print(f"❌ 定時配信エラー: {e}")
        if channel:
            await channel.send(f"❌ 予想配信エラーが発生しました: {str(e)}")

@daily_broadcast.before_loop
async def before_daily_broadcast():
    """定時配信前の準備"""
    await bot.wait_until_ready()
    
    # 次の配信時刻まで待機
    now = datetime.now()
    target = now.replace(
        hour=BROADCAST_TIME.hour,
        minute=BROADCAST_TIME.minute,
        second=0,
        microsecond=0
    )
    
    # 今日の配信時刻が過ぎていたら明日に設定
    if now >= target:
        target = target.replace(day=target.day + 1)
    
    wait_seconds = (target - now).total_seconds()
    print(f"⏰ 次回配信: {target} ({wait_seconds/3600:.1f}時間後)")
    
    await asyncio.sleep(wait_seconds)

# =====================================================================
# コマンド
# =====================================================================

@bot.command(name='予想')
async def manual_prediction(ctx, date: str = None):
    """
    手動で予想を取得
    
    使い方:
        !予想          - 今日の予想
        !予想 20260102 - 指定日の予想
    """
    try:
        # 日付が指定されていなければ今日
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        await ctx.send(f"🔄 {format_date(date)}の予想を生成中...")
        
        # 予想取得
        try:
            data = await fetch_predictions(date)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                await ctx.send(f"❌ {format_date(date)}のレースが見つかりません。")
                return
            raise
        
        # ヘッダー
        await ctx.send(
            f"🏇 **{format_date(date)} 地方競馬AI予想**\n"
            f"全{len(data['races'])}レース"
        )
        
        # 推奨度★4以上
        recommended_races = [
            race for race in data['races']
            if race['rating'] in ['★★★★★', '★★★★☆']
        ]
        
        if not recommended_races:
            await ctx.send("推奨レースがありません。")
            return
        
        await ctx.send(f"**推奨レース**: {len(recommended_races)}レース")
        
        # 最大10レースまで表示
        for race in recommended_races[:10]:
            embed = create_race_embed(race)
            await ctx.send(embed=embed)
            await asyncio.sleep(0.5)
        
        if len(recommended_races) > 10:
            await ctx.send(f"（残り{len(recommended_races) - 10}レースは省略）")
        
    except Exception as e:
        await ctx.send(f"❌ エラー: {str(e)}")
        print(f"Error in manual_prediction: {e}")

@bot.command(name='ヘルプ')
async def help_command(ctx):
    """ヘルプを表示"""
    embed = discord.Embed(
        title="🏇 EOI-PL Discord Bot コマンド一覧",
        description="地方競馬AI予想システム",
        color=0x00FF00
    )
    
    embed.add_field(
        name="!予想",
        value="今日の予想を表示",
        inline=False
    )
    
    embed.add_field(
        name="!予想 20260102",
        value="指定日の予想を表示",
        inline=False
    )
    
    embed.add_field(
        name="!ヘルプ",
        value="このヘルプを表示",
        inline=False
    )
    
    embed.add_field(
        name="定時配信",
        value=f"毎朝{BROADCAST_TIME.hour}:{BROADCAST_TIME.minute:02d}に自動配信",
        inline=False
    )
    
    embed.set_footer(text="EOI-PL v1.0-Prime | Enable CEO")
    
    await ctx.send(embed=embed)

# =====================================================================
# メイン実行
# =====================================================================

if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("❌ エラー: DISCORD_BOT_TOKEN を設定してください")
        exit(1)
    
    if TARGET_CHANNEL_ID == 0:
        print("⚠️  警告: TARGET_CHANNEL_ID が設定されていません")
    
    print("🚀 Discord Bot起動中...")
    bot.run(DISCORD_BOT_TOKEN)
```

### **Step 2-2: 依存関係追加**

**ファイル**: `E:\eoi-pl\api\requirements.txt` に追加

```
discord.py>=2.3.0
httpx>=0.25.0
```

---

## 🔧 Windows環境セットアップ手順

### **Step 3-1: Discord Bot Token取得**

1. https://discord.com/developers/applications にアクセス
2. 「New Application」をクリック
3. アプリケーション名: `EOI-PL-Bot`
4. 「Bot」タブへ移動
5. 「Add Bot」をクリック
6. 「TOKEN」の「Copy」をクリック
7. `discord_bot.py` の `DISCORD_BOT_TOKEN` に貼り付け

### **Step 3-2: Discord Bot招待**

1. 「OAuth2」→「URL Generator」
2. **SCOPES**: `bot`
3. **BOT PERMISSIONS**: 
   - Send Messages
   - Embed Links
   - Read Message History
4. 生成されたURLでBotを招待

### **Step 3-3: チャンネルID取得**

1. Discordで開発者モードを有効化
2. 配信先チャンネルを右クリック
3. 「IDをコピー」
4. `discord_bot.py` の `TARGET_CHANNEL_ID` に貼り付け

### **Step 3-4: Python環境構築（Windows）**

```powershell
# プロジェクトディレクトリへ移動
cd E:\eoi-pl

# 仮想環境作成
python -m venv venv

# 仮想環境有効化
.\venv\Scripts\Activate.ps1

# 依存関係インストール
cd api
pip install -r requirements.txt

# Discord Bot依存関係インストール
pip install 'discord.py>=2.3.0' 'httpx>=0.25.0'
```

### **Step 3-5: Windows Service化（NSSM）**

**NSSM ダウンロード**: https://nssm.cc/download

#### **Python API サービス**

```powershell
# サービス登録
nssm install EOI-PL-API "E:\eoi-pl\venv\Scripts\python.exe" "E:\eoi-pl\api\main.py"
nssm set EOI-PL-API AppDirectory E:\eoi-pl\api
nssm set EOI-PL-API DisplayName "EOI-PL FastAPI Server"
nssm set EOI-PL-API Description "地方競馬AI予想APIサーバー"
nssm set EOI-PL-API Start SERVICE_AUTO_START

# サービス開始
nssm start EOI-PL-API

# 状態確認
nssm status EOI-PL-API
```

#### **Discord Bot サービス**

```powershell
# サービス登録
nssm install EOI-PL-Discord "E:\eoi-pl\venv\Scripts\python.exe" "E:\eoi-pl\discord_bot.py"
nssm set EOI-PL-Discord AppDirectory E:\eoi-pl
nssm set EOI-PL-Discord DisplayName "EOI-PL Discord Bot"
nssm set EOI-PL-Discord Description "地方競馬AI予想Discord配信Bot"
nssm set EOI-PL-Discord Start SERVICE_AUTO_START

# サービス開始
nssm start EOI-PL-Discord

# 状態確認
nssm status EOI-PL-Discord
```

---

## ✅ 動作確認チェックリスト

### **Web UI**
- [ ] http://localhost:8000/ にアクセス
- [ ] 日付選択ドロップダウンが表示される
- [ ] 「予想を生成」ボタンをクリック
- [ ] 全レース・全馬が表示される
- [ ] 「note用にコピー」でMarkdown形式がコピーされる
- [ ] 「Discord用にコピー」でDiscord形式がコピーされる

### **Discord Bot**
- [ ] Botがオンライン状態
- [ ] `!ヘルプ` コマンドが応答する
- [ ] `!予想` コマンドで今日の予想が表示される
- [ ] `!予想 20260102` で指定日の予想が表示される
- [ ] Embedが正しく表示される
- [ ] 定時配信（毎朝9:00）が動作する

### **Windows Service**
- [ ] EOI-PL-API サービスが起動している
- [ ] EOI-PL-Discord サービスが起動している
- [ ] PC再起動後も自動起動する
- [ ] サービスログが正常

---

## 🎯 次のステップ

### **即座に実装**
1. ✅ Python APIにHTML配信機能を追加
2. ✅ Frontend JavaScript実装
3. ✅ note用コピー機能実装
4. ✅ Discord Bot実装
5. ✅ 定時配信機能実装

### **テスト**
1. ⏳ ローカル環境でWeb UI動作確認
2. ⏳ Discord Bot手動実行テスト
3. ⏳ 定時配信テスト（時刻変更して確認）

### **本番デプロイ**
1. ⏳ Windows環境で両サービスを起動
2. ⏳ 24時間稼働確認
3. ⏳ エラーログ監視

---

## 📚 参考情報

### **ファイル構成**

```
E:\eoi-pl\
├── api\
│   ├── main.py              # FastAPI サーバー（HTML配信追加）
│   ├── requirements.txt     # Python依存関係
│   └── static\
│       └── app.js           # Frontend JavaScript
├── discord_bot.py           # Discord Bot
├── data\
│   └── feature_database_2020_2025.json
├── venv\                    # Python仮想環境
└── README.md
```

### **重要なURL**

- **Web UI**: http://localhost:8000/
- **API Health**: http://localhost:8000/api/health
- **API Dates**: http://localhost:8000/api/dates
- **API Predictions**: http://localhost:8000/api/predictions/20260102

### **Discord コマンド**

- `!予想` - 今日の予想
- `!予想 20260102` - 指定日の予想
- `!ヘルプ` - ヘルプ表示

### **PostgreSQL接続情報**

- Host: localhost
- Port: 5432
- Database: eoi_pl
- User: postgres
- Password: postgres123

---

**作成者**: Claude (AI Developer)  
**最終更新**: 2026-02-01  
**バージョン**: v1.0-Final  
**ステータス**: ✅ 実装準備完了
