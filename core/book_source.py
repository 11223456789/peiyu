"""
书源解析模块 - 支持Legado格式的书源解析
"""
import json
import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup


@dataclass
class BookSource:
    """书源数据结构"""
    bookSourceName: str = ""
    bookSourceUrl: str = ""
    bookSourceGroup: str = ""
    bookSourceType: int = 0  # 0: 文本, 1: 音频, 2: 图片
    bookUrlPattern: str = ""
    concurrentRate: str = ""
    customOrder: int = 0
    enabled: bool = True
    enabledCookieJar: bool = False
    enabledExplore: bool = True
    exploreUrl: str = ""
    header: str = ""
    lastUpdateTime: int = 0
    loginUrl: str = ""
    respondTime: int = 0
    ruleBookInfo: Dict[str, str] = field(default_factory=dict)
    ruleContent: Dict[str, str] = field(default_factory=dict)
    ruleExplore: Dict[str, str] = field(default_factory=dict)
    ruleSearch: Dict[str, str] = field(default_factory=dict)
    ruleToc: Dict[str, str] = field(default_factory=dict)
    searchUrl: str = ""
    weight: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookSource':
        """从字典创建书源对象"""
        return cls(
            bookSourceName=data.get('bookSourceName', ''),
            bookSourceUrl=data.get('bookSourceUrl', ''),
            bookSourceGroup=data.get('bookSourceGroup', ''),
            bookSourceType=data.get('bookSourceType', 0),
            bookUrlPattern=data.get('bookUrlPattern', ''),
            concurrentRate=data.get('concurrentRate', ''),
            customOrder=data.get('customOrder', 0),
            enabled=data.get('enabled', True),
            enabledCookieJar=data.get('enabledCookieJar', False),
            enabledExplore=data.get('enabledExplore', True),
            exploreUrl=data.get('exploreUrl', ''),
            header=data.get('header', ''),
            lastUpdateTime=data.get('lastUpdateTime', 0),
            loginUrl=data.get('loginUrl', ''),
            respondTime=data.get('respondTime', 0),
            ruleBookInfo=data.get('ruleBookInfo', {}),
            ruleContent=data.get('ruleContent', {}),
            ruleExplore=data.get('ruleExplore', {}),
            ruleSearch=data.get('ruleSearch', {}),
            ruleToc=data.get('ruleToc', {}),
            searchUrl=data.get('searchUrl', ''),
            weight=data.get('weight', 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'bookSourceName': self.bookSourceName,
            'bookSourceUrl': self.bookSourceUrl,
            'bookSourceGroup': self.bookSourceGroup,
            'bookSourceType': self.bookSourceType,
            'bookUrlPattern': self.bookUrlPattern,
            'concurrentRate': self.concurrentRate,
            'customOrder': self.customOrder,
            'enabled': self.enabled,
            'enabledCookieJar': self.enabledCookieJar,
            'enabledExplore': self.enabledExplore,
            'exploreUrl': self.exploreUrl,
            'header': self.header,
            'lastUpdateTime': self.lastUpdateTime,
            'loginUrl': self.loginUrl,
            'respondTime': self.respondTime,
            'ruleBookInfo': self.ruleBookInfo,
            'ruleContent': self.ruleContent,
            'ruleExplore': self.ruleExplore,
            'ruleSearch': self.ruleSearch,
            'ruleToc': self.ruleToc,
            'searchUrl': self.searchUrl,
            'weight': self.weight
        }


class RuleParser:
    """规则解析器 - 解析Legado的各种规则"""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url

    def parse_rule(self, rule: str, element: Any) -> Any:
        """
        解析规则并提取内容
        支持: @css:, @xpath:, @json:, @regex: 等前缀
        """
        if not rule or not element:
            return None

        # 处理多个规则（用||分隔）
        if '||' in rule:
            for r in rule.split('||'):
                result = self.parse_rule(r.strip(), element)
                if result:
                    return result
            return None

        # 处理替换规则 @js: 等
        if '@js:' in rule:
            return self._handle_js_rule(rule, element)

        # 处理CSS选择器
        if rule.startswith('@css:'):
            return self._parse_css(rule[5:], element)

        # 处理XPath
        if rule.startswith('@xpath:'):
            return self._parse_xpath(rule[7:], element)

        # 处理JSONPath
        if rule.startswith('@json:'):
            return self._parse_jsonpath(rule[6:], element)

        # 处理正则
        if rule.startswith('@regex:'):
            return self._parse_regex(rule[7:], element)

        # 默认按CSS处理
        return self._parse_css(rule, element)

    def _parse_css(self, selector: str, element: Any) -> Any:
        """解析CSS选择器"""
        if isinstance(element, str):
            soup = BeautifulSoup(element, 'html.parser')
        elif isinstance(element, BeautifulSoup):
            soup = element
        else:
            soup = BeautifulSoup(str(element), 'html.parser')

        # 处理属性提取，如 a@href 或 a@text
        attr = None
        if '@' in selector and not selector.startswith('@'):
            parts = selector.rsplit('@', 1)
            selector = parts[0]
            attr = parts[1]

        results = soup.select(selector)

        if not results:
            return None

        if attr:
            if attr == 'text':
                return [r.get_text(strip=True) for r in results]
            elif attr == 'html':
                return [str(r) for r in results]
            else:
                return [r.get(attr, '') for r in results]

        return results

    def _parse_xpath(self, xpath: str, element: Any) -> Any:
        """解析XPath"""
        from lxml import html as lh

        if isinstance(element, str):
            tree = lh.fromstring(element)
        elif isinstance(element, lh.HtmlElement):
            tree = element
        else:
            tree = lh.fromstring(str(element))

        results = tree.xpath(xpath)
        return results if results else None

    def _parse_jsonpath(self, jsonpath: str, data: Any) -> Any:
        """解析JSONPath"""
        from jsonpath_ng import parse

        if isinstance(data, str):
            data = json.loads(data)

        jsonpath_expr = parse(jsonpath)
        results = [match.value for match in jsonpath_expr.find(data)]
        return results if results else None

    def _parse_regex(self, pattern: str, text: str) -> Any:
        """解析正则表达式"""
        if not isinstance(text, str):
            text = str(text)

        matches = re.findall(pattern, text)
        return matches if matches else None

    def _handle_js_rule(self, rule: str, element: Any) -> Any:
        """处理JS规则（简化版，主要处理替换逻辑）"""
        # 提取替换规则
        if 'replace' in rule.lower():
            # 简单的替换处理
            match = re.search(r"replace\(['\"](.+?)['\"],\s*['\"](.*?)['\"]\)", rule)
            if match:
                old, new = match.groups()
                if isinstance(element, str):
                    return element.replace(old, new)
        return element

    def format_url(self, url_template: str, **kwargs) -> str:
        """格式化URL模板"""
        url = url_template
        for key, value in kwargs.items():
            placeholder = f"${{{key}}}"
            if placeholder in url:
                url = url.replace(placeholder, quote(str(value)) if key == 'key' else str(value))

        # 处理page变量
        if '${page}' in url:
            url = url.replace('${page}', '1')

        # 补全URL
        if url and not url.startswith('http'):
            url = urljoin(self.base_url, url)

        return url


class BookSourceManager:
    """书源管理器"""

    def __init__(self):
        self.sources: Dict[str, BookSource] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def load_from_json(self, json_path: str) -> int:
        """从JSON文件加载书源"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    source = BookSource.from_dict(item)
                    if source.enabled:
                        self.sources[source.bookSourceName] = source
            elif isinstance(data, dict):
                source = BookSource.from_dict(data)
                if source.enabled:
                    self.sources[source.bookSourceName] = source

            return len(self.sources)
        except Exception as e:
            print(f"加载书源失败: {e}")
            return 0

    def load_from_json_string(self, json_str: str) -> int:
        """从JSON字符串加载书源"""
        try:
            data = json.loads(json_str)

            if isinstance(data, list):
                for item in data:
                    source = BookSource.from_dict(item)
                    if source.enabled:
                        self.sources[source.bookSourceName] = source
            elif isinstance(data, dict):
                source = BookSource.from_dict(data)
                if source.enabled:
                    self.sources[source.bookSourceName] = source

            return len(self.sources)
        except Exception as e:
            print(f"加载书源失败: {e}")
            return 0

    def add_source(self, source: BookSource):
        """添加单个书源"""
        self.sources[source.bookSourceName] = source

    def remove_source(self, name: str):
        """移除书源"""
        if name in self.sources:
            del self.sources[name]

    def get_source(self, name: str) -> Optional[BookSource]:
        """获取书源"""
        return self.sources.get(name)

    def list_sources(self) -> List[BookSource]:
        """列出所有书源"""
        return list(self.sources.values())

    def save_to_json(self, json_path: str):
        """保存书源到JSON文件"""
        data = [source.to_dict() for source in self.sources.values()]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def search_book(self, source_name: str, keyword: str) -> List[Dict[str, Any]]:
        """在指定书源搜索书籍"""
        source = self.get_source(source_name)
        if not source:
            return []

        parser = RuleParser(source.bookSourceUrl)

        try:
            # 构建搜索URL
            search_url = parser.format_url(source.searchUrl, key=keyword)

            # 发送请求
            headers = {}
            if source.header:
                try:
                    headers = json.loads(source.header)
                except:
                    pass

            response = self.session.get(search_url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding or 'utf-8'

            # 解析搜索结果
            return self._parse_search_results(response.text, source, parser)

        except Exception as e:
            print(f"搜索失败 [{source_name}]: {e}")
            return []

    def _parse_search_results(self, html: str, source: BookSource, parser: RuleParser) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        results = []
        rule = source.ruleSearch

        if not rule:
            return results

        try:
            # 获取书籍列表
            book_list_rule = rule.get('bookList', '')
            if not book_list_rule:
                return results

            soup = BeautifulSoup(html, 'html.parser')
            book_elements = parser.parse_rule(book_list_rule, soup)

            if not book_elements:
                return results

            for elem in book_elements[:20]:  # 最多20条结果
                book = {}

                # 书名
                name_rule = rule.get('name', '')
                if name_rule:
                    name = parser.parse_rule(name_rule, elem)
                    book['name'] = name[0] if isinstance(name, list) and name else str(name) if name else ''

                # 作者
                author_rule = rule.get('author', '')
                if author_rule:
                    author = parser.parse_rule(author_rule, elem)
                    book['author'] = author[0] if isinstance(author, list) and author else str(author) if author else ''

                # 书籍URL
                book_url_rule = rule.get('bookUrl', '')
                if book_url_rule:
                    book_url = parser.parse_rule(book_url_rule, elem)
                    url = book_url[0] if isinstance(book_url, list) and book_url else str(book_url) if book_url else ''
                    if url and not url.startswith('http'):
                        url = urljoin(source.bookSourceUrl, url)
                    book['bookUrl'] = url

                # 封面
                cover_rule = rule.get('coverUrl', '')
                if cover_rule:
                    cover = parser.parse_rule(cover_rule, elem)
                    cover_url = cover[0] if isinstance(cover, list) and cover else str(cover) if cover else ''
                    if cover_url and not cover_url.startswith('http'):
                        cover_url = urljoin(source.bookSourceUrl, cover_url)
                    book['coverUrl'] = cover_url

                # 简介
                intro_rule = rule.get('intro', '')
                if intro_rule:
                    intro = parser.parse_rule(intro_rule, elem)
                    book['intro'] = intro[0] if isinstance(intro, list) and intro else str(intro) if intro else ''

                # 最新章节
                last_chapter_rule = rule.get('lastChapter', '')
                if last_chapter_rule:
                    last_chapter = parser.parse_rule(last_chapter_rule, elem)
                    book['lastChapter'] = last_chapter[0] if isinstance(last_chapter, list) and last_chapter else str(last_chapter) if last_chapter else ''

                if book.get('name'):
                    results.append(book)

        except Exception as e:
            print(f"解析搜索结果失败: {e}")

        return results

    def get_book_info(self, source_name: str, book_url: str) -> Dict[str, Any]:
        """获取书籍详细信息"""
        source = self.get_source(source_name)
        if not source:
            return {}

        parser = RuleParser(source.bookSourceUrl)

        try:
            headers = {}
            if source.header:
                try:
                    headers = json.loads(source.header)
                except:
                    pass

            response = self.session.get(book_url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding or 'utf-8'

            return self._parse_book_info(response.text, source, parser, book_url)

        except Exception as e:
            print(f"获取书籍信息失败: {e}")
            return {}

    def _parse_book_info(self, html: str, source: BookSource, parser: RuleParser, book_url: str) -> Dict[str, Any]:
        """解析书籍详细信息"""
        info = {'bookUrl': book_url}
        rule = source.ruleBookInfo

        if not rule:
            return info

        soup = BeautifulSoup(html, 'html.parser')

        # 书名
        name_rule = rule.get('name', '')
        if name_rule:
            name = parser.parse_rule(name_rule, soup)
            info['name'] = name[0] if isinstance(name, list) and name else str(name) if name else ''

        # 作者
        author_rule = rule.get('author', '')
        if author_rule:
            author = parser.parse_rule(author_rule, soup)
            info['author'] = author[0] if isinstance(author, list) and author else str(author) if author else ''

        # 封面
        cover_rule = rule.get('coverUrl', '')
        if cover_rule:
            cover = parser.parse_rule(cover_rule, soup)
            cover_url = cover[0] if isinstance(cover, list) and cover else str(cover) if cover else ''
            if cover_url and not cover_url.startswith('http'):
                cover_url = urljoin(source.bookSourceUrl, cover_url)
            info['coverUrl'] = cover_url

        # 简介
        intro_rule = rule.get('intro', '')
        if intro_rule:
            intro = parser.parse_rule(intro_rule, soup)
            info['intro'] = intro[0] if isinstance(intro, list) and intro else str(intro) if intro else ''

        # 分类
        kind_rule = rule.get('kind', '')
        if kind_rule:
            kind = parser.parse_rule(kind_rule, soup)
            info['kind'] = kind[0] if isinstance(kind, list) and kind else str(kind) if kind else ''

        # 最新章节
        last_chapter_rule = rule.get('lastChapter', '')
        if last_chapter_rule:
            last_chapter = parser.parse_rule(last_chapter_rule, soup)
            info['lastChapter'] = last_chapter[0] if isinstance(last_chapter, list) and last_chapter else str(last_chapter) if last_chapter else ''

        # 章节列表URL
        toc_url_rule = rule.get('tocUrl', '')
        if toc_url_rule:
            toc_url = parser.parse_rule(toc_url_rule, soup)
            url = toc_url[0] if isinstance(toc_url, list) and toc_url else str(toc_url) if toc_url else ''
            if url and not url.startswith('http'):
                url = urljoin(source.bookSourceUrl, url)
            info['tocUrl'] = url
        else:
            info['tocUrl'] = book_url

        return info

    def get_chapter_list(self, source_name: str, toc_url: str) -> List[Dict[str, str]]:
        """获取章节列表"""
        source = self.get_source(source_name)
        if not source:
            return []

        parser = RuleParser(source.bookSourceUrl)

        try:
            headers = {}
            if source.header:
                try:
                    headers = json.loads(source.header)
                except:
                    pass

            response = self.session.get(toc_url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding or 'utf-8'

            return self._parse_chapter_list(response.text, source, parser)

        except Exception as e:
            print(f"获取章节列表失败: {e}")
            return []

    def _parse_chapter_list(self, html: str, source: BookSource, parser: RuleParser) -> List[Dict[str, str]]:
        """解析章节列表"""
        chapters = []
        rule = source.ruleToc

        if not rule:
            return chapters

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 章节列表
            chapter_list_rule = rule.get('chapterList', '')
            if not chapter_list_rule:
                return chapters

            elements = parser.parse_rule(chapter_list_rule, soup)

            if not elements:
                return chapters

            for elem in elements:
                chapter = {}

                # 章节名
                name_rule = rule.get('chapterName', '')
                if name_rule:
                    name = parser.parse_rule(name_rule, elem)
                    chapter['title'] = name[0] if isinstance(name, list) and name else str(name) if name else ''
                else:
                    # 默认取文本
                    if hasattr(elem, 'get_text'):
                        chapter['title'] = elem.get_text(strip=True)
                    else:
                        chapter['title'] = str(elem)

                # 章节URL
                url_rule = rule.get('chapterUrl', '')
                if url_rule:
                    url = parser.parse_rule(url_rule, elem)
                    chapter_url = url[0] if isinstance(url, list) and url else str(url) if url else ''
                else:
                    # 默认取href
                    if hasattr(elem, 'get'):
                        chapter_url = elem.get('href', '')
                    else:
                        chapter_url = ''

                if chapter_url and not chapter_url.startswith('http'):
                    chapter_url = urljoin(source.bookSourceUrl, chapter_url)
                chapter['url'] = chapter_url

                if chapter.get('title'):
                    chapters.append(chapter)

        except Exception as e:
            print(f"解析章节列表失败: {e}")

        return chapters

    def get_chapter_content(self, source_name: str, chapter_url: str) -> str:
        """获取章节内容"""
        source = self.get_source(source_name)
        if not source:
            return ""

        parser = RuleParser(source.bookSourceUrl)

        try:
            headers = {}
            if source.header:
                try:
                    headers = json.loads(source.header)
                except:
                    pass

            response = self.session.get(chapter_url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding or 'utf-8'

            return self._parse_chapter_content(response.text, source, parser)

        except Exception as e:
            print(f"获取章节内容失败: {e}")
            return ""

    def _parse_chapter_content(self, html: str, source: BookSource, parser: RuleParser) -> str:
        """解析章节内容"""
        rule = source.ruleContent

        if not rule:
            return ""

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 内容规则
            content_rule = rule.get('content', '')
            if not content_rule:
                return ""

            content = parser.parse_rule(content_rule, soup)

            if isinstance(content, list):
                # 合并内容
                texts = []
                for item in content:
                    if hasattr(item, 'get_text'):
                        texts.append(item.get_text())
                    else:
                        texts.append(str(item))
                text = '\n'.join(texts)
            else:
                text = str(content) if content else ""

            # 清理内容
            text = self._clean_content(text, rule)

            return text

        except Exception as e:
            print(f"解析章节内容失败: {e}")
            return ""

    def _clean_content(self, text: str, rule: Dict[str, str]) -> str:
        """清理章节内容"""
        if not text:
            return ""

        # 替换规则
        replace_rule = rule.get('replaceRegex', '')
        if replace_rule:
            try:
                pattern, repl = replace_rule.split('->')
                text = re.sub(pattern.strip(), repl.strip(), text)
            except:
                pass

        # 移除脚本和样式
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)

        # 转换HTML标签
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)

        # 解码HTML实体
        from html import unescape
        text = unescape(text)

        # 清理空白
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = text.strip()

        return text
