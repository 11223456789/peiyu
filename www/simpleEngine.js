// 简化版书源引擎 - 专注于核心功能
class SimpleBookEngine {
    constructor() {
        this.sources = [];
    }

    async init() {
        try {
            const response = await fetch('book_sources.json');
            const allSources = await response.json();
            
            // 只保留有搜索功能的书源
            this.sources = allSources.filter(s => 
                s.bookSourceType === 0 && 
                s.ruleSearch && 
                s.searchUrl &&
                s.enabled !== false
            );
            
            console.log(`[引擎] 加载 ${this.sources.length} 个有效书源`);
            return this.sources;
        } catch (e) {
            console.error('[引擎] 加载失败:', e);
            return [];
        }
    }

    // 搜索书籍 - 使用单个书源测试
    async search(keyword, maxResults = 20) {
        const results = [];
        
        // 优先使用简单的JSON API书源
        const testSources = this.sources.slice(0, 3);
        
        for (const source of testSources) {
            try {
                const books = await this.searchWithSource(source, keyword);
                results.push(...books);
                if (results.length >= maxResults) break;
            } catch (e) {
                console.log(`[搜索] ${source.bookSourceName} 失败`);
            }
        }
        
        return results.slice(0, maxResults);
    }

    async searchWithSource(source, keyword) {
        // 构建URL
        let url = source.searchUrl;
        if (typeof url === 'string') {
            url = url.replace(/\{\{key\}\}/g, encodeURIComponent(keyword));
            url = url.replace(/\{\{page\}\}/g, '1');
        }

        // 分离URL和选项
        let finalUrl = url;
        let options = { method: 'GET' };
        
        if (url.includes(',{')) {
            const idx = url.indexOf(',{');
            finalUrl = url.substring(0, idx);
            try {
                const optStr = url.substring(idx + 1);
                const opt = JSON.parse(optStr);
                if (opt.method) options.method = opt.method;
                if (opt.body) options.body = opt.body;
                if (opt.headers) options.headers = opt.headers;
            } catch (e) {}
        }

        // 补全URL
        if (!finalUrl.startsWith('http')) {
            finalUrl = source.bookSourceUrl + finalUrl;
        }

        console.log(`[请求] ${source.bookSourceName}: ${finalUrl}`);

        // 发送请求
        const html = await this.httpRequest(finalUrl, options);
        
        // 解析结果
        return this.parseBooks(html, source.ruleSearch, source);
    }

    async httpRequest(url, options = {}) {
        const headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            ...options.headers
        };

        // 尝试使用 Capacitor HTTP
        if (window.Capacitor?.Plugins?.Http) {
            try {
                const res = await Capacitor.Plugins.Http.request({
                    method: options.method || 'GET',
                    url: url,
                    headers: headers,
                    data: options.body
                });
                return res.data;
            } catch (e) {
                console.warn('Capacitor HTTP 失败，使用 fetch');
            }
        }

        // 使用 fetch
        const res = await fetch(url, {
            method: options.method || 'GET',
            headers: headers,
            body: options.body
        });
        return await res.text();
    }

    parseBooks(html, rule, source) {
        const books = [];
        
        // 尝试解析JSON
        let data = null;
        try {
            data = JSON.parse(html);
        } catch (e) {}

        if (data && rule.bookList) {
            // JSONPath 解析
            const list = this.getValueByPath(data, rule.bookList);
            if (Array.isArray(list)) {
                for (const item of list.slice(0, 10)) {
                    const book = this.extractBookFromJson(item, rule, source);
                    if (book.name) books.push(book);
                }
            }
        }

        return books;
    }

    extractBookFromJson(item, rule, source) {
        const getVal = (path) => {
            if (!path) return '';
            
            // 处理 {{}} 模板
            if (path.includes('{{')) {
                return path.replace(/\{\{([^}]+)\}\}/g, (m, p1) => {
                    return this.getValueByPath(item, p1.replace('$.', '')) || '';
                });
            }
            
            // 普通路径
            if (path.startsWith('$.') || path.includes('.')) {
                return this.getValueByPath(item, path.replace('$.', '')) || '';
            }
            
            // 直接属性
            return item[path] || '';
        };

        const bookUrl = getVal(rule.bookUrl);
        
        return {
            name: getVal(rule.name),
            author: getVal(rule.author),
            coverUrl: this.fixUrl(getVal(rule.coverUrl), source.bookSourceUrl),
            intro: getVal(rule.intro),
            bookUrl: bookUrl.startsWith('http') ? bookUrl : source.bookSourceUrl + bookUrl,
            latestChapter: getVal(rule.lastChapter),
            sourceName: source.bookSourceName,
            source: source
        };
    }

    getValueByPath(obj, path) {
        if (!path) return obj;
        
        // 处理 [*] 语法
        if (path.includes('[*]')) {
            const parts = path.split('[*]');
            let result = obj;
            
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i].replace(/^\./, '');
                if (part) {
                    result = result[part];
                }
                if (i < parts.length - 1 && Array.isArray(result)) {
                    // 返回数组供上层处理
                    return result;
                }
            }
            return result;
        }
        
        // 普通路径
        const keys = path.split('.');
        let value = obj;
        for (const key of keys) {
            if (value === null || value === undefined) return null;
            value = value[key];
        }
        return value;
    }

    fixUrl(url, base) {
        if (!url) return '';
        if (url.startsWith('http')) return url;
        if (url.startsWith('//')) return 'https:' + url;
        return base + url;
    }

    // 获取章节列表
    async getChapters(book) {
        const source = book.source;
        const tocUrl = book.tocUrl || book.bookUrl;
        
        const html = await this.httpRequest(tocUrl);
        const rule = source.ruleToc;
        
        if (!rule?.chapterList) return [];

        const chapters = [];
        
        // 尝试JSON
        try {
            const data = JSON.parse(html);
            const list = this.getValueByPath(data, rule.chapterList);
            if (Array.isArray(list)) {
                for (let i = 0; i < list.length; i++) {
                    const item = list[i];
                    chapters.push({
                        index: i,
                        title: this.getValueByPath(item, rule.chapterName.replace('$.', '')) || `第${i+1}章`,
                        url: this.fixUrl(
                            this.getValueByPath(item, rule.chapterUrl.replace('$.', '')) || '',
                            source.bookSourceUrl
                        )
                    });
                }
            }
        } catch (e) {
            console.log('章节解析失败:', e);
        }
        
        return chapters;
    }

    // 获取章节内容
    async getContent(chapter, book) {
        const source = book.source;
        const html = await this.httpRequest(chapter.url);
        const rule = source.ruleContent;
        
        if (!rule?.content) return '内容获取失败';

        try {
            const data = JSON.parse(html);
            let content = this.getValueByPath(data, rule.content.replace('$.', ''));
            if (Array.isArray(content)) content = content.join('\n\n');
            return this.cleanText(content);
        } catch (e) {
            return '内容获取失败';
        }
    }

    cleanText(text) {
        if (!text) return '';
        return text
            .replace(/一秒记住.*精彩阅读。/g, '')
            .replace(/7017k/g, '')
            .replace(/手机阅读.*请访问.*/g, '')
            .trim();
    }
}

// 全局实例
const bookEngine = new SimpleBookEngine();
