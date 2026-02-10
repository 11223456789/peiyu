// 佩宇Reader - 简化版核心
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

// 全局状态
let bookshelf = [];
let currentBook = null;

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 加载书架
    bookshelf = await Storage.get('bookshelf') || [];
    renderBookshelf();
    
    // 初始化书源引擎
    try {
        await bookEngine.init();
        showToast(`加载了 ${bookEngine.sources.length} 个书源`);
    } catch (e) {
        showToast('书源加载失败');
    }
    
    // 绑定事件
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
    
    // 搜索
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', doSearch);
    }
    
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

// 渲染书架
function renderBookshelf() {
    const grid = document.getElementById('bookshelf-grid');
    if (!grid) return;
    
    if (bookshelf.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <div style="font-size: 64px; margin-bottom: 20px;">📚</div>
                <p>书架空空如也</p>
                <p style="font-size: 14px; margin-top: 10px;">去"发现"页面搜索书籍吧</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = bookshelf.map(book => `
        <div class="book-card" onclick="readBook('${book.id}')">
            <img src="${book.coverUrl || 'https://via.placeholder.com/150x200/4a90e2/ffffff?text=' + encodeURIComponent(book.name?.slice(0,2) || '书')}" 
                 class="book-cover" 
                 onerror="this.src='https://via.placeholder.com/150x200/4a90e2/ffffff?text=书'">
            <div class="book-title">${book.name || '未知书名'}</div>
            <div class="book-author">${book.author || '未知作者'}</div>
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
            <div class="book-card" onclick='addBook(${JSON.stringify(book).replace(/'/g, "&#39;")})'>
                <img src="${book.coverUrl || 'https://via.placeholder.com/150x200/4a90e2/ffffff?text=' + encodeURIComponent(book.name?.slice(0,2) || '书')}" 
                     class="book-cover"
                     onerror="this.src='https://via.placeholder.com/150x200/4a90e2/ffffff?text=书'">
                <div class="book-title">${book.name || '未知书名'}</div>
                <div class="book-author">${book.author || '未知作者'}</div>
                <div class="book-progress" style="color: #27ae60;">${book.sourceName || '网络'}</div>
            </div>
        `).join('');
        
        showToast(`找到 ${results.length} 本书`);
    } catch (e) {
        console.error('搜索失败:', e);
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <p>搜索失败</p>
                <p style="font-size: 14px; margin-top: 10px;">${e.message}</p>
            </div>
        `;
    }
}

// 添加书籍到书架
async function addBook(book) {
    // 检查是否已存在
    const exists = bookshelf.find(b => b.name === book.name && b.author === book.author);
    if (exists) {
        showToast('已在书架中');
        readBook(exists.id);
        return;
    }
    
    // 创建书籍对象
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
    
    // 自动打开
    readBook(newBook.id);
}

// 阅读书籍
async function readBook(bookId) {
    const book = bookshelf.find(b => b.id === bookId);
    if (!book) return;
    
    currentBook = book;
    showToast('加载中...');
    
    try {
        // 获取章节列表
        if (!book.chapters || book.chapters.length === 0) {
            const chapters = await bookEngine.getChapters(book);
            book.chapters = chapters;
            await Storage.set('bookshelf', bookshelf);
        }
        
        // 打开阅读器
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

// 设置功能
function showReadingSettings() {
    showToast('请在阅读界面点击中间打开设置');
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

// 兼容函数
function closeReader() { reader.close(); }
function showReaderSettings() { reader.showMenu(); }
function hideReaderSettings() { reader.hideMenu(); }
function changeFontSize(d) { reader.changeFontSize(d); }
function changeBg(bg) { reader.changeBackground(bg); }
function changeFlip(f) { reader.changeFlipMode(f); }
function toggleChapterList() { 
    const panel = document.querySelector('.chapter-panel');
    if (panel) panel.classList.toggle('active');
}
