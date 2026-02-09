"""
简化版书源解析器 - 用于Web后端
支持Legado书源格式的搜索和内容解析
"""
import json
import re
import requests
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import html

class SimpleSourceParser:
    """简化版书源解析器"""
    
    def __init__(self, source_config: Dict):
        self.config = source_config
        self.base_url = source_config.get('bookSourceUrl', '')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def search(self, keyword: str) -> List[Dict]:
        """搜索书籍"""
        try:
            search_url_template = self.config.get('searchUrl', '')
            if not search_url_template:
                return []
            
            # 构建搜索URL
            search_url = search_url_template.replace('{{key}}', quote(keyword))
            if not search_url.startswith('http'):
                search_url = urljoin(self.base_url, search_url)
            
            # 发送请求
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.encoding = response.apparent_encoding or 'utf-8'
            
            # 解析搜索结果
            rule_search = self.config.get('ruleSearch', {})
            book_list_rule = rule_search.get('bookList', '')
            
            if not book_list_rule:
                return []
            
            # 使用BeautifulSoup解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据规则提取书籍列表
            books = []
            book_elements = self._extract_by_rule(soup, book_list_rule)
            
            for elem in book_elements[:10]:  # 限制返回数量
                book = self._parse_book_info(elem, rule_search)
                if book.get('name'):
                    books.append(book)
            
            return books
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_chapters(self, book_url: str) -> List[Dict]:
        """获取章节列表"""
        try:
            response = requests.get(book_url, headers=self.headers, timeout=10)
            response.encoding = response.apparent_encoding or 'utf-8'
            
            rule_toc = self.config.get('ruleToc', {})
            chapter_list_rule = rule_toc.get('chapterList', '')
            
            if not chapter_list_rule:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            chapters = []
            
            # 提取章节列表
            chapter_elements = self._extract_by_rule(soup, chapter_list_rule)
            
            for i, elem in enumerate(chapter_elements):
                chapter = self._parse_chapter_info(elem, rule_toc, book_url)
                if chapter.get('title'):
                    chapter['id'] = i + 1
                    chapters.append(chapter)
            
            return chapters
            
        except Exception as e:
            print(f"Get chapters error: {e}")
            return []
    
    def get_content(self, chapter_url: str) -> str:
        """获取章节内容"""
        try:
            response = requests.get(chapter_url, headers=self.headers, timeout=10)
            response.encoding = response.apparent_encoding or 'utf-8'
            
            rule_content = self.config.get('ruleContent', {})
            content_rule = rule_content.get('content', '')
            
            if not content_rule:
                return "无法解析内容"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取内容
            content_elem = self._extract_first_by_rule(soup, content_rule)
            
            if content_elem:
                # 清理内容
                content = self._clean_content(content_elem)
                return content
            
            return "内容获取失败"
            
        except Exception as e:
            print(f"Get content error: {e}")
            return f"获取内容失败: {str(e)}"
    
    def _extract_by_rule(self, soup: BeautifulSoup, rule: str) -> List:
        """根据规则提取元素"""
        if not rule:
            return []
        
        # 处理简单的CSS选择器规则
        if rule.startswith('@css:'):
            selector = rule[5:]
            return soup.select(selector)
        elif rule.startswith('//'):
            # XPath简化处理
            return []
        else:
            # 默认作为CSS选择器
            return soup.select(rule)
    
    def _extract_first_by_rule(self, soup: BeautifulSoup, rule: str) -> Any:
        """根据规则提取第一个元素"""
        elements = self._extract_by_rule(soup, rule)
        return elements[0] if elements else None
    
    def _parse_book_info(self, elem, rule_search: Dict) -> Dict:
        """解析书籍信息"""
        book = {}
        
        # 书名
        name_rule = rule_search.get('name', '')
        if name_rule:
            book['name'] = self._extract_text(elem, name_rule)
        
        # 作者
        author_rule = rule_search.get('author', '')
        if author_rule:
            book['author'] = self._extract_text(elem, author_rule)
        
        # 书籍链接
        book_url_rule = rule_search.get('bookUrl', '')
        if book_url_rule:
            url = self._extract_attr(elem, book_url_rule, 'href')
            if url:
                book['url'] = urljoin(self.base_url, url)
        
        # 封面
        cover_rule = rule_search.get('coverUrl', '')
        if cover_rule:
            cover = self._extract_attr(elem, cover_rule, 'src')
            if cover:
                book['cover'] = urljoin(self.base_url, cover)
        
        # 简介
        intro_rule = rule_search.get('intro', '')
        if intro_rule:
            book['intro'] = self._extract_text(elem, intro_rule)
        
        return book
    
    def _parse_chapter_info(self, elem, rule_toc: Dict, book_url: str) -> Dict:
        """解析章节信息"""
        chapter = {}
        
        # 章节标题
        title_rule = rule_toc.get('chapterName', '')
        if title_rule:
            chapter['title'] = self._extract_text(elem, title_rule)
        
        # 章节链接
        url_rule = rule_toc.get('chapterUrl', '')
        if url_rule:
            url = self._extract_attr(elem, url_rule, 'href')
            if url:
                chapter['url'] = urljoin(book_url, url)
        
        return chapter
    
    def _extract_text(self, elem, rule: str) -> str:
        """提取文本"""
        try:
            if rule.startswith('@css:'):
                selector = rule[5:]
                found = elem.select_one(selector)
                if found:
                    return found.get_text(strip=True)
            elif rule.startswith('@'):
                # 属性提取
                attr = rule[1:]
                return elem.get(attr, '')
            else:
                found = elem.select_one(rule)
                if found:
                    return found.get_text(strip=True)
            return elem.get_text(strip=True) if hasattr(elem, 'get_text') else str(elem)
        except:
            return ''
    
    def _extract_attr(self, elem, rule: str, attr: str) -> str:
        """提取属性"""
        try:
            if rule.startswith('@css:'):
                selector = rule[5:]
                found = elem.select_one(selector)
                if found:
                    return found.get(attr, '')
            elif rule.startswith('@'):
                return elem.get(rule[1:], '')
            else:
                found = elem.select_one(rule)
                if found:
                    return found.get(attr, '')
            return elem.get(attr, '') if hasattr(elem, 'get') else ''
        except:
            return ''
    
    def _clean_content(self, elem) -> str:
        """清理内容"""
        # 移除脚本和样式
        for script in elem.find_all(['script', 'style']):
            script.decompose()
        
        # 获取文本
        text = elem.get_text(separator='\n', strip=True)
        
        # 清理多余空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # 转换为HTML段落
        paragraphs = []
        for line in lines:
            # 跳过广告和无关内容
            if any(keyword in line for keyword in ['广告', '本章未完', '点击下一页', '笔趣阁', '顶点小说']):
                continue
            if len(line) < 5 and not line.endswith('。'):
                continue
            
            paragraphs.append(f'<p>{html.escape(line)}</p>')
        
        return '\n'.join(paragraphs) if paragraphs else '<p>内容加载中...</p>'


class BookSourceManager:
    """书源管理器"""
    
    def __init__(self, sources_file: str = None):
        self.sources = []
        self.parsers = {}
        
        if sources_file:
            self.load_sources(sources_file)
    
    def load_sources(self, file_path: str):
        """加载书源文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.sources = data
                elif isinstance(data, dict) and 'sources' in data:
                    self.sources = data['sources']
                
                # 初始化解析器
                for source in self.sources:
                    if source.get('enabled', True):
                        source_id = source.get('bookSourceName', '')
                        if source_id:
                            self.parsers[source_id] = SimpleSourceParser(source)
        except Exception as e:
            print(f"Load sources error: {e}")
    
    def search_all(self, keyword: str) -> List[Dict]:
        """在所有书源中搜索"""
        all_results = []
        
        for name, parser in self.parsers.items():
            try:
                results = parser.search(keyword)
                for book in results:
                    book['source'] = name
                all_results.extend(results)
            except Exception as e:
                print(f"Search in {name} failed: {e}")
        
        return all_results
    
    def get_parser(self, source_name: str) -> Optional[SimpleSourceParser]:
        """获取指定书源的解析器"""
        return self.parsers.get(source_name)
