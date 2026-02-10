// 佩宇Reader APP - 核心JavaScript
// 使用 Legado 书源规则

// ==================== 数据存储 ====================
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
            await Capacitor.Plugins.Preferences.set({
                key,
                value: JSON.stringify(value)
            });
        } catch (e) {
            localStorage.setItem(key, JSON.stringify(value));
        }
    }
};

// ==================== 全局状态 ====================
let appData = {
    bookshelf: [],
    sources: [],
    currentBook: null
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
    setupNavigation();
    setupEventListeners();
});

async function initApp() {
    // 加载书架
    appData.bookshelf = await Storage.get('bookshelf') || [];
    renderBookshelf();
    
    // 加载书源
    try {
        await bookSourceEngine.loadSources();
        appData.sources = bookSourceEngine.sources;
        showToast(`已加载 ${appData.sources.length} 个书源`);
    } catch (e) {
        console.error('书源加载失败:', e);
        showToast('书源加载失败，使用默认书源');
    }
    
    renderSources();
}

// ==================== 导航 ====================
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const pageId = item.dataset.page;
            switchPage(pageId);
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function switchPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
}

function setupEventListeners() {
    // 搜索按钮
    document.getElementById('search-btn')?.addEventListener('click', searchBooks);
    
    // 回车搜索
    document.getElementById('search-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchBooks();
    });
    
    // 分类标签
    document.querySelectorAll('.category-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            document.getElementById('search-input').value = tag.textContent;
            searchBooks();
        });
    });
}

// ==================== 书架 ====================
function renderBookshelf() {
    const grid = document.getElementById('bookshelf-grid');
    if (!grid) return;
    
    if (appData.bookshelf.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <div style="font-size: 64px; margin-bottom: 20px;">📚</div>
                <p>书架空空如也</p>
                <p style="font-size: 14px; margin-top: 10px;">去"发现"页面搜索书籍吧</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = appData.bookshelf.map(book => `
        <div class="book-card" onclick="openBook('${book.id}')">
            <img src="${book.coverUrl || 'https://via.placeholder.com/150x200/4a90e2/ffffff?text=' + encodeURIComponent(book.name.slice(0,2))}" 
                 class="book-cover" 
                 alt="${book.name}">
            <div class="book-title">${book.name}</div>
            <div class="book-author">${book.author}</div>
            <div class="book-progress">${book.latestChapter || '未读'}</div>
        </div>
    `).join('');
}

// ==================== 搜索 ====================
async function searchBooks() {
    const keyword = document.getElementById('search-input').value.trim();
    if (!keyword) {
        showToast('请输入搜索关键词');
        return;
    }
    
    showToast('搜索中...');
    const grid = document.getElementById('discover-grid');
    grid.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';
    
    try {
        const results = await bookSourceEngine.search(keyword);
        
        if (results.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1;">
                    <p>未找到相关书籍</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = results.map(book => `
            <div class="book-card" onclick='addToBookshelf(${JSON.stringify(book).replace(/'/g, "&#39;")})'>
                <img src="${book.coverUrl || 'https://via.placeholder.com/150x200/4a90e2/ffffff?text=' + encodeURIComponent(book.name.slice(0,2))}" 
                     class="book-cover" 
                     alt="${book.name}">
                <div class="book-title">${book.name}</div>
                <div class="book-author">${book.author}</div>
                <div class="book-progress" style="color: #27ae60;">来源: ${book.sourceName}</div>
            </div>
        `).join('');
        
        showToast(`找到 ${results.length} 本书`);
    } catch (e) {
        console.error('搜索失败:', e);
        showToast('搜索失败: ' + e.message);
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <p>搜索失败</p>
            </div>
        `;
    }
}

// ==================== 书籍操作 ====================
async function addToBookshelf(book) {
    // 检查是否已存在
    const exists = appData.bookshelf.find(b => b.name === book.name && b.author === book.author);
    if (exists) {
        showToast('书籍已在书架中');
        openBook(exists.id);
        return;
    }
    
    // 生成ID
    book.id = Date.now().toString(36) + Math.random().toString(36).substr(2);
    book.lastChapterIndex = 0;
    book.lastPage = 0;
    
    appData.bookshelf.push(book);
    await Storage.set('bookshelf', appData.bookshelf);
    
    renderBookshelf();
    showToast(`《${book.name}》已添加到书架`);
    
    // 打开书籍
    openBook(book.id);
}

async function openBook(bookId) {
    const book = appData.bookshelf.find(b => b.id === bookId);
    if (!book) return;
    
    appData.currentBook = book;
    showToast('加载中...');
    
    try {
        // 获取章节列表
        let chapters = book.chapters;
        if (!chapters || chapters.length === 0) {
            chapters = await bookSourceEngine.getChapterList(book);
            book.chapters = chapters;
            await Storage.set('bookshelf', appData.bookshelf);
        }
        
        // 打开阅读器
        reader.openBook(book, chapters);
    } catch (e) {
        console.error('打开书籍失败:', e);
        showToast('加载失败: ' + e.message);
    }
}

// ==================== 书源管理 ====================
function renderSources() {
    const list = document.getElementById('source-list');
    if (!list) return;
    
    if (appData.sources.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <p>暂无书源</p>
            </div>
        `;
        return;
    }
    
    list.innerHTML = `
        <div style="background: var(--bg-card); border-radius: 12px; padding: 15px; margin-bottom: 15px;">
            <p style="color: var(--text-secondary); font-size: 14px;">
                共 ${appData.sources.length} 个书源
            </p>
        </div>
    ` + appData.sources.slice(0, 50).map((source, idx) => `
        <div class="source-item">
            <div class="source-info">
                <h3>${source.bookSourceName || '未命名'}</h3>
                <p>${source.bookSourceUrl}</p>
            </div>
            <div class="source-toggle active"></div>
        </div>
    `).join('');
}

// ==================== 工具函数 ====================
function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

// 保存阅读进度
window.saveBookProgress = async function(book) {
    const idx = appData.bookshelf.findIndex(b => b.id === book.id);
    if (idx >= 0) {
        appData.bookshelf[idx] = { ...appData.bookshelf[idx], ...book };
        await Storage.set('bookshelf', appData.bookshelf);
    }
};

// 返回书架
window.showBookshelf = function() {
    switchPage('bookshelf-page');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector('[data-page="bookshelf-page"]').classList.add('active');
    renderBookshelf();
};

// ==================== 设置功能 ====================
function showReadingSettings() {
    showToast('阅读设置请在阅读界面中点击屏幕中间打开');
}

function clearCache() {
    if (confirm('确定要清理缓存吗？这将清除所有已下载的章节内容。')) {
        appData.bookshelf.forEach(book => {
            if (book.chapters) {
                book.chapters.forEach(ch => {
                    ch.content = null;
                });
            }
        });
        Storage.set('bookshelf', appData.bookshelf);
        showToast('缓存已清理');
    }
}

// 阅读器设置（兼容旧版）
function showReaderSettings() {
    reader.showMenu();
}

function hideReaderSettings() {
    reader.hideMenu();
}

function changeFontSize(delta) {
    reader.changeFontSize(delta);
}

function changeBg(bg) {
    reader.changeBackground(bg);
}

function changeFlip(flip) {
    reader.changeFlipMode(flip);
}

function closeReader() {
    reader.close();
}

function toggleChapterList() {
    const panel = document.getElementById('chapter-panel');
    if (panel) {
        panel.classList.toggle('active');
    }
}

function prevChapter() {
    reader.prevPage();
}

function nextChapter() {
    reader.nextPage();
}
