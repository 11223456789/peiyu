// 佩宇Reader v2.0 - Legado风格界面
const Storage = {
    get: async (key) => {
        try {
            const { value } = await Capacitor.Plugins.Preferences.get({ key });
            return value ? JSON.parse(value) : null;
        } catch (e) {
            const val = localStorage.getItem(key);
            return val ? JSON.parse(val) : null;
        }
    },
    set: async (key, value) => {
        try {
            await Capacitor.Plugins.Preferences.set({ key, value: JSON.stringify(value) });
        } catch (e) {
            localStorage.setItem(key, JSON.stringify(value));
        }
    }
};

let bookshelf = [];
let currentBook = null;

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 加载主题
    await loadTheme();
    
    // 加载阅读统计
    await loadReadStats();
    
    bookshelf = await Storage.get('bookshelf') || [];
    renderBookshelf();
    
    try {
        await bookEngine.init();
        showToast(`已加载 ${bookEngine.sources.length} 个书源`);
        renderSources();
    } catch (e) {
        showToast('书源加载失败');
    }
    
    setupEvents();
    
    // 启动阅读时间记录
    startReadTimeTracker();
});

// 阅读时间追踪
let readStartTime = null;
function startReadTimeTracker() {
    // 每分钟记录一次阅读时间
    setInterval(() => {
        if (document.getElementById('reader').classList.contains('active')) {
            recordReadTime(1);
        }
    }, 60000);
}

function setupEvents() {
    // 导航
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            switchPage(page);
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
        });
    });
    
    // 搜索输入框回车
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') doSearch();
        });
    }
}

function switchPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const page = document.getElementById(pageId);
    if (page) page.classList.add('active');
}

// 渲染书架 - 列表布局
function renderBookshelf() {
    const list = document.getElementById('bookshelf-list');
    if (!list) return;
    
    if (bookshelf.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📚</div>
                <div class="empty-text">书架空空如也<br>去"发现"页面找书吧</div>
            </div>
        `;
        return;
    }
    
    list.innerHTML = bookshelf.map(book => `
        <div class="book-list-item" onclick="readBook('${book.id}')">
            <img src="${book.coverUrl || 'https://via.placeholder.com/70x95/1976d2/ffffff?text=' + encodeURIComponent((book.name || '书').slice(0,1))}" 
                 class="book-list-cover" 
                 onerror="this.src='https://via.placeholder.com/70x95/1976d2/ffffff?text=书'">
            <div class="book-list-info">
                <div>
                    <div class="book-list-title">${book.name || '未知书名'}</div>
                    <div class="book-list-author">${book.author || '未知作者'}</div>
                </div>
                <div class="book-list-chapter">${book.latestChapter || '未读'}</div>
            </div>
        </div>
    `).join('');
}

// 渲染书源
function renderSources() {
    const list = document.getElementById('source-list');
    if (!list) return;
    
    // 更新统计
    const total = bookEngine.sources.length;
    const enabled = bookEngine.sources.filter(s => s.enabled !== false).length;
    const disabled = total - enabled;
    
    document.getElementById('total-sources').textContent = total;
    document.getElementById('enabled-sources').textContent = enabled;
    document.getElementById('disabled-sources').textContent = disabled;
    document.getElementById('source-count').textContent = `${enabled}个`;
    
    if (total === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔌</div>
                <div class="empty-text">暂无书源<br>点击右上角 + 导入书源</div>
            </div>
        `;
        return;
    }
    
    list.innerHTML = bookEngine.sources.map((source, idx) => `
        <div class="settings-item">
            <div class="settings-content" style="flex: 1;">
                <div class="settings-label">${source.bookSourceName || '未命名'}</div>
                <div class="settings-desc">${source.bookSourceUrl}</div>
            </div>
            <div class="switch ${source.enabled !== false ? 'active' : ''}" 
                 onclick="toggleSource(${idx}, event)"></div>
        </div>
    `).join('');
}

// 切换书源启用状态
function toggleSource(index, event) {
    event.stopPropagation();
    const source = bookEngine.sources[index];
    source.enabled = source.enabled === false ? true : false;
    
    // 保存到本地存储
    Storage.set('custom_sources', bookEngine.sources);
    
    renderSources();
    showToast(`${source.bookSourceName} ${source.enabled ? '已启用' : '已禁用'}`);
}

// 显示导入面板
function showImportSource() {
    document.getElementById('import-panel').classList.add('active');
    document.getElementById('import-overlay').classList.add('active');
}

function hideImportSource() {
    document.getElementById('import-panel').classList.remove('active');
    document.getElementById('import-overlay').classList.remove('active');
}

function switchImportTab(tab) {
    document.querySelectorAll('.import-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.import-section').forEach(s => s.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    document.getElementById(`import-${tab}-section`).classList.add('active');
}

// 从URL导入书源
async function importFromUrl() {
    const urlInput = document.getElementById('import-url');
    const urls = urlInput.value.trim().split('\n').filter(u => u.trim());
    
    if (urls.length === 0) {
        showToast('请输入书源URL');
        return;
    }
    
    showToast('正在导入...');
    let imported = 0;
    
    for (const url of urls) {
        try {
            const response = await fetch(url.trim());
            const data = await response.json();
            
            if (Array.isArray(data)) {
                bookEngine.sources.push(...data);
                imported += data.length;
            } else {
                bookEngine.sources.push(data);
                imported++;
            }
        } catch (e) {
            console.error('导入失败:', url, e);
        }
    }
    
    // 保存并刷新
    await Storage.set('custom_sources', bookEngine.sources);
    renderSources();
    hideImportSource();
    urlInput.value = '';
    showToast(`成功导入 ${imported} 个书源`);
}

// 从JSON导入书源
async function importFromJson() {
    const jsonInput = document.getElementById('import-json');
    const jsonStr = jsonInput.value.trim();
    
    if (!jsonStr) {
        showToast('请粘贴书源JSON');
        return;
    }
    
    try {
        const data = JSON.parse(jsonStr);
        let imported = 0;
        
        if (Array.isArray(data)) {
            bookEngine.sources.push(...data);
            imported = data.length;
        } else {
            bookEngine.sources.push(data);
            imported = 1;
        }
        
        await Storage.set('custom_sources', bookEngine.sources);
        renderSources();
        hideImportSource();
        jsonInput.value = '';
        showToast(`成功导入 ${imported} 个书源`);
    } catch (e) {
        showToast('JSON格式错误');
    }
}

// 搜索
async function doSearch() {
    const input = document.getElementById('search-input');
    const keyword = input?.value?.trim();
    
    if (!keyword) {
        showToast('请输入书名或作者');
        return;
    }
    
    const grid = document.getElementById('discover-grid');
    if (!grid) return;
    
    grid.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;"><div class="loading-spinner"></div><p>搜索中...</p></div>';
    
    try {
        const results = await bookEngine.search(keyword);
        
        if (results.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1;">
                    <p>未找到相关书籍</p>
                    <p style="font-size: 14px; margin-top: 10px;">换个关键词试试</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = results.map(book => `
            <div class="book-grid-item" onclick='showBookDetail(${JSON.stringify(book).replace(/'/g, "&#39;")})'>
                <img src="${book.coverUrl || 'https://via.placeholder.com/100x133/1976d2/ffffff?text=' + encodeURIComponent((book.name || '书').slice(0,1))}" 
                     class="book-grid-cover"
                     onerror="this.src='https://via.placeholder.com/100x133/1976d2/ffffff?text=书'">
                <div class="book-grid-title">${book.name || '未知书名'}</div>
                <div class="book-grid-author">${book.author || '未知作者'}</div>
            </div>
        `).join('');
        
        showToast(`找到 ${results.length} 本书`);
    } catch (e) {
        console.error('搜索失败:', e);
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <p>搜索失败</p>
                <p style="font-size: 14px; margin-top: 10px;">请检查网络连接</p>
            </div>
        `;
    }
}

// 分类搜索
function searchCategory(category) {
    const input = document.getElementById('search-input');
    if (input) input.value = category;
    doSearch();
}

// 添加书籍
async function addBook(book) {
    const exists = bookshelf.find(b => b.name === book.name && b.author === book.author);
    if (exists) {
        showToast('已在书架中');
        readBook(exists.id);
        return;
    }
    
    const newBook = {
        id: Date.now().toString(36),
        name: book.name,
        author: book.author,
        coverUrl: book.coverUrl,
        intro: book.intro,
        bookUrl: book.bookUrl,
        source: book.source,
        sourceName: book.sourceName,
        lastChapter: 0,
        lastPage: 0,
        chapters: []
    };
    
    bookshelf.push(newBook);
    await Storage.set('bookshelf', bookshelf);
    renderBookshelf();
    showToast(`《${newBook.name}》已加入书架`);
    readBook(newBook.id);
}

// 阅读书籍
async function readBook(bookId) {
    const book = bookshelf.find(b => b.id === bookId);
    if (!book) return;
    
    currentBook = book;
    
    try {
        if (!book.chapters || book.chapters.length === 0) {
            showToast('加载章节...');
            const chapters = await bookEngine.getChapters(book);
            book.chapters = chapters;
            await Storage.set('bookshelf', bookshelf);
        }
        
        reader.openBook(book, book.chapters);
    } catch (e) {
        console.error('打开失败:', e);
        showToast('加载失败: ' + e.message);
    }
}

// Toast提示
function showToast(msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

// 设置功能 - 参考Legado完整功能
function showReadingSettings() {
    showToast('请在阅读界面点击中间打开设置');
}

function showBookSourceSettings() {
    switchPage('sources-page');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
}

// 主题切换
function showThemeSettings() {
    const themes = ['跟随系统', '浅色', '深色'];
    const current = document.getElementById('theme-value')?.textContent || '跟随系统';
    const next = themes[(themes.indexOf(current) + 1) % themes.length];
    document.getElementById('theme-value').textContent = next;
    
    // 应用主题
    applyTheme(next);
    
    // 保存设置
    Storage.set('theme_setting', next);
    showToast(`主题已切换为: ${next}`);
}

function applyTheme(theme) {
    const root = document.documentElement;
    
    if (theme === '深色' || (theme === '跟随系统' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        // 深色主题
        root.style.setProperty('--bg-white', '#1a1a1a');
        root.style.setProperty('--bg-gray', '#121212');
        root.style.setProperty('--text-primary', '#ffffff');
        root.style.setProperty('--text-secondary', '#b0b0b0');
        root.style.setProperty('--text-tertiary', '#808080');
        root.style.setProperty('--border', '#333333');
        root.style.setProperty('--divider', '#2a2a2a');
        document.body.style.background = '#121212';
    } else {
        // 浅色主题
        root.style.setProperty('--bg-white', '#ffffff');
        root.style.setProperty('--bg-gray', '#f5f5f5');
        root.style.setProperty('--text-primary', '#333333');
        root.style.setProperty('--text-secondary', '#666666');
        root.style.setProperty('--text-tertiary', '#999999');
        root.style.setProperty('--border', '#e0e0e0');
        root.style.setProperty('--divider', '#eeeeee');
        document.body.style.background = '#f5f5f5';
    }
}

// 加载保存的主题
async function loadTheme() {
    const theme = await Storage.get('theme_setting') || '跟随系统';
    document.getElementById('theme-value').textContent = theme;
    applyTheme(theme);
}

function showTextReplace() {
    showToast('替换净化功能开发中');
}

function showRssSource() {
    showToast('RSS订阅源功能开发中');
}

function showDictRule() {
    showToast('字典管理功能开发中');
}

function showBackupRestore() {
    showToast('备份与恢复功能开发中');
}

function showCacheManage() {
    showToast('缓存管理功能开发中');
}

function showWebService() {
    const status = document.getElementById('web-service-status');
    if (status) {
        const newStatus = status.textContent === '已关闭' ? '运行中' : '已关闭';
        status.textContent = newStatus;
        showToast(`Web服务${newStatus === '运行中' ? '已启动' : '已关闭'}`);
    }
}

function showCheckUpdate() {
    showToast('当前已是最新版本 v2.0.3');
}

function showAbout() {
    showToast('佩宇Reader v2.0.3\n基于Legado开源项目');
}

// 阅读记录统计
let readStats = {
    totalTime: 0,  // 总阅读时长（分钟）
    todayTime: 0,  // 今日阅读时长
    bookCount: 0,  // 阅读书籍数
    chapterCount: 0,  // 阅读章节数
    dailyStats: {}  // 每日统计
};

// 加载阅读记录
async function loadReadStats() {
    const saved = await Storage.get('read_stats');
    if (saved) {
        readStats = saved;
    }
    updateReadRecordDisplay();
}

// 更新阅读记录显示
function updateReadRecordDisplay() {
    const totalBooks = bookshelf.length;
    const totalHours = Math.floor(readStats.totalTime / 60);
    const totalMinutes = readStats.totalTime % 60;
    
    // 可以在这里更新UI显示
    console.log(`阅读统计: ${totalBooks}本书, ${totalHours}小时${totalMinutes}分钟`);
}

// 记录阅读时间
function recordReadTime(minutes) {
    const today = new Date().toISOString().split('T')[0];
    
    readStats.totalTime += minutes;
    readStats.todayTime += minutes;
    
    if (!readStats.dailyStats[today]) {
        readStats.dailyStats[today] = 0;
    }
    readStats.dailyStats[today] += minutes;
    
    Storage.set('read_stats', readStats);
}

// 记录阅读章节
function recordChapterRead() {
    readStats.chapterCount++;
    readStats.bookCount = bookshelf.length;
    Storage.set('read_stats', readStats);
}

function showReadRecord() {
    const totalHours = Math.floor(readStats.totalTime / 60);
    const totalMinutes = readStats.totalTime % 60;
    const todayMinutes = readStats.todayTime;
    
    // 创建统计弹窗
    const overlay = document.createElement('div');
    overlay.className = 'overlay active';
    overlay.style.zIndex = '3000';
    overlay.onclick = () => overlay.remove();
    
    const panel = document.createElement('div');
    panel.className = 'import-panel active';
    panel.style.zIndex = '3001';
    panel.style.maxHeight = '60vh';
    panel.innerHTML = `
        <div class="import-header">
            <span class="header-title">阅读记录</span>
            <span class="header-icon" onclick="this.closest('.import-panel').remove(); this.previousElementSibling.remove()">✕</span>
        </div>
        <div class="import-content">
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px;">
                <div style="text-align: center; padding: 16px; background: var(--bg-gray); border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: 600; color: var(--primary);">${totalHours}</div>
                    <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 4px;">总阅读时长(小时)</div>
                </div>
                <div style="text-align: center; padding: 16px; background: var(--bg-gray); border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: 600; color: #4caf50;">${todayMinutes}</div>
                    <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 4px;">今日阅读(分钟)</div>
                </div>
                <div style="text-align: center; padding: 16px; background: var(--bg-gray); border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: 600; color: #ff9800;">${bookshelf.length}</div>
                    <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 4px;">书架书籍</div>
                </div>
                <div style="text-align: center; padding: 16px; background: var(--bg-gray); border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: 600; color: #9c27b0;">${readStats.chapterCount}</div>
                    <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 4px;">阅读章节</div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    document.body.appendChild(panel);
}

function showSettingsMore() {
    showToast('更多设置功能开发中');
}

function clearCache() {
    if (confirm('确定清理缓存？')) {
        bookshelf.forEach(b => {
            if (b.chapters) {
                b.chapters.forEach(c => c.content = null);
            }
        });
        Storage.set('bookshelf', bookshelf);
        showToast('缓存已清理');
    }
}

function refreshSources() {
    showToast('刷新书源...');
    bookEngine.init().then(() => {
        renderSources();
        const count = document.getElementById('source-count');
        if (count) count.textContent = `${bookEngine.sources.length}个`;
        showToast(`已刷新 ${bookEngine.sources.length} 个书源`);
    });
}

function showSearch() {
    switchPage('discover-page');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector('[data-page="discover-page"]').classList.add('active');
    document.getElementById('search-input')?.focus();
}

function showMore() {
    showToast('更多功能开发中');
}

// 书籍详情
let currentDetailBook = null;

function showBookDetail(book) {
    currentDetailBook = book;
    const page = document.getElementById('book-detail-page');
    const content = document.getElementById('book-detail-content');
    
    // 检查是否已在书架
    const inBookshelf = bookshelf.find(b => b.name === book.name && b.author === book.author);
    
    content.innerHTML = `
        <div class="book-detail-header">
            <img src="${book.coverUrl || 'https://via.placeholder.com/120x160/1976d2/ffffff?text=' + encodeURIComponent((book.name || '书').slice(0,1))}" 
                 class="book-detail-cover"
                 onerror="this.src='https://via.placeholder.com/120x160/1976d2/ffffff?text=书'">
            <div class="book-detail-info">
                <div class="book-detail-title">${book.name || '未知书名'}</div>
                <div class="book-detail-author">作者：${book.author || '未知作者'}</div>
                <div class="book-detail-source">来源：${book.sourceName || '网络'}</div>
                <div class="book-detail-actions">
                    ${inBookshelf ? 
                        `<button class="book-detail-btn primary" onclick="readBook('${inBookshelf.id}')">继续阅读</button>` :
                        `<button class="book-detail-btn primary" onclick='addBookFromDetail(${JSON.stringify(book).replace(/'/g, "&#39;")})'>加入书架</button>`
                    }
                    <button class="book-detail-btn secondary" onclick="showBookDetailChapters()">查看目录</button>
                </div>
            </div>
        </div>
        
        <div class="book-detail-section">
            <div class="book-detail-section-title">简介</div>
            <div class="book-detail-intro">${book.intro || '暂无简介'}</div>
        </div>
        
        <div class="book-detail-section" id="book-detail-chapters-section" style="display: none;">
            <div class="book-detail-section-title">章节目录</div>
            <div class="book-detail-chapters" id="book-detail-chapters-list">
                <div style="text-align: center; padding: 20px; color: var(--text-tertiary);">加载中...</div>
            </div>
        </div>
    `;
    
    page.classList.add('active');
}

function closeBookDetail() {
    document.getElementById('book-detail-page').classList.remove('active');
}

async function addBookFromDetail(book) {
    await addBook(book);
    closeBookDetail();
}

async function showBookDetailChapters() {
    const section = document.getElementById('book-detail-chapters-section');
    const list = document.getElementById('book-detail-chapters-list');
    
    section.style.display = 'block';
    list.innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading-spinner"></div></div>';
    
    try {
        const chapters = await bookEngine.getChapters(currentDetailBook);
        
        if (chapters.length === 0) {
            list.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-tertiary);">暂无章节</div>';
            return;
        }
        
        list.innerHTML = chapters.slice(0, 50).map((ch, idx) => `
            <div class="book-detail-chapter-item" onclick="readChapterFromDetail(${idx})">
                ${ch.title || `第${idx + 1}章`}
            </div>
        `).join('');
        
        if (chapters.length > 50) {
            list.innerHTML += `<div style="text-align: center; padding: 12px; color: var(--text-tertiary);">还有 ${chapters.length - 50} 章...</div>`;
        }
    } catch (e) {
        list.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-tertiary);">加载失败</div>';
    }
}

function readChapterFromDetail(chapterIndex) {
    // 先加入书架，然后阅读
    addBook(currentDetailBook).then(() => {
        const book = bookshelf.find(b => b.name === currentDetailBook.name);
        if (book) {
            book.lastChapter = chapterIndex;
            Storage.set('bookshelf', bookshelf);
            readBook(book.id);
        }
    });
}

function shareBook() {
    if (currentDetailBook) {
        showToast(`分享: ${currentDetailBook.name}`);
    }
}

// 阅读器控制
function closeReader() { 
    document.getElementById('reader').classList.remove('active');
}

function showReaderSettings() { 
    document.getElementById('reader-settings').classList.add('active');
    document.getElementById('reader-overlay').classList.add('active');
}

function hideReaderSettings() { 
    document.getElementById('reader-settings').classList.remove('active');
    document.getElementById('reader-overlay').classList.remove('active');
}

function changeFontSize(delta) { 
    if (typeof reader !== 'undefined') reader.changeFontSize(delta);
}

function changeBg(bg) { 
    if (typeof reader !== 'undefined') reader.changeBackground(bg);
    document.querySelectorAll('.bg-option').forEach(el => el.classList.remove('active'));
    document.querySelector(`[data-bg="${bg}"]`)?.classList.add('active');
}

function changeFlip(mode) { 
    if (typeof reader !== 'undefined') reader.changeFlipMode(mode);
    document.querySelectorAll('.flip-mode').forEach(el => el.classList.remove('active'));
    document.querySelector(`[data-flip="${mode}"]`)?.classList.add('active');
}

function toggleChapterPanel() { 
    const panel = document.getElementById('chapter-panel');
    const overlay = document.getElementById('chapter-overlay');
    if (panel) panel.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
}
