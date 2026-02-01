import { Hono } from 'hono'
import { cors } from 'hono/cors'

const app = new Hono()

// CORS設定
app.use('/api/*', cors())

// 静的ファイル配信（Cloudflare Pagesは自動で /static を配信）

// Python API のベースURL（環境変数から取得、デフォルトはlocalhost）
const PYTHON_API_URL = typeof process !== 'undefined' && process.env?.PYTHON_API_URL 
  ? process.env.PYTHON_API_URL 
  : 'http://localhost:8000'

// =====================================================================
// API エンドポイント
// =====================================================================

// 利用可能な日付一覧を取得（Python APIへプロキシ）
app.get('/api/dates', async (c) => {
  try {
    const response = await fetch(`${PYTHON_API_URL}/api/dates`)
    
    if (!response.ok) {
      throw new Error(`Python API error: ${response.status}`)
    }
    
    const data = await response.json()
    return c.json(data)
  } catch (error) {
    console.error('API dates error:', error)
    return c.json({ error: 'データ取得エラー', details: String(error) }, 500)
  }
})

// 指定日の予想を取得（Python APIへプロキシ）
app.get('/api/predictions/:date', async (c) => {
  const date = c.req.param('date')
  
  try {
    const response = await fetch(`${PYTHON_API_URL}/api/predictions/${date}`)
    
    if (!response.ok) {
      if (response.status === 404) {
        return c.json({ error: `日付 ${date} のレースが見つかりません` }, 404)
      }
      throw new Error(`Python API error: ${response.status}`)
    }
    
    const data = await response.json()
    return c.json(data)
  } catch (error) {
    console.error('API predictions error:', error)
    return c.json({ error: '予想生成エラー', details: String(error) }, 500)
  }
})

// ヘルスチェック（Python API接続確認）
app.get('/api/health', async (c) => {
  try {
    const response = await fetch(`${PYTHON_API_URL}/api/health`)
    
    if (!response.ok) {
      throw new Error(`Python API error: ${response.status}`)
    }
    
    const data = await response.json()
    return c.json({
      status: 'healthy',
      python_api: data,
      proxy: 'ok'
    })
  } catch (error) {
    console.error('Health check error:', error)
    return c.json({ 
      status: 'unhealthy',
      error: String(error),
      python_api_url: PYTHON_API_URL
    }, 500)
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

// Cloudflare Workers用のエクスポート
export default {
  fetch: app.fetch.bind(app)
}
