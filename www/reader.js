// 佩宇Reader - 核心阅读器模块
// 参考 Legado 阅读实现

class BookReader {
    constructor() {
        this.container = null;
        this.content = null;
        this.currentBook = null;
        this.chapters = [];
        this.currentChapterIndex = 0;
        this.currentPage = 0;
        this.totalPages = 1;
        
        // 阅读设置
        this.settings = {
            fontSize: 18,
            lineHeight: 1.8,
            background: 'dark',
            textColor: '#ccc',
            flipMode: 'slide', // slide, cover, fade, none
            useVolumeKey: true,
            keepScreenOn: true,
            padding: { top: 20, bottom: 20, left: 15, right: 15 }
        };
        
        // 触摸相关
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        
        // 页面内容缓存
        this.pages = [];
    }
    
    // 初始化阅读器
    init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('阅读器容器不存在');
            return;
        }
        
        this.createReaderUI();
        this.bindEvents();
        this.loadSettings();
    }
    
    // 创建阅读器UI
    createReaderUI() {
        this.container.innerHTML = `
            <div id="reader-container" class="reader-container">
                <!-- 顶部栏 -->
                <div id="reader-header" class="reader-header">
                    <button class="reader-btn" id="back-btn">←</button>
                    <span id="chapter-title" class="chapter-title">章节标题</span>
                    <button class="reader-btn" id="menu-btn">☰</button>
                </div>
                
                <!-- 阅读内容区 -->
                <div id="reader-content-wrapper" class="reader-content-wrapper">
                    <div id="reader-content" class="reader-content"></div>
                </div>
                
                <!-- 底部栏 -->
                <div id="reader-footer" class="reader-footer">
                    <span id="page-info">1 / 1</span>
                    <span id="battery-info">🔋 100%</span>
                </div>
                
                <!-- 点击区域 -->
                <div id="click-zones" class="click-zones">
                    <div id="zone-prev" class="zone zone-prev"></div>
                    <div id="zone-menu" class="zone zone-menu"></div>
                    <div id="zone-next" class="zone zone-next"></div>
                </div>
                
                <!-- 菜单面板 -->
                <div id="reader-menu" class="reader-menu">
                    <div class="menu-header">
                        <button id="close-menu">✕</button>
                        <span>阅读设置</span>
                    </div>
                    
                    <div class="menu-section">
                        <h4>字体大小</h4>
                        <div class="font-control">
                            <button id="font-decrease">A-</button>
                            <span id="font-size-display">18</span>
                            <button id="font-increase">A+</button>
                        </div>
                    </div>
                    
                    <div class="menu-section">
                        <h4>背景主题</h4>
                        <div class="bg-options">
                            <div class="bg-option" data-bg="dark" style="background: #1a1a1a;"></div>
                            <div class="bg-option" data-bg="light" style="background: #f5f5f5;"></div>
                            <div class="bg-option" data-bg="sepia" style="background: #f4ecd8;"></div>
                            <div class="bg-option" data-bg="green" style="background: #c7edcc;"></div>
                        </div>
                    </div>
                    
                    <div class="menu-section">
                        <h4>翻页模式</h4>
                        <div class="flip-options">
                            <button class="flip-option" data-flip="slide">滑动</button>
                            <button class="flip-option" data-flip="cover">覆盖</button>
                            <button class="flip-option" data-flip="fade">淡入</button>
                            <button class="flip-option" data-flip="none">无</button>
                        </div>
                    </div>
                    
                    <div class="menu-section">
                        <label class="toggle-label">
                            <span>音量键翻页</span>
                            <input type="checkbox" id="volume-key-toggle" checked>
                            <span class="toggle-switch"></span>
                        </label>
                    </div>
                </div>
                
                <!-- 章节列表 -->
                <div id="chapter-panel" class="chapter-panel">
                    <div class="chapter-header">
                        <h3>章节目录</h3>
                        <button id="close-chapters">✕</button>
                    </div>
                    <div id="chapter-list" class="chapter-list"></div>
                </div>
                
                <!-- 遮罩层 -->
                <div id="overlay" class="overlay"></div>
            </div>
        `;
        
        this.content = document.getElementById('reader-content');
    }
    
    // 绑定事件
    bindEvents() {
        // 点击区域
        const zonePrev = document.getElementById('zone-prev');
        const zoneNext = document.getElementById('zone-next');
        const zoneMenu = document.getElementById('zone-menu');
        
        zonePrev.addEventListener('click', (e) => {
            e.stopPropagation();
            this.prevPage();
        });
        
        zoneNext.addEventListener('click', (e) => {
            e.stopPropagation();
            this.nextPage();
        });
        
        zoneMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showMenu();
        });
        
        // 触摸事件
        this.container.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        this.container.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
        
        // 音量键
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // 菜单按钮
        document.getElementById('back-btn').addEventListener('click', () => this.close());
        document.getElementById('menu-btn').addEventListener('click', () => this.showChapterPanel());
        document.getElementById('close-menu').addEventListener('click', () => this.hideMenu());
        document.getElementById('close-chapters').addEventListener('click', () => this.hideChapterPanel());
        document.getElementById('overlay').addEventListener('click', () => this.hideAllPanels());
        
        // 字体控制
        document.getElementById('font-decrease').addEventListener('click', () => this.changeFontSize(-2));
        document.getElementById('font-increase').addEventListener('click', () => this.changeFontSize(2));
        
        // 背景选项
        document.querySelectorAll('.bg-option').forEach(opt => {
            opt.addEventListener('click', () => this.changeBackground(opt.dataset.bg));
        });
        
        // 翻页模式
        document.querySelectorAll('.flip-option').forEach(opt => {
            opt.addEventListener('click', () => this.changeFlipMode(opt.dataset.flip));
        });
        
        // 音量键开关
        document.getElementById('volume-key-toggle').addEventListener('change', (e) => {
            this.settings.useVolumeKey = e.target.checked;
            this.saveSettings();
        });
    }
    
    // 处理触摸开始
    handleTouchStart(e) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
    }
    
    // 处理触摸结束
    handleTouchEnd(e) {
        this.touchEndX = e.changedTouches[0].clientX;
        this.touchEndY = e.changedTouches[0].clientY;
        
        const diffX = this.touchEndX - this.touchStartX;
        const diffY = this.touchEndY - this.touchStartY;
        
        // 水平滑动翻页
        if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
            if (diffX > 0) {
                this.prevPage();
            } else {
                this.nextPage();
            }
        }
    }
    
    // 处理键盘事件
    handleKeyDown(e) {
        if (!this.settings.useVolumeKey) return;
        
        // 音量键翻页
        if (e.key === 'VolumeUp' || e.key === 'ArrowUp') {
            e.preventDefault();
            this.prevPage();
        } else if (e.key === 'VolumeDown' || e.key === 'ArrowDown' || e.key === 'ArrowRight') {
            e.preventDefault();
            this.nextPage();
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            this.prevPage();
        } else if (e.key === 'Escape') {
            this.close();
        }
    }
    
    // 打开书籍
    async openBook(book, chapters) {
        this.currentBook = book;
        this.chapters = chapters || [];
        this.currentChapterIndex = book.lastChapterIndex || 0;
        this.currentPage = book.lastPage || 0;
        
        document.getElementById('reader-container').classList.add('active');
        
        // 加载章节内容
        await this.loadChapter(this.currentChapterIndex);
        
        // 更新章节列表
        this.updateChapterList();
    }
    
    // 加载章节
    async loadChapter(index) {
        if (index < 0 || index >= this.chapters.length) return;
        
        this.currentChapterIndex = index;
        const chapter = this.chapters[index];
        
        document.getElementById('chapter-title').textContent = chapter.title || `第${index + 1}章`;
        
        // 获取章节内容
        let content = chapter.content;
        if (!content && chapter.url) {
            content = await this.fetchChapterContent(chapter.url);
            chapter.content = content;
        }
        
        // 分页显示
        this.paginateContent(content || '暂无内容');
        this.showPage(0);
        
        // 保存阅读进度
        this.saveProgress();
    }
    
    // 获取章节内容
    async fetchChapterContent(url) {
        try {
            // 使用 Capacitor HTTP
            if (window.Capacitor && Capacitor.Plugins.Http) {
                const response = await Capacitor.Plugins.Http.request({
                    method: 'GET',
                    url: url,
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                });
                return this.parseContent(response.data);
            }
        } catch (e) {
            console.error('获取章节内容失败:', e);
        }
        return '获取内容失败，请检查网络连接';
    }
    
    // 解析内容
    parseContent(html) {
        // 简单的HTML解析
        const div = document.createElement('div');
        div.innerHTML = html;
        
        // 移除脚本和样式
        div.querySelectorAll('script, style, iframe').forEach(el => el.remove());
        
        // 获取文本
        let text = div.textContent || div.innerText || '';
        
        // 清理
        text = text.replace(/\s+/g, ' ').trim();
        
        // 分段
        return text.split(/[。！？.!?]/).filter(p => p.trim()).map(p => p.trim() + '。').join('\n\n');
    }
    
    // 内容分页
    paginateContent(content) {
        this.pages = [];
        
        const wrapper = document.getElementById('reader-content-wrapper');
        const wrapperHeight = wrapper.clientHeight - this.settings.padding.top - this.settings.padding.bottom;
        const wrapperWidth = wrapper.clientWidth - this.settings.padding.left - this.settings.padding.right;
        
        // 临时元素计算
        const tempDiv = document.createElement('div');
        tempDiv.style.cssText = `
            position: absolute;
            visibility: hidden;
            width: ${wrapperWidth}px;
            font-size: ${this.settings.fontSize}px;
            line-height: ${this.settings.lineHeight};
        `;
        document.body.appendChild(tempDiv);
        
        // 按段落分割
        const paragraphs = content.split('\n\n');
        let currentPage = '';
        let currentHeight = 0;
        
        paragraphs.forEach(para => {
            tempDiv.textContent = para;
            const paraHeight = tempDiv.clientHeight;
            
            if (currentHeight + paraHeight > wrapperHeight && currentPage) {
                this.pages.push(currentPage);
                currentPage = para;
                currentHeight = paraHeight;
            } else {
                currentPage += (currentPage ? '\n\n' : '') + para;
                currentHeight += paraHeight;
            }
        });
        
        if (currentPage) {
            this.pages.push(currentPage);
        }
        
        document.body.removeChild(tempDiv);
        
        this.totalPages = this.pages.length || 1;
        this.currentPage = 0;
    }
    
    // 显示指定页
    showPage(pageIndex) {
        if (pageIndex < 0) {
            // 上一章
            if (this.currentChapterIndex > 0) {
                this.loadChapter(this.currentChapterIndex - 1);
            }
            return;
        }
        
        if (pageIndex >= this.totalPages) {
            // 下一章
            if (this.currentChapterIndex < this.chapters.length - 1) {
                this.loadChapter(this.currentChapterIndex + 1);
            }
            return;
        }
        
        this.currentPage = pageIndex;
        this.content.textContent = this.pages[pageIndex] || '';
        this.content.style.fontSize = this.settings.fontSize + 'px';
        this.content.style.lineHeight = this.settings.lineHeight;
        this.content.style.padding = `${this.settings.padding.top}px ${this.settings.padding.right}px ${this.settings.padding.bottom}px ${this.settings.padding.left}px`;
        
        // 更新页码
        document.getElementById('page-info').textContent = `${pageIndex + 1} / ${this.totalPages}`;
        
        // 应用动画
        this.applyFlipAnimation();
    }
    
    // 应用翻页动画
    applyFlipAnimation() {
        const wrapper = document.getElementById('reader-content-wrapper');
        wrapper.style.animation = 'none';
        
        switch (this.settings.flipMode) {
            case 'slide':
                wrapper.style.animation = 'slideIn 0.3s ease';
                break;
            case 'fade':
                wrapper.style.animation = 'fadeIn 0.3s ease';
                break;
            case 'cover':
                wrapper.style.animation = 'coverIn 0.3s ease';
                break;
        }
    }
    
    // 上一页
    prevPage() {
        this.showPage(this.currentPage - 1);
    }
    
    // 下一页
    nextPage() {
        this.showPage(this.currentPage + 1);
    }
    
    // 显示菜单
    showMenu() {
        document.getElementById('reader-menu').classList.add('active');
        document.getElementById('overlay').classList.add('active');
        document.getElementById('reader-header').classList.add('visible');
        document.getElementById('reader-footer').classList.add('visible');
    }
    
    // 隐藏菜单
    hideMenu() {
        document.getElementById('reader-menu').classList.remove('active');
        document.getElementById('overlay').classList.remove('active');
        document.getElementById('reader-header').classList.remove('visible');
        document.getElementById('reader-footer').classList.remove('visible');
    }
    
    // 显示章节面板
    showChapterPanel() {
        document.getElementById('chapter-panel').classList.add('active');
        document.getElementById('overlay').classList.add('active');
    }
    
    // 隐藏章节面板
    hideChapterPanel() {
        document.getElementById('chapter-panel').classList.remove('active');
        document.getElementById('overlay').classList.remove('active');
    }
    
    // 隐藏所有面板
    hideAllPanels() {
        this.hideMenu();
        this.hideChapterPanel();
    }
    
    // 更新章节列表
    updateChapterList() {
        const list = document.getElementById('chapter-list');
        list.innerHTML = this.chapters.map((ch, idx) => `
            <div class="chapter-item ${idx === this.currentChapterIndex ? 'active' : ''}" 
                 onclick="reader.loadChapter(${idx})">
                ${ch.title || `第${idx + 1}章`}
            </div>
        `).join('');
    }
    
    // 改变字体大小
    changeFontSize(delta) {
        this.settings.fontSize = Math.max(12, Math.min(32, this.settings.fontSize + delta));
        document.getElementById('font-size-display').textContent = this.settings.fontSize;
        this.saveSettings();
        
        // 重新分页
        if (this.pages.length > 0) {
            const currentContent = this.pages.join('\n\n');
            this.paginateContent(currentContent);
            this.showPage(Math.min(this.currentPage, this.totalPages - 1));
        }
    }
    
    // 改变背景
    changeBackground(bg) {
        this.settings.background = bg;
        
        const bgMap = {
            dark: { bg: '#1a1a1a', text: '#ccc' },
            light: { bg: '#f5f5f5', text: '#333' },
            sepia: { bg: '#f4ecd8', text: '#5b4636' },
            green: { bg: '#c7edcc', text: '#333' }
        };
        
        const colors = bgMap[bg];
        if (colors) {
            this.container.style.background = colors.bg;
            this.content.style.color = colors.text;
            this.settings.textColor = colors.text;
        }
        
        document.querySelectorAll('.bg-option').forEach(opt => opt.classList.remove('active'));
        document.querySelector(`[data-bg="${bg}"]`)?.classList.add('active');
        
        this.saveSettings();
    }
    
    // 改变翻页模式
    changeFlipMode(mode) {
        this.settings.flipMode = mode;
        
        document.querySelectorAll('.flip-option').forEach(opt => opt.classList.remove('active'));
        document.querySelector(`[data-flip="${mode}"]`)?.classList.add('active');
        
        this.saveSettings();
    }
    
    // 保存设置
    saveSettings() {
        localStorage.setItem('reader_settings', JSON.stringify(this.settings));
    }
    
    // 加载设置
    loadSettings() {
        const saved = localStorage.getItem('reader_settings');
        if (saved) {
            this.settings = { ...this.settings, ...JSON.parse(saved) };
        }
        
        // 应用设置
        document.getElementById('font-size-display').textContent = this.settings.fontSize;
        document.getElementById('volume-key-toggle').checked = this.settings.useVolumeKey;
        this.changeBackground(this.settings.background);
        this.changeFlipMode(this.settings.flipMode);
    }
    
    // 保存阅读进度
    saveProgress() {
        if (this.currentBook) {
            this.currentBook.lastChapterIndex = this.currentChapterIndex;
            this.currentBook.lastPage = this.currentPage;
            this.currentBook.progress = ((this.currentChapterIndex + 1) / this.chapters.length) * 100;
            
            // 触发保存到书架
            if (window.saveBookProgress) {
                window.saveBookProgress(this.currentBook);
            }
        }
    }
    
    // 关闭阅读器
    close() {
        this.saveProgress();
        document.getElementById('reader-container').classList.remove('active');
        
        // 返回书架
        if (window.showBookshelf) {
            window.showBookshelf();
        }
    }
}

// 创建全局阅读器实例
const reader = new BookReader();
