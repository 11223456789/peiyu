// 简化版书源引擎 - 专注于核心功能
class SimpleBookEngine {
    constructor() {
        this.sources = [];
    }

    async init() {
        try {
            // 先加载内置书源
            const response = await fetch('book_sources.json');
            const allSources = await response.json();
            
            // 加载自定义书源
            let customSources = [];
            try {
                const { value } = await Capacitor.Plugins.Preferences.get({ key: 'custom_sources' });
                if (value) {
                    customSources = JSON.parse(value);
                }
            } catch (e) {}
            
            // 合并书源（自定义优先）
            const builtinSources = allSources.filter(s => 
                s.bookSourceType === 0 && 
                s.ruleSearch && 
                s.searchUrl
            );
            
            this.sources = [...customSources, ...builtinSources];
            
            console.log(`[引擎] 加载 ${this.sources.length} 个书源（内置:${builtinSources.length} 自定义:${customSources.length}）`);
            return this.sources;
        } catch (e) {
            console.error('[引擎] 加载失败:', e);
            return [];
        }
    }

    // 搜索书籍 - 使用多个书源并行搜索
    async search(keyword, maxResults = 20) {
        const results = [];
        const seen = new Set(); // 去重
        
        // 只使用已启用的书源
        const enabledSources = this.sources.filter(s => s.enabled !== false);
        console.log(`[搜索] 关键词: ${keyword}, 可用书源: ${enabledSources.length}个`);
        
        // 并行搜索前5个书源
        const searchPromises = enabledSources.slice(0, 5).map(async (source, idx) => {
            try {
                console.log(`[搜索] [${idx + 1}/5] 使用书源: ${source.bookSourceName}`);
                const books = await this.searchWithSource(source, keyword);
                console.log(`[搜索] [${idx + 1}/5] ${source.bookSourceName} 返回 ${books.length} 本书`);
                return books;
            } catch (e) {
                console.log(`[搜索] [${idx + 1}/5] ${source.bookSourceName} 失败: ${e.message}`);
                return [];
            }
        });
        
        const allResults = await Promise.all(searchPromises);
        
        // 合并结果并去重
        for (const books of allResults) {
            for (const book of books) {
                const key = `${book.name}-${book.author}`;
                if (!seen.has(key) && book.name && book.author) {
                    seen.add(key);
                    results.push(book);
                }
            }
        }
        
        console.log(`[搜索] 总计找到 ${results.length} 本不重复书籍`);
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
        
        console.log(`[解析] 书源: ${source.bookSourceName}, bookList规则: ${rule.bookList}`);
        
        // 尝试解析JSON
        let data = null;
        try {
            data = JSON.parse(html);
            console.log('[解析] JSON解析成功');
        } catch (e) {
            console.log('[解析] 不是JSON格式:', e.message);
            return books;
        }

        if (data && rule.bookList) {
            // JSONPath 解析
            console.log(`[解析] 尝试获取路径: ${rule.bookList}`);
            const list = this.getValueByPath(data, rule.bookList);
            console.log(`[解析] 获取结果:`, list);
            
            if (Array.isArray(list)) {
                console.log(`[解析] 是数组，长度: ${list.length}`);
                for (let i = 0; i < Math.min(list.length, 10); i++) {
                    const item = list[i];
                    console.log(`[解析] 处理第${i+1}项:`, item);
                    const book = this.extractBookFromJson(item, rule, source);
                    console.log(`[解析] 提取结果:`, book);
                    if (book.name) {
                        books.push(book);
                        console.log(`[解析] 成功添加书籍: ${book.name}`);
                    }
                }
            } else {
                console.log('[解析] 结果不是数组:', typeof list);
            }
        }

        console.log(`[解析] 总计返回 ${books.length} 本书`);
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
        
        // 移除开头的 $. 
        let cleanPath = path.replace(/^\$\./, '');
        
        // 处理 [*] 语法，例如: data[*] -> 返回 data 数组
        if (cleanPath.includes('[*]')) {
            const arrayKey = cleanPath.replace('[*]', '');
            console.log(`[JSONPath] 数组路径: ${arrayKey}`);
            return obj[arrayKey];
        }
        
        // 普通路径
        const keys = cleanPath.split('.');
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
