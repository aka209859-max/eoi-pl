import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { serveStatic } from 'hono/cloudflare-workers'

// 型定義
type Bindings = {
  DB?: D1Database
}

type Env = {
  Bindings: Bindings
}

const app = new Hono<Env>()

// CORS設定
app.use('/api/*', cors())

// 静的ファイル配信
app.use('/static/*', serveStatic({ root: './public' }))

// =====================================================================
// API エンドポイント
// =====================================================================

// 利用可能な日付一覧を取得
app.get('/api/dates', async (c) => {
  try {
    // TODO: PostgreSQL から日付一覧を取得
    // 開発中は仮データを返す
    const dates = [
      '20251220',
      '20251221',
      '20251222',
      '20251223',
      '20251224',
      '20251225',
      '20251226',
      '20251227',
      '20251228',
      '20251229',
      '20251230',
      '20251231'
    ]
    
    return c.json({ dates })
  } catch (error) {
    return c.json({ error: 'データ取得エラー' }, 500)
  }
})

// 指定日の予想を取得
app.get('/api/predictions/:date', async (c) => {
  const date = c.req.param('date')
  
  try {
    // TODO: PostgreSQL からレース情報を取得して予想を生成
    // 開発中は仮データを返す
    const predictions = {
      date: date,
      races: [
        {
          race_id: `${date}5401`,
          venue: '高知',
          race_no: 1,
          rating: '★★★★★',
          top_deviation: 72.6,
          horses: [
            { rank: 1, umaban: 7, bamei: 'シーザソング', deviation: 72.6 },
            { rank: 2, umaban: 9, bamei: 'ランギロア', deviation: 54.2 },
            { rank: 3, umaban: 8, bamei: 'カンタベリービーム', deviation: 53.5 },
            { rank: 4, umaban: 4, bamei: 'チュラリヴァル', deviation: 51.7 },
            { rank: 5, umaban: 6, bamei: 'コスモラパウィラ', deviation: 50.8 }
          ],
          top3: [7, 9, 8],
          top5: [7, 9, 8, 4, 6],
          analysis: '本命が圧倒的で非常に予想しやすいレースです'
        }
      ]
    }
    
    return c.json(predictions)
  } catch (error) {
    return c.json({ error: '予想生成エラー' }, 500)
  }
})

// 単一レース予想を取得
app.get('/api/race/:race_id', async (c) => {
  const raceId = c.req.param('race_id')
  
  try {
    // TODO: PostgreSQL から単一レースの予想を生成
    return c.json({ message: `Race ${raceId} prediction` })
  } catch (error) {
    return c.json({ error: '予想生成エラー' }, 500)
  }
})

// =====================================================================
// メインページ
// =====================================================================

app.get('/', (c) => {
  return c.html(`
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

        <script src="https://cdn.jsdelivr.net/npm/axios@1.6.0/dist/axios.min.js"></script>
        <script src="/static/app.js"></script>
    </body>
    </html>
  `)
})

export default app
