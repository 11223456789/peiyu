"""
核心模块 - 包含书源解析、书架管理和配置管理
"""
from .book_source import BookSource, BookSourceManager
from .bookshelf import Book, Chapter, BookshelfManager
from .config import ConfigManager, TextFormatter, AutoCacheManager
from .async_search import ConcurrentSearcher, SearchHistory, SourceHealthChecker

__all__ = [
    'BookSource',
    'BookSourceManager',
    'Book',
    'Chapter',
    'BookshelfManager',
    'ConfigManager',
    'TextFormatter',
    'AutoCacheManager',
    'ConcurrentSearcher',
    'SearchHistory',
    'SourceHealthChecker',
]
