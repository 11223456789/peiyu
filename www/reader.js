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
        
        // TTS (语音合成)
        this.tts = {
            speaking: false,
            paused: false,
            currentUtterance: null,
            rate: 1.0,
            queue: []
        };
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
                        <h4>听书模式</h4>
                        <div class="tts-control">
                            <button id="tts-play" class="tts-btn">▶️ 开始朗读</button>
                            <button id="tts-pause" class="tts-btn" style="display: none;">⏸️ 暂停</button>
                            <button id="tts-stop" class="tts-btn">⏹️ 停止</button>
                        </div>
                        <div class="tts-speed">
                            <span>语速:</span>
                            <input type="range" id="tts-rate" min="0.5" max="2" step="0.1" value="1">
                            <span id="tts-rate-value">1.0x</span>
                        </div>
                    </div>
                    
                    <div class="menu-section">
                        <h4>字体设置</h4>
                        <div class="font-control">
                            <button id="font-decrease">A-</button>
                            <span id="font-size-display">18</span>
                            <button id="font-increase">A+</button>
                        </div>
                        <div class="font-family-control" style="margin-top: 12px;">
                            <span>字体:</span>
                            <select id="font-family" style="margin-left: 8px; padding: 4px 8px; border-radius: 4px; border: 1px solid var(--border);">
                                <option value="system">系统默认</option>
                                <option value="serif">宋体</option>
                                <option value="sans-serif">黑体</option>
                                <option value="monospace">等宽</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="menu-section">
                        <h4>行间距</h4>
                        <div class="line-height-control">
                            <input type="range" id="line-height" min="1.2" max="2.5" step="0.1" value="1.8">
                            <span id="line-height-value">1.8</span>
                        </div>
                    </div>
                    
                    <div class="menu-section">
                        <h4>背景主题</h4>
                        <div class="bg-options">
                            <div class="bg-option" data-bg="dark" style="background: #1a1a1a;"></div>
                            <div class="bg-option" data-bg="light" style="background: #f5f5f5;"></div>
                            <div class="bg-option" data-bg="sepia" style="background: #f4ecd8;"></div>
                            <div class="bg-option" data-bg="green" style="background: #c7edcc;"></div>
                            <div class="bg-option" data-bg="blue" style="background: #e3f2fd;"></div>
                            <div class="bg-option" data-bg="pink" style="background: #fce4ec;"></div>
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
                    
                    <div class="menu-section">
                        <label class="toggle-label">
                            <span>屏幕常亮</span>
                            <input type="checkbox" id="keep-screen-on" checked>
                            <span class="toggle-switch"></span>
                        </label>
                    </div>
                    
                    <div class="menu-section">
                        <label class="toggle-label">
                            <span>自动翻页</span>
                            <input type="checkbox" id="auto-flip">
                            <span class="toggle-switch"></span>
                        </label>
                        <div class="auto-flip-speed" style="margin-top: 8px; display: none;">
                            <span>间隔:</span>
                            <input type="range" id="auto-flip-interval" min="3" max="30" step="1" value="10">
                            <span id="auto-flip-value">10秒</span>
                        </div>
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
        
        // 屏幕常亮
        document.getElementById('keep-screen-on')?.addEventListener('change', (e) => {
            this.settings.keepScreenOn = e.target.checked;
            this.saveSettings();
            this.applyKeepScreenOn();
        });
        
        // 自动翻页
        document.getElementById('auto-flip')?.addEventListener('change', (e) => {
            this.settings.autoFlip = e.target.checked;
            this.saveSettings();
            const speedControl = document.querySelector('.auto-flip-speed');
            if (speedControl) {
                speedControl.style.display = e.target.checked ? 'block' : 'none';
            }
            this.applyAutoFlip();
        });
        
        document.getElementById('auto-flip-interval')?.addEventListener('input', (e) => {
            this.settings.autoFlipInterval = parseInt(e.target.value);
            document.getElementById('auto-flip-value').textContent = e.target.value + '秒';
            this.saveSettings();
            this.applyAutoFlip();
        });
        
        // 字体选择
        document.getElementById('font-family')?.addEventListener('change', (e) => {
            this.settings.fontFamily = e.target.value;
            this.saveSettings();
            this.applyFontFamily();
        });
        
        // 行间距
        document.getElementById('line-height')?.addEventListener('input', (e) => {
            this.settings.lineHeight = parseFloat(e.target.value);
            document.getElementById('line-height-value').textContent = e.target.value;
            this.saveSettings();
            this.applyLineHeight();
        });
        
        // TTS 控制
        document.getElementById('tts-play')?.addEventListener('click', () => this.startTTS());
        document.getElementById('tts-pause')?.addEventListener('click', () => this.pauseTTS());
        document.getElementById('tts-stop')?.addEventListener('click', () => this.stopTTS());
        document.getElementById('tts-rate')?.addEventListener('input', (e) => {
            this.tts.rate = parseFloat(e.target.value);
            document.getElementById('tts-rate-value').textContent = this.tts.rate.toFixed(1) + 'x';
        });
    }
    
    // 应用字体
    applyFontFamily() {
        const fontMap = {
            'system': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            'serif': '"Noto Serif SC", "Source Han Serif SC", "SimSun", serif',
            'sans-serif': '"Noto Sans SC", "Source Han Sans SC", "SimHei", sans-serif',
            'monospace': '"Fira Code", "Source Code Pro", monospace'
        };
        
        if (this.content) {
            this.content.style.fontFamily = fontMap[this.settings.fontFamily] || fontMap['system'];
        }
    }
    
    // 应用行间距
    applyLineHeight() {
        if (this.content) {
            this.content.style.lineHeight = this.settings.lineHeight;
        }
    }
    
    // 应用屏幕常亮
    applyKeepScreenOn() {
        if (this.settings.keepScreenOn) {
            // 使用 Capacitor 插件保持屏幕常亮
            if (window.Capacitor && Capacitor.Plugins.KeepAwake) {
                Capacitor.Plugins.KeepAwake.keepAwake();
            } else {
                // 备用方案：使用 NoSleep.js 或屏幕锁定API
                if ('wakeLock' in navigator) {
                    navigator.wakeLock.request('screen').catch(err => {
                        console.log('屏幕常亮请求失败:', err);
                    });
                }
            }
        } else {
            if (window.Capacitor && Capacitor.Plugins.KeepAwake) {
                Capacitor.Plugins.KeepAwake.allowSleep();
            }
        }
    }
    
    // 应用自动翻页
    applyAutoFlip() {
        if (this.autoFlipTimer) {
            clearInterval(this.autoFlipTimer);
            this.autoFlipTimer = null;
        }
        
        if (this.settings.autoFlip) {
            const interval = (this.settings.autoFlipInterval || 10) * 1000;
            this.autoFlipTimer = setInterval(() => {
                if (!this.tts.speaking) { // 听书时不自动翻页
                    this.nextPage();
                }
            }, interval);
        }
    }
    
    // 开始朗读
    startTTS() {
        if (!window.speechSynthesis) {
            alert('您的设备不支持语音合成');
            return;
        }
        
        if (this.tts.paused) {
            window.speechSynthesis.resume();
            this.tts.paused = false;
            this.updateTTSUI();
            return;
        }
        
        // 获取当前页面内容
        const text = this.pages[this.currentPage] || '';
        if (!text.trim()) return;
        
        // 停止之前的朗读
        window.speechSynthesis.cancel();
        
        // 创建语音合成实例
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'zh-CN';
        utterance.rate = this.tts.rate;
        utterance.pitch = 1;
        
        utterance.onend = () => {
            // 自动翻页并继续朗读
            if (this.currentPage < this.totalPages - 1) {
                this.nextPage();
                setTimeout(() => this.startTTS(), 500);
            } else {
                this.tts.speaking = false;
                this.updateTTSUI();
            }
        };
        
        utterance.onerror = (e) => {
            console.error('TTS错误:', e);
            this.tts.speaking = false;
            this.updateTTSUI();
        };
        
        this.tts.currentUtterance = utterance;
        this.tts.speaking = true;
        this.tts.paused = false;
        
        window.speechSynthesis.speak(utterance);
        this.updateTTSUI();
    }
    
    // 暂停朗读
    pauseTTS() {
        if (window.speechSynthesis && this.tts.speaking) {
            window.speechSynthesis.pause();
            this.tts.paused = true;
            this.updateTTSUI();
        }
    }
    
    // 停止朗读
    stopTTS() {
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        this.tts.speaking = false;
        this.tts.paused = false;
        this.tts.currentUtterance = null;
        this.updateTTSUI();
    }
    
    // 更新TTS UI
    updateTTSUI() {
        const playBtn = document.getElementById('tts-play');
        const pauseBtn = document.getElementById('tts-pause');
        
        if (!playBtn || !pauseBtn) return;
        
        if (this.tts.speaking) {
            if (this.tts.paused) {
                playBtn.style.display = 'inline-block';
                playBtn.textContent = '▶️ 继续';
                pauseBtn.style.display = 'none';
            } else {
                playBtn.style.display = 'none';
                pauseBtn.style.display = 'inline-block';
            }
        } else {
            playBtn.style.display = 'inline-block';
            playBtn.textContent = '▶️ 开始朗读';
            pauseBtn.style.display = 'none';
        }
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
        document.getElementById('volume-key-toggle').checked = this.settings.useVolumeKey !== false;
        document.getElementById('keep-screen-on').checked = this.settings.keepScreenOn !== false;
        document.getElementById('auto-flip').checked = this.settings.autoFlip === true;
        document.getElementById('auto-flip-interval').value = this.settings.autoFlipInterval || 10;
        document.getElementById('auto-flip-value').textContent = (this.settings.autoFlipInterval || 10) + '秒';
        document.getElementById('font-family').value = this.settings.fontFamily || 'system';
        document.getElementById('line-height').value = this.settings.lineHeight || 1.8;
        document.getElementById('line-height-value').textContent = this.settings.lineHeight || 1.8;
        
        // 显示/隐藏自动翻页速度控制
        const speedControl = document.querySelector('.auto-flip-speed');
        if (speedControl) {
            speedControl.style.display = this.settings.autoFlip ? 'block' : 'none';
        }
        
        this.changeBackground(this.settings.background);
        this.changeFlipMode(this.settings.flipMode);
        this.applyFontFamily();
        this.applyLineHeight();
        this.applyKeepScreenOn();
        this.applyAutoFlip();
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
        // 停止朗读
        this.stopTTS();
        
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
