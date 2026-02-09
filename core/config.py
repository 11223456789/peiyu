"""
配置管理模块 - 阅读主题、字体、排版设置
"""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from enum import Enum


class Theme(Enum):
    """主题枚举"""
    LIGHT = "light"
    DARK = "dark"
    SEPIA = "sepia"
    GREEN = "green"


@dataclass
class ReaderConfig:
    """阅读器配置"""

    # 主题设置
    theme: str = "dark"  # light, dark, sepia, green

    # 字体设置
    font_size: int = 16  # 字体大小
    line_height: float = 1.8  # 行间距倍数
    paragraph_spacing: int = 1  # 段落间距（空行数）
    text_width: int = 80  # 文本宽度（字符数）

    # 阅读设置
    lines_per_page: int = 25  # 每页显示行数
    auto_scroll: bool = False  # 自动滚动
    auto_scroll_speed: int = 3  # 自动滚动速度（秒）

    # 缓存设置
    auto_cache: bool = True  # 自动缓存章节
    cache_chapters_ahead: int = 3  # 提前缓存章节数
    max_cache_size_mb: int = 500  # 最大缓存大小(MB)

    # 搜索设置
    max_search_results: int = 20  # 最大搜索结果数
    search_timeout: int = 10  # 搜索超时(秒)
    concurrent_search: bool = True  # 并发搜索

    # 界面设置
    show_progress_bar: bool = True  # 显示进度条
    show_chapter_title: bool = True  # 显示章节标题
    show_time: bool = False  # 显示当前时间
    show_battery: bool = False  # 显示电量（如果支持）

    # 翻页设置
    page_turn_animation: bool = False  # 翻页动画（终端不支持，预留）
    tap_to_turn_page: bool = True  # 点击翻页

    # 其他
    last_read_book: str = ""  # 上次阅读的书籍ID
    check_update_on_startup: bool = True  # 启动时检查更新

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReaderConfig':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ConfigManager:
    """配置管理器"""

    # 主题配色方案
    THEMES = {
        "light": {
            "name": "白天",
            "bg_color": "white",
            "text_color": "black",
            "header_style": "bold blue",
            "border_style": "blue",
            "panel_style": "white on black",
            "highlight_style": "bold green",
            "dim_style": "dim"
        },
        "dark": {
            "name": "夜间",
            "bg_color": "black",
            "text_color": "white",
            "header_style": "bold cyan",
            "border_style": "cyan",
            "panel_style": "black on white",
            "highlight_style": "bold yellow",
            "dim_style": "dim white"
        },
        "sepia": {
            "name": "护眼",
            "bg_color": "#F5E6D3",
            "text_color": "#5C4033",
            "header_style": "bold #8B4513",
            "border_style": "#8B4513",
            "panel_style": "#F5E6D3 on #5C4033",
            "highlight_style": "bold #A0522D",
            "dim_style": "dim #8B7355"
        },
        "green": {
            "name": "绿底",
            "bg_color": "#0D3328",
            "text_color": "#90EE90",
            "header_style": "bold #00FF7F",
            "border_style": "#00FF7F",
            "panel_style": "#0D3328 on #90EE90",
            "highlight_style": "bold #7CFC00",
            "dim_style": "dim #3CB371"
        }
    }

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.expanduser('~/.legado_reader')

        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)

        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.config = ReaderConfig()

        self._load_config()

    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = ReaderConfig.from_dict(data)
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")
                self.config = ReaderConfig()

    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def get_config(self) -> ReaderConfig:
        """获取配置"""
        return self.config
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self.save_config()

    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()

    def get_theme(self) -> Dict[str, str]:
        """获取当前主题配置"""
        return self.THEMES.get(self.config.theme, self.THEMES["dark"])

    def set_theme(self, theme_name: str):
        """设置主题"""
        if theme_name in self.THEMES:
            self.config.theme = theme_name
            self.save_config()

    def list_themes(self) -> Dict[str, str]:
        """列出所有主题"""
        return {k: v["name"] for k, v in self.THEMES.items()}

    def reset_to_default(self):
        """重置为默认配置"""
        self.config = ReaderConfig()
        self.save_config()


class TextFormatter:
    """文本格式化器 - 根据配置格式化文本"""

    def __init__(self, config: ReaderConfig):
        self.config = config

    def format_content(self, content: str) -> str:
        """
        格式化章节内容
        包括：段落处理、自动换行、行间距等
        """
        if not content:
            return ""

        # 清理内容
        content = self._clean_content(content)

        # 分段处理
        paragraphs = content.split('\n')
        formatted_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 自动换行
            lines = self._wrap_text(para, self.config.text_width)
            formatted_paragraphs.extend(lines)

            # 添加段落间距
            for _ in range(self.config.paragraph_spacing):
                formatted_paragraphs.append('')

        return '\n'.join(formatted_paragraphs)

    def _clean_content(self, content: str) -> str:
        """清理内容"""
        import re

        # 移除多余空白
        content = re.sub(r'\s+', ' ', content)

        # 移除特殊字符
        content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', content)

        # 规范化换行
        content = re.sub(r'\n\s*\n+', '\n\n', content)

        return content.strip()

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """
        自动换行
        支持中文和英文混合文本
        """
        lines = []
        current_line = ""
        current_width = 0

        i = 0
        while i < len(text):
            char = text[i]

            # 中文字符占2个宽度
            char_width = 2 if ord(char) > 127 else 1

            if current_width + char_width > width:
                # 当前行已满，保存并开始新行
                if current_line:
                    lines.append(current_line)
                current_line = char
                current_width = char_width
            else:
                current_line += char
                current_width += char_width

            i += 1

        # 保存最后一行
        if current_line:
            lines.append(current_line)

        return lines

    def paginate(self, content: str) -> List[str]:
        """
        将内容分页
        返回每页的内容列表
        """
        formatted = self.format_content(content)
        lines = formatted.split('\n')

        pages = []
        current_page = []
        line_count = 0

        for line in lines:
            current_page.append(line)
            line_count += 1

            # 考虑行间距
            if line == '':
                line_count += int(self.config.line_height - 1)

            if line_count >= self.config.lines_per_page:
                pages.append('\n'.join(current_page))
                current_page = []
                line_count = 0

        # 保存最后一页
        if current_page:
            pages.append('\n'.join(current_page))

        return pages if pages else [formatted]

    def get_reading_progress(self, content: str, current_line: int) -> str:
        """获取阅读进度百分比"""
        lines = content.split('\n')
        total_lines = len(lines)

        if total_lines == 0:
            return "0%"

        progress = min(100, int((current_line / total_lines) * 100))
        return f"{progress}%"


class AutoCacheManager:
    """自动缓存管理器"""

    def __init__(self, bookshelf, source_manager, config: ReaderConfig):
        self.bookshelf = bookshelf
        self.source_manager = source_manager
        self.config = config
        self._cache_thread = None
        self._stop_cache = False

    def start_auto_cache(self, book_id: str, current_chapter: int):
        """启动自动缓存"""
        if not self.config.auto_cache:
            return

        import threading

        self._stop_cache = False
        self._cache_thread = threading.Thread(
            target=self._cache_worker,
            args=(book_id, current_chapter)
        )
        self._cache_thread.daemon = True
        self._cache_thread.start()

    def stop_auto_cache(self):
        """停止自动缓存"""
        self._stop_cache = True
        if self._cache_thread:
            self._cache_thread.join(timeout=1)

    def _cache_worker(self, book_id: str, current_chapter: int):
        """缓存工作线程"""
        book = self.bookshelf.get_book(book_id)
        if not book:
            return

        chapters = self.bookshelf.get_chapters(book_id)
        if not chapters:
            return

        # 缓存后续章节
        for i in range(current_chapter + 1,
                       min(current_chapter + 1 + self.config.cache_chapters_ahead, len(chapters))):
            if self._stop_cache:
                break

            # 检查是否已缓存
            if self.bookshelf.is_chapter_cached(book_id, i):
                continue

            try:
                chapter = chapters[i]
                content = self.source_manager.get_chapter_content(
                    book.source_name, chapter.url
                )

                if content:
                    self.bookshelf.save_chapter_content(book_id, i, content)

            except Exception as e:
                print(f"自动缓存失败: {e}")

    def clean_old_cache(self, max_size_mb: int = None):
        """清理旧缓存"""
        if max_size_mb is None:
            max_size_mb = self.config.max_cache_size_mb

        import sqlite3

        # 获取缓存大小
        with sqlite3.connect(self.bookshelf.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(LENGTH(content)) FROM chapters WHERE is_cached = 1
            ''')
            result = cursor.fetchone()
            total_size = result[0] if result[0] else 0

        # 转换为MB
        total_size_mb = total_size / (1024 * 1024)

        if total_size_mb > max_size_mb:
            # 删除最旧的缓存
            with sqlite3.connect(self.bookshelf.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE chapters
                    SET content = '', is_cached = 0
                    WHERE id IN (
                        SELECT id FROM chapters
                        WHERE is_cached = 1
                        ORDER BY idx ASC
                        LIMIT (SELECT COUNT(*) / 4 FROM chapters WHERE is_cached = 1)
                    )
                ''')
                conn.commit()

            print(f"已清理缓存，释放空间")
