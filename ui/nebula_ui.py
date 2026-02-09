"""
PeiYu UI - 佩宇界面系统
完全原创的UI设计，独特的视觉体验
"""

from typing import List, Dict, Any, Optional, Callable
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich.box import Box, ROUNDED, DOUBLE, HEAVY, SIMPLE
from rich.style import Style
from rich.theme import Theme
import time
import random


# 佩宇主题配色 - 完全原创
PEIYU_THEMES = {
    "cosmic": {
        "name": "宇宙深空",
        "bg": "#0a0a0f",
        "fg": "#e0e0ff",
        "accent1": "#ff6b9d",  # 星云粉
        "accent2": "#00d4ff",  # 星尘蓝
        "accent3": "#9d4edd",  # 深空紫
        "accent4": "#ff9f1c",  # 恒星橙
        "dim": "#4a4a6a",
        "highlight": "#ffffff",
        "border": "#2d2d44",
    },
    "aurora": {
        "name": "极光之夜",
        "bg": "#0d1f1d",
        "fg": "#d4f1e0",
        "accent1": "#00ff9f",  # 极光绿
        "accent2": "#00d9ff",  # 冰蓝
        "accent3": "#7b2cbf",  # 极光紫
        "accent4": "#ff006e",  # 玫瑰红
        "dim": "#2d4a44",
        "highlight": "#ffffff",
        "border": "#1a3d38",
    },
    "solar": {
        "name": "恒星耀斑",
        "bg": "#1a0f00",
        "fg": "#ffe4c4",
        "accent1": "#ff4500",  # 火焰红
        "accent2": "#ffd700",  # 金色
        "accent3": "#ff6b35",  # 太阳橙
        "accent4": "#ff1744",  # 耀斑红
        "dim": "#5a3d20",
        "highlight": "#ffffff",
        "border": "#3d2800",
    },
    "nebula": {
        "name": "星云迷雾",
        "bg": "#1a0a2e",
        "fg": "#e8d5f2",
        "accent1": "#ff00ff",  # 亮紫
        "accent2": "#00ffff",  # 青蓝
        "accent3": "#ff1493",  # 深粉
        "accent4": "#7fff00",  # 酸橙绿
        "dim": "#4a3050",
        "highlight": "#ffffff",
        "border": "#2d1b3e",
    },
}


class PeiYuTheme:
    """佩宇主题管理器"""
    
    def __init__(self, theme_name: str = "cosmic"):
        self.theme_name = theme_name
        self.colors = PEIYU_THEMES.get(theme_name, PEIYU_THEMES["cosmic"])
        self.console = Console(theme=self._create_rich_theme())
    
    def _create_rich_theme(self) -> Theme:
        """创建Rich主题"""
        return Theme({
            "peiyu.text": self.colors["fg"],
            "peiyu.accent1": self.colors["accent1"],
            "peiyu.accent2": self.colors["accent2"],
            "peiyu.accent3": self.colors["accent3"],
            "peiyu.accent4": self.colors["accent4"],
            "peiyu.dim": self.colors["dim"],
            "peiyu.highlight": self.colors["highlight"],
            "peiyu.border": self.colors["border"],
        })
    
    def switch_theme(self, theme_name: str):
        """切换主题"""
        self.theme_name = theme_name
        self.colors = PEIYU_THEMES.get(theme_name, PEIYU_THEMES["cosmic"])
        self.console = Console(theme=self._create_rich_theme())


class PeiYuBox(Box):
    """自定义佩宇边框样式"""
    
    def __init__(self):
        super().__init__(
            "╭─┬╮\n"
            "│ ││\n"
            "├─┼┤\n"
            "│ ││\n"
            "╰─┴╯",
            ascii=False,
        )


class StarField:
    """星空背景效果"""
    
    STARS = ["✦", "✧", "⋆", "✶", "✷", "✸", "✹", "✺"]
    
    @classmethod
    def generate(cls, width: int = 80, height: int = 3) -> Text:
        """生成星空背景"""
        lines = []
        for _ in range(height):
            line = [" "] * width
            # 随机放置星星
            for _ in range(random.randint(3, 8)):
                pos = random.randint(0, width - 1)
                line[pos] = random.choice(cls.STARS)
            lines.append("".join(line))
        
        text = Text("\n".join(lines))
        text.stylize("dim #666699")
        return text


class PeiYuHeader:
    """佩宇标题组件"""
    
    @staticmethod
    def create(title: str, subtitle: str = "", theme: PeiYuTheme = None) -> Panel:
        """创建佩宇风格标题"""
        if theme is None:
            theme = PeiYuTheme()
        
        # 创建装饰线
        deco_line = "━" * 50
        
        # 主标题
        main_text = Text()
        main_text.append("◈ ", style=theme.colors["accent1"])
        main_text.append(title, style=f"bold {theme.colors['highlight']}")
        main_text.append(" ◈", style=theme.colors["accent1"])
        
        # 副标题
        content = Text()
        content.append(main_text)
        content.append("\n")
        content.append(deco_line, style=theme.colors["accent2"])
        
        if subtitle:
            content.append("\n")
            content.append(f"  {subtitle}", style=f"dim {theme.colors['fg']}")
        
        # 添加星空背景
        starfield = StarField.generate(width=60, height=2)
        content.append("\n")
        content.append(starfield)
        
        return Panel(
            content,
            border_style=theme.colors["accent3"],
            box=DOUBLE,
            padding=(1, 2),
        )


class PeiYuMenu:
    """佩宇菜单组件 - 创新的环形菜单风格"""
    
    ICONS = {
        "search": "🔍",
        "bookshelf": "📚",
        "source": "🌐",
        "settings": "⚙️",
        "exit": "🚪",
        "back": "◀",
        "next": "▶",
        "star": "★",
        "heart": "♥",
        "book": "📖",
        "download": "⬇",
        "info": "ℹ",
    }
    
    def __init__(self, theme: PeiYuTheme = None):
        self.theme = theme or PeiYuTheme()
    
    def create_vertical(self, items: List[Dict[str, Any]], title: str = "") -> Panel:
        """创建垂直佩宇菜单"""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("icon", style=self.theme.colors["accent2"], width=4)
        table.add_column("text", style=self.theme.colors["fg"])
        table.add_column("hotkey", style=f"dim {self.theme.colors['dim']}", width=10)
        
        for i, item in enumerate(items, 1):
            icon = item.get("icon", "•")
            text = item.get("text", "")
            hotkey = item.get("hotkey", str(i))
            
            # 高亮当前选中项
            if item.get("selected"):
                table.add_row(
                    f"[{self.theme.colors['accent1']}]{icon}[/{self.theme.colors['accent1']}]",
                    f"[bold {self.theme.colors['highlight']}]{text}[/bold {self.theme.colors['highlight']}]",
                    f"[{self.theme.colors['accent4']}]{hotkey}[/{self.theme.colors['accent4']}]"
                )
            else:
                table.add_row(icon, text, hotkey)
        
        return Panel(
            table,
            title=f"[bold {self.theme.colors['accent1']}]{title}[/bold {self.theme.colors['accent1']}]" if title else None,
            border_style=self.theme.colors["border"],
            box=ROUNDED,
        )
    
    def create_grid(self, items: List[Dict[str, Any]], cols: int = 2) -> Table:
        """创建网格佩宇菜单"""
        table = Table(show_header=False, box=None, padding=(1, 2))
        
        for _ in range(cols):
            table.add_column(style=self.theme.colors["fg"])
        
        # 分组显示
        for i in range(0, len(items), cols):
            row_items = items[i:i + cols]
            row = []
            for item in row_items:
                icon = item.get("icon", "◆")
                text = item.get("text", "")
                hotkey = item.get("hotkey", "")
                
                cell = Text()
                cell.append(f"{icon} ", style=self.theme.colors["accent2"])
                cell.append(text, style=self.theme.colors["fg"])
                if hotkey:
                    cell.append(f" [{hotkey}]", style=f"dim {self.theme.colors['dim']}")
                row.append(cell)
            
            # 填充空列
            while len(row) < cols:
                row.append("")
            
            table.add_row(*row)
        
        return table


class PeiYuBookCard:
    """佩宇书籍卡片组件"""
    
    def __init__(self, theme: PeiYuTheme = None):
        self.theme = theme or PeiYuTheme()
    
    def create(self, book: Dict[str, Any], index: int = 0) -> Panel:
        """创建书籍卡片"""
        title = book.get("title", "未知书名")
        author = book.get("author", "未知作者")
        progress = book.get("progress", 0)
        last_read = book.get("last_read", "")
        chapter = book.get("current_chapter", "")
        
        # 进度条
        progress_width = 20
        filled = int(progress / 100 * progress_width)
        progress_bar = "█" * filled + "░" * (progress_width - filled)
        
        content = Text()
        
        # 序号和标题
        content.append(f"{index:2d}. ", style=self.theme.colors["accent2"])
        content.append(f"{title}\n", style=f"bold {self.theme.colors['highlight']}")
        
        # 作者
        content.append(f"   作者: ", style=f"dim {self.theme.colors['dim']}")
        content.append(f"{author}\n", style=self.theme.colors["accent3"])
        
        # 进度
        content.append(f"   进度: ", style=f"dim {self.theme.colors['dim']}")
        content.append(f"{progress_bar} ", style=self.theme.colors["accent1"])
        content.append(f"{progress}%\n", style=self.theme.colors["accent4"])
        
        # 当前章节
        if chapter:
            content.append(f"   读到: ", style=f"dim {self.theme.colors['dim']}")
            content.append(f"{chapter}\n", style=self.theme.colors["fg"])
        
        # 上次阅读时间
        if last_read:
            content.append(f"   时间: ", style=f"dim {self.theme.colors['dim']}")
            content.append(last_read, style=f"dim {self.theme.colors['dim']}")
        
        return Panel(
            content,
            border_style=self.theme.colors["border"],
            box=SIMPLE,
            padding=(1, 2),
        )


class PeiYuReaderUI:
    """佩宇阅读器UI组件 - 创新的沉浸式阅读界面"""
    
    def __init__(self, theme: PeiYuTheme = None):
        self.theme = theme or PeiYuTheme()
        self.console = self.theme.console
    
    def create_page(self, content: str, chapter_title: str, 
                   page_info: str, theme: PeiYuTheme = None) -> Layout:
        """创建阅读页面布局"""
        if theme is None:
            theme = self.theme
        
        layout = Layout()
        
        # 顶部章节标题
        header = self._create_reader_header(chapter_title, theme)
        
        # 中间内容区域
        body = self._create_reader_body(content, theme)
        
        # 底部状态栏
        footer = self._create_reader_footer(page_info, theme)
        
        layout.split_column(
            Layout(header, size=3),
            Layout(body),
            Layout(footer, size=1),
        )
        
        return layout
    
    def _create_reader_header(self, title: str, theme: PeiYuTheme) -> Panel:
        """创建阅读器头部"""
        text = Text()
        text.append("◆ ", style=theme.colors["accent1"])
        text.append(title, style=f"bold {theme.colors['highlight']}")
        text.append(" ◆", style=theme.colors["accent1"])
        
        return Panel(
            Align.center(text),
            border_style=theme.colors["border"],
            box=SIMPLE,
            padding=(0, 1),
        )
    
    def _create_reader_body(self, content: str, theme: PeiYuTheme) -> Panel:
        """创建阅读器内容区域"""
        # 处理内容格式
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                # 段落首行缩进
                formatted_lines.append(f"    {line}")
            else:
                formatted_lines.append("")
        
        text = Text("\n".join(formatted_lines))
        text.stylize(theme.colors["fg"])
        
        return Panel(
            text,
            border_style=theme.colors["border"],
            box=SIMPLE,
            padding=(1, 2),
        )
    
    def _create_reader_footer(self, info: str, theme: PeiYuTheme) -> Text:
        """创建阅读器底部状态栏"""
        text = Text()
        text.append("◀ 上一页 ", style=f"dim {theme.colors['dim']}")
        text.append("|", style=theme.colors["accent2"])
        text.append(f" {info} ", style=theme.colors["accent4"])
        text.append("|", style=theme.colors["accent2"])
        text.append(" 下一页 ▶", style=f"dim {theme.colors['dim']}")
        text.append("  ", style="")
        text.append("[Q]退出 ", style=f"dim {theme.colors['dim']}")
        text.append("[C]目录", style=f"dim {theme.colors['dim']}")
        
        return text


class PeiYuProgress:
    """佩宇进度组件"""
    
    def __init__(self, theme: PeiYuTheme = None):
        self.theme = theme or PeiYuTheme()
    
    def create(self, current: int, total: int, width: int = 40) -> Text:
        """创建进度条"""
        percentage = current / total if total > 0 else 0
        filled = int(percentage * width)
        
        # 使用渐变效果
        bar = Text()
        bar.append("╾", style=self.theme.colors["accent2"])
        
        for i in range(width):
            if i < filled:
                # 渐变颜色
                if i < width * 0.3:
                    color = self.theme.colors["accent1"]
                elif i < width * 0.7:
                    color = self.theme.colors["accent2"]
                else:
                    color = self.theme.colors["accent3"]
                bar.append("━", style=color)
            else:
                bar.append("─", style=f"dim {self.theme.colors['dim']}")
        
        bar.append("╼", style=self.theme.colors["accent2"])
        bar.append(f" {current}/{total} ({percentage*100:.1f}%)", 
                  style=self.theme.colors["accent4"])
        
        return bar


class PeiYuSearchBox:
    """佩宇搜索框组件"""
    
    def __init__(self, theme: PeiYuTheme = None):
        self.theme = theme or PeiYuTheme()
    
    def create(self, keyword: str = "", history: List[str] = None) -> Panel:
        """创建搜索框"""
        content = Text()
        
        # 搜索图标和输入框
        content.append("🔮 ", style=self.theme.colors["accent2"])
        content.append("搜索: ", style=f"bold {self.theme.colors['highlight']}")
        
        if keyword:
            content.append(keyword, style=self.theme.colors["accent1"])
            content.append("█", style=self.theme.colors["accent2"])  # 光标
        else:
            content.append("█", style=self.theme.colors["accent2"])  # 光标
        
        # 历史记录提示
        if history:
            content.append("\n\n")
            content.append("  历史: ", style=f"dim {self.theme.colors['dim']}")
            for i, h in enumerate(history[:5], 1):
                content.append(f"[{i}]{h} ", style=self.theme.colors["accent3"])
        
        return Panel(
            content,
            title=f"[bold {self.theme.colors['accent1']}]佩宇搜索[/bold {self.theme.colors['accent1']}]",
            border_style=self.theme.colors["accent2"],
            box=DOUBLE,
            padding=(1, 2),
        )


class PeiYuNotification:
    """佩宇通知组件"""
    
    ICONS = {
        "success": "✦",
        "error": "✦",
        "info": "✦",
        "warning": "✦",
    }
    
    COLORS = {
        "success": "accent2",
        "error": "accent4",
        "info": "accent3",
        "warning": "accent1",
    }
    
    @classmethod
    def create(cls, message: str, notif_type: str = "info", 
               theme: PeiYuTheme = None) -> Panel:
        """创建通知"""
        if theme is None:
            theme = PeiYuTheme()
        
        icon = cls.ICONS.get(notif_type, "✦")
        color_attr = cls.COLORS.get(notif_type, "accent3")
        color = theme.colors[color_attr]
        
        content = Text()
        content.append(f"{icon} ", style=color)
        content.append(message, style=theme.colors["fg"])
        
        return Panel(
            content,
            border_style=color,
            box=SIMPLE,
            padding=(1, 2),
        )


# 导出主要组件
__all__ = [
    'PeiYuTheme',
    'PeiYuHeader',
    'PeiYuMenu',
    'PeiYuBookCard',
    'PeiYuReader',
    'PeiYuProgress',
    'PeiYuSearchBox',
    'PeiYuNotification',
    'StarField',
    'PEIYU_THEMES',
]
