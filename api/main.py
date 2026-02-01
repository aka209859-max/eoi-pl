#!/usr/bin/env python3
"""
EOI-PL v1.0-Prime FastAPI Server
完全版予想APIサーバー

仕様:
- GET /api/health: ヘルスチェック
- GET /api/dates: 利用可能な日付一覧（当日+翌日）
- GET /api/predictions/{date}: 指定日の全レース予想
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import psycopg2
import json
import numpy as np
import sys
import os
from pathlib import Path

# モジュールパス追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# =====================================================================
# 設定
# =====================================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'eoi_pl',
    'user': 'postgres',
    'password': 'postgres123'
}

WEIGHTS = {
    'avg_rank': 0.30, 'jockey': 0.15, 'trainer': 0.10,
    'corner': 0.15, 'time': 0.15, 'distance': 0.10, 'track': 0.05
}

VENUE_NAMES = {
    30: '門別', 35: '盛岡', 36: '水沢', 42: '浦和', 43: '船橋', 44: '大井', 45: '川崎',
    46: '金沢', 47: '笠松', 48: '名古屋', 50: '園田', 51: '姫路', 54: '高知', 55: '佐賀'
}

DISTANCE_BENCHMARKS = {
    800: (492.0, 13.9), 820: (510.6, 7.4), 850: (516.1, 8.9),
    900: (553.1, 10.1), 920: (567.8, 10.0), 1000: (982.5, 119.3),
    1100: (1087.1, 9.9), 1200: (1147.3, 14.1), 1230: (1206.8, 13.3),
    1300: (1249.1, 15.8), 1400: (1313.8, 20.9), 1500: (1374.6, 15.5),
    1600: (1436.7, 24.6), 1650: (1457.6, 14.9), 1700: (1515.7, 29.0),
    1750: (1578.7, 74.0), 1800: (1655.5, 185.8), 1860: (2002.3, 117.5),
    1870: (2055.7, 56.0), 1900: (2049.1, 42.1), 2000: (2120.0, 34.7),
    2100: (2167.2, 25.9), 2200: (2279.0, 24.2), 2400: (2377.9, 55.9),
    2500: (2475.4, 30.8), 2600: (2505.0, 21.3),
}

# feature_database_2020_2025.json のパス
FEATURE_DB_PATH = Path(__file__).parent.parent / 'data' / 'feature_database_2020_2025.json'

# =====================================================================
# FastAPI アプリケーション
# =====================================================================

app = FastAPI(title="EOI-PL API", version="1.0.0")

# 静的ファイルディレクトリの作成
STATIC_DIR = Path(__file__).parent / 'static'
STATIC_DIR.mkdir(exist_ok=True)

# 静的ファイル配信
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# データモデル
# =====================================================================

class Horse(BaseModel):
    rank: int
    umaban: int
    bamei: str
    deviation: float

class Race(BaseModel):
    race_id: str
    venue: str
    race_no: int
    rating: str
    top_deviation: float
    horses: List[Horse]
    top3: List[int]
    top5: List[int]
    sanrenpuku: List[List[int]] = []
    sanrentan: List[List[int]] = []
    analysis: str

class PredictionsResponse(BaseModel):
    date: str
    generated_at: str
    races: List[Race]

class DatesResponse(BaseModel):
    dates: List[str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    feature_db: str

# =====================================================================
# 予測モデル（format_predictions_discord.py から移植）
# =====================================================================

class EOIPLPredictor:
    """EOI-PL v1.0-Prime 予測モデル"""
    
    def __init__(self, feature_db_path: str):
        with open(feature_db_path, 'r', encoding='utf-8') as f:
            self.feature_db = json.load(f)
    
    def calculate_horse_skill(self, ketto: str) -> float:
        if ketto in self.feature_db['horses']:
            return -np.log(max(self.feature_db['horses'][ketto]['avg_rank'], 1.0))
        return -np.log(10.0)
    
    def calculate_jockey_skill(self, kishu_code: int) -> float:
        kishu_key = str(kishu_code)
        if kishu_key in self.feature_db['jockeys']:
            return -np.log(max(self.feature_db['jockeys'][kishu_key]['avg_rank'], 1.0))
        return -np.log(8.0)
    
    def calculate_trainer_skill(self, chokyoshi_code: int) -> float:
        trainer_key = str(chokyoshi_code)
        if trainer_key in self.feature_db['trainers']:
            return -np.log(max(self.feature_db['trainers'][trainer_key]['avg_rank'], 1.0))
        return -np.log(8.0)
    
    def calculate_corner_skill(self, ketto: str) -> float:
        if ketto in self.feature_db['horses']:
            avg_corner = self.feature_db['horses'][ketto].get('avg_corner')
            if avg_corner is not None:
                return -np.log(max(avg_corner, 1.0))
        return 0.0
    
    def calculate_time_skill(self, ketto: str, kyori: int) -> float:
        if ketto not in self.feature_db['horses']:
            return 0.0
        
        horse_data = self.feature_db['horses'][ketto]
        if 'distances' not in horse_data:
            return 0.0
        
        distances = horse_data['distances']
        if str(kyori) in distances:
            dist_data = distances[str(kyori)]
            avg_time = dist_data.get('avg_time', 0)
            
            if kyori in DISTANCE_BENCHMARKS and avg_time > 0:
                bench_avg, bench_std = DISTANCE_BENCHMARKS[kyori]
                z_score = (bench_avg - avg_time) / max(bench_std, 1.0)
                return z_score * 0.5
        
        return 0.0
    
    def calculate_distance_adaptation(self, ketto: str, kyori: int) -> float:
        if ketto not in self.feature_db['horses']:
            return 0.0
        
        horse_data = self.feature_db['horses'][ketto]
        if 'distances' not in horse_data:
            return 0.0
        
        distances = horse_data['distances']
        if str(kyori) in distances:
            dist_data = distances[str(kyori)]
            count = dist_data.get('count', 0)
            avg_rank = dist_data.get('avg_rank', 10.0)
            
            if count >= 3:
                adaptation = -np.log(max(avg_rank, 1.0))
                return adaptation * min(count / 10.0, 1.0)
        
        return 0.0
    
    def calculate_track_adaptation(self, ketto: str, track_code: int) -> float:
        """トラック適応度を計算（競馬場別）"""
        if ketto not in self.feature_db.get('track_adaptation', {}):
            return 0.0
        
        track_data = self.feature_db['track_adaptation'][ketto]
        track_key = str(track_code)
        track_info = track_data.get(track_key)
        
        if track_info is None:
            return 0.0
        
        if isinstance(track_info, dict):
            avg_rank = track_info.get('avg_rank', 8.0)
            return -np.log(max(avg_rank, 1.0))
        
        return 0.0
    
    def predict_race(self, race_data: Dict, entries: List[Dict]) -> List[Dict]:
        """レース予想を実行"""
        kyori = race_data.get('kyori', 1400)
        track_code = race_data.get('track_code', 23)
        
        predictions = []
        
        for entry in entries:
            ketto = str(entry['ketto_toroku_bango'])
            kishu_code = entry.get('kishu_code', 0) or 0
            chokyoshi_code = entry.get('chokyoshi_code', 0) or 0
            
            # スキル計算
            horse_skill = self.calculate_horse_skill(ketto)
            jockey_skill = self.calculate_jockey_skill(kishu_code)
            trainer_skill = self.calculate_trainer_skill(chokyoshi_code)
            corner_skill = self.calculate_corner_skill(ketto)
            time_skill = self.calculate_time_skill(ketto, kyori)
            distance_skill = self.calculate_distance_adaptation(ketto, kyori)
            track_skill = self.calculate_track_adaptation(ketto, track_code)
            
            # 総合スキル
            total_skill = (
                WEIGHTS['avg_rank'] * horse_skill +
                WEIGHTS['jockey'] * jockey_skill +
                WEIGHTS['trainer'] * trainer_skill +
                WEIGHTS['corner'] * corner_skill +
                WEIGHTS['time'] * time_skill +
                WEIGHTS['distance'] * distance_skill +
                WEIGHTS['track'] * track_skill
            )
            
            predictions.append({
                'umaban': entry['umaban'],
                'bamei': entry['bamei'],
                'total_skill': total_skill,
                'ketto': ketto
            })
        
        # スキルでソート（降順）
        predictions.sort(key=lambda x: x['total_skill'], reverse=True)
        
        # ランク付け
        for rank, pred in enumerate(predictions, 1):
            pred['rank'] = rank
        
        return predictions

# グローバル予測器インスタンス
predictor = EOIPLPredictor(str(FEATURE_DB_PATH))

# =====================================================================
# ユーティリティ関数
# =====================================================================

def calculate_deviation_score(skills: List[float]) -> List[float]:
    """スキル値を偏差値に変換"""
    skills_array = np.array(skills)
    mean = np.mean(skills_array)
    std = np.std(skills_array)
    
    if std == 0:
        return [50.0] * len(skills)
    
    deviations = 50.0 + 10.0 * (skills_array - mean) / std
    return deviations.tolist()

def get_race_recommendation(top_deviation: float) -> tuple:
    """1位馬の偏差値からレース全体の推奨度を取得"""
    if top_deviation >= 70:
        return '★★★★★', '本命が圧倒的で非常に予想しやすいレースです'
    elif top_deviation >= 65:
        return '★★★★☆', '本命が明確で予想しやすいレースです'
    elif top_deviation >= 60:
        return '★★★☆☆', '本命が有力で信頼できるレースです'
    elif top_deviation >= 55:
        return '★★☆☆☆', '混戦模様ですが予想可能なレースです'
    elif top_deviation >= 50:
        return '★☆☆☆☆', '大混戦で予想が難しいレースです'
    else:
        return '☆☆☆☆☆', '荒れ模様で予想が非常に難しいレースです'

def generate_betting(top_horses: List[int], max_count: int = 9) -> List[List[int]]:
    """上位馬から買い目を生成（三連複/三連単）"""
    from itertools import combinations, permutations
    
    betting = []
    
    if len(top_horses) < 3:
        return betting
    
    # 三連複: 組み合わせ（順序なし）
    if max_count == 9:
        for combo in combinations(top_horses[:5], 3):
            betting.append(list(combo))
            if len(betting) >= max_count:
                break
    # 三連単: 順列（順序あり）
    else:
        for perm in permutations(top_horses[:4], 3):
            betting.append(list(perm))
            if len(betting) >= max_count:
                break
    
    return betting

def get_db_connection():
    """PostgreSQL接続を取得"""
    return psycopg2.connect(**DB_CONFIG)

def parse_date(date_str: str) -> tuple:
    """日付文字列をパース (YYYYMMDD -> YYYY, MMDD)"""
    if len(date_str) != 8:
        raise ValueError(f"Invalid date format: {date_str}")
    
    year = int(date_str[:4])
    month_day = int(date_str[4:])
    
    return year, month_day

def format_date(year: int, month_day: int) -> str:
    """日付をフォーマット (YYYY, MMDD -> YYYYMMDD)"""
    return f"{year}{month_day:04d}"

# =====================================================================
# API エンドポイント
# =====================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
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
                    note用にコピー（全レース）
                </button>
            </div>
            <p class="text-sm text-gray-600 mt-2 text-center">
                <i class="fas fa-info-circle mr-1"></i>
                Discord用コピーは各レースの個別ボタンをご利用ください（★4以上のみ表示）
            </p>
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

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェック"""
    try:
        # DB接続確認
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM races;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        db_status = f"OK ({count:,} races)"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    # feature_db確認
    feature_db_status = "OK" if FEATURE_DB_PATH.exists() else "ERROR: Not found"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "feature_db": feature_db_status
    }

@app.get("/api/dates", response_model=DatesResponse)
async def get_available_dates():
    """利用可能な日付一覧を取得（当日+翌日）"""
    try:
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        dates_to_check = [
            today.strftime("%Y%m%d"),
            tomorrow.strftime("%Y%m%d")
        ]
        
        available_dates = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for date_str in dates_to_check:
            year, month_day = parse_date(date_str)
            
            # レース存在確認
            cursor.execute("""
                SELECT COUNT(*) FROM races 
                WHERE kaisai_nen = %s AND kaisai_tsukihi = %s
            """, (year, month_day))
            
            count = cursor.fetchone()[0]
            if count > 0:
                available_dates.append(date_str)
        
        cursor.close()
        conn.close()
        
        return {"dates": available_dates}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"日付取得エラー: {str(e)}")

@app.get("/api/predictions/{date}", response_model=PredictionsResponse)
async def get_predictions(date: str):
    """指定日の予想を生成"""
    try:
        # 日付パース
        year, month_day = parse_date(date)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # レース情報取得（会場83を除外）
        cursor.execute("""
            SELECT race_id, keibajo_code, race_bango, kyori, track_code, tosu
            FROM races
            WHERE kaisai_nen = %s AND kaisai_tsukihi = %s
              AND keibajo_code != 83
            ORDER BY keibajo_code, race_bango
        """, (year, month_day))
        
        races_data = cursor.fetchall()
        
        if not races_data:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"日付 {date} のレースが見つかりません")
        
        all_races = []
        
        for race_row in races_data:
            race_id, keibajo_code, race_bango, kyori, track_code, tosu = race_row
            
            # エントリー情報取得
            cursor.execute("""
                SELECT umaban, bamei, ketto_toroku_bango, kishu_code, chokyoshi_code
                FROM entries
                WHERE race_id = %s
                ORDER BY umaban
            """, (race_id,))
            
            entries_data = cursor.fetchall()
            
            if not entries_data:
                continue
            
            # エントリーをDict化
            entries = [
                {
                    'umaban': row[0],
                    'bamei': row[1],
                    'ketto_toroku_bango': row[2],
                    'kishu_code': row[3],
                    'chokyoshi_code': row[4]
                }
                for row in entries_data
            ]
            
            # レースデータ
            race_data = {
                'kyori': kyori if kyori else 1400,
                'track_code': track_code if track_code else 23
            }
            
            # 予想実行
            predictions = predictor.predict_race(race_data, entries)
            
            # 偏差値計算
            skills = [p['total_skill'] for p in predictions]
            deviations = calculate_deviation_score(skills)
            
            # 偏差値を追加
            for pred, dev in zip(predictions, deviations):
                pred['deviation'] = round(dev, 1)
            
            # Top5抽出
            top5_predictions = predictions[:5]
            top_deviation = top5_predictions[0]['deviation']
            rating, analysis = get_race_recommendation(top_deviation)
            
            # 会場名取得
            venue_name = VENUE_NAMES.get(keibajo_code, f"会場{keibajo_code}")
            
            # レース情報構築
            race_info = {
                'race_id': race_id,
                'venue': venue_name,
                'race_no': race_bango,
                'rating': rating,
                'top_deviation': top_deviation,
                'horses': [
                    {
                        'rank': p['rank'],
                        'umaban': p['umaban'],
                        'bamei': p['bamei'],
                        'deviation': p['deviation']
                    }
                    for p in predictions
                ],
                'top3': [p['umaban'] for p in predictions[:3]],
                'top5': [p['umaban'] for p in predictions[:5]],
                'sanrenpuku': generate_betting([p['umaban'] for p in predictions[:5]], max_count=9),
                'sanrentan': generate_betting([p['umaban'] for p in predictions[:4]], max_count=12),
                'analysis': analysis
            }
            
            all_races.append(race_info)
        
        cursor.close()
        conn.close()
        
        return {
            'date': date,
            'generated_at': datetime.now().isoformat(),
            'races': all_races
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予想生成エラー: {str(e)}")

# =====================================================================
# メイン実行
# =====================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
