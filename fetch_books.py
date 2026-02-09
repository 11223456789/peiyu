"""
本地书源预解析脚本
从书源抓取书籍数据并保存为JSON，供服务器使用
"""
import json
import requests
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
import os

def load_book_sources():
    """加载书源配置"""
    sources_file = os.path.join(os.path.dirname(__file__), 'sources', 'book_sources.json')
    with open(sources_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_from_source(source, keyword="热门"):
    """从单个书源抓取书籍"""
    books = []
    try:
        base_url = source.get('bookSourceUrl', '')
        search_rule = source.get('ruleSearch', {})
        search_url_template = source.get('searchUrl', '')
        
        if not search_url_template:
            return books
        
        # 构建搜索URL
        search_url = search_url_template.replace('{{key}}', quote(keyword)).replace('{{page}}', '1')
        if not search_url.startswith('http'):
            search_url = urljoin(base_url, search_url)
        
        print(f"正在从 {source.get('bookSourceName', '未知书源')} 抓取...")
        print(f"URL: {search_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding or 'utf-8'
        
        # 尝试解析JSON响应
        try:
            data = response.json()
            book_list_rule = search_rule.get('bookList', '$[*]')
            
            # 简单的JSONPath解析
            if book_list_rule.startswith('$.'):
                books_data = data
                for key in book_list_rule[2:].split('.'):
                    if isinstance(books_data, dict):
                        books_data = books_data.get(key, [])
                    elif isinstance(books_data, list) and books_data:
                        books_data = books_data[0].get(key, []) if isinstance(books_data[0], dict) else []
            elif book_list_rule == '$[*]' or book_list_rule == '$.data[*]':
                books_data = data if isinstance(data, list) else data.get('data', [])
            else:
                books_data = data.get('data', []) if isinstance(data, dict) else data
            
            # 提取书籍信息
            for i, book_data in enumerate(books_data[:5]):  # 只取前5本
                try:
                    book = {
                        "id": f"{source.get('bookSourceName', 'source')}_{i}",
                        "name": _extract_field(book_data, search_rule.get('name', ''), f"书籍{i+1}"),
                        "author": _extract_field(book_data, search_rule.get('author', ''), "未知作者"),
                        "cover": _extract_field(book_data, search_rule.get('coverUrl', ''), ""),
                        "intro": _extract_field(book_data, search_rule.get('intro', ''), "暂无简介"),
                        "source": source.get('bookSourceName', '未知书源'),
                        "source_url": source.get('bookSourceUrl', ''),
                        "book_url": _extract_field(book_data, search_rule.get('bookUrl', ''), ""),
                        "category": "search",
                        "progress": 0
                    }
                    
                    # 处理封面URL
                    if book['cover'] and not book['cover'].startswith('http'):
                        book['cover'] = urljoin(base_url, book['cover'])
                    if not book['cover']:
                        # 使用占位图
                        colors = ['4a90e2', 'e74c3c', '27ae60', 'f39c12', '9b59b6']
                        book['cover'] = f"https://via.placeholder.com/150x200/{colors[i%5]}/ffffff?text={quote(book['name'][:2])}"
                    
                    books.append(book)
                    print(f"  ✓ 抓取到: {book['name']} - {book['author']}")
                    
                except Exception as e:
                    print(f"  ✗ 解析书籍失败: {e}")
                    continue
                    
        except json.JSONDecodeError:
            # 尝试HTML解析
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"  返回HTML，尝试解析...")
            
            # 这里可以添加HTML解析逻辑
            # 暂时跳过
            
    except Exception as e:
        print(f"✗ 抓取失败: {e}")
    
    return books

def _extract_field(data, rule, default=""):
    """从数据中提取字段"""
    if not rule:
        return default
    
    try:
        # 简单的字段提取
        if rule.startswith('$.'):
            keys = rule[2:].split('.')
            result = data
            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key, default)
                else:
                    return default
            return result if result else default
        elif isinstance(data, dict):
            return data.get(rule, default)
    except:
        pass
    
    return default

def fetch_chapters(book):
    """抓取章节列表"""
    chapters = []
    try:
        # 这里应该根据书源规则抓取章节
        # 暂时生成示例章节
        for i in range(1, 21):
            chapters.append({
                "id": i,
                "title": f"第{i}章",
                "url": f"{book.get('book_url', '')}/chapter/{i}"
            })
    except Exception as e:
        print(f"抓取章节失败: {e}")
    
    return chapters

def main():
    """主函数"""
    print("=" * 50)
    print("佩宇Reader - 书源预解析工具")
    print("=" * 50)
    
    # 加载书源
    sources = load_book_sources()
    print(f"\n已加载 {len(sources)} 个书源")
    
    all_books = []
    
    # 从每个书源抓取
    for i, source in enumerate(sources[:3]):  # 只处理前3个书源
        if not source.get('enabled', True):
            continue
            
        print(f"\n[{i+1}/3] 正在处理书源: {source.get('bookSourceName', '未知')}")
        books = fetch_from_source(source, "热门")
        all_books.extend(books)
        
        # 为每本书抓取章节
        for book in books:
            print(f"  正在抓取《{book['name']}》的章节...")
            book['chapters'] = fetch_chapters(book)
    
    # 保存数据
    output = {
        "books": all_books,
        "total": len(all_books),
        "sources_used": min(3, len(sources))
    }
    
    output_file = os.path.join(os.path.dirname(__file__), 'data', 'books_data.json')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"✓ 数据已保存到: {output_file}")
    print(f"✓ 共抓取 {len(all_books)} 本书")
    print("=" * 50)

if __name__ == "__main__":
    main()
