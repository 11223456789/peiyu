"""
书架管理模块 - 管理本地书籍、阅读进度和缓存
"""
import json
import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Book:
    """书籍数据模型"""
    name: str = ""
    author: str = ""
    cover_url: str = ""
    intro: str = ""
    book_url: str = ""
    toc_url: str = ""
    source_name: str = ""
    kind: str = ""
    last_chapter: str = ""

    # 阅读进度
    current_chapter_index: int = 0
    current_chapter_title: str = ""
    current_position: int = 0  # 章节内位置

    # 元数据
    added_time: str = field(default_factory=lambda: datetime.now().isoformat())
    last_read_time: str = ""
    total_chapters: int = 0
    is_finished: bool = False

    # 本地缓存
    chapters_cached: bool = False
    content_cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Book':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Chapter:
    """章节数据模型"""
    title: str = ""
    url: str = ""
    index: int = 0
    content: str = ""
    is_cached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BookshelfManager:
    """书架管理器"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.expanduser('~'), '.legado_reader')

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.books_dir = self.data_dir / 'books'
        self.books_dir.mkdir(exist_ok=True)

        self.cache_dir = self.data_dir / 'cache'
        self.cache_dir.mkdir(exist_ok=True)

        self.db_path = self.data_dir / 'bookshelf.db'
        self._init_database()

        # 内存中的书架
        self.books: Dict[str, Book] = {}
        self._load_books()

    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 书籍表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    author TEXT,
                    cover_url TEXT,
                    intro TEXT,
                    book_url TEXT,
                    toc_url TEXT,
                    source_name TEXT,
                    kind TEXT,
                    last_chapter TEXT,
                    current_chapter_index INTEGER DEFAULT 0,
                    current_chapter_title TEXT,
                    current_position INTEGER DEFAULT 0,
                    added_time TEXT,
                    last_read_time TEXT,
                    total_chapters INTEGER DEFAULT 0,
                    is_finished INTEGER DEFAULT 0,
                    chapters_cached INTEGER DEFAULT 0,
                    content_cached INTEGER DEFAULT 0
                )
            ''')

            # 章节表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chapters (
                    id TEXT PRIMARY KEY,
                    book_id TEXT,
                    title TEXT,
                    url TEXT,
                    idx INTEGER,
                    content TEXT,
                    is_cached INTEGER DEFAULT 0,
                    FOREIGN KEY (book_id) REFERENCES books(id)
                )
            ''')

            # 阅读历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reading_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT,
                    chapter_index INTEGER,
                    chapter_title TEXT,
                    position INTEGER,
                    read_time TEXT,
                    FOREIGN KEY (book_id) REFERENCES books(id)
                )
            ''')

            conn.commit()

    def _load_books(self):
        """从数据库加载书籍"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM books')

            for row in cursor.fetchall():
                book = Book(
                    name=row['name'],
                    author=row['author'],
                    cover_url=row['cover_url'],
                    intro=row['intro'],
                    book_url=row['book_url'],
                    toc_url=row['toc_url'],
                    source_name=row['source_name'],
                    kind=row['kind'],
                    last_chapter=row['last_chapter'],
                    current_chapter_index=row['current_chapter_index'],
                    current_chapter_title=row['current_chapter_title'],
                    current_position=row['current_position'],
                    added_time=row['added_time'],
                    last_read_time=row['last_read_time'],
                    total_chapters=row['total_chapters'],
                    is_finished=bool(row['is_finished']),
                    chapters_cached=bool(row['chapters_cached']),
                    content_cached=bool(row['content_cached'])
                )
                self.books[row['id']] = book

    def _generate_book_id(self, book: Book) -> str:
        """生成书籍唯一ID"""
        key = f"{book.name}_{book.author}_{book.source_name}"
        return hashlib.md5(key.encode()).hexdigest()

    def add_book(self, book: Book) -> str:
        """添加书籍到书架"""
        book_id = self._generate_book_id(book)

        if book_id in self.books:
            return book_id

        self.books[book_id] = book

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                book_id, book.name, book.author, book.cover_url, book.intro,
                book.book_url, book.toc_url, book.source_name, book.kind,
                book.last_chapter, book.current_chapter_index, book.current_chapter_title,
                book.current_position, book.added_time, book.last_read_time,
                book.total_chapters, int(book.is_finished), int(book.chapters_cached),
                int(book.content_cached)
            ))
            conn.commit()

        return book_id

    def remove_book(self, book_id: str) -> bool:
        """从书架移除书籍"""
        if book_id not in self.books:
            return False

        del self.books[book_id]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
            cursor.execute('DELETE FROM chapters WHERE book_id = ?', (book_id,))
            cursor.execute('DELETE FROM reading_history WHERE book_id = ?', (book_id,))
            conn.commit()

        # 删除缓存文件
        cache_file = self.cache_dir / f'{book_id}.json'
        if cache_file.exists():
            cache_file.unlink()

        return True

    def get_book(self, book_id: str) -> Optional[Book]:
        """获取书籍信息"""
        return self.books.get(book_id)

    def update_book_progress(self, book_id: str, chapter_index: int,
                            chapter_title: str, position: int = 0):
        """更新阅读进度"""
        if book_id not in self.books:
            return

        book = self.books[book_id]
        book.current_chapter_index = chapter_index
        book.current_chapter_title = chapter_title
        book.current_position = position
        book.last_read_time = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE books SET
                    current_chapter_index = ?,
                    current_chapter_title = ?,
                    current_position = ?,
                    last_read_time = ?
                WHERE id = ?
            ''', (chapter_index, chapter_title, position, book.last_read_time, book_id))

            # 记录阅读历史
            cursor.execute('''
                INSERT INTO reading_history (book_id, chapter_index, chapter_title, position, read_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (book_id, chapter_index, chapter_title, position, book.last_read_time))

            conn.commit()

    def list_books(self) -> List[Book]:
        """列出所有书籍"""
        return list(self.books.values())

    def get_recent_books(self, limit: int = 10) -> List[Book]:
        """获取最近阅读的书籍"""
        sorted_books = sorted(
            [b for b in self.books.values() if b.last_read_time],
            key=lambda x: x.last_read_time,
            reverse=True
        )
        return sorted_books[:limit]

    # ==================== 章节管理 ====================

    def save_chapters(self, book_id: str, chapters: List[Chapter]):
        """保存章节列表"""
        if book_id not in self.books:
            return

        book = self.books[book_id]
        book.total_chapters = len(chapters)
        book.chapters_cached = True

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 删除旧章节
            cursor.execute('DELETE FROM chapters WHERE book_id = ?', (book_id,))

            # 插入新章节
            for idx, chapter in enumerate(chapters):
                chapter_id = f"{book_id}_{idx}"
                cursor.execute('''
                    INSERT INTO chapters (id, book_id, title, url, idx, content, is_cached)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (chapter_id, book_id, chapter.title, chapter.url, idx, '', 0))

            cursor.execute('''
                UPDATE books SET total_chapters = ?, chapters_cached = ? WHERE id = ?
            ''', (len(chapters), 1, book_id))

            conn.commit()

    def get_chapters(self, book_id: str) -> List[Chapter]:
        """获取章节列表"""
        chapters = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM chapters WHERE book_id = ? ORDER BY idx
            ''', (book_id,))

            for row in cursor.fetchall():
                chapter = Chapter(
                    title=row['title'],
                    url=row['url'],
                    index=row['idx'],
                    content=row['content'] if row['is_cached'] else '',
                    is_cached=bool(row['is_cached'])
                )
                chapters.append(chapter)

        return chapters

    def get_chapter(self, book_id: str, chapter_index: int) -> Optional[Chapter]:
        """获取单个章节"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM chapters WHERE book_id = ? AND idx = ?
            ''', (book_id, chapter_index))

            row = cursor.fetchone()
            if row:
                return Chapter(
                    title=row['title'],
                    url=row['url'],
                    index=row['idx'],
                    content=row['content'] if row['is_cached'] else '',
                    is_cached=bool(row['is_cached'])
                )
        return None

    def save_chapter_content(self, book_id: str, chapter_index: int, content: str):
        """保存章节内容"""
        chapter_id = f"{book_id}_{chapter_index}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chapters SET content = ?, is_cached = 1 WHERE id = ?
            ''', (content, chapter_id))
            conn.commit()

    def is_chapter_cached(self, book_id: str, chapter_index: int) -> bool:
        """检查章节是否已缓存"""
        chapter_id = f"{book_id}_{chapter_index}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT is_cached FROM chapters WHERE id = ?', (chapter_id,))
            row = cursor.fetchone()
            return bool(row[0]) if row else False

    # ==================== 批量缓存 ====================

    def cache_book_content(self, book_id: str, source_manager,
                          start_chapter: int = 0, end_chapter: int = None,
                          progress_callback=None):
        """批量缓存书籍内容"""
        book = self.get_book(book_id)
        if not book:
            return False

        chapters = self.get_chapters(book_id)
        if not chapters:
            return False

        if end_chapter is None:
            end_chapter = len(chapters)

        total = end_chapter - start_chapter
        cached = 0

        for i in range(start_chapter, min(end_chapter, len(chapters))):
            chapter = chapters[i]

            if self.is_chapter_cached(book_id, i):
                cached += 1
                if progress_callback:
                    progress_callback(cached, total, chapter.title, True)
                continue

            try:
                content = source_manager.get_chapter_content(
                    book.source_name, chapter.url
                )

                if content:
                    self.save_chapter_content(book_id, i, content)
                    cached += 1

                if progress_callback:
                    progress_callback(cached, total, chapter.title, bool(content))

            except Exception as e:
                print(f"缓存章节失败 [{chapter.title}]: {e}")
                if progress_callback:
                    progress_callback(cached, total, chapter.title, False)

        # 更新缓存状态
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE books SET content_cached = ? WHERE id = ?
            ''', (1 if cached == total else 0, book_id))
            conn.commit()

        return True

    # ==================== 导入导出 ====================

    def export_book(self, book_id: str, output_path: str, format: str = 'txt'):
        """导出书籍"""
        book = self.get_book(book_id)
        if not book:
            return False

        chapters = self.get_chapters(book_id)

        if format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"《{book.name}》\n")
                f.write(f"作者：{book.author}\n")
                f.write(f"来源：{book.source_name}\n")
                f.write("=" * 50 + "\n\n")

                for chapter in chapters:
                    f.write(f"\n{chapter.title}\n")
                    f.write("-" * 30 + "\n")

                    if chapter.is_cached and chapter.content:
                        f.write(chapter.content)
                    else:
                        f.write("[章节内容未缓存]\n")

                    f.write("\n\n")

        elif format == 'json':
            data = {
                'book': book.to_dict(),
                'chapters': [c.to_dict() for c in chapters]
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """获取阅读统计"""
        stats = {
            'total_books': len(self.books),
            'finished_books': sum(1 for b in self.books.values() if b.is_finished),
            'total_chapters_cached': 0,
            'total_reading_time': 0
        }

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 缓存章节数
            cursor.execute('SELECT COUNT(*) FROM chapters WHERE is_cached = 1')
            result = cursor.fetchone()
            stats['total_chapters_cached'] = result[0] if result else 0

            # 阅读历史记录数
            cursor.execute('SELECT COUNT(*) FROM reading_history')
            result = cursor.fetchone()
            stats['total_read_records'] = result[0] if result else 0

        return stats
