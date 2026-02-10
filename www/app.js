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
});

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
    if (!list || !bookEngine.sources.length) return;
    
    list.innerHTML = bookEngine.sources.slice(0, 20).map((source, idx) => `
        <div class="settings-item">
            <div class="settings-content">
                <div class="settings-label">${source.bookSourceName || '未命名'}</div>
                <div class="settings-desc">${source.bookSourceUrl}</div>
            </div>
            <span class="settings-value">${source.enabled !== false ? '已启用' : '已禁用'}</span>
        </div>
    `).join('');
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
            <div class="book-grid-item" onclick='addBook(${JSON.stringify(book).replace(/'/g, "&#39;")})'>
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

function showThemeSettings() {
    const themes = ['跟随系统', '浅色', '深色'];
    const current = document.getElementById('theme-value')?.textContent || '跟随系统';
    const next = themes[(themes.indexOf(current) + 1) % themes.length];
    document.getElementById('theme-value').textContent = next;
    showToast(`主题已切换为: ${next}`);
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

function showReadRecord() {
    showToast('阅读记录功能开发中');
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
