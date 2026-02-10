// 佩宇Reader APP - 核心JavaScript
// 支持Capacitor原生功能

// ==================== 数据存储 ====================
const Storage = {
    get: async (key) => {
        try {
            const { value } = await Capacitor.Plugins.Preferences.get({ key });
            return value ? JSON.parse(value) : null;
        } catch (e) {
            // 降级到localStorage
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
    },
    remove: async (key) => {
        try {
            await Capacitor.Plugins.Preferences.remove({ key });
        } catch (e) {
            localStorage.removeItem(key);
        }
    }
};

// ==================== 全局状态 ====================
let appData = {
    bookshelf: [],
    sources: [],
    readingSettings: {
        fontSize: 18,
        background: 'dark',
        flipEffect: 'slide'
    }
};

let currentBook = null;
let chapters = [];
let currentChapter = 0;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
    setupNavigation();
    setupEventListeners();
});

async function initApp() {
    // 加载数据
    const bookshelf = await Storage.get('bookshelf') || [];
    const sources = await Storage.get('sources') || [];
    const readingSettings = await Storage.get('readingSettings');
    
    appData.bookshelf = bookshelf;
    appData.sources = sources;
    if (readingSettings) {
        appData.readingSettings = readingSettings;
    }
    
    // 如果没有书源，加载默认书源
    if (appData.sources.length === 0) {
        await loadDefaultSources();
    }
    
    // 渲染页面
    renderBookshelf();
    renderSources();
    applyReadingSettings();
    
    showToast('佩宇Reader 已启动');
}

async function loadDefaultSources() {
    // 加载内置书源
    try {
        const response = await fetch('book_sources.json');
        const sources = await response.json();
        // 加载全部书源
        appData.sources = sources.map(s => ({
            ...s,
            enabled: true
        }));
        await Storage.set('sources', appData.sources);
        console.log(`已加载 ${appData.sources.length} 个书源`);
    } catch (e) {
        console.error('加载内置书源失败:', e);
        // 备用默认书源
        appData.sources = [
            {
                bookSourceName: "笔趣阁",
                bookSourceUrl: "https://www.biquge.com.cn",
                enabled: true
            }
        ];
        await Storage.set('sources', appData.sources);
    }
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
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
}

function setupEventListeners() {
    // 分类标签
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const parent = tab.parentElement;
            parent.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
        });
    });
}

// ==================== 书架功能 ====================
function renderBookshelf() {
    const grid = document.getElementById('bookshelf-grid');
    const emptyState = document.getElementById('empty-bookshelf');
    
    if (appData.bookshelf.length === 0) {
        grid.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    grid.innerHTML = appData.bookshelf.map(book => `
        <div class="book-card" onclick="openBook('${book.id}')">
            <img src="${book.cover}" class="book-cover" alt="${book.name}" onerror="this.src='https://via.placeholder.com/150x200/4a90e2/ffffff?text=${encodeURIComponent(book.name.slice(0,2))}'">
            <div class="book-title">${book.name}</div>
            <div class="book-author">${book.author}</div>
            <div class="book-progress">${book.progress > 0 ? '已读 ' + Math.round(book.progress) + '%' : '未读'}</div>
        </div>
    `).join('');
}

function showAddBook() {
    switchPage('discover-page');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector('[data-page="discover-page"]').classList.add('active');
}

// ==================== 搜索功能 ====================
async function searchBooks() {
    const keyword = document.getElementById('search-input').value.trim();
    if (!keyword) {
        showToast('请输入搜索关键词');
        return;
    }
    
    showToast(`搜索中... 共${appData.sources.length}个书源`);
    const grid = document.getElementById('discover-grid');
    grid.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';
    
    const results = [];
    
    // 从所有启用的书源搜索
    for (const source of appData.sources.filter(s => s.enabled)) {
        try {
            console.log(`正在搜索书源: ${source.bookSourceName}`);
            const books = await searchFromSource(source, keyword);
            console.log(`书源 ${source.bookSourceName} 返回 ${books.length} 本书`);
            results.push(...books);
        } catch (e) {
            console.error('搜索失败:', source.bookSourceName, e);
        }
    }
    
    if (results.length === 0) {
        // 如果没有结果，显示模拟数据
        const mockResults = getMockSearchResults(keyword);
        grid.innerHTML = mockResults.map(book => `
            <div class="book-card" onclick='addToBookshelf(${JSON.stringify(book)})'>
                <img src="${book.cover}" class="book-cover" alt="${book.name}" onerror="this.src='https://via.placeholder.com/150x200/4a90e2/ffffff?text=${encodeURIComponent(book.name.slice(0,2))}'">
                <div class="book-title">${book.name}</div>
                <div class="book-author">${book.author}</div>
                <div class="book-progress" style="color: #27ae60;">点击添加</div>
            </div>
        `).join('');
        showToast(`显示${mockResults.length}本推荐书籍`);
        return;
    }
    
    grid.innerHTML = results.map(book => `
        <div class="book-card" onclick="addToBookshelf(${JSON.stringify(book).replace(/"/g, '&quot;')})">
            <img src="${book.cover}" class="book-cover" alt="${book.name}" onerror="this.src='https://via.placeholder.com/150x200/4a90e2/ffffff?text=${encodeURIComponent(book.name.slice(0,2))}'">
            <div class="book-title">${book.name}</div>
            <div class="book-author">${book.author}</div>
            <div class="book-progress" style="color: #27ae60;">点击添加</div>
        </div>
    `).join('');
}

async function searchFromSource(source, keyword) {
    // 使用原生HTTP插件
    try {
        const response = await Capacitor.Plugins.Http.request({
            method: 'GET',
            url: `${source.bookSourceUrl}/search?keyword=${encodeURIComponent(keyword)}`,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });
        
        // 解析结果
        const data = JSON.parse(response.data);
        const books = [];
        
        // 根据书源规则解析
        const bookList = data[source.ruleSearch?.bookList?.replace('$.', '')] || data.data || [];
        
        for (const item of bookList.slice(0, 10)) {
            books.push({
                id: Date.now() + Math.random().toString(36),
                name: item[source.ruleSearch?.name] || item.name || '未知书名',
                author: item[source.ruleSearch?.author] || item.author || '未知作者',
                cover: item[source.ruleSearch?.coverUrl] || item.cover || '',
                intro: item[source.ruleSearch?.intro] || item.intro || '',
                source: source.bookSourceName,
                sourceUrl: source.bookSourceUrl,
                bookUrl: item[source.ruleSearch?.bookUrl] || item.bookUrl || '',
                progress: 0,
                chapters: []
            });
        }
        
        return books;
    } catch (e) {
        // 如果原生HTTP失败，返回模拟数据（演示用）
        return getMockSearchResults(keyword);
    }
}

function getMockSearchResults(keyword) {
    // 模拟搜索结果
    const mockBooks = [
        { name: '斗破苍穹', author: '天蚕土豆', cover: 'https://www.biquge.com.cn/files/article/image/1/1235/1235s.jpg', intro: '这里是斗气大陆...' },
        { name: '完美世界', author: '辰东', cover: 'https://www.biquge.com.cn/files/article/image/1/1345/1345s.jpg', intro: '一粒尘可填海...' },
        { name: '遮天', author: '辰东', cover: 'https://www.biquge.com.cn/files/article/image/1/1568/1568s.jpg', intro: '九龙拉棺...' },
        { name: '神墓', author: '辰东', cover: 'https://www.biquge.com.cn/files/article/image/1/1678/1678s.jpg', intro: '穿越了宇宙洪荒...' },
        { name: '凡人修仙传', author: '忘语', cover: 'https://www.biquge.com.cn/files/article/image/1/1898/1898s.jpg', intro: '一个普通山村小子...' }
    ];
    
    return mockBooks
        .filter(b => b.name.includes(keyword) || b.author.includes(keyword))
        .map(b => ({
            id: Date.now() + Math.random().toString(36),
            ...b,
            source: '笔趣阁',
            sourceUrl: 'https://www.biquge.com.cn',
            progress: 0,
            chapters: []
        }));
}

async function addToBookshelf(book) {
    // 检查是否已存在
    const exists = appData.bookshelf.find(b => b.name === book.name && b.author === book.author);
    if (exists) {
        showToast('书籍已在书架中');
        return;
    }
    
    appData.bookshelf.push(book);
    await Storage.set('bookshelf', appData.bookshelf);
    
    renderBookshelf();
    showToast(`《${book.name}》已添加到书架`);
    
    // 切换回书架页面
    switchPage('bookshelf-page');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector('[data-page="bookshelf-page"]').classList.add('active');
}

// ==================== 阅读器功能 ====================
async function openBook(bookId) {
    const book = appData.bookshelf.find(b => b.id === bookId);
    if (!book) return;
    
    showToast('加载章节...');
    
    // 获取章节列表
    let chapters = [];
    if (book.chapters && book.chapters.length > 0) {
        chapters = book.chapters;
    } else {
        chapters = await fetchChapters(book);
        book.chapters = chapters;
        await Storage.set('bookshelf', appData.bookshelf);
    }
    
    // 使用新的阅读器打开书籍
    reader.openBook(book, chapters);
}

async function fetchChapters(book) {
    try {
        // 使用原生HTTP获取章节
        const response = await Capacitor.Plugins.Http.request({
            method: 'GET',
            url: book.bookUrl,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });
        
        // 解析章节（简化版）
        // 实际应该根据书源规则解析HTML
        return parseChaptersFromHTML(response.data);
    } catch (e) {
        // 返回模拟章节
        return Array.from({length: 100}, (_, i) => ({
            id: i + 1,
            title: `第${i + 1}章`,
            url: `${book.bookUrl}/${i + 1}`
        }));
    }
}

function parseChaptersFromHTML(html) {
    // 简化的HTML解析
    const chapters = [];
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    // 尝试查找章节链接
    const links = doc.querySelectorAll('a');
    let id = 1;
    
    for (const link of links) {
        const text = link.textContent.trim();
        if (text.match(/^第[\d一二三四五六七八九十百千]+章/) || text.match(/Chapter\s*\d+/i)) {
            chapters.push({
                id: id++,
                title: text,
                url: link.href
            });
        }
    }
    
    return chapters.length > 0 ? chapters : getDefaultChapters();
}

function getDefaultChapters() {
    return Array.from({length: 100}, (_, i) => ({
        id: i + 1,
        title: `第${i + 1}章`,
        url: ''
    }));
}

function renderChapterList() {
    const list = document.getElementById('chapter-list-content');
    list.innerHTML = chapters.map((ch, idx) => `
        <div class="chapter-item ${idx === currentChapter ? 'active' : ''}" onclick="loadChapter(${idx})">
            ${ch.title}
        </div>
    `).join('');
}

async function loadChapter(idx) {
    if (idx < 0 || idx >= chapters.length) return;
    
    currentChapter = idx;
    const chapter = chapters[idx];
    document.getElementById('reader-title').textContent = chapter.title;
    
    showToast('加载内容...');
    
    const content = await fetchChapterContent(chapter);
    document.getElementById('reader-content').innerHTML = `
        <h2>${chapter.title}</h2>
        <div class="chapter-body">${content}</div>
    `;
    
    // 更新阅读进度
    currentBook.progress = ((idx + 1) / chapters.length) * 100;
    await Storage.set('bookshelf', appData.bookshelf);
    
    // 关闭章节列表
    document.getElementById('chapter-list').classList.remove('active');
    document.getElementById('chapter-overlay').classList.remove('active');
    
    // 滚动到顶部
    document.getElementById('reader-content').scrollTop = 0;
}

async function fetchChapterContent(chapter) {
    if (!chapter.url) {
        return '<p>暂无内容</p>';
    }
    
    try {
        const response = await Capacitor.Plugins.Http.request({
            method: 'GET',
            url: chapter.url,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });
        
        return parseContentFromHTML(response.data);
    } catch (e) {
        return `<p>加载失败，请检查网络连接</p><p>${e.message}</p>`;
    }
}

function parseContentFromHTML(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    // 尝试查找正文内容
    const contentSelectors = ['#content', '.content', '#chapter-content', '.chapter-content', 'article'];
    
    for (const selector of contentSelectors) {
        const element = doc.querySelector(selector);
        if (element) {
            // 清理内容
            let content = element.innerHTML;
            content = content.replace(/<script[^>]*>.*?<\/script>/gi, '');
            content = content.replace(/<style[^>]*>.*?<\/style>/gi, '');
            content = content.replace(/<a[^>]*>.*?<\/a>/gi, '');
            
            // 将<br>转换为<p>
            content = content.replace(/<br\s*\/?>/gi, '</p><p>');
            
            return content;
        }
    }
    
    // 如果没有找到，返回所有段落
    const paragraphs = doc.querySelectorAll('p');
    if (paragraphs.length > 5) {
        return Array.from(paragraphs).map(p => `<p>${p.textContent}</p>`).join('');
    }
    
    return '<p>无法解析章节内容</p>';
}

function prevChapter() {
    if (currentChapter > 0) {
        loadChapter(currentChapter - 1);
    } else {
        showToast('已经是第一章了');
    }
}

function nextChapter() {
    if (currentChapter < chapters.length - 1) {
        loadChapter(currentChapter + 1);
    } else {
        showToast('已经是最后一章了');
    }
}

function closeReader() {
    document.getElementById('reader').classList.remove('active');
    renderBookshelf(); // 更新进度显示
}

function toggleChapterList() {
    document.getElementById('chapter-list').classList.toggle('active');
    document.getElementById('chapter-overlay').classList.toggle('active');
}

// ==================== 阅读设置 ====================
function showReaderSettings() {
    document.getElementById('reader-settings').classList.add('active');
}

function hideReaderSettings() {
    document.getElementById('reader-settings').classList.remove('active');
}

async function changeFontSize(delta) {
    appData.readingSettings.fontSize = Math.max(12, Math.min(32, appData.readingSettings.fontSize + delta));
    document.getElementById('font-size-display').textContent = appData.readingSettings.fontSize + 'px';
    applyReadingSettings();
    await Storage.set('readingSettings', appData.readingSettings);
}

async function changeBg(bg) {
    appData.readingSettings.background = bg;
    document.querySelectorAll('.bg-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector(`[data-bg="${bg}"]`).classList.add('active');
    applyReadingSettings();
    await Storage.set('readingSettings', appData.readingSettings);
}

async function changeFlip(flip) {
    appData.readingSettings.flipEffect = flip;
    document.querySelectorAll('.flip-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector(`[data-flip="${flip}"]`).classList.add('active');
    await Storage.set('readingSettings', appData.readingSettings);
}

function applyReadingSettings() {
    const content = document.getElementById('reader-content');
    const settings = appData.readingSettings;
    
    // 字体大小
    content.style.fontSize = settings.fontSize + 'px';
    document.getElementById('font-size-display').textContent = settings.fontSize + 'px';
    
    // 背景颜色
    const bgColors = {
        dark: { bg: '#1a1a1a', text: '#ccc' },
        light: { bg: '#f5f5f5', text: '#333' },
        sepia: { bg: '#f4ecd8', text: '#5b4636' },
        green: { bg: '#c7edcc', text: '#333' },
        blue: { bg: '#cce8cf', text: '#333' }
    };
    
    const colors = bgColors[settings.background];
    content.style.background = colors.bg;
    content.style.color = colors.text;
    
    // 更新选中状态
    document.querySelectorAll('.bg-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector(`[data-bg="${settings.background}"]`)?.classList.add('active');
    document.querySelectorAll('.flip-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector(`[data-flip="${settings.flipEffect}"]`)?.classList.add('active');
}

// ==================== 书源管理 ====================
function renderSources() {
    const list = document.getElementById('source-list');
    
    if (appData.sources.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 48px; margin-bottom: 15px;">🔌</div>
                <p>暂无书源</p>
            </div>
        `;
        return;
    }
    
    // 添加书源统计
    const enabledCount = appData.sources.filter(s => s.enabled).length;
    
    list.innerHTML = `
        <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 15px;">
            <p style="color: var(--text-secondary); font-size: 14px;">
                共 ${appData.sources.length} 个书源，已启用 ${enabledCount} 个
            </p>
        </div>
    ` + appData.sources.map((source, idx) => `
        <div class="source-item">
            <div class="source-info">
                <h3>${source.bookSourceName || '未命名书源'}</h3>
                <p>${source.bookSourceUrl || '无URL'}</p>
            </div>
            <div class="source-toggle ${source.enabled ? 'active' : ''}" onclick="toggleSource(${idx})"></div>
        </div>
    `).join('');
}

async function toggleSource(idx) {
    appData.sources[idx].enabled = !appData.sources[idx].enabled;
    await Storage.set('sources', appData.sources);
    renderSources();
    showToast(appData.sources[idx].enabled ? '书源已启用' : '书源已禁用');
}

function showImportDialog() {
    document.getElementById('import-modal').classList.add('active');
}

function closeImportDialog() {
    document.getElementById('import-modal').classList.remove('active');
    document.getElementById('source-input').value = '';
}

async function importSource() {
    const input = document.getElementById('source-input').value.trim();
    if (!input) {
        showToast('请输入书源内容');
        return;
    }
    
    try {
        let sources;
        try {
            sources = JSON.parse(input);
        } catch (e) {
            // 尝试解析单个书源
            sources = [JSON.parse(input)];
        }
        
        if (!Array.isArray(sources)) {
            sources = [sources];
        }
        
        let imported = 0;
        for (const source of sources) {
            if (source.bookSourceName && source.bookSourceUrl) {
                // 检查是否已存在
                const exists = appData.sources.find(s => 
                    s.bookSourceUrl === source.bookSourceUrl
                );
                
                if (!exists) {
                    source.enabled = true;
                    appData.sources.push(source);
                    imported++;
                }
            }
        }
        
        await Storage.set('sources', appData.sources);
        renderSources();
        closeImportDialog();
        showToast(`成功导入 ${imported} 个书源`);
        
    } catch (e) {
        showToast('导入失败：' + e.message);
    }
}

// ==================== 工具函数 ====================
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

async function clearCache() {
    if (confirm('确定要清除所有缓存吗？')) {
        // 清除章节内容缓存
        for (const book of appData.bookshelf) {
            book.chapters = [];
        }
        await Storage.set('bookshelf', appData.bookshelf);
        showToast('缓存已清除');
    }
}

function showSearch() {
    switchPage('discover-page');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector('[data-page="discover-page"]').classList.add('active');
    document.getElementById('search-input').focus();
}

function showReadingSettings() {
    showToast('请在阅读器中点击"设置"按钮');
}
