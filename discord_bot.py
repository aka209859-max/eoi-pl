#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime Discord Bot
- 定時配信（毎朝8:00）: 1レースずつ順次送信
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
API_URL = os.getenv('API_URL', 'http://localhost:8001')

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
# 定時配信タスク（毎朝8:00）
# =====================================================================
@tasks.loop(hours=24)
async def daily_prediction_task():
    """毎朝8:00に自動配信（1レースずつ）"""
    now = datetime.now(JST)
    
    # 8:00になるまで待機
    target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
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
# 定時配信実行（1レースずつ送信）
# =====================================================================
async def send_daily_prediction():
    """当日の予想を配信チャンネルに1レースずつ送信"""
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
            description=f'推奨レース: {len(high_rating_races)}件 / 全{len(data["races"])}レース\n配信方式: 1レースずつ順次送信',
            color=0x00ff00,
            timestamp=datetime.now(JST)
        )
        header_embed.set_footer(text='EOI-PL v1.0-Prime | 的中率: Top3≥1 90.06%')
        await channel.send(embed=header_embed)
        
        # 各レースを1つずつ送信（間隔を開ける）
        for index, race in enumerate(high_rating_races, 1):
            # レース情報のEmbed作成
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
            
            # 進捗表示
            embed.set_footer(text=f'配信進捗: {index}/{len(high_rating_races)}レース | EOI-PL v1.0-Prime')
            
            await channel.send(embed=embed)
            
            # レート制限回避（3秒間隔）
            if index < len(high_rating_races):
                await asyncio.sleep(3)
        
        # 配信完了メッセージ
        completion_embed = discord.Embed(
            title='✅ 配信完了',
            description=f'{len(high_rating_races)}レースの予想配信が完了しました',
            color=0x00ff00
        )
        completion_embed.add_field(
            name='的中率',
            value='Top3≥1: 90.06% | Top5≥3: 28.23%',
            inline=False
        )
        await channel.send(embed=completion_embed)
        
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
    手動で予想を取得（1レースずつ送信）
    
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
            await ctx.send(f'📢 推奨レース（★4以上）を1レースずつ送信します...')
            
            for index, race in enumerate(high_rating_races, 1):
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
                
                embed.set_footer(text=f'{index}/{len(high_rating_races)}レース | EOI-PL v1.0-Prime')
                
                await ctx.send(embed=embed)
                
                # レート制限回避
                if index < len(high_rating_races):
                    await asyncio.sleep(2)
        
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
    print(f'⏰ 配信時刻: 毎朝8:00 JST')
    print(f'📡 API URL: {API_URL}')
    bot.run(DISCORD_TOKEN)
