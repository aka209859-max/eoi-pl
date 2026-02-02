// =====================================================================
// EOI-PL 予想配信センター - Frontend JavaScript
// =====================================================================

let currentPredictions = null;
let currentVenue = 'all'; // 現在選択中の競馬場

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
            // 日付がない場合は、テスト用に2026/01/02を追加
            select.innerHTML = '<option value="">--- 日付を選択 ---</option>';
            select.innerHTML += '<option value="20260102">2026/01/02 (テストデータ)</option>';
            select.innerHTML += '<option value="20260103">2026/01/03 (テストデータ)</option>';
            select.innerHTML += '<option value="20260104">2026/01/04 (テストデータ)</option>';
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
    // 更新ボタン
    document.getElementById('refreshBtn').addEventListener('click', refreshData);
    
    // 予想生成ボタン
    document.getElementById('generateBtn').addEventListener('click', generatePredictions);
}

// =====================================================================
// 最新データの更新
// =====================================================================
async function refreshData() {
    const refreshBtn = document.getElementById('refreshBtn');
    const refreshStatus = document.getElementById('refreshStatus');
    
    // ボタンを無効化
    refreshBtn.disabled = true;
    refreshStatus.classList.remove('hidden');
    refreshStatus.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>最新データを取得中...';
    
    try {
        const response = await fetch('/api/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 成功メッセージ
            refreshStatus.innerHTML = '<i class="fas fa-check-circle mr-2 text-green-600"></i>' + data.message;
            
            // 日付リストを再読み込み
            await loadDates();
            
            // 最新日付を自動選択
            if (data.latest_date) {
                const select = document.getElementById('dateSelect');
                select.value = data.latest_date;
            }
            
            // 3秒後に自動で予想生成
            setTimeout(() => {
                generatePredictions();
            }, 1000);
            
        } else {
            refreshStatus.innerHTML = '<i class="fas fa-exclamation-triangle mr-2 text-yellow-600"></i>' + data.message;
        }
        
    } catch (error) {
        console.error('更新エラー:', error);
        refreshStatus.innerHTML = '<i class="fas fa-times-circle mr-2 text-red-600"></i>更新に失敗しました';
    } finally {
        // 5秒後にボタンを再度有効化
        setTimeout(() => {
            refreshBtn.disabled = false;
            refreshStatus.classList.add('hidden');
        }, 5000);
    }
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
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        currentPredictions = data;
        currentVenue = 'all'; // リセット
        displayPredictions(data);
    } catch (error) {
        console.error('予想生成エラー:', error);
        predictionsDiv.innerHTML = `<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded"><strong>エラー:</strong> ${error.message}</div>`;
    }
}

// =====================================================================
// 競馬場別にグループ化
// =====================================================================
function groupByVenue(races) {
    const grouped = {};
    
    races.forEach(race => {
        if (!grouped[race.venue]) {
            grouped[race.venue] = [];
        }
        grouped[race.venue].push(race);
    });
    
    return grouped;
}

// =====================================================================
// 競馬場タブの切り替え
// =====================================================================
function switchVenue(venue) {
    currentVenue = venue;
    displayPredictions(currentPredictions);
}

// =====================================================================
// 予想結果の表示（競馬場別タブ対応）
// =====================================================================
function displayPredictions(data) {
    const predictionsDiv = document.getElementById('predictions');
    
    // 競馬場別にグループ化
    const groupedRaces = groupByVenue(data.races);
    const venues = Object.keys(groupedRaces).sort();
    
    // ヘッダー
    let html = `
        <div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg shadow-lg p-6 mb-6">
            <h2 class="text-2xl font-bold">📅 ${formatDate(data.date)} の予想</h2>
            <p class="mt-2">生成日時: ${new Date(data.generated_at).toLocaleString('ja-JP')}</p>
            <p class="mt-1">レース数: ${data.races.length}レース | 競馬場数: ${venues.length}</p>
        </div>
    `;
    
    // 競馬場タブ + コピーボタン
    html += `
        <div class="bg-white rounded-lg shadow-md p-4 mb-6">
            <div class="flex flex-col gap-4">
                <!-- タブ -->
                <div class="flex flex-wrap gap-2">
                    <button 
                        onclick="switchVenue('all')" 
                        class="px-6 py-3 rounded-lg font-bold transition ${currentVenue === 'all' ? 'bg-blue-600 text-white shadow-lg' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}">
                        <i class="fas fa-th-large mr-2"></i>全競馬場 (${data.races.length})
                    </button>
                    ${venues.map(venue => `
                        <button 
                            onclick="switchVenue('${venue}')" 
                            class="px-6 py-3 rounded-lg font-bold transition ${currentVenue === venue ? 'bg-blue-600 text-white shadow-lg' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}">
                            🏇 ${venue} (${groupedRaces[venue].length})
                        </button>
                    `).join('')}
                </div>
                
                <!-- コピーボタン（現在表示中の競馬場用） -->
                <div class="flex flex-wrap gap-2">
                    ${currentVenue === 'all' ? `
                        <button 
                            onclick="copyForNote()" 
                            class="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-lg transition">
                            <i class="fas fa-copy mr-2"></i>
                            全競馬場をnote用にコピー
                        </button>
                        <button 
                            onclick="copyAllForDiscord()" 
                            class="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg shadow-lg transition">
                            <i class="fab fa-discord mr-2"></i>
                            全競馬場をDiscord用にコピー（★4以上のみ）
                        </button>
                    ` : `
                        <button 
                            onclick="copyVenueForNote('${currentVenue}')" 
                            class="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-lg transition">
                            <i class="fas fa-copy mr-2"></i>
                            ${currentVenue}のレースをnote用にコピー
                        </button>
                        <button 
                            onclick="copyVenueForDiscord('${currentVenue}')" 
                            class="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg shadow-lg transition">
                            <i class="fab fa-discord mr-2"></i>
                            ${currentVenue}のレースをDiscord用にコピー（★4以上のみ）
                        </button>
                    `}
                </div>
            </div>
        </div>
    `;
    
    // レース表示
    const racesToDisplay = currentVenue === 'all' ? data.races : groupedRaces[currentVenue];
    
    if (!racesToDisplay || racesToDisplay.length === 0) {
        html += `
            <div class="bg-white rounded-lg shadow-md p-8 text-center text-gray-500">
                <i class="fas fa-info-circle text-4xl mb-4"></i>
                <p class="text-lg">この競馬場のレースはありません</p>
            </div>
        `;
    } else {
        // 競馬場ごとのサマリー（全競馬場表示時のみ）
        if (currentVenue === 'all') {
            html += `
                <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h3 class="text-xl font-bold mb-4"><i class="fas fa-chart-bar mr-2"></i>競馬場別サマリー</h3>
                    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        ${venues.map(venue => {
                            const venueRaces = groupedRaces[venue];
                            const star5 = venueRaces.filter(r => r.rating === '★★★★★').length;
                            const star4 = venueRaces.filter(r => r.rating === '★★★★☆').length;
                            return `
                                <div class="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition cursor-pointer" onclick="switchVenue('${venue}')">
                                    <h4 class="font-bold text-lg mb-2">🏇 ${venue}</h4>
                                    <p class="text-sm text-gray-600">全${venueRaces.length}R</p>
                                    <p class="text-sm text-yellow-600">★5: ${star5}R | ★4: ${star4}R</p>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        // 各レース詳細
        racesToDisplay.forEach((race, index) => {
            // 全レース表示時はインデックスを保持、競馬場別表示時は検索
            const globalIndex = currentVenue === 'all' ? index : data.races.findIndex(r => r.race_id === race.race_id);
            
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
                    
                    <!-- コピーボタン（★4以上のみ表示） -->
                    ${(race.rating === '★★★★★' || race.rating === '★★★★☆') ? `
                        <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                            <button onclick="copyRaceForTwitter(${globalIndex})" class="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-lg shadow-lg transition">
                                <i class="fab fa-twitter mr-2"></i>
                                X用にコピー
                            </button>
                            <button onclick="copyRaceForDiscord(${globalIndex})" class="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg shadow-lg transition">
                                <i class="fab fa-discord mr-2"></i>
                                Discord用にコピー
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }
    
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
// 競馬場別 note用コピー機能
// =====================================================================
function copyVenueForNote(venue) {
    if (!currentPredictions) {
        alert('予想データがありません');
        return;
    }
    
    const venueRaces = currentPredictions.races.filter(r => r.venue === venue);
    
    if (venueRaces.length === 0) {
        alert('この競馬場のレースがありません');
        return;
    }
    
    let noteText = `# 🏇 ${formatDate(currentPredictions.date)} ${venue} AI予想\n\n`;
    noteText += `**生成日時**: ${new Date(currentPredictions.generated_at).toLocaleString('ja-JP')}\n`;
    noteText += `**レース数**: ${venueRaces.length}R\n\n`;
    noteText += `---\n\n`;
    
    venueRaces.forEach(race => {
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
        alert(`✅ ${venue}のnote記事用テキストをクリップボードにコピーしました！\n（${venueRaces.length}レース）`);
    }).catch(err => {
        console.error('コピーエラー:', err);
        alert('❌ コピーに失敗しました');
    });
}

// =====================================================================
// 全競馬場 Discord用コピー機能（★4以上のみ）
// =====================================================================
function copyAllForDiscord() {
    if (!currentPredictions) {
        alert('予想データがありません');
        return;
    }
    
    const highRatedRaces = currentPredictions.races.filter(r => 
        r.rating === '★★★★★' || r.rating === '★★★★☆'
    );
    
    if (highRatedRaces.length === 0) {
        alert('★4以上のレースがありません');
        return;
    }
    
    let discordText = `**🏇 ${formatDate(currentPredictions.date)} 地方競馬AI予想（厳選${highRatedRaces.length}レース）**\n\n`;
    
    highRatedRaces.forEach((race, index) => {
        discordText += `**【${race.venue} ${race.race_no}R】${race.rating}**\n`;
        discordText += `偏差値Top: ${race.top_deviation.toFixed(1)} | 予想: ${race.top3.join('-')}\n`;
        discordText += `推奨買い目: ${race.top5.join('-')}\n`;
        
        // 上位3頭
        race.horses.slice(0, 3).forEach(h => {
            discordText += `${h.rank}位: ${h.umaban}番 ${h.bamei} (${h.deviation.toFixed(1)})\n`;
        });
        
        discordText += `${race.analysis}\n`;
        
        if (index < highRatedRaces.length - 1) {
            discordText += `\n---\n\n`;
        }
    });
    
    discordText += `\n\n*的中率: Top3≥1 90.06% | Top5≥3 28.23%*`;
    
    navigator.clipboard.writeText(discordText).then(() => {
        alert(`✅ Discord用テキストをクリップボードにコピーしました！\n（★4以上 ${highRatedRaces.length}レース）`);
    }).catch(err => {
        console.error('コピーエラー:', err);
        alert('❌ コピーに失敗しました');
    });
}

// =====================================================================
// 競馬場別 Discord用コピー機能（★4以上のみ）
// =====================================================================
function copyVenueForDiscord(venue) {
    if (!currentPredictions) {
        alert('予想データがありません');
        return;
    }
    
    const venueRaces = currentPredictions.races.filter(r => r.venue === venue);
    const highRatedRaces = venueRaces.filter(r => 
        r.rating === '★★★★★' || r.rating === '★★★★☆'
    );
    
    if (highRatedRaces.length === 0) {
        alert(`${venue}には★4以上のレースがありません`);
        return;
    }
    
    let discordText = `**🏇 ${formatDate(currentPredictions.date)} ${venue} AI予想（厳選${highRatedRaces.length}レース）**\n\n`;
    
    highRatedRaces.forEach((race, index) => {
        discordText += `**【${race.race_no}R】${race.rating}**\n`;
        discordText += `偏差値Top: ${race.top_deviation.toFixed(1)} | 予想: ${race.top3.join('-')}\n`;
        discordText += `推奨買い目: ${race.top5.join('-')}\n`;
        
        // 上位3頭
        race.horses.slice(0, 3).forEach(h => {
            discordText += `${h.rank}位: ${h.umaban}番 ${h.bamei} (${h.deviation.toFixed(1)})\n`;
        });
        
        discordText += `${race.analysis}\n`;
        
        if (index < highRatedRaces.length - 1) {
            discordText += `\n---\n\n`;
        }
    });
    
    discordText += `\n\n*的中率: Top3≥1 90.06% | Top5≥3 28.23%*`;
    
    navigator.clipboard.writeText(discordText).then(() => {
        alert(`✅ ${venue}のDiscord用テキストをクリップボードにコピーしました！\n（★4以上 ${highRatedRaces.length}レース）`);
    }).catch(err => {
        console.error('コピーエラー:', err);
        alert('❌ コピーに失敗しました');
    });
}

// =====================================================================
// X用コピー機能（1レースずつ、140文字制限）
// =====================================================================
function copyRaceForTwitter(raceIndex) {
    if (!currentPredictions || !currentPredictions.races[raceIndex]) {
        alert('予想データがありません');
        return;
    }
    
    const race = currentPredictions.races[raceIndex];
    const date = formatDate(currentPredictions.date);
    
    // パターン3: データ重視型
    let twitterText = `${date}\n\n`;
    twitterText += `${race.rating}\n`;
    twitterText += `${race.venue}${race.race_no}R: ${race.top3.join('-')} (${race.top_deviation.toFixed(1)})\n\n`;
    twitterText += `全${currentPredictions.races.length}レース公開中\n`;
    twitterText += `note→[リンク]`;
    
    navigator.clipboard.writeText(twitterText).then(() => {
        alert(`✅ X用テキストをクリップボードにコピーしました！\n【${race.venue} ${race.race_no}R】${race.rating}\n（${twitterText.length}文字）`);
    }).catch(err => {
        console.error('コピーエラー:', err);
        alert('❌ コピーに失敗しました');
    });
}

// =====================================================================
// Discord用コピー機能（1レースずつ）
// =====================================================================
function copyRaceForDiscord(raceIndex) {
    if (!currentPredictions || !currentPredictions.races[raceIndex]) {
        alert('予想データがありません');
        return;
    }
    
    const race = currentPredictions.races[raceIndex];
    
    let discordText = `**🏇 ${formatDate(currentPredictions.date)} ${race.venue} ${race.race_no}R ${race.rating}**\n\n`;
    discordText += `**偏差値Top**: ${race.top_deviation.toFixed(1)}\n`;
    discordText += `**予想**: ${race.top3.join('-')}\n`;
    discordText += `**推奨買い目**: ${race.top5.join('-')}\n\n`;
    
    // 上位3頭の詳細
    discordText += `**上位3頭**\n`;
    race.horses.slice(0, 3).forEach(h => {
        discordText += `${h.rank}位: ${h.umaban}番 **${h.bamei}** (偏差値: ${h.deviation.toFixed(1)})\n`;
    });
    
    discordText += `\n${race.analysis}\n\n`;
    discordText += `*的中率: Top3≥1 90.06% | Top5≥3 28.23%*`;
    
    navigator.clipboard.writeText(discordText).then(() => {
        alert(`✅ Discord用テキストをクリップボードにコピーしました！\n【${race.venue} ${race.race_no}R】${race.rating}`);
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
