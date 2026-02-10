// 书源解析引擎 - 参考 Legado 实现
class BookSourceEngine {
    constructor() {
        this.sources = [];
        this.currentSource = null;
    }

    // 加载书源
    async loadSources() {
        try {
            const response = await fetch('book_sources.json');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.sources = await response.json();
            console.log(`[书源引擎] 加载了 ${this.sources.length} 个书源`);
            
            // 过滤掉无效书源
            this.sources = this.sources.filter(s => 
                s.bookSourceUrl && 
                s.ruleSearch && 
                s.bookSourceType === 0 // 只保留文字书源
            );
            
            console.log(`[书源引擎] 有效书源: ${this.sources.length} 个`);
            return this.sources;
        } catch (e) {
            console.error('[书源引擎] 加载失败:', e);
            throw e;
        }
    }

    // 搜索书籍
    async search(keyword, sourceIndex = 0) {
        if (this.sources.length === 0) {
            await this.loadSources();
        }

        console.log(`[搜索] 关键词: ${keyword}, 可用书源: ${this.sources.length}`);

        const results = [];
        const maxSources = Math.min(10, this.sources.length); // 最多用10个书源
        let successCount = 0;
        
        for (let i = 0; i < maxSources; i++) {
            const source = this.sources[i];
            try {
                console.log(`[搜索] [${i+1}/${maxSources}] 书源: ${source.bookSourceName}`);
                console.log(`[搜索] 搜索URL: ${source.searchUrl}`);
                console.log(`[搜索] 规则:`, source.ruleSearch);
                
                const books = await this.searchFromSource(source, keyword);
                console.log(`[搜索] ${source.bookSourceName} 返回 ${books.length} 本书`);
                
                if (books.length > 0) {
                    results.push(...books);
                    successCount++;
                    if (successCount >= 3) break; // 获取3个成功结果就停止
                }
            } catch (e) {
                console.error(`[搜索] ${source.bookSourceName} 失败:`, e.message);
                console.error(`[搜索] 错误详情:`, e);
            }
        }
        
        console.log(`[搜索] 总计找到 ${results.length} 本书`);
        return results;
    }

    // 从单个书源搜索
    async searchFromSource(source, keyword) {
        const rule = source.ruleSearch;
        if (!rule || !source.searchUrl) return [];

        // 构建搜索URL
        let searchUrl = source.searchUrl;
        if (typeof searchUrl === 'string') {
            searchUrl = searchUrl.replace('{{key}}', encodeURIComponent(keyword));
            searchUrl = searchUrl.replace('{{page}}', '1');
        }

        // 解析URL和选项
        let url = searchUrl;
        let options = { method: 'GET', headers: {} };
        
        if (searchUrl.includes(',{')) {
            const parts = searchUrl.split(',{');
            url = parts[0];
            try {
                const optStr = '{' + parts.slice(1).join('{');
                const opt = JSON.parse(optStr);
                if (opt.method) options.method = opt.method;
                if (opt.body) options.body = opt.body;
                if (opt.headers) options.headers = opt.headers;
                if (opt.charset) options.charset = opt.charset;
            } catch (e) {}
        }

        // 确保URL完整
        if (!url.startsWith('http')) {
            url = source.bookSourceUrl + url;
        }

        // 发送请求
        const html = await this.fetchHtml(url, options);
        
        // 解析结果
        return this.parseSearchResults(html, rule, source);
    }

    // 获取HTML
    async fetchHtml(url, options = {}) {
        const defaultHeaders = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        };

        try {
            // 使用 Capacitor HTTP
            if (window.Capacitor && Capacitor.Plugins.Http) {
                const response = await Capacitor.Plugins.Http.request({
                    method: options.method || 'GET',
                    url: url,
                    headers: { ...defaultHeaders, ...options.headers },
                    data: options.body
                });
                return response.data;
            }
        } catch (e) {
            console.warn('[HTTP] Capacitor失败，使用fetch:', e.message);
        }

        // 降级到 fetch
        const response = await fetch(url, {
            method: options.method || 'GET',
            headers: { ...defaultHeaders, ...options.headers },
            body: options.body
        });
        
        return await response.text();
    }

    // 解析搜索结果
    parseSearchResults(html, rule, source) {
        const books = [];
        
        console.log(`[解析] bookList规则: ${rule.bookList}`);
        
        // 尝试解析为JSON
        let json = null;
        try {
            json = JSON.parse(html);
            console.log('[解析] 成功解析为JSON');
        } catch (e) {
            console.log('[解析] 不是JSON，按HTML处理');
        }
        
        // 使用 JSONPath
        if (json && rule.bookList && (rule.bookList.startsWith('$.') || rule.bookList.startsWith('@json:'))) {
            try {
                const path = rule.bookList.replace('@json:', '').replace('$.', '');
                console.log(`[解析] JSONPath: ${path}`);
                const list = this.getJsonPath(json, path);
                console.log(`[解析] 获取到 ${list?.length || 0} 条数据`);
                
                if (Array.isArray(list)) {
                    list.slice(0, 10).forEach((item, idx) => {
                        console.log(`[解析] 处理第${idx+1}本书:`, item);
                        const book = this.parseBookFromJson(item, rule, source);
                        console.log(`[解析] 解析结果:`, book);
                        if (book.name) {
                            books.push(book);
                        }
                    });
                }
            } catch (e) {
                console.error('[JSON解析失败]', e);
            }
        }
        // 使用 XPath
        else if (rule.bookList && rule.bookList.startsWith('//')) {
            const doc = this.parseHTML(html);
            const list = this.evaluateXPath(doc, rule.bookList);
            
            list.forEach((item, index) => {
                if (index >= 10) return;
                
                const book = {
                    name: this.getXPathValue(item, rule.name) || '未知书名',
                    author: this.getXPathValue(item, rule.author) || '未知作者',
                    coverUrl: this.resolveUrl(this.getXPathValue(item, rule.coverUrl), source.bookSourceUrl),
                    intro: this.getXPathValue(item, rule.intro) || '',
                    bookUrl: this.resolveUrl(this.getXPathValue(item, rule.bookUrl), source.bookSourceUrl),
                    latestChapter: this.getXPathValue(item, rule.lastChapter) || '',
                    sourceName: source.bookSourceName,
                    source: source
                };
                
                if (book.name && book.bookUrl) {
                    books.push(book);
                }
            });
        }
        // 使用 CSS 选择器
        else if (rule.bookList && rule.bookList.startsWith('@css:')) {
            const doc = this.parseHTML(html);
            const selector = rule.bookList.replace('@css:', '');
            const list = doc.querySelectorAll(selector);
            
            list.forEach((item, index) => {
                if (index >= 10) return;
                
                const book = this.parseBookFromElement(item, rule, source);
                if (book.name && book.bookUrl) {
                    books.push(book);
                }
            });
        }
        
        return books;
    }

    // 解析书籍详情
    async getBookInfo(book) {
        if (!book.bookUrl) return book;
        
        const source = book.source;
        const html = await this.fetchHtml(book.bookUrl);
        
        const rule = source.ruleBookInfo;
        if (!rule) return book;

        const doc = this.parseHTML(html);
        
        // 更新书籍信息
        if (rule.author) book.author = this.extractValue(doc, html, rule.author) || book.author;
        if (rule.coverUrl) book.coverUrl = this.resolveUrl(this.extractValue(doc, html, rule.coverUrl), source.bookSourceUrl);
        if (rule.intro) book.intro = this.extractValue(doc, html, rule.intro) || book.intro;
        if (rule.lastChapter) book.latestChapter = this.extractValue(doc, html, rule.lastChapter) || book.latestChapter;
        if (rule.tocUrl) book.tocUrl = this.resolveUrl(this.extractValue(doc, html, rule.tocUrl), source.bookSourceUrl);
        
        return book;
    }

    // 获取章节列表
    async getChapterList(book) {
        const source = book.source;
        let tocUrl = book.tocUrl || book.bookUrl;
        
        const html = await this.fetchHtml(tocUrl);
        const rule = source.ruleToc;
        
        if (!rule || !rule.chapterList) return [];

        const chapters = [];
        
        // XPath
        if (rule.chapterList.startsWith('//')) {
            const doc = this.parseHTML(html);
            const list = this.evaluateXPath(doc, rule.chapterList);
            
            list.forEach((item, index) => {
                const chapter = {
                    index: index,
                    title: this.getXPathValue(item, rule.chapterName) || `第${index + 1}章`,
                    url: this.resolveUrl(this.getXPathValue(item, rule.chapterUrl), source.bookSourceUrl),
                    isVip: false
                };
                if (chapter.url) chapters.push(chapter);
            });
        }
        // CSS
        else if (rule.chapterList.startsWith('@css:')) {
            const doc = this.parseHTML(html);
            const selector = rule.chapterList.replace('@css:', '');
            const list = doc.querySelectorAll(selector);
            
            list.forEach((item, index) => {
                const chapter = this.parseChapterFromElement(item, rule, source, index);
                if (chapter.url) chapters.push(chapter);
            });
        }
        
        // 检查是否需要反转
        if (rule.chapterList.startsWith('-')) {
            chapters.reverse();
        }
        
        return chapters;
    }

    // 获取章节内容
    async getChapterContent(chapter, book) {
        const source = book.source;
        const html = await this.fetchHtml(chapter.url);
        const rule = source.ruleContent;
        
        if (!rule || !rule.content) return '内容获取失败';

        let content = '';
        
        // XPath
        if (rule.content.startsWith('//')) {
            const doc = this.parseHTML(html);
            content = this.evaluateXPath(doc, rule.content).map(n => n.textContent).join('\n\n');
        }
        // CSS
        else if (rule.content.startsWith('@css:')) {
            const doc = this.parseHTML(html);
            const selector = rule.content.replace('@css:', '');
            const elements = doc.querySelectorAll(selector);
            content = Array.from(elements).map(el => el.textContent).join('\n\n');
        }
        // 特殊规则 "all" 或 "text"
        else if (rule.content === 'all' || rule.content === 'text') {
            const doc = this.parseHTML(html);
            // 尝试找到正文区域
            const contentEl = doc.querySelector('#content, .content, #chapter-content, .chapter-content, article');
            if (contentEl) {
                content = contentEl.textContent;
            } else {
                // 清理并提取文本
                doc.querySelectorAll('script, style, nav, header, footer').forEach(el => el.remove());
                content = doc.body.textContent;
            }
        }
        // JSONPath
        else if (rule.content.startsWith('$.') || rule.content.startsWith('@json:')) {
            try {
                const json = JSON.parse(html);
                const path = rule.content.replace('@json:', '').replace('$.', '');
                content = this.getJsonPath(json, path);
                if (Array.isArray(content)) content = content.join('\n\n');
            } catch (e) {}
        }
        
        // 清理内容
        return this.cleanContent(content);
    }

    // 辅助方法
    parseHTML(html) {
        const parser = new DOMParser();
        return parser.parseFromString(html, 'text/html');
    }

    evaluateXPath(doc, expression) {
        const results = [];
        try {
            const xpath = document.evaluate(
                expression,
                doc,
                null,
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                null
            );
            for (let i = 0; i < xpath.snapshotLength; i++) {
                results.push(xpath.snapshotItem(i));
            }
        } catch (e) {
            console.error('[XPath错误]', e);
        }
        return results;
    }

    getXPathValue(context, expression) {
        if (!expression) return '';
        try {
            const result = document.evaluate(
                expression,
                context,
                null,
                XPathResult.STRING_TYPE,
                null
            );
            return result.stringValue;
        } catch (e) {
            return '';
        }
    }

    extractValue(doc, html, rule) {
        if (!rule) return '';
        
        // XPath
        if (rule.startsWith('//')) {
            return this.getXPathValue(doc, rule);
        }
        // CSS
        else if (rule.startsWith('@css:')) {
            const selector = rule.replace('@css:', '');
            const el = doc.querySelector(selector);
            return el ? el.textContent : '';
        }
        // 正则
        else if (rule.startsWith('##')) {
            const match = html.match(new RegExp(rule.replace(/##/g, '')));
            return match ? match[1] || match[0] : '';
        }
        
        return '';
    }

    parseBookFromElement(element, rule, source) {
        const getValue = (selector) => {
            if (!selector) return '';
            if (selector.startsWith('@css:')) {
                const sel = selector.replace('@css:', '');
                const el = element.querySelector(sel);
                return el ? el.textContent.trim() : '';
            }
            return '';
        };

        const getAttr = (selector, attr) => {
            if (!selector) return '';
            if (selector.startsWith('@css:')) {
                const sel = selector.replace('@css:', '');
                const el = element.querySelector(sel);
                return el ? el.getAttribute(attr) : '';
            }
            return '';
        };

        return {
            name: getValue(rule.name),
            author: getValue(rule.author),
            coverUrl: this.resolveUrl(getAttr(rule.coverUrl, 'src') || getAttr(rule.coverUrl, 'data-src'), source.bookSourceUrl),
            intro: getValue(rule.intro),
            bookUrl: this.resolveUrl(getAttr(rule.bookUrl, 'href'), source.bookSourceUrl),
            latestChapter: getValue(rule.lastChapter),
            sourceName: source.bookSourceName,
            source: source
        };
    }

    parseBookFromJson(item, rule, source) {
        const getValue = (path) => {
            if (!path) return '';
            
            // 处理 {{}} 模板语法
            if (path.includes('{{') && path.includes('}}')) {
                return path.replace(/\{\{([^}]+)\}\}/g, (match, p1) => {
                    const val = this.getJsonPath(item, p1.replace('$.', ''));
                    return val || '';
                });
            }
            
            // 普通路径
            if (path.startsWith('$.') || path.includes('.')) {
                const cleanPath = path.replace('$.', '');
                return this.getJsonPath(item, cleanPath) || '';
            }
            
            // 直接属性名
            return item?.[path] || '';
        };

        const bookUrl = getValue(rule.bookUrl);
        const resolvedUrl = bookUrl.startsWith('http') ? bookUrl : 
                           bookUrl.startsWith('/') ? source.bookSourceUrl + bookUrl :
                           source.bookSourceUrl + '/' + bookUrl;

        return {
            name: getValue(rule.name),
            author: getValue(rule.author),
            coverUrl: this.resolveUrl(getValue(rule.coverUrl), source.bookSourceUrl),
            intro: getValue(rule.intro),
            bookUrl: resolvedUrl,
            latestChapter: getValue(rule.lastChapter),
            sourceName: source.bookSourceName,
            source: source
        };
    }

    parseChapterFromElement(element, rule, source, index) {
        const getValue = (selector) => {
            if (!selector) return '';
            if (selector.startsWith('@css:')) {
                const sel = selector.replace('@css:', '');
                const el = element.querySelector(sel);
                return el ? el.textContent.trim() : '';
            }
            return element.textContent.trim();
        };

        const getUrl = (selector) => {
            if (!selector) return '';
            if (selector.startsWith('@css:')) {
                const sel = selector.replace('@css:', '');
                const el = element.querySelector(sel);
                return el ? el.getAttribute('href') : element.getAttribute('href');
            }
            return element.getAttribute('href');
        };

        return {
            index: index,
            title: getValue(rule.chapterName) || `第${index + 1}章`,
            url: this.resolveUrl(getUrl(rule.chapterUrl), source.bookSourceUrl),
            isVip: false
        };
    }

    resolveUrl(url, baseUrl) {
        if (!url) return '';
        if (url.startsWith('http')) return url;
        if (url.startsWith('//')) return 'https:' + url;
        
        const base = new URL(baseUrl);
        if (url.startsWith('/')) {
            return base.origin + url;
        }
        return base.origin + '/' + url;
    }

    getJsonPath(obj, path) {
        console.log(`[JSONPath] 解析路径: ${path}`, obj);
        
        // 处理 [*] 语法
        if (path.includes('[*]')) {
            const parts = path.split('[*]');
            let value = obj;
            
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i].replace(/^\./, '').replace(/\.$/, '');
                if (part) {
                    value = value?.[part];
                }
                
                // 如果不是最后一部分，展开数组
                if (i < parts.length - 1 && Array.isArray(value)) {
                    // 继续处理下一层
                    const nextPart = parts[i + 1].replace(/^\./, '');
                    if (nextPart) {
                        value = value.flatMap(item => item?.[nextPart] || []);
                    }
                }
            }
            
            console.log(`[JSONPath] [*] 结果:`, value);
            return value;
        }
        
        // 普通路径
        const keys = path.split('.');
        let value = obj;
        
        for (const key of keys) {
            if (key.includes('[') && key.includes(']')) {
                const arrName = key.split('[')[0];
                const indexMatch = key.match(/\[(\d+|\*)\]/);
                if (indexMatch) {
                    if (indexMatch[1] === '*') {
                        value = value?.[arrName];
                    } else {
                        const index = parseInt(indexMatch[1]);
                        value = value?.[arrName]?.[index];
                    }
                }
            } else {
                value = value?.[key];
            }
            if (value === undefined) break;
        }
        
        console.log(`[JSONPath] 结果:`, value);
        return value;
    }

    cleanContent(content) {
        if (!content) return '';
        
        return content
            .replace(/\s+/g, ' ')
            .replace(/<[^>]+>/g, '')
            .replace(/一秒记住.*精彩阅读。/g, '')
            .replace(/7017k/g, '')
            .replace(/手机阅读.*请访问.*/g, '')
            .replace(/最新网址.*com/g, '')
            .trim();
    }
}

// 创建全局实例
const bookSourceEngine = new BookSourceEngine();
