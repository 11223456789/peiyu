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
    
    // 加载 WebDAV 配置
    await loadWebDAVConfig();
    
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
        const readerEl = document.getElementById('reader');
        if (readerEl && readerEl.classList.contains('active')) {
            recordReadTime(1);
        }
    }, 60000);
}

// 图片懒加载
function setupLazyLoading() {
    // 使用 Intersection Observer 实现懒加载
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.dataset.src;
                if (src) {
                    img.src = src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            }
        });
    }, {
        rootMargin: '50px 0px',
        threshold: 0.01
    });
    
    // 观察所有带有 data-src 属性的图片
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
    
    return imageObserver;
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 虚拟列表渲染（用于长列表）
function renderVirtualList(container, items, itemHeight, renderItem, visibleCount = 20) {
    const totalHeight = items.length * itemHeight;
    container.style.height = totalHeight + 'px';
    container.style.position = 'relative';
    
    let visibleItems = [];
    
    function updateVisibleItems() {
        const scrollTop = container.parentElement.scrollTop;
        const startIndex = Math.floor(scrollTop / itemHeight);
        const endIndex = Math.min(startIndex + visibleCount, items.length);
        
        // 移除不可见的项目
        visibleItems.forEach(el => el.remove());
        visibleItems = [];
        
        // 渲染可见项目
        for (let i = startIndex; i < endIndex; i++) {
            const el = renderItem(items[i], i);
            el.style.position = 'absolute';
            el.style.top = (i * itemHeight) + 'px';
            el.style.height = itemHeight + 'px';
            container.appendChild(el);
            visibleItems.push(el);
        }
    }
    
    container.parentElement.addEventListener('scroll', throttle(updateVisibleItems, 16));
    updateVisibleItems();
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

let currentPageId = 'bookshelf-page';

function switchPage(pageId) {
    if (pageId === currentPageId) return;
    
    // 直接切换，不使用动画
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const page = document.getElementById(pageId);
    if (page) page.classList.add('active');
    
    currentPageId = pageId;
    
    // 关闭编辑模式
    if (pageId !== 'bookshelf-page') {
        exitBookshelfEditMode();
    }
}

// 渲染书架 - 列表布局
let bookshelfEditMode = false;
let selectedBooks = new Set();

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
    
    list.innerHTML = bookshelf.map((book, index) => `
        <div class="book-list-item ${selectedBooks.has(book.id) ? 'selected' : ''}" 
             data-book-id="${book.id}"
             data-index="${index}"
             onclick="handleBookClick('${book.id}', ${index})"
             oncontextmenu="handleBookLongPress(event, '${book.id}')">
            ${bookshelfEditMode ? `<div class="book-select-checkbox ${selectedBooks.has(book.id) ? 'checked' : ''}"></div>` : ''}
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
            ${bookshelfEditMode ? '' : `
            <div class="book-drag-handle" onclick="event.stopPropagation(); showBookOptions('${book.id}')">
                <span style="color: var(--text-tertiary); font-size: 20px;">⋮</span>
            </div>
            `}
        </div>
    `).join('');
    
    // 添加编辑模式工具栏
    updateBookshelfToolbar();
}

// 处理书籍点击
function handleBookClick(bookId, index) {
    if (bookshelfEditMode) {
        // 编辑模式：切换选择
        if (selectedBooks.has(bookId)) {
            selectedBooks.delete(bookId);
        } else {
            selectedBooks.add(bookId);
        }
        renderBookshelf();
    } else {
        // 正常模式：打开阅读
        readBook(bookId);
    }
}

// 处理长按/右键
function handleBookLongPress(event, bookId) {
    event.preventDefault();
    if (!bookshelfEditMode) {
        showBookOptions(bookId);
    }
}

// 显示书籍选项菜单
let currentOptionsBookId = null;

function showBookOptions(bookId) {
    const book = bookshelf.find(b => b.id === bookId);
    if (!book) return;
    
    currentOptionsBookId = bookId;
    
    const overlay = document.createElement('div');
    overlay.className = 'overlay active';
    overlay.style.zIndex = '3000';
    
    const menu = document.createElement('div');
    menu.className = 'book-options-menu';
    menu.style.cssText = `
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--bg-white);
        border-top-left-radius: 16px;
        border-top-right-radius: 16px;
        z-index: 3001;
        padding: 16px;
    `;
    menu.innerHTML = `
        <div style="text-align: center; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--divider);">
            <div style="font-weight: 600; font-size: 16px;">${(book.name || '未知书名').replace(/</g, '&lt;')}</div>
            <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 4px;">${book.author || '未知作者'}</div>
        </div>
        <div class="book-option-item" id="opt-read" style="padding: 16px; border-bottom: 1px solid var(--divider); cursor: pointer; display: flex; align-items: center; gap: 12px;">
            <span>📖</span> <span>阅读</span>
        </div>
        <div class="book-option-item" id="opt-detail" style="padding: 16px; border-bottom: 1px solid var(--divider); cursor: pointer; display: flex; align-items: center; gap: 12px;">
            <span>ℹ️</span> <span>书籍详情</span>
        </div>
        <div class="book-option-item" id="opt-top" style="padding: 16px; border-bottom: 1px solid var(--divider); cursor: pointer; display: flex; align-items: center; gap: 12px;">
            <span>⬆️</span> <span>置顶</span>
        </div>
        <div class="book-option-item" id="opt-delete" style="padding: 16px; color: #ff5252; cursor: pointer; display: flex; align-items: center; gap: 12px;">
            <span>🗑️</span> <span>删除</span>
        </div>
        <div class="book-option-item" id="opt-cancel" style="padding: 16px; text-align: center; color: var(--text-tertiary); cursor: pointer; margin-top: 8px; border-top: 1px solid var(--divider);">
            取消
        </div>
    `;
    
    // 绑定事件
    menu.querySelector('#opt-read').onclick = () => {
        readBook(currentOptionsBookId);
        closeMenu();
    };
    menu.querySelector('#opt-detail').onclick = () => {
        const b = bookshelf.find(bk => bk.id === currentOptionsBookId);
        if (b) showBookDetail(b);
        closeMenu();
    };
    menu.querySelector('#opt-top').onclick = () => {
        moveBookToTop(currentOptionsBookId);
        closeMenu();
    };
    menu.querySelector('#opt-delete').onclick = () => {
        deleteBook(currentOptionsBookId);
        closeMenu();
    };
    menu.querySelector('#opt-cancel').onclick = closeMenu;
    
    function closeMenu() {
        overlay.remove();
        menu.remove();
        currentOptionsBookId = null;
    }
    
    overlay.onclick = closeMenu;
    
    document.body.appendChild(overlay);
    document.body.appendChild(menu);
}

// 置顶书籍
async function moveBookToTop(bookId) {
    const index = bookshelf.findIndex(b => b.id === bookId);
    if (index > 0) {
        const book = bookshelf.splice(index, 1)[0];
        bookshelf.unshift(book);
        await Storage.set('bookshelf', bookshelf);
        renderBookshelf();
        showToast('已置顶');
    }
}

// 删除书籍
async function deleteBook(bookId) {
    if (!confirm('确定从书架删除这本书？')) return;
    
    bookshelf = bookshelf.filter(b => b.id !== bookId);
    await Storage.set('bookshelf', bookshelf);
    renderBookshelf();
    showToast('已删除');
}

// 批量删除
async function deleteSelectedBooks() {
    if (selectedBooks.size === 0) {
        showToast('请先选择书籍');
        return;
    }
    
    if (!confirm(`确定删除选中的 ${selectedBooks.size} 本书？`)) return;
    
    bookshelf = bookshelf.filter(b => !selectedBooks.has(b.id));
    selectedBooks.clear();
    await Storage.set('bookshelf', bookshelf);
    exitBookshelfEditMode();
    renderBookshelf();
    showToast('已删除');
}

// 进入编辑模式
function enterBookshelfEditMode() {
    bookshelfEditMode = true;
    selectedBooks.clear();
    renderBookshelf();
}

// 退出编辑模式
function exitBookshelfEditMode() {
    bookshelfEditMode = false;
    selectedBooks.clear();
    renderBookshelf();
}

// 更新书架工具栏
function updateBookshelfToolbar() {
    let toolbar = document.getElementById('bookshelf-toolbar');
    
    if (bookshelfEditMode) {
        if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.id = 'bookshelf-toolbar';
            toolbar.style.cssText = `
                position: fixed;
                bottom: 60px;
                left: 0;
                right: 0;
                background: var(--bg-white);
                border-top: 1px solid var(--divider);
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                z-index: 999;
            `;
            document.body.appendChild(toolbar);
        }
        
        toolbar.innerHTML = `
            <span style="color: var(--text-secondary); font-size: 14px;">已选择 ${selectedBooks.size} 本</span>
            <div style="display: flex; gap: 12px;">
                <button onclick="selectAllBooks()" style="padding: 8px 16px; border: none; background: var(--bg-gray); border-radius: 4px; cursor: pointer;">全选</button>
                <button onclick="deleteSelectedBooks()" style="padding: 8px 16px; border: none; background: #ff5252; color: white; border-radius: 4px; cursor: pointer;">删除</button>
                <button onclick="exitBookshelfEditMode()" style="padding: 8px 16px; border: none; background: var(--primary); color: white; border-radius: 4px; cursor: pointer;">完成</button>
            </div>
        `;
        toolbar.style.display = 'flex';
    } else {
        if (toolbar) {
            toolbar.style.display = 'none';
        }
    }
}

// 全选书籍
function selectAllBooks() {
    if (selectedBooks.size === bookshelf.length) {
        selectedBooks.clear();
    } else {
        selectedBooks = new Set(bookshelf.map(b => b.id));
    }
    renderBookshelf();
}

// 渲染书源 - 支持分页显示全部书源
let sourcePageSize = 50;
let sourceCurrentPage = 0;
let filteredSources = [];
let sourceEditMode = false;
let selectedSources = new Set();

function renderSources(page = 0, filter = '') {
    const list = document.getElementById('source-list');
    if (!list) return;
    
    // 更新统计
    const total = bookEngine.sources.length;
    
    // 安全地更新元素
    const totalEl = document.getElementById('total-sources');
    const enabledEl = document.getElementById('enabled-sources');
    const disabledEl = document.getElementById('disabled-sources');
    const countEl = document.getElementById('source-count');
    
    if (totalEl) totalEl.textContent = total;
    if (enabledEl) enabledEl.textContent = total;
    if (disabledEl) disabledEl.textContent = 0;
    if (countEl) countEl.textContent = `${total}个`;
    
    if (total === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔌</div>
                <div class="empty-text">暂无书源<br>点击右上角 + 导入书源</div>
            </div>
        `;
        updateSourceToolbar();
        return;
    }
    
    // 过滤书源
    if (filter) {
        filteredSources = bookEngine.sources.filter(s => 
            (s.bookSourceName || '').toLowerCase().includes(filter.toLowerCase()) ||
            (s.bookSourceUrl || '').toLowerCase().includes(filter.toLowerCase())
        );
    } else {
        filteredSources = bookEngine.sources;
    }
    
    sourceCurrentPage = page;
    const start = page * sourcePageSize;
    const end = start + sourcePageSize;
    const pageSources = filteredSources.slice(start, end);
    
    const html = pageSources.map((source, idx) => {
        const realIdx = bookEngine.sources.indexOf(source);
        const isSelected = selectedSources.has(realIdx);
        
        if (sourceEditMode) {
            // 编辑模式：显示复选框
            return `
            <div class="settings-item ${isSelected ? 'selected' : ''}" style="padding: 12px 16px;" onclick="toggleSourceSelection(${realIdx})">
                <div class="book-select-checkbox ${isSelected ? 'checked' : ''}" style="margin-right: 12px;"></div>
                <div class="settings-content" style="flex: 1; min-width: 0;">
                    <div class="settings-label" style="font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${source.bookSourceName || '未命名'}</div>
                    <div class="settings-desc" style="font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${source.bookSourceUrl}</div>
                </div>
            </div>
            `;
        } else {
            // 普通模式：显示删除按钮
            return `
            <div class="settings-item" style="padding: 12px 16px;">
                <div class="settings-content" style="flex: 1; min-width: 0;">
                    <div class="settings-label" style="font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${source.bookSourceName || '未命名'}</div>
                    <div class="settings-desc" style="font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${source.bookSourceUrl}</div>
                </div>
                <button onclick="deleteSource(${realIdx})" 
                        style="flex-shrink: 0; margin-left: 12px; padding: 6px 12px; background: #ff5252; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer;">
                    删除
                </button>
            </div>
            `;
        }
    }).join('');
    
    // 添加加载更多按钮
    const loadMoreHtml = end < filteredSources.length ? `
        <div class="settings-item" onclick="loadMoreSources()" style="justify-content: center; color: var(--primary); cursor: pointer;">
            <span>加载更多 (${filteredSources.length - end} 个)</span>
        </div>
    ` : '';
    
    if (page === 0) {
        // 添加搜索框和操作按钮
        const searchHtml = `
            <div style="padding: 12px 16px; background: var(--bg-white); border-bottom: 1px solid var(--divider);">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <div style="flex: 1; display: flex; align-items: center; background: var(--bg-gray); border-radius: 20px; padding: 8px 12px;">
                        <span>🔍</span>
                        <input type="text" id="source-search-input" placeholder="搜索书源..." 
                               style="flex: 1; border: none; background: transparent; font-size: 14px; outline: none; margin-left: 8px;"
                               oninput="searchSources(this.value)">
                    </div>
                    ${!sourceEditMode ? `
                    <button onclick="enterSourceEditMode()" style="padding: 8px 12px; background: var(--bg-gray); border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
                        多选
                    </button>
                    <button onclick="deleteAllSources()" style="padding: 8px 12px; background: #ff5252; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
                        清空
                    </button>
                    ` : ''}
                </div>
            </div>
        `;
        list.innerHTML = searchHtml + html + loadMoreHtml;
    } else {
        // 移除旧的加载更多按钮，添加新内容
        const oldLoadMore = list.querySelector('.settings-item:last-child');
        if (oldLoadMore && oldLoadMore.onclick && oldLoadMore.onclick.toString().includes('loadMoreSources')) {
            oldLoadMore.remove();
        }
        list.insertAdjacentHTML('beforeend', html + loadMoreHtml);
    }
    
    updateSourceToolbar();
}

// 进入书源编辑模式
function enterSourceEditMode() {
    sourceEditMode = true;
    selectedSources.clear();
    renderSources();
}

// 退出书源编辑模式
function exitSourceEditMode() {
    sourceEditMode = false;
    selectedSources.clear();
    renderSources();
}

// 切换书源选择
function toggleSourceSelection(index) {
    if (selectedSources.has(index)) {
        selectedSources.delete(index);
    } else {
        selectedSources.add(index);
    }
    renderSources();
}

// 更新书源工具栏
function updateSourceToolbar() {
    let toolbar = document.getElementById('source-toolbar');
    
    if (sourceEditMode) {
        if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.id = 'source-toolbar';
            toolbar.style.cssText = `
                position: fixed;
                bottom: 60px;
                left: 0;
                right: 0;
                background: var(--bg-white);
                border-top: 1px solid var(--divider);
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                z-index: 999;
            `;
            document.body.appendChild(toolbar);
        }
        
        toolbar.innerHTML = `
            <span style="color: var(--text-secondary); font-size: 14px;">已选择 ${selectedSources.size} 个</span>
            <div style="display: flex; gap: 12px;">
                <button onclick="selectAllSources()" style="padding: 8px 16px; border: none; background: var(--bg-gray); border-radius: 4px; cursor: pointer;">全选</button>
                <button onclick="deleteSelectedSources()" style="padding: 8px 16px; border: none; background: #ff5252; color: white; border-radius: 4px; cursor: pointer;">删除</button>
                <button onclick="exitSourceEditMode()" style="padding: 8px 16px; border: none; background: var(--primary); color: white; border-radius: 4px; cursor: pointer;">完成</button>
            </div>
        `;
        toolbar.style.display = 'flex';
    } else {
        if (toolbar) {
            toolbar.style.display = 'none';
        }
    }
}

// 全选书源
function selectAllSources() {
    if (selectedSources.size === bookEngine.sources.length) {
        selectedSources.clear();
    } else {
        selectedSources = new Set(bookEngine.sources.map((_, i) => i));
    }
    renderSources();
}

// 删除选中的书源
async function deleteSelectedSources() {
    if (selectedSources.size === 0) {
        showToast('请先选择书源');
        return;
    }
    
    if (!confirm(`确定删除选中的 ${selectedSources.size} 个书源？`)) return;
    
    // 将索引转换为数组并排序（从大到小）
    const indices = Array.from(selectedSources).sort((a, b) => b - a);
    
    // 删除书源
    indices.forEach(index => {
        bookEngine.sources.splice(index, 1);
    });
    
    selectedSources.clear();
    await Storage.set('custom_sources', bookEngine.sources);
    exitSourceEditMode();
    renderSources();
    showToast('已删除');
}

// 删除所有书源
async function deleteAllSources() {
    if (bookEngine.sources.length === 0) {
        showToast('书源列表为空');
        return;
    }
    
    if (!confirm(`确定删除全部 ${bookEngine.sources.length} 个书源？此操作不可恢复！`)) return;
    
    bookEngine.sources = [];
    await Storage.set('custom_sources', []);
    renderSources();
    showToast('已清空所有书源');
}

// 导入本地TXT文件
function importLocalTxt() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        showToast('正在读取文件...');
        
        try {
            // 读取文件内容
            const text = await file.text();
            console.log('[TXT导入] 文件大小:', file.size, '字符数:', text.length);
            
            // 生成书籍信息
            const bookId = 'local_' + Date.now();
            const bookName = file.name.replace('.txt', '');
            
            // 解析章节（简单按行分割）
            const chapters = parseTxtChapters(text);
            
            // 创建书籍对象
            const book = {
                id: bookId,
                name: bookName,
                author: '本地导入',
                coverUrl: '',
                intro: `本地导入的TXT文件，共${chapters.length}章`,
                bookUrl: 'local://' + bookId,
                tocUrl: 'local://' + bookId,
                sourceUrl: 'local',
                sourceName: '本地文件',
                latestChapter: chapters.length > 0 ? chapters[chapters.length - 1].title : '',
                isLocal: true,
                chapters: chapters,
                lastChapter: 0,
                lastReadTime: Date.now()
            };
            
            // 保存到本地存储
            await Storage.set('book_' + bookId, book);
            
            // 添加到书架
            bookshelf.unshift(book);
            await Storage.set('bookshelf', bookshelf);
            
            renderBookshelf();
            showToast(`✅ 成功导入《${bookName}》`);
            
        } catch (err) {
            console.error('[TXT导入] 失败:', err);
            showToast('❌ 导入失败: ' + err.message);
        }
    };
    input.click();
}

// 解析TXT章节
function parseTxtChapters(text) {
    const chapters = [];
    const lines = text.split('\n');
    
    // 尝试按常见章节标题格式识别
    const chapterRegex = /^(第[一二三四五六七八九十百千万亿\d]+章|第[\d]+章|Chapter[\s]*[\d]+|^[\d]+[、\.\s])/i;
    
    let currentChapter = null;
    let chapterIndex = 0;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (!line) continue;
        
        // 检查是否是章节标题
        if (chapterRegex.test(line) || (line.length < 50 && (line.includes('章') || line.includes('节')))) {
            // 保存上一章
            if (currentChapter) {
                chapters.push(currentChapter);
            }
            
            // 创建新章节
            currentChapter = {
                index: chapterIndex++,
                title: line.replace(/\s+/g, ' ').substring(0, 100),
                content: '',
                url: 'local://chapter_' + chapterIndex
            };
        } else if (currentChapter) {
            // 添加到当前章节内容
            currentChapter.content += line + '\n';
        } else {
            // 还没有章节，创建默认第一章
            currentChapter = {
                index: 0,
                title: '正文',
                content: line + '\n',
                url: 'local://chapter_0'
            };
            chapterIndex = 1;
        }
    }
    
    // 保存最后一章
    if (currentChapter) {
        chapters.push(currentChapter);
    }
    
    // 如果没有识别到章节，按固定长度分割
    if (chapters.length === 0 || (chapters.length === 1 && chapters[0].title === '正文')) {
        return splitByLength(text);
    }
    
    return chapters;
}

// 按固定长度分割章节
function splitByLength(text, charsPerChapter = 5000) {
    const chapters = [];
    let index = 0;
    
    for (let i = 0; i < text.length; i += charsPerChapter) {
        const chunk = text.substring(i, i + charsPerChapter);
        chapters.push({
            index: index,
            title: `第${index + 1}章`,
            content: chunk,
            url: 'local://chapter_' + index
        });
        index++;
    }
    
    return chapters;
}

function loadMoreSources() {
    renderSources(sourceCurrentPage + 1, document.getElementById('source-search-input')?.value || '');
}

function searchSources(keyword) {
    renderSources(0, keyword);
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

// 处理导入文件 - Legado格式支持
async function handleImportFile(input) {
    const file = input.files[0];
    if (!file) {
        showToast('请选择文件');
        return;
    }
    
    console.log('[导入] 文件:', file.name, '大小:', file.size, '类型:', file.type);
    showToast('正在读取文件...');
    
    try {
        const text = await file.text();
        console.log('[导入] 文件内容长度:', text.length);
        
        if (!text.trim()) {
            showToast('文件为空');
            return;
        }
        
        // 尝试解析JSON
        let data;
        try {
            data = JSON.parse(text);
        } catch (parseError) {
            console.error('[导入] JSON解析失败:', parseError);
            showToast('❌ JSON格式错误');
            return;
        }
        
        // 解析书源数据
        const sources = parseBookSources(data);
        
        if (sources.length === 0) {
            showToast('❌ 未找到有效的书源');
            return;
        }
        
        // 添加到书源列表
        bookEngine.sources.push(...sources);
        await Storage.set('custom_sources', bookEngine.sources);
        
        renderSources();
        hideImportSource();
        input.value = '';
        
        showToast(`✅ 成功导入 ${sources.length} 个书源`);
        
    } catch (e) {
        console.error('[导入] 失败:', e);
        showToast('❌ 导入失败: ' + e.message);
    }
}

// 解析书源数据 - 支持多种格式
function parseBookSources(data) {
    const sources = [];
    
    // 处理数组格式
    if (Array.isArray(data)) {
        data.forEach((item, index) => {
            const source = normalizeBookSource(item, index);
            if (source) sources.push(source);
        });
    } 
    // 处理单个对象
    else if (data && typeof data === 'object') {
        const source = normalizeBookSource(data, 0);
        if (source) sources.push(source);
    }
    
    return sources;
}

// 标准化书源对象
function normalizeBookSource(data, index) {
    if (!data || typeof data !== 'object') return null;
    
    // 检查是否是有效的书源
    const hasBookSourceUrl = data.bookSourceUrl || data.url || data.sourceUrl;
    const hasBookSourceName = data.bookSourceName || data.sourceName || data.name;
    const hasRuleSearch = data.ruleSearch || data.searchRule;
    
    if (!hasBookSourceUrl && !hasRuleSearch) {
        console.log('[导入] 跳过无效书源:', data);
        return null;
    }
    
    // 标准化书源字段
    const source = {
        bookSourceName: hasBookSourceName || `书源${index + 1}`,
        bookSourceUrl: data.bookSourceUrl || data.url || data.sourceUrl || '',
        bookSourceType: data.bookSourceType || 0,
        bookSourceGroup: data.bookSourceGroup || '',
        bookSourceComment: data.bookSourceComment || '',
        enabled: true,
        enabledExplore: data.enabledExplore !== false,
        
        // 搜索规则
        ruleSearch: data.ruleSearch || data.searchRule || null,
        searchUrl: data.searchUrl || '',
        
        // 目录规则
        ruleToc: data.ruleToc || data.tocRule || null,
        
        // 内容规则
        ruleContent: data.ruleContent || data.contentRule || null,
        
        // 详情规则
        ruleBookInfo: data.ruleBookInfo || data.bookInfoRule || null,
        
        // 发现规则
        ruleExplore: data.ruleExplore || data.exploreRule || null,
        
        // 其他字段
        header: data.header || '',
        weight: data.weight || 0,
        customOrder: data.customOrder || 0
    };
    
    return source;
}

// 删除书源
async function deleteSource(index) {
    if (!confirm('确定删除此书源？')) return;
    
    const source = bookEngine.sources[index];
    bookEngine.sources.splice(index, 1);
    
    await Storage.set('custom_sources', bookEngine.sources);
    renderSources();
    showToast(`已删除: ${source.bookSourceName || '未命名'}`);
}

// 搜索 - 涡轮增压版
let lastSearchResults = [];
let lastSearchKeyword = '';
let isSearching = false;

async function doSearch() {
    const input = document.getElementById('search-input');
    const keyword = input?.value?.trim();
    
    if (!keyword) {
        showToast('请输入书名或作者');
        return;
    }
    
    if (isSearching) {
        showToast('🚀 搜索中，请稍候...');
        return;
    }
    
    isSearching = true;
    lastSearchKeyword = keyword;
    const grid = document.getElementById('discover-grid');
    if (!grid) return;
    
    // 显示涡轮增压搜索中状态
    grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1/-1;">
            <div style="font-size: 48px; margin-bottom: 16px;">🚀</div>
            <p style="font-size: 16px; font-weight: 600; color: var(--primary);">涡轮增压搜索中...</p>
            <p style="font-size: 14px; color: var(--text-secondary); margin-top: 8px;">正在全速搜索「${keyword}」</p>
            <div style="margin-top: 20px; width: 200px; height: 4px; background: var(--divider); border-radius: 2px; overflow: hidden; margin-left: auto; margin-right: auto;">
                <div id="turbo-progress" style="width: 0%; height: 100%; background: linear-gradient(90deg, #ff6b6b, #feca57); transition: width 0.3s;"></div>
            </div>
            <p id="turbo-status" style="font-size: 12px; color: var(--text-tertiary); margin-top: 8px;">准备起飞...</p>
        </div>
    `;
    
    // 更新进度条
    const progressBar = document.getElementById('turbo-progress');
    const statusText = document.getElementById('turbo-status');
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 5;
        if (progress <= 90 && progressBar) {
            progressBar.style.width = progress + '%';
        }
        if (statusText) {
            const statuses = ['准备起飞...', '加速中...', '涡轮增压启动！', '全速搜索中...', '即将到达...'];
            statusText.textContent = statuses[Math.floor(progress / 20)] || '搜索中...';
        }
    }, 100);
    
    try {
        const startTime = Date.now();
        const results = await bookEngine.search(keyword);
        const searchTime = ((Date.now() - startTime) / 1000).toFixed(1);
        
        clearInterval(progressInterval);
        if (progressBar) progressBar.style.width = '100%';
        
        lastSearchResults = results;
        
        if (results.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1;">
                    <div style="font-size: 48px; margin-bottom: 16px;">😔</div>
                    <p>未找到相关书籍</p>
                    <p style="font-size: 14px; margin-top: 10px;">换个关键词试试</p>
                </div>
            `;
            isSearching = false;
            return;
        }
        
        renderSearchResults(results);
        showToast(`🚀 涡轮增压完成！找到 ${results.length} 本书 (${searchTime}秒)`);
    } catch (e) {
        clearInterval(progressInterval);
        console.error('搜索失败:', e);
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                <p>搜索失败</p>
                <p style="font-size: 14px; margin-top: 10px;">请检查网络连接</p>
            </div>
        `;
    } finally {
        isSearching = false;
    }
}

// 渲染搜索结果
function renderSearchResults(results, filterSource = '') {
    const grid = document.getElementById('discover-grid');
    if (!grid) return;
    
    // 过滤结果
    let filteredResults = results;
    if (filterSource) {
        filteredResults = results.filter(book => book.sourceName === filterSource);
    }
    
    // 获取所有书源列表用于过滤
    const sourceMap = new Map();
    results.forEach(book => {
        if (book.sourceName) {
            sourceMap.set(book.sourceName, (sourceMap.get(book.sourceName) || 0) + 1);
        }
    });
    
    // 保存过滤状态
    window._currentFilterSource = filterSource;
    
    // 构建过滤栏HTML
    let filterHtml = '';
    if (sourceMap.size > 0) {
        const sources = Array.from(sourceMap.entries()).sort((a, b) => b[1] - a[1]);
        filterHtml = `
            <div style="grid-column: 1/-1; margin-bottom: 12px;">
                <div id="source-filter-container" style="display: flex; gap: 8px; overflow-x: auto; padding: 4px 0; -webkit-overflow-scrolling: touch;">
                    <div class="source-filter-chip ${!filterSource ? 'active' : ''}" data-filter=""
                         style="flex-shrink: 0; padding: 6px 12px; background: ${!filterSource ? 'var(--primary)' : 'var(--bg-gray)'}; 
                                color: ${!filterSource ? 'white' : 'var(--text-secondary)'}; border-radius: 16px; font-size: 12px; cursor: pointer;">
                        全部 (${results.length})
                    </div>
                    ${sources.map(([source, count]) => `
                        <div class="source-filter-chip ${filterSource === source ? 'active' : ''}" data-filter="${source.replace(/"/g, '&quot;')}"
                             style="flex-shrink: 0; padding: 6px 12px; background: ${filterSource === source ? 'var(--primary)' : 'var(--bg-gray)'}; 
                                    color: ${filterSource === source ? 'white' : 'var(--text-secondary)'}; border-radius: 16px; font-size: 12px; cursor: pointer;
                                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;">
                            ${source} (${count})
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    if (filteredResults.length === 0) {
        grid.innerHTML = filterHtml + `
            <div class="empty-state" style="grid-column: 1/-1;">
                <p>该书源暂无结果</p>
            </div>
        `;
        return;
    }
    
    // 保存搜索结果到全局变量供点击使用
    window._searchResults = filteredResults;
    
    const resultsHtml = filteredResults.map((book, index) => `
        <div class="book-grid-item" data-book-index="${index}">
            <img src="${book.coverUrl || 'https://via.placeholder.com/100x133/1976d2/ffffff?text=' + encodeURIComponent((book.name || '书').slice(0,1))}" 
                 class="book-grid-cover"
                 onerror="this.src='https://via.placeholder.com/100x133/1976d2/ffffff?text=书'">
            <div class="book-grid-title">${(book.name || '未知书名').replace(/</g, '&lt;')}</div>
            <div class="book-grid-author">${book.author || '未知作者'}</div>
            <div style="font-size: 10px; color: var(--text-tertiary); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${book.sourceName || ''}</div>
        </div>
    `).join('');
    
    grid.innerHTML = filterHtml + resultsHtml;
    
    // 绑定过滤芯片点击事件
    const filterContainer = document.getElementById('source-filter-container');
    if (filterContainer) {
        filterContainer.querySelectorAll('.source-filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const filter = chip.dataset.filter || '';
                renderSearchResults(lastSearchResults, filter);
            });
        });
    }
    
    // 绑定书籍点击事件
    grid.querySelectorAll('.book-grid-item').forEach((item, idx) => {
        item.addEventListener('click', () => {
            const book = window._searchResults[idx];
            if (book) showBookDetail(book);
        });
    });
}

// 分类搜索
function searchCategory(category) {
    const input = document.getElementById('search-input');
    if (input) input.value = category;
    doSearch();
}

// 排行榜功能
let currentRanking = 'hot';
let rankingData = {
    hot: [],
    new: [],
    finish: [],
    update: []
};

// 切换排行榜
async function switchRanking(type) {
    currentRanking = type;
    
    // 更新标签样式
    document.querySelectorAll('.ranking-tab').forEach(tab => {
        if (tab.dataset.rank === type) {
            tab.classList.add('active');
            tab.style.background = 'var(--primary)';
            tab.style.color = 'white';
        } else {
            tab.classList.remove('active');
            tab.style.background = 'var(--bg-gray)';
            tab.style.color = 'var(--text-secondary)';
        }
    });
    
    // 显示加载中
    const list = document.getElementById('ranking-list');
    if (list) {
        list.innerHTML = `
            <div class="empty-state" style="padding: 20px;">
                <div class="loading-spinner"></div>
                <p>加载中...</p>
            </div>
        `;
    }
    
    // 加载排行榜数据
    await loadRanking(type);
}

// 加载排行榜数据
async function loadRanking(type) {
    // 如果已有缓存数据，直接显示
    if (rankingData[type] && rankingData[type].length > 0) {
        renderRankingList(rankingData[type]);
        return;
    }
    
    // 使用搜索模拟排行榜
    const keywords = {
        hot: ['热门', '畅销', '经典'],
        new: ['新书', '最新'],
        finish: ['完结', '全本'],
        update: ['更新', '连载']
    };
    
    const searchKeyword = keywords[type][0];
    
    try {
        const results = await bookEngine.search(searchKeyword, 10);
        rankingData[type] = results;
        renderRankingList(results);
    } catch (e) {
        const list = document.getElementById('ranking-list');
        if (list) {
            list.innerHTML = `
                <div class="empty-state" style="padding: 20px;">
                    <p>加载失败</p>
                </div>
            `;
        }
    }
}

// 渲染排行榜列表
function renderRankingList(books) {
    const list = document.getElementById('ranking-list');
    if (!list) return;
    
    if (books.length === 0) {
        list.innerHTML = `
            <div class="empty-state" style="padding: 20px;">
                <p>暂无数据</p>
            </div>
        `;
        return;
    }
    
    const rankColors = ['#ff5252', '#ff9800', '#ffc107', '#8bc34a', '#4caf50'];
    
    list.innerHTML = books.slice(0, 10).map((book, idx) => `
        <div class="ranking-item" onclick='showBookDetail(${JSON.stringify(book).replace(/'/g, "&#39;")})' 
             style="display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--divider); cursor: pointer;">
            <div class="ranking-number" style="
                width: 24px; height: 24px; 
                background: ${idx < 3 ? rankColors[idx] : 'var(--bg-gray)'}; 
                color: ${idx < 3 ? 'white' : 'var(--text-secondary)'};
                border-radius: 4px; 
                display: flex; align-items: center; justify-content: center;
                font-size: 12px; font-weight: 600; margin-right: 12px;
            ">${idx + 1}</div>
            <img src="${book.coverUrl || 'https://via.placeholder.com/50x67/1976d2/ffffff?text=' + encodeURIComponent((book.name || '书').slice(0,1))}" 
                 style="width: 40px; height: 53px; object-fit: cover; border-radius: 4px; margin-right: 12px;"
                 onerror="this.src='https://via.placeholder.com/50x67/1976d2/ffffff?text=书'">
            <div style="flex: 1; min-width: 0;">
                <div style="font-size: 14px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${book.name || '未知书名'}</div>
                <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 2px;">${book.author || '未知作者'}</div>
            </div>
        </div>
    `).join('');
}

// 页面加载完成后初始化排行榜
document.addEventListener('DOMContentLoaded', () => {
    // 延迟加载排行榜
    setTimeout(() => {
        if (document.getElementById('ranking-list')) {
            switchRanking('hot');
        }
    }, 1000);
});

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
        // 本地书籍直接打开
        if (book.isLocal) {
            if (book.chapters && book.chapters.length > 0) {
                reader.openBook(book, book.chapters);
            } else {
                showToast('书籍内容为空');
            }
            return;
        }
        
        // 网络书籍需要获取章节
        if (!book.chapters || book.chapters.length === 0) {
            showToast('加载章节...');
            const chapters = await bookEngine.getChapters(book);
            book.chapters = chapters;
            await Storage.set('bookshelf', bookshelf);
        }
        
        if (book.chapters && book.chapters.length > 0) {
            reader.openBook(book, book.chapters);
        } else {
            showToast('无法获取章节，请检查书源');
        }
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
    const isDark = theme === '深色' || (theme === '跟随系统' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    if (isDark) {
        // 深色主题
        root.style.setProperty('--bg-white', '#1e1e1e');
        root.style.setProperty('--bg-gray', '#121212');
        root.style.setProperty('--text-primary', '#e0e0e0');
        root.style.setProperty('--text-secondary', '#a0a0a0');
        root.style.setProperty('--text-tertiary', '#707070');
        root.style.setProperty('--border', '#333333');
        root.style.setProperty('--divider', '#2a2a2a');
        document.body.style.background = '#121212';
        document.body.classList.add('dark-theme');
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
        document.body.classList.remove('dark-theme');
    }
    
    // 应用到所有页面
    document.querySelectorAll('.page').forEach(page => {
        page.style.background = isDark ? '#121212' : '#f5f5f5';
    });
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

// WebDAV 备份与恢复
let webdavConfig = {
    url: '',
    username: '',
    password: '',
    enabled: false
};

// 加载 WebDAV 配置
async function loadWebDAVConfig() {
    const saved = await Storage.get('webdav_config');
    if (saved) {
        webdavConfig = { ...webdavConfig, ...saved };
    }
}

// 保存 WebDAV 配置
async function saveWebDAVConfig(config) {
    webdavConfig = { ...webdavConfig, ...config };
    await Storage.set('webdav_config', webdavConfig);
}

function showBackupRestore() {
    const overlay = document.createElement('div');
    overlay.className = 'overlay active';
    overlay.style.zIndex = '3000';
    
    const panel = document.createElement('div');
    panel.className = 'import-panel active';
    panel.style.zIndex = '3001';
    panel.style.maxHeight = '80vh';
    panel.innerHTML = `
        <div class="import-header">
            <span class="header-title">备份与恢复</span>
            <span class="header-icon" onclick="this.closest('.import-panel').remove(); document.querySelector('.overlay').remove()">✕</span>
        </div>
        <div class="import-content">
            <!-- WebDAV 配置 -->
            <div style="margin-bottom: 20px;">
                <div style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">WebDAV 配置</div>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <input type="text" id="webdav-url" placeholder="WebDAV 服务器地址" 
                           value="${webdavConfig.url || ''}"
                           style="padding: 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 14px;">
                    <input type="text" id="webdav-username" placeholder="用户名" 
                           value="${webdavConfig.username || ''}"
                           style="padding: 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 14px;">
                    <input type="password" id="webdav-password" placeholder="密码" 
                           value="${webdavConfig.password || ''}"
                           style="padding: 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 14px;">
                    <button onclick="testWebDAVConnection()" style="padding: 10px; background: var(--bg-gray); border: none; border-radius: 6px; cursor: pointer;">测试连接</button>
                    <button onclick="saveWebDAVSettings()" style="padding: 10px; background: var(--primary); color: white; border: none; border-radius: 6px; cursor: pointer;">保存配置</button>
                </div>
            </div>
            
            <!-- 备份操作 -->
            <div style="margin-bottom: 20px;">
                <div style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">备份操作</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <button onclick="backupToWebDAV()" style="padding: 12px; background: var(--primary); color: white; border: none; border-radius: 6px; cursor: pointer;">📤 备份到 WebDAV</button>
                    <button onclick="restoreFromWebDAV()" style="padding: 12px; background: var(--bg-gray); border: none; border-radius: 6px; cursor: pointer;">📥 从 WebDAV 恢复</button>
                </div>
            </div>
            
            <!-- 本地备份 -->
            <div>
                <div style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">本地备份</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <button onclick="exportLocalBackup()" style="padding: 12px; background: var(--bg-gray); border: none; border-radius: 6px; cursor: pointer;">📦 导出备份</button>
                    <button onclick="importLocalBackup()" style="padding: 12px; background: var(--bg-gray); border: none; border-radius: 6px; cursor: pointer;">📂 导入备份</button>
                </div>
            </div>
        </div>
    `;
    
    overlay.onclick = () => {
        overlay.remove();
        panel.remove();
    };
    
    document.body.appendChild(overlay);
    document.body.appendChild(panel);
}

// 测试 WebDAV 连接
async function testWebDAVConnection() {
    const url = document.getElementById('webdav-url').value.trim();
    const username = document.getElementById('webdav-username').value.trim();
    const password = document.getElementById('webdav-password').value;
    
    if (!url) {
        showToast('请输入 WebDAV 地址');
        return;
    }
    
    showToast('正在测试连接...');
    
    try {
        // 尝试访问 WebDAV 根目录
        const response = await fetch(url, {
            method: 'PROPFIND',
            headers: {
                'Authorization': 'Basic ' + btoa(username + ':' + password),
                'Content-Type': 'text/xml'
            },
            body: `<?xml version="1.0" encoding="utf-8"?>
                   <propfind xmlns="DAV:">
                       <prop>
                           <resourcetype/>
                       </prop>
                   </propfind>`
        });
        
        if (response.status === 207) {
            showToast('✅ 连接成功');
        } else {
            showToast('❌ 连接失败: ' + response.status);
        }
    } catch (e) {
        showToast('❌ 连接失败: ' + e.message);
    }
}

// 保存 WebDAV 设置
async function saveWebDAVSettings() {
    const url = document.getElementById('webdav-url').value.trim();
    const username = document.getElementById('webdav-username').value.trim();
    const password = document.getElementById('webdav-password').value;
    
    await saveWebDAVConfig({ url, username, password });
    showToast('配置已保存');
}

// 备份到 WebDAV
async function backupToWebDAV() {
    if (!webdavConfig.url) {
        showToast('请先配置 WebDAV');
        return;
    }
    
    showToast('正在备份...');
    
    try {
        // 准备备份数据
        const backupData = {
            version: '2.0.5',
            timestamp: new Date().toISOString(),
            bookshelf: bookshelf,
            readStats: readStats,
            bookSources: bookEngine.sources.filter(s => s.enabled !== false)
        };
        
        const backupJson = JSON.stringify(backupData, null, 2);
        const blob = new Blob([backupJson], { type: 'application/json' });
        
        // 上传到 WebDAV
        const filename = `peiyu_backup_${new Date().toISOString().split('T')[0]}.json`;
        const uploadUrl = webdavConfig.url.replace(/\/$/, '') + '/' + filename;
        
        const response = await fetch(uploadUrl, {
            method: 'PUT',
            headers: {
                'Authorization': 'Basic ' + btoa(webdavConfig.username + ':' + webdavConfig.password),
                'Content-Type': 'application/json'
            },
            body: blob
        });
        
        if (response.ok) {
            showToast('✅ 备份成功: ' + filename);
        } else {
            showToast('❌ 备份失败: ' + response.status);
        }
    } catch (e) {
        showToast('❌ 备份失败: ' + e.message);
    }
}

// 从 WebDAV 恢复
async function restoreFromWebDAV() {
    if (!webdavConfig.url) {
        showToast('请先配置 WebDAV');
        return;
    }
    
    if (!confirm('恢复将覆盖当前数据，确定继续？')) return;
    
    showToast('正在获取备份列表...');
    
    try {
        // 列出 WebDAV 文件
        const response = await fetch(webdavConfig.url, {
            method: 'PROPFIND',
            headers: {
                'Authorization': 'Basic ' + btoa(webdavConfig.username + ':' + webdavConfig.password),
                'Content-Type': 'text/xml',
                'Depth': '1'
            },
            body: `<?xml version="1.0" encoding="utf-8"?>
                   <propfind xmlns="DAV:">
                       <prop>
                           <displayname/>
                           <getlastmodified/>
                       </prop>
                   </propfind>`
        });
        
        if (!response.ok) {
            showToast('❌ 获取备份列表失败');
            return;
        }
        
        // 这里简化处理，直接恢复最新的备份
        // 实际应该让用户选择备份文件
        showToast('请使用本地导入功能恢复备份文件');
    } catch (e) {
        showToast('❌ 恢复失败: ' + e.message);
    }
}

// 导出本地备份
async function exportLocalBackup() {
    const backupData = {
        version: '2.0.5',
        timestamp: new Date().toISOString(),
        bookshelf: bookshelf,
        readStats: readStats,
        bookSources: bookEngine.sources.filter(s => s.enabled !== false)
    };
    
    const backupJson = JSON.stringify(backupData, null, 2);
    const blob = new Blob([backupJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    // 创建下载链接
    const a = document.createElement('a');
    a.href = url;
    a.download = `peiyu_backup_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('✅ 备份已导出');
}

// 导入本地备份
async function importLocalBackup() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        try {
            const text = await file.text();
            const backupData = JSON.parse(text);
            
            if (!confirm('恢复备份将覆盖当前数据，确定继续？')) return;
            
            // 恢复数据
            if (backupData.bookshelf) {
                bookshelf = backupData.bookshelf;
                await Storage.set('bookshelf', bookshelf);
                renderBookshelf();
            }
            
            if (backupData.readStats) {
                readStats = backupData.readStats;
                await Storage.set('read_stats', readStats);
            }
            
            if (backupData.bookSources) {
                const customSources = backupData.bookSources;
                await Storage.set('custom_sources', customSources);
                // 重新加载书源
                await bookEngine.init();
                renderSources();
            }
            
            showToast('✅ 恢复成功');
        } catch (e) {
            showToast('❌ 恢复失败: ' + e.message);
        }
    };
    
    input.click();
}

// 缓存管理
let cacheStats = {
    bookCache: 0,      // 书籍缓存大小
    chapterCache: 0,   // 章节缓存大小
    imageCache: 0,     // 图片缓存大小
    totalCache: 0      // 总缓存大小
};

async function calculateCacheSize() {
    let totalSize = 0;
    let bookSize = 0;
    let chapterSize = 0;
    
    // 计算书架缓存
    for (const book of bookshelf) {
        if (book.chapters) {
            bookSize += JSON.stringify(book).length;
            for (const ch of book.chapters) {
                if (ch.content) {
                    chapterSize += ch.content.length * 2; // UTF-16 编码
                }
            }
        }
    }
    
    cacheStats.bookCache = bookSize;
    cacheStats.chapterCache = chapterSize;
    cacheStats.totalCache = bookSize + chapterSize;
    
    return cacheStats;
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    return (bytes / 1024 / 1024 / 1024).toFixed(1) + ' GB';
}

async function showCacheManage() {
    await calculateCacheSize();
    
    // 创建缓存管理弹窗
    const overlay = document.createElement('div');
    overlay.className = 'overlay active';
    overlay.style.zIndex = '3000';
    overlay.onclick = () => {
        overlay.remove();
        panel.remove();
    };
    
    const panel = document.createElement('div');
    panel.className = 'import-panel active';
    panel.style.zIndex = '3001';
    panel.style.maxHeight = '70vh';
    panel.innerHTML = `
        <div class="import-header">
            <span class="header-title">缓存管理</span>
            <span class="header-icon" onclick="this.closest('.import-panel').remove(); document.querySelector('.overlay').remove()">✕</span>
        </div>
        <div class="import-content">
            <div style="margin-bottom: 20px;">
                <div style="text-align: center; padding: 20px; background: var(--bg-gray); border-radius: 8px; margin-bottom: 16px;">
                    <div style="font-size: 32px; font-weight: 600; color: var(--primary);">${formatSize(cacheStats.totalCache)}</div>
                    <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 4px;">总缓存大小</div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
                    <div style="text-align: center; padding: 12px; background: var(--bg-gray); border-radius: 8px;">
                        <div style="font-size: 16px; font-weight: 600; color: #4caf50;">${formatSize(cacheStats.bookCache)}</div>
                        <div style="font-size: 11px; color: var(--text-tertiary); margin-top: 4px;">书籍数据</div>
                    </div>
                    <div style="text-align: center; padding: 12px; background: var(--bg-gray); border-radius: 8px;">
                        <div style="font-size: 16px; font-weight: 600; color: #ff9800;">${formatSize(cacheStats.chapterCache)}</div>
                        <div style="font-size: 11px; color: var(--text-tertiary); margin-top: 4px;">章节内容</div>
                    </div>
                    <div style="text-align: center; padding: 12px; background: var(--bg-gray); border-radius: 8px;">
                        <div style="font-size: 16px; font-weight: 600; color: #9c27b0;">${bookshelf.length}</div>
                        <div style="font-size: 11px; color: var(--text-tertiary); margin-top: 4px;">缓存书籍</div>
                    </div>
                </div>
            </div>
            
            <div style="margin-bottom: 16px;">
                <div style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">清理选项</div>
                
                <div class="settings-item" onclick="clearChapterCache()" style="cursor: pointer; margin-bottom: 8px; border-radius: 8px; background: var(--bg-gray);">
                    <div class="settings-content">
                        <div class="settings-label">清理章节内容</div>
                        <div class="settings-desc">保留书籍信息，仅删除已下载的章节内容</div>
                    </div>
                    <span class="settings-arrow">›</span>
                </div>
                
                <div class="settings-item" onclick="clearAllCache()" style="cursor: pointer; margin-bottom: 8px; border-radius: 8px; background: var(--bg-gray);">
                    <div class="settings-content">
                        <div class="settings-label">清理全部缓存</div>
                        <div class="settings-desc">删除所有缓存数据，包括书籍信息和章节内容</div>
                    </div>
                    <span class="settings-arrow">›</span>
                </div>
                
                <div class="settings-item" onclick="clearReadRecord()" style="cursor: pointer; border-radius: 8px; background: var(--bg-gray);">
                    <div class="settings-content">
                        <div class="settings-label">清理阅读记录</div>
                        <div class="settings-desc">删除阅读时长统计和阅读历史</div>
                    </div>
                    <span class="settings-arrow">›</span>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    document.body.appendChild(panel);
}

async function clearChapterCache() {
    if (!confirm('确定清理所有章节内容缓存？')) return;
    
    let clearedCount = 0;
    for (const book of bookshelf) {
        if (book.chapters) {
            for (const ch of book.chapters) {
                if (ch.content) {
                    ch.content = null;
                    clearedCount++;
                }
            }
        }
    }
    
    await Storage.set('bookshelf', bookshelf);
    await calculateCacheSize();
    showToast(`已清理 ${clearedCount} 个章节的缓存`);
}

async function clearAllCache() {
    if (!confirm('确定清理全部缓存？这将删除所有书籍数据和章节内容！')) return;
    
    // 清空书架
    bookshelf = [];
    await Storage.set('bookshelf', bookshelf);
    renderBookshelf();
    
    showToast('全部缓存已清理');
}

async function clearReadRecord() {
    if (!confirm('确定清理阅读记录？')) return;
    
    readStats = {
        totalTime: 0,
        todayTime: 0,
        bookCount: 0,
        chapterCount: 0,
        dailyStats: {}
    };
    
    await Storage.set('read_stats', readStats);
    showToast('阅读记录已清理');
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
    
    // 清理简介中的特殊字符
    const cleanIntro = (book.intro || '暂无简介').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    content.innerHTML = `
        <div class="book-detail-header">
            <img src="${book.coverUrl || 'https://via.placeholder.com/120x160/1976d2/ffffff?text=' + encodeURIComponent((book.name || '书').slice(0,1))}" 
                 class="book-detail-cover"
                 onerror="this.src='https://via.placeholder.com/120x160/1976d2/ffffff?text=书'">
            <div class="book-detail-info">
                <div class="book-detail-title">${(book.name || '未知书名').replace(/</g, '&lt;')}</div>
                <div class="book-detail-author">作者：${book.author || '未知作者'}</div>
                <div class="book-detail-source">来源：${book.sourceName || '网络'}</div>
                <div class="book-detail-actions">
                    ${inBookshelf ? 
                        `<button class="book-detail-btn primary" onclick="readBook('${inBookshelf.id}')">继续阅读</button>` :
                        `<button class="book-detail-btn primary" id="detail-add-btn">加入书架</button>`
                    }
                    <button class="book-detail-btn secondary" onclick="showBookDetailChapters()">查看目录</button>
                </div>
            </div>
        </div>
        
        <div class="book-detail-section">
            <div class="book-detail-section-title">简介</div>
            <div class="book-detail-intro">${cleanIntro}</div>
        </div>
        
        <div class="book-detail-section" id="book-detail-chapters-section" style="display: none;">
            <div class="book-detail-section-title">章节目录</div>
            <div class="book-detail-chapters" id="book-detail-chapters-list">
                <div style="text-align: center; padding: 20px; color: var(--text-tertiary);">加载中...</div>
            </div>
        </div>
    `;
    
    // 绑定加入书架按钮事件
    const addBtn = document.getElementById('detail-add-btn');
    if (addBtn) {
        addBtn.onclick = () => addBookFromDetail();
    }
    
    page.classList.add('active');
}

function closeBookDetail() {
    document.getElementById('book-detail-page').classList.remove('active');
}

async function addBookFromDetail() {
    if (currentDetailBook) {
        await addBook(currentDetailBook);
        closeBookDetail();
    }
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
