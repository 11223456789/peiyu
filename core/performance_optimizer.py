"""
性能优化模块 - 数据库优化、缓存管理、连接池
"""
import sqlite3
import threading
import functools
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import OrderedDict
from pathlib import Path
import json
import hashlib


class DatabaseOptimizer:
    """数据库优化器 - 索引、查询优化、连接池"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._pool_lock = threading.Lock()
        self._connection_pool: List[sqlite3.Connection] = []
        self._max_pool_size = 10
        
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（连接池）"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            with self._pool_lock:
                if self._connection_pool:
                    self._local.connection = self._connection_pool.pop()
                else:
                    self._local.connection = sqlite3.connect(
                        self.db_path, 
                        check_same_thread=False,
                        timeout=30.0
                    )
                    self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _return_connection(self, conn: sqlite3.Connection):
        """归还连接到连接池"""
        with self._pool_lock:
            if len(self._connection_pool) < self._max_pool_size:
                self._connection_pool.append(conn)
            else:
                conn.close()
    
    def create_indexes(self):
        """创建性能优化索引"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 书籍表索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_books_name ON books(name)",
            "CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)",
            "CREATE INDEX IF NOT EXISTS idx_books_last_read ON books(last_read_time DESC)",
            "CREATE INDEX IF NOT EXISTS idx_books_added ON books(added_time DESC)",
            
            # 章节表索引
            "CREATE INDEX IF NOT EXISTS idx_chapters_book_id ON chapters(book_id)",
            "CREATE INDEX IF NOT EXISTS idx_chapters_book_idx ON chapters(book_id, idx)",
            
            # 阅读历史表索引
            "CREATE INDEX IF NOT EXISTS idx_history_book ON reading_history(book_id)",
            "CREATE INDEX IF NOT EXISTS idx_history_time ON reading_history(read_time DESC)",
            
            # 推荐表索引
            "CREATE INDEX IF NOT EXISTS idx_recommendations_time ON recommendations(recommended_at DESC)",
            
            # 成就表索引
            "CREATE INDEX IF NOT EXISTS idx_achievements_type ON achievements(type)",
            "CREATE INDEX IF NOT EXISTS idx_achievements_unlocked ON achievements(unlocked_at DESC)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError:
                pass  # 索引已存在
        
        conn.commit()
    
    def optimize_database(self):
        """数据库优化 - VACUUM, ANALYZE"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 分析表以优化查询计划
        cursor.execute("ANALYZE")
        
        # 优化数据库文件
        cursor.execute("VACUUM")
        
        conn.commit()
    
    def query_with_cache(self, query: str, params: tuple = (), 
                         cache_key: str = None, ttl: int = 300) -> List[Dict]:
        """带缓存的查询"""
        if cache_key is None:
            cache_key = hashlib.md5(f"{query}{params}".encode()).hexdigest()
        
        # 检查缓存
        cached = CacheManager.get(cache_key)
        if cached is not None:
            return cached
        
        # 执行查询
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # 存入缓存
        CacheManager.set(cache_key, results, ttl)
        
        return results


class CacheManager:
    """智能缓存管理器 - LRU + TTL"""
    
    _cache: Dict[str, Dict] = {}
    _lock = threading.RLock()
    _max_size = 1000
    _cleanup_interval = 60  # 秒
    _last_cleanup = time.time()
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """获取缓存值"""
        with cls._lock:
            cls._cleanup_if_needed()
            
            if key in cls._cache:
                item = cls._cache[key]
                if item['expires'] > time.time():
                    # 更新访问时间（LRU）
                    item['accessed'] = time.time()
                    return item['value']
                else:
                    del cls._cache[key]
            return None
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: int = 300):
        """设置缓存值"""
        with cls._lock:
            # 如果缓存已满，移除最久未使用的
            if len(cls._cache) >= cls._max_size:
                cls._evict_lru()
            
            cls._cache[key] = {
                'value': value,
                'expires': time.time() + ttl,
                'accessed': time.time()
            }
    
    @classmethod
    def delete(cls, key: str):
        """删除缓存"""
        with cls._lock:
            if key in cls._cache:
                del cls._cache[key]
    
    @classmethod
    def clear(cls):
        """清空缓存"""
        with cls._lock:
            cls._cache.clear()
    
    @classmethod
    def _evict_lru(cls):
        """移除最久未使用的项"""
        if cls._cache:
            oldest_key = min(cls._cache.keys(), 
                           key=lambda k: cls._cache[k]['accessed'])
            del cls._cache[oldest_key]
    
    @classmethod
    def _cleanup_if_needed(cls):
        """清理过期缓存"""
        current_time = time.time()
        if current_time - cls._last_cleanup > cls._cleanup_interval:
            expired_keys = [
                k for k, v in cls._cache.items() 
                if v['expires'] <= current_time
            ]
            for key in expired_keys:
                del cls._cache[key]
            cls._last_cleanup = current_time


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def paginate(query: str, page: int = 1, page_size: int = 20) -> str:
        """添加分页"""
        offset = (page - 1) * page_size
        return f"{query} LIMIT {page_size} OFFSET {offset}"
    
    @staticmethod
    def add_sorting(query: str, sort_by: str, order: str = "DESC") -> str:
        """添加排序"""
        valid_orders = ["ASC", "DESC"]
        if order.upper() not in valid_orders:
            order = "DESC"
        return f"{query} ORDER BY {sort_by} {order}"
    
    @staticmethod
    def build_search_query(table: str, fields: List[str], 
                          keyword: str, filters: Dict = None) -> tuple:
        """构建搜索查询"""
        conditions = []
        params = []
        
        # 关键词搜索
        if keyword:
            field_conditions = [f"{field} LIKE ?" for field in fields]
            conditions.append(f"({' OR '.join(field_conditions)})")
            params.extend([f"%{keyword}%"] * len(fields))
        
        # 过滤条件
        if filters:
            for field, value in filters.items():
                if value is not None:
                    conditions.append(f"{field} = ?")
                    params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        
        return query, params


def memoize(ttl: int = 300):
    """函数结果缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # 检查缓存
            result = CacheManager.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            CacheManager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class BatchProcessor:
    """批处理器 - 批量插入/更新"""
    
    def __init__(self, db_path: str, batch_size: int = 100):
        self.db_path = db_path
        self.batch_size = batch_size
        self._buffer: List[tuple] = []
        self._lock = threading.Lock()
    
    def add(self, item: tuple):
        """添加项目到缓冲区"""
        with self._lock:
            self._buffer.append(item)
            if len(self._buffer) >= self.batch_size:
                self.flush()
    
    def flush(self):
        """刷新缓冲区到数据库"""
        with self._lock:
            if not self._buffer:
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 批量插入
            try:
                cursor.executemany(
                    "INSERT INTO reading_history (book_id, chapter_index, chapter_title, position, read_time) VALUES (?, ?, ?, ?, ?)",
                    self._buffer
                )
                conn.commit()
            except Exception as e:
                print(f"批量插入失败: {e}")
            finally:
                conn.close()
            
            self._buffer.clear()


class PerformanceMonitor:
    """性能监控器"""
    
    _metrics: Dict[str, List[float]] = {}
    _lock = threading.Lock()
    
    @classmethod
    def record(cls, metric_name: str, value: float):
        """记录性能指标"""
        with cls._lock:
            if metric_name not in cls._metrics:
                cls._metrics[metric_name] = []
            cls._metrics[metric_name].append(value)
            
            # 只保留最近100条记录
            if len(cls._metrics[metric_name]) > 100:
                cls._metrics[metric_name] = cls._metrics[metric_name][-100:]
    
    @classmethod
    def get_stats(cls, metric_name: str) -> Dict:
        """获取统计信息"""
        with cls._lock:
            values = cls._metrics.get(metric_name, [])
            if not values:
                return {}
            
            return {
                'count': len(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'last': values[-1]
            }
    
    @classmethod
    def get_all_stats(cls) -> Dict:
        """获取所有统计"""
        with cls._lock:
            return {name: cls.get_stats(name) for name in cls._metrics.keys()}


def timed(metric_name: str):
    """性能计时装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            PerformanceMonitor.record(metric_name, elapsed)
            return result
        return wrapper
    return decorator


class FullTextSearch:
    """全文搜索模块 - 使用SQLite FTS5"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_fts()
    
    def _init_fts(self):
        """初始化FTS5虚拟表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 先检查books表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='books'")
        if not cursor.fetchone():
            # 创建books表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    author TEXT,
                    url TEXT,
                    cover TEXT,
                    intro TEXT,
                    source TEXT,
                    progress REAL DEFAULT 0,
                    current_chapter INTEGER DEFAULT 0,
                    current_position INTEGER DEFAULT 0,
                    added_time TEXT,
                    last_read TEXT,
                    reading INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0
                )
            ''')
        
        # 创建FTS5虚拟表
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
                name, author, intro,
                content='books',
                content_rowid='rowid'
            )
        ''')
        
        # 创建触发器保持同步
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS books_ai AFTER INSERT ON books BEGIN
                INSERT INTO books_fts(rowid, name, author, intro)
                VALUES (new.rowid, new.name, new.author, new.intro);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS books_ad AFTER DELETE ON books BEGIN
                INSERT INTO books_fts(books_fts, rowid, name, author, intro)
                VALUES ('delete', old.rowid, old.name, old.author, old.intro);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS books_au AFTER UPDATE ON books BEGIN
                INSERT INTO books_fts(books_fts, rowid, name, author, intro)
                VALUES ('delete', old.rowid, old.name, old.author, old.intro);
                INSERT INTO books_fts(rowid, name, author, intro)
                VALUES (new.rowid, new.name, new.author, new.intro);
            END
        ''')
        
        conn.commit()
        conn.close()
    
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """执行全文搜索"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 使用FTS5查询
        cursor.execute('''
            SELECT b.*, rank 
            FROM books_fts 
            JOIN books b ON books_fts.rowid = b.rowid
            WHERE books_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (query, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def rebuild_index(self):
        """重建FTS索引"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books_fts(books_fts) VALUES('rebuild')")
        conn.commit()
        conn.close()
