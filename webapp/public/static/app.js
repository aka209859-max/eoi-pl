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
        const response = await axios.get('/api/dates');
        const dates = response.data.dates;
        
        const select = document.getElementById('dateSelect');
        select.innerHTML = '<option value="">日付を選択してください</option>';
        
        dates.forEach(date => {
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
        const response = await axios.get(`/api/predictions/${selectedDate}`);
        currentPredictions = response.data;
        displayPredictions(currentPredictions);
        
        // アクションボタンを表示
        document.getElementById('actionButtons').classList.remove('hidden');
    } catch (error) {
        console.error('予想生成エラー:', error);
        predictionsDiv.innerHTML = `
            <div class="text-center py-12 text-red-600">
                <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                <p class="text-lg">予想の生成に失敗しました</p>
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
                ${formatDate(data.date)} の予想
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
                    <div class="text-right">
                        <div class="text-2xl font-bold text-yellow-500">${race.rating}</div>
                        <div class="text-sm text-gray-600">1位偏差値: ${race.top_deviation}</div>
                    </div>
                </div>
                
                <!-- 出走馬一覧 -->
                <div class="overflow-x-auto mb-4">
                    <table class="w-full">
                        <thead class="bg-gray-100">
                            <tr>
                                <th class="px-4 py-2 text-left">順位</th>
                                <th class="px-4 py-2 text-left">馬番</th>
                                <th class="px-4 py-2 text-left">馬名</th>
                                <th class="px-4 py-2 text-right">偏差値</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
                            ${race.horses.map(horse => `
                                <tr class="${horse.rank <= 3 ? 'bg-yellow-50 font-semibold' : ''}">
                                    <td class="px-4 py-2">${horse.rank}</td>
                                    <td class="px-4 py-2">${horse.umaban}番</td>
                                    <td class="px-4 py-2">${horse.bamei}</td>
                                    <td class="px-4 py-2 text-right">${horse.deviation}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                <!-- 推奨買い目 -->
                <div class="bg-blue-50 rounded-lg p-4 mb-3">
                    <h4 class="font-bold text-blue-900 mb-2">
                        <i class="fas fa-bullseye mr-2"></i>
                        推奨買い目
                    </h4>
                    <div class="space-y-1 text-sm">
                        <div><strong>Top3（馬連BOXなど）:</strong> ${race.top3.join(', ')}</div>
                        <div><strong>Top5（三連複BOXなど）:</strong> ${race.top5.join(', ')}</div>
                    </div>
                </div>
                
                <!-- レース分析 -->
                <div class="bg-gray-50 rounded-lg p-4">
                    <h4 class="font-bold text-gray-900 mb-2">
                        <i class="fas fa-chart-line mr-2"></i>
                        レース分析
                    </h4>
                    <p class="text-sm text-gray-700">${race.analysis}</p>
                </div>
            </div>
        `;
    });
    
    predictionsDiv.innerHTML = html;
}

// クリップボードにコピー
async function copyToClipboard(format) {
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
    
    try {
        await navigator.clipboard.writeText(text);
        alert(`${format === 'note' ? 'note' : 'Discord'}用テキストをコピーしました！`);
    } catch (error) {
        console.error('コピーエラー:', error);
        alert('コピーに失敗しました');
    }
}

// note用フォーマット生成
function generateNoteFormat(data) {
    let text = `# ${formatDateJP(data.date)} 地方競馬AI予想\n\n`;
    
    data.races.forEach(race => {
        text += `## ${race.venue} ${race.race_no}R ${race.rating}\n\n`;
        text += `**本命:** ${race.horses[0].umaban}番 ${race.horses[0].bamei} (偏差値: ${race.horses[0].deviation})\n`;
        text += `**対抗:** ${race.horses[1].umaban}番 ${race.horses[1].bamei} (${race.horses[1].deviation})\n`;
        text += `**単穴:** ${race.horses[2].umaban}番 ${race.horses[2].bamei} (${race.horses[2].deviation})\n\n`;
        text += `**推奨買い目:**\n`;
        text += `- 馬連BOX: ${race.top3.join('-')}\n`;
        text += `- 三連複BOX: ${race.top5.join('-')}\n\n`;
        text += `**分析:** ${race.analysis}\n\n`;
        text += `---\n\n`;
    });
    
    return text;
}

// Discord用フォーマット生成
function generateDiscordFormat(data) {
    let text = `🏇 **${formatDateJP(data.date)} NAR AI予想**\n`;
    text += `${'='.repeat(60)}\n\n`;
    
    data.races.forEach(race => {
        text += `**【${race.venue} ${race.race_no}R】${race.rating}** (1位偏差値: ${race.top_deviation})\n`;
        text += '```\n';
        text += '順位 馬番 馬名                 偏差値\n';
        text += '-'.repeat(50) + '\n';
        race.horses.forEach(horse => {
            const nameWidth = 20 - horse.bamei.length;
            text += `${String(horse.rank).padStart(2)}  ${String(horse.umaban).padStart(2)}番 ${horse.bamei}${' '.repeat(nameWidth)}${horse.deviation}\n`;
        });
        text += '```\n';
        text += `🎯 **推奨買い目**\n`;
        text += `  Top3（馬連BOX）: ${race.top3.join(', ')}\n`;
        text += `  Top5（三連複BOX）: ${race.top5.join(', ')}\n\n`;
        text += `💡 **レース分析**\n`;
        text += `  ${race.analysis}\n\n`;
        text += `${'='.repeat(60)}\n\n`;
    });
    
    return text;
}

// 日付フォーマット (YYYYMMDD -> YYYY/MM/DD)
function formatDate(dateStr) {
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${year}/${month}/${day}`;
}

// 日付フォーマット (YYYYMMDD -> YYYY年MM月DD日)
function formatDateJP(dateStr) {
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    return `${year}年${month}月${day}日`;
}
