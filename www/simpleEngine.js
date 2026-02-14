// 简化版书源引擎 - 专注于核心功能
class SimpleBookEngine {
    constructor() {
        this.sources = [];
    }

    async init() {
        try {
            // 先加载内置书源
            let builtinSources = [];
            try {
                const response = await fetch('book_sources.json');
                const allSources = await response.json();
                // 放宽过滤条件：只要有搜索URL或搜索规则即可
                builtinSources = allSources.filter(s => 
                    s && (s.searchUrl || s.ruleSearch)
                );
                console.log(`[引擎] 内置书源: ${builtinSources.length}个`);
            } catch (e) {
                console.warn('[引擎] 加载内置书源失败:', e);
            }
            
            // 加载自定义书源
            let customSources = [];
            try {
                const { value } = await Capacitor.Plugins.Preferences.get({ key: 'custom_sources' });
                if (value) {
                    customSources = JSON.parse(value);
                    console.log(`[引擎] 自定义书源: ${customSources.length}个`);
                }
            } catch (e) {
                console.warn('[引擎] 加载自定义书源失败:', e);
            }
            
            // 合并书源（自定义优先，去重）
            const existingUrls = new Set();
            const sources = [];
            
            // 先添加自定义书源
            for (const s of customSources) {
                if (s && s.bookSourceUrl && !existingUrls.has(s.bookSourceUrl)) {
                    existingUrls.add(s.bookSourceUrl);
                    sources.push(s);
                }
            }
            
            // 再添加内置书源（不重复）
            for (const s of builtinSources) {
                if (s && s.bookSourceUrl && !existingUrls.has(s.bookSourceUrl)) {
                    existingUrls.add(s.bookSourceUrl);
                    sources.push(s);
                }
            }
            
            this.sources = sources;
            
            console.log(`[引擎] 总计加载 ${this.sources.length} 个书源`);
            return this.sources;
        } catch (e) {
            console.error('[引擎] 初始化失败:', e);
            return [];
        }
    }

    // 搜索书籍 - 使用所有已启用的书源并行搜索（带超时控制）
    async search(keyword, maxResults = 20) {
        const results = [];
        const seen = new Set(); // 去重
        
        // 使用所有有搜索能力的书源
        const enabledSources = this.sources.filter(s => 
            s.enabled !== false && (s.searchUrl || s.ruleSearch)
        );
        console.log(`[搜索] 关键词: ${keyword}, 可用书源: ${enabledSources.length}个`);
        
        // 限制同时搜索的书源数量，避免请求过多
        const batchSize = 10; // 每批10个书源（减少并发）
        const batches = Math.ceil(Math.min(enabledSources.length, 50) / batchSize); // 最多搜索50个书源
        
        for (let batch = 0; batch < batches; batch++) {
            const start = batch * batchSize;
            const end = Math.min(start + batchSize, enabledSources.length, 50);
            const batchSources = enabledSources.slice(start, end);
            
            console.log(`[搜索] 批次 ${batch + 1}/${batches}, 书源 ${start + 1}-${end}`);
            
            // 并行搜索当前批次（带5秒超时）
            const searchPromises = batchSources.map(async (source, idx) => {
                try {
                    const timeoutPromise = new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('timeout')), 5000)
                    );
                    const searchPromise = this.searchWithSource(source, keyword);
                    const books = await Promise.race([searchPromise, timeoutPromise]);
                    
                    if (books.length > 0) {
                        console.log(`[搜索] ✓ ${source.bookSourceName}: ${books.length}本`);
                    }
                    return books;
                } catch (e) {
                    // 超时或错误，静默失败
                    return [];
                }
            });
            
            const batchResults = await Promise.all(searchPromises);
            
            // 合并结果并去重
            for (const books of batchResults) {
                for (const book of books) {
                    const key = `${book.name}-${book.author}`;
                    if (!seen.has(key) && book.name && book.author) {
                        seen.add(key);
                        results.push(book);
                        if (results.length >= maxResults) {
                            console.log(`[搜索] 已达到最大结果数 ${maxResults}`);
                            return results;
                        }
                    }
                }
            }
            
            // 如果已经找到足够的结果，提前结束
            if (results.length >= maxResults) break;
            
            // 批次间添加小延迟，避免请求过快
            if (batch < batches - 1) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
        
        console.log(`[搜索] 总计找到 ${results.length} 本不重复书籍`);
        return results;
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

    // 章节缓存
    chapterCache = new Map();
    chapterCacheMaxSize = 100; // 最多缓存100本书的章节

    // 获取章节列表（带缓存）
    async getChapters(book) {
        const cacheKey = `${book.source?.bookSourceUrl || book.sourceUrl}-${book.bookUrl}`;
        
        // 检查缓存
        if (this.chapterCache.has(cacheKey)) {
            console.log('[章节] 使用缓存:', book.name);
            return this.chapterCache.get(cacheKey);
        }
        
        const source = book.source || this.getSourceByUrl(book.sourceUrl);
        if (!source) {
            console.error('[章节] 未找到书源:', book.sourceUrl);
            return [];
        }
        
        const tocUrl = book.tocUrl || book.bookUrl;
        if (!tocUrl) {
            console.error('[章节] 无目录URL');
            return [];
        }
        
        try {
            const html = await this.httpRequest(tocUrl);
            if (!html) {
                console.error('[章节] 请求返回空内容');
                return [];
            }
            
            const rule = source.ruleToc;
            if (!rule?.chapterList) {
                console.log('[章节] 无目录规则，返回模拟章节');
                // 返回模拟章节
                return Array.from({length: 100}, (_, i) => ({
                    index: i,
                    title: `第${i+1}章`,
                    url: tocUrl
                }));
            }

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
                            title: this.getValueByPath(item, rule.chapterName?.replace('$.', '')) || `第${i+1}章`,
                            url: this.fixUrl(
                                this.getValueByPath(item, rule.chapterUrl?.replace('$.', '')) || '',
                                source.bookSourceUrl
                            )
                        });
                    }
                }
            } catch (e) {
                console.log('[章节] JSON解析失败，尝试HTML解析:', e.message);
                // 尝试HTML解析（简化版）
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const links = doc.querySelectorAll('a');
                links.forEach((link, i) => {
                    if (link.textContent && link.href) {
                        chapters.push({
                            index: i,
                            title: link.textContent.trim(),
                            url: this.fixUrl(link.href, source.bookSourceUrl)
                        });
                    }
                });
            }
            
            // 存入缓存
            this.setChapterCache(cacheKey, chapters);
            
            console.log(`[章节] 获取到 ${chapters.length} 章`);
            return chapters;
        } catch (e) {
            console.error('[章节] 获取失败:', e.message);
            return [];
        }
    }
    
    // 设置章节缓存（LRU策略）
    setChapterCache(key, chapters) {
        // 如果缓存已满，删除最早的条目
        if (this.chapterCache.size >= this.chapterCacheMaxSize) {
            const firstKey = this.chapterCache.keys().next().value;
            this.chapterCache.delete(firstKey);
        }
        
        this.chapterCache.set(key, chapters);
    }
    
    // 清除章节缓存
    clearChapterCache() {
        this.chapterCache.clear();
        console.log('[章节] 缓存已清除');
    }
    
    // 简单正文提取（无规则时使用）
    extractContentSimple(html) {
        try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // 移除脚本和样式
            doc.querySelectorAll('script, style, nav, header, footer').forEach(el => el.remove());
            
            // 查找最长的段落
            let maxLength = 0;
            let content = '';
            
            const paragraphs = doc.querySelectorAll('p, div, article');
            paragraphs.forEach(p => {
                const text = p.textContent.trim();
                if (text.length > maxLength && text.length > 100) {
                    maxLength = text.length;
                    content = text;
                }
            });
            
            if (content) {
                return content.split('\n').map(line => line.trim()).filter(line => line).join('\n\n');
            }
            
            return '无法提取正文内容';
        } catch (e) {
            return '内容解析失败';
        }
    }

    // 获取章节内容
    async getContent(chapter, book) {
        try {
            const source = book.source || this.getSourceByUrl(book.sourceUrl);
            if (!source) {
                console.error('[内容] 未找到书源');
                return '书源未找到，请检查书源配置';
            }
            
            if (!chapter?.url) {
                console.error('[内容] 无章节URL');
                return '章节链接无效';
            }
            
            const html = await this.httpRequest(chapter.url);
            if (!html) {
                return '内容获取失败，请检查网络连接';
            }
            
            const rule = source.ruleContent;
            if (!rule?.content) {
                // 如果没有内容规则，尝试提取正文
                return this.extractContentSimple(html);
            }

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
