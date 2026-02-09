"""
佩宇Reader - 增强版CLI界面
提供高级UI功能和交互体验
"""

from typing import Optional, List, Dict, Any, Callable
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich.columns import Columns
from rich.tree import Tree
from rich.syntax import Syntax
import time
import asyncio
from datetime import datetime

from .cli import ReaderUI, ContentReader, BookSelector, SearchInterface

console = Console()


class EnhancedReaderUI(ReaderUI):
    """增强版阅读器UI"""
    
    def __init__(self):
        super().__init__()
        self.theme = {
            "primary": "cyan",
            "secondary": "green",
            "accent": "yellow",
            "error": "red",
            "warning": "yellow",
            "success": "green",
            "info": "blue"
        }
    
    def show_welcome(self):
        """显示欢迎界面"""
        welcome_text = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██████╗ ███████╗██╗██╗   ██╗██████╗ ███████╗ █████╗ ██████╗ ███████╗██████╗  ║
║   ██╔══██╗██╔════╝██║██║   ██║██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗ ║
║   ██████╔╝█████╗  ██║██║   ██║██████╔╝█████╗  ███████║██║  ██║█████╗  ██████╔╝ ║
║   ██╔═══╝ ██╔══╝  ██║╚██╗ ██╔╝██╔══██╗██╔══╝  ██╔══██║██║  ██║██╔══╝  ██╔══██╗ ║
║   ██║     ███████╗██║ ╚████╔╝ ██║  ██║██║     ██║  ██║██████╔╝███████╗██║  ██║ ║
║   ╚═╝     ╚══════╝╚═╝  ╚═══╝  ╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝ ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        
        self.console.print(Panel(
            Text(welcome_text, style="bold cyan", justify="center"),
            border_style="cyan",
            title="[bold]佩宇Reader - 智能阅读器[/bold]",
            subtitle="[dim]基于Legado书源的高级阅读体验[/dim]"
        ))
        
        # 显示版本信息
        version_info = """
[dim]版本: 2.0.0 | Python 3.8+ | 支持书源: 笔趣阁、番茄小说、起点等[/dim]
        """
        self.console.print(Align.center(Text.from_markup(version_info)))
    
    def show_main_menu(self) -> str:
        """显示主菜单"""
        menu_items = [
            ("📚", "我的书架", "管理您的书籍收藏"),
            ("🔍", "搜索书籍", "从网络书源搜索新书"),
            ("📖", "继续阅读", "回到上次阅读的位置"),
            ("🎯", "智能推荐", "AI为您推荐好书"),
            ("📊", "阅读统计", "查看您的阅读数据"),
            ("🏆", "成就系统", "解锁阅读成就"),
            ("⚙️ ", "阅读设置", "自定义阅读体验"),
            ("💾", "数据管理", "备份、同步、导入导出"),
            ("🔊", "语音朗读", "TTS语音朗读功能"),
            ("❓", "帮助中心", "使用指南和快捷键"),
            ("🚪", "退出程序", "保存数据并退出"),
        ]
        
        self.console.print("\n[bold cyan]═══ 主菜单 ═══[/bold cyan]\n")
        
        for i, (icon, title, desc) in enumerate(menu_items, 1):
            self.console.print(f"  [{self.theme['primary']}]{i:2d}.[/] {icon} [bold]{title}[/] - [dim]{desc}[/]")
        
        return Prompt.ask("\n[bold]请选择操作[/bold]", choices=[str(i) for i in range(1, 12)])
    
    def show_bookshelf(self, books: List[Dict[str, Any]], reading_book: Optional[str] = None):
        """显示书架"""
        if not books:
            self.console.print(Panel(
                "[yellow]书架是空的，快去搜索添加书籍吧！[/yellow]",
                title="📚 我的书架",
                border_style="yellow"
            ))
            return None
        
        # 创建表格
        table = Table(
            title=f"📚 我的书架 (共 {len(books)} 本)",
            border_style="cyan",
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("序号", style="cyan", width=4, justify="center")
        table.add_column("书名", style="white", min_width=20)
        table.add_column("作者", style="green", width=15)
        table.add_column("进度", style="yellow", width=10)
        table.add_column("状态", style="blue", width=8)
        table.add_column("最后阅读", style="dim", width=12)
        
        for i, book in enumerate(books, 1):
            name = book.get('name', '未知')
            if reading_book and book.get('id') == reading_book:
                name = f"[bold green]▶ {name}[/]"
            
            progress = book.get('progress', 0)
            progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
            
            status = "在读" if book.get('reading', False) else "未读"
            if book.get('completed', False):
                status = "已读完"
            
            last_read = book.get('last_read', '从未')
            if last_read and last_read != '从未':
                try:
                    last_read = last_read.split()[0]  # 只显示日期
                except:
                    pass
            
            table.add_row(
                str(i),
                name,
                book.get('author', '未知'),
                f"{progress_bar} {progress}%",
                status,
                str(last_read)
            )
        
        self.console.print(table)
        
        # 显示操作选项
        self.console.print("\n[dim]操作: [数字]选择书籍 [d]删除 [r]刷新 [0]返回[/dim]")
        return Prompt.ask("选择")
    
    def show_book_detail(self, book: Dict[str, Any]):
        """显示书籍详情"""
        # 创建信息面板
        info_text = f"""
[bold]{book.get('name', '未知')}[/bold]

[cyan]作者:[/] {book.get('author', '未知')}
[cyan]来源:[/] {book.get('source', '未知')}
[cyan]进度:[/] {book.get('progress', 0)}%
[cyan]状态:[/] {'在读' if book.get('reading', False) else '未读'}
[cyan]添加时间:[/] {book.get('added_time', '未知')}
[cyan]最后阅读:[/] {book.get('last_read', '从未')}
        """
        
        self.console.print(Panel(
            info_text,
            title="📖 书籍详情",
            border_style="cyan"
        ))
        
        # 显示操作菜单
        actions = [
            ("1", "开始阅读", "继续阅读此书"),
            ("2", "查看目录", "浏览章节列表"),
            ("3", "书籍信息", "查看完整信息"),
            ("4", "删除书籍", "从书架移除"),
            ("0", "返回", "返回书架"),
        ]
        
        for num, title, desc in actions:
            self.console.print(f"  [{num}] {title} - [dim]{desc}[/]")
        
        return Prompt.ask("\n选择操作", choices=["0", "1", "2", "3", "4"])
    
    def show_search_interface(self) -> str:
        """显示搜索界面"""
        self.console.print(Panel(
            "[bold]🔍 搜索书籍[/bold]\n\n"
            "支持从多个书源同时搜索\n"
            "输入关键词开始搜索，输入 0 取消",
            border_style="cyan"
        ))
        
        return Prompt.ask("[bold]请输入书名或作者[/bold]")
    
    def show_search_results(self, results: List[Dict[str, Any]], keyword: str = "") -> Optional[Dict]:
        """显示搜索结果"""
        if not results:
            self.console.print(f"[yellow]未找到与 '{keyword}' 相关的结果[/yellow]")
            return None
        
        self.console.print(f"\n[green]找到 {len(results)} 个结果:[/green]\n")
        
        table = Table(
            title=f"🔍 搜索结果: {keyword}" if keyword else "🔍 搜索结果",
            border_style="cyan"
        )
        
        table.add_column("序号", style="cyan", width=4)
        table.add_column("书名", style="white", min_width=20)
        table.add_column("作者", style="green", width=15)
        table.add_column("来源", style="yellow", width=15)
        table.add_column("最新章节", style="dim", min_width=20)
        
        for i, result in enumerate(results[:20], 1):  # 最多显示20条
            table.add_row(
                str(i),
                result.get('name', '未知')[:20],
                result.get('author', '未知')[:14],
                result.get('source', '未知')[:14],
                result.get('latest_chapter', '未知')[:25]
            )
        
        self.console.print(table)
        
        self.console.print("\n[dim]操作: [数字]添加到书架 [0]返回 [n]下一页[/dim]")
        
        choice = Prompt.ask("选择")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                return results[idx]
        except ValueError:
            pass
        
        return None
    
    def show_reading_progress(self, title: str, current: int, total: int, content: str):
        """显示阅读进度"""
        progress = current / total if total > 0 else 0
        
        # 创建进度条
        bar_width = 30
        filled = int(bar_width * progress)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        progress_text = f"{bar} {current}/{total} ({progress*100:.1f}%)"
        
        self.console.print(Panel(
            content[:500] + "..." if len(content) > 500 else content,
            title=f"📖 {title}",
            subtitle=progress_text,
            border_style="cyan"
        ))
    
    def show_statistics(self, stats: Dict[str, Any]):
        """显示阅读统计"""
        # 创建统计面板
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column()
        
        # 基本统计
        basic_stats = f"""
[bold]📊 阅读概览[/bold]

总阅读时间: {stats.get('total_reading_time', 0)//60} 小时 {stats.get('total_reading_time', 0)%60} 分钟
总阅读字数: {stats.get('total_words', 0):,} 字
完成书籍: {stats.get('completed_books', 0)} 本
连续阅读: {stats.get('reading_streak', 0)} 天
        """
        
        grid.add_row(
            Panel(basic_stats, border_style="cyan"),
            Panel("[yellow]图表功能开发中...[/]", border_style="yellow")
        )
        
        self.console.print(grid)
        
        # 显示详细统计
        if 'daily_stats' in stats:
            self.console.print("\n[bold]📈 每日阅读[/bold]")
            daily_table = Table(border_style="dim")
            daily_table.add_column("日期", style="cyan")
            daily_table.add_column("阅读时长(分钟)", style="green")
            daily_table.add_column("阅读字数", style="yellow")
            
            for date, data in list(stats['daily_stats'].items())[-7:]:  # 最近7天
                daily_table.add_row(
                    date,
                    str(data.get('duration', 0)),
                    f"{data.get('words', 0):,}"
                )
            
            self.console.print(daily_table)
    
    def show_achievements(self, achievements: List[Dict[str, Any]]):
        """显示成就列表"""
        if not achievements:
            self.console.print("[yellow]暂无成就数据[/yellow]")
            return
        
        table = Table(title="🏆 成就系统", border_style="yellow")
        table.add_column("成就", style="yellow")
        table.add_column("名称", style="white")
        table.add_column("描述", style="dim")
        table.add_column("状态", style="green")
        table.add_column("解锁时间", style="cyan")
        
        for ach in achievements:
            icon = "✓" if ach.get('unlocked') else "○"
            status = "[green]已解锁[/]" if ach.get('unlocked') else "[dim]未解锁[/]"
            unlock_time = ach.get('unlocked_at', '-') if ach.get('unlocked') else "-"
            
            table.add_row(
                icon,
                ach.get('name', '未知'),
                ach.get('description', ''),
                status,
                unlock_time
            )
        
        self.console.print(table)
    
    def show_settings(self, settings: Dict[str, Any]):
        """显示设置界面"""
        self.console.print(Panel(
            "[bold]⚙️ 阅读设置[/bold]",
            border_style="cyan"
        ))
        
        table = Table(border_style="dim")
        table.add_column("序号", style="cyan", width=4)
        table.add_column("设置项", style="white")
        table.add_column("当前值", style="green")
        table.add_column("说明", style="dim")
        
        settings_list = [
            ("font_size", "字体大小", "阅读字体大小"),
            ("line_height", "行间距", "行与行之间的间距"),
            ("page_size", "每页行数", "每页显示的行数"),
            ("theme", "主题", "界面颜色主题"),
            ("auto_save", "自动保存", "是否自动保存进度"),
            ("tts_voice", "语音音色", "TTS朗读声音"),
            ("tts_speed", "语音速度", "TTS朗读速度"),
        ]
        
        for i, (key, name, desc) in enumerate(settings_list, 1):
            value = settings.get(key, '默认')
            table.add_row(str(i), name, str(value), desc)
        
        self.console.print(table)
        
        self.console.print("\n[dim]操作: [数字]修改设置 [0]返回[/dim]")
        return Prompt.ask("选择")
    
    def show_loading(self, message: str = "加载中..."):
        """显示加载动画"""
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[cyan]{message}[/]"),
            console=self.console
        ) as progress:
            task = progress.add_task(message, total=None)
            # 这里可以添加实际的加载逻辑
            time.sleep(0.5)
    
    def show_notification(self, message: str, type_: str = "info"):
        """显示通知"""
        colors = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red"
        }
        color = colors.get(type_, "white")
        
        icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗"
        }
        icon = icons.get(type_, "•")
        
        self.console.print(f"[{color}]{icon} {message}[/{color}]")
    
    def confirm_action(self, message: str) -> bool:
        """确认操作"""
        return Confirm.ask(f"[yellow]{message}[/]")


class EnhancedContentReader(ContentReader):
    """增强版内容阅读器"""
    
    def __init__(self, content: str = "", title: str = "", chapter_title: str = ""):
        super().__init__(content, title)
        self.chapter_title = chapter_title
        self.bookmarks = []
        self.notes = []
    
    def read_with_toc(self, chapters: List[Dict], current_idx: int = 0) -> int:
        """带目录的阅读"""
        while True:
            self.console.clear()
            
            # 显示标题
            header = f"📖 {self.title}"
            if self.chapter_title:
                header += f" - {self.chapter_title}"
            
            self.console.print(Panel(
                Text(header, style="bold cyan", justify="center"),
                border_style="cyan"
            ))
            
            # 显示当前章节内容
            if current_idx < len(chapters):
                chapter = chapters[current_idx]
                self.console.print(Panel(
                    chapter.get('content', '无内容')[:1000],
                    title=f"第 {current_idx + 1}/{len(chapters)} 章: {chapter.get('title', '未知')}",
                    border_style="dim cyan"
                ))
            
            # 显示导航
            self.console.print("\n[dim]导航: [n]下一章 [p]上一章 [c]目录 [b]书签 [q]退出[/dim]")
            
            choice = Prompt.ask("选择", choices=["n", "p", "c", "b", "q"], default="n")
            
            if choice == "q":
                return current_idx
            elif choice == "n" and current_idx < len(chapters) - 1:
                current_idx += 1
                self.chapter_title = chapters[current_idx].get('title', '')
            elif choice == "p" and current_idx > 0:
                current_idx -= 1
                self.chapter_title = chapters[current_idx].get('title', '')
            elif choice == "c":
                # 显示目录
                new_idx = self._show_toc(chapters, current_idx)
                if new_idx is not None:
                    current_idx = new_idx
                    self.chapter_title = chapters[current_idx].get('title', '')
            elif choice == "b":
                self._add_bookmark(current_idx)
        
        return current_idx
    
    def _show_toc(self, chapters: List[Dict], current_idx: int) -> Optional[int]:
        """显示目录"""
        self.console.clear()
        
        table = Table(title="📑 章节目录", border_style="cyan")
        table.add_column("序号", style="cyan", width=6)
        table.add_column("章节标题", style="white")
        table.add_column("状态", style="dim", width=8)
        
        for i, chapter in enumerate(chapters, 1):
            status = "[green]当前[/]" if i - 1 == current_idx else ""
            table.add_row(str(i), chapter.get('title', f'第{i}章'), status)
        
        self.console.print(table)
        
        choice = Prompt.ask("\n输入章节编号跳转 (0取消)", default="0")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(chapters):
                return idx
        except ValueError:
            pass
        
        return None
    
    def _add_bookmark(self, chapter_idx: int):
        """添加书签"""
        note = Prompt.ask("书签备注 (可选)", default="")
        bookmark = {
            'chapter': chapter_idx,
            'chapter_title': self.chapter_title,
            'note': note,
            'time': datetime.now().isoformat()
        }
        self.bookmarks.append(bookmark)
        self.show_notification("书签已添加", "success")


class AIRecommendationUI:
    """AI推荐界面"""
    
    def __init__(self):
        self.console = Console()
    
    def show_recommendations(self, recommendations: List[Dict[str, Any]]):
        """显示AI推荐"""
        self.console.print(Panel(
            "[bold]🎯 AI智能推荐[/bold]\n\n"
            "基于您的阅读历史和偏好，为您推荐以下书籍",
            border_style="cyan"
        ))
        
        if not recommendations:
            self.console.print("[yellow]暂无推荐，请多阅读一些书籍[/yellow]")
            return None
        
        table = Table(border_style="cyan")
        table.add_column("序号", style="cyan", width=4)
        table.add_column("书名", style="white")
        table.add_column("推荐理由", style="green")
        table.add_column("匹配度", style="yellow")
        
        for i, rec in enumerate(recommendations, 1):
            match_score = rec.get('match_score', 0)
            stars = "★" * int(match_score / 20) + "☆" * (5 - int(match_score / 20))
            
            table.add_row(
                str(i),
                rec.get('name', '未知'),
                rec.get('reason', '基于您的阅读偏好')[:30],
                f"{stars} {match_score}%"
            )
        
        self.console.print(table)
        
        self.console.print("\n[dim]操作: [数字]查看详情 [0]返回[/dim]")
        
        choice = Prompt.ask("选择")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(recommendations):
                return recommendations[idx]
        except ValueError:
            pass
        
        return None
    
    def show_book_analysis(self, analysis: Dict[str, Any]):
        """显示书籍分析"""
        content = f"""
[bold]{analysis.get('name', '未知')}[/bold]

[cyan]质量评分:[/] {analysis.get('quality_score', 0)}/10
[cyan]预计阅读时间:[/] {analysis.get('reading_time', '未知')}
[cyan]难度等级:[/] {analysis.get('difficulty', '未知')}
[cyan]内容标签:[/] {', '.join(analysis.get('tags', []))}

[bold]简介:[/]
{analysis.get('summary', '暂无简介')}
        """
        
        self.console.print(Panel(content, border_style="cyan"))


class DataManagementUI:
    """数据管理界面"""
    
    def __init__(self):
        self.console = Console()
    
    def show_menu(self) -> str:
        """显示数据管理菜单"""
        self.console.print(Panel(
            "[bold]💾 数据管理[/bold]",
            border_style="cyan"
        ))
        
        options = [
            ("1", "创建备份", "备份当前所有数据"),
            ("2", "恢复备份", "从备份文件恢复"),
            ("3", "查看备份", "列出所有备份"),
            ("4", "删除备份", "删除旧备份"),
            ("5", "数据同步", "同步到云端"),
            ("6", "导入书籍", "从文件导入"),
            ("7", "导出书籍", "导出到文件"),
            ("0", "返回", "返回主菜单"),
        ]
        
        for num, title, desc in options:
            self.console.print(f"  [{num}] {title} - [dim]{desc}[/]")
        
        return Prompt.ask("\n选择操作", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
    
    def show_backup_list(self, backups: List[Dict[str, Any]]):
        """显示备份列表"""
        if not backups:
            self.console.print("[yellow]暂无备份[/yellow]")
            return None
        
        table = Table(title="📦 备份列表", border_style="cyan")
        table.add_column("序号", style="cyan", width=4)
        table.add_column("备份ID", style="white")
        table.add_column("大小", style="green")
        table.add_column("创建时间", style="yellow")
        table.add_column("描述", style="dim")
        
        for i, backup in enumerate(backups, 1):
            size = backup.get('size', 0)
            size_str = f"{size/1024/1024:.1f} MB" if size > 1024*1024 else f"{size/1024:.1f} KB"
            
            table.add_row(
                str(i),
                backup.get('id', '未知')[:20],
                size_str,
                backup.get('created', '未知'),
                backup.get('description', '-')[:20]
            )
        
        self.console.print(table)
        
        self.console.print("\n[dim]操作: [数字]选择备份 [0]返回[/dim]")
        
        choice = Prompt.ask("选择")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                return backups[idx]
        except ValueError:
            pass
        
        return None


# 便捷函数
def create_progress_bar(description: str = "处理中"):
    """创建进度条"""
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[progress.description]{description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    )


def show_error(message: str):
    """显示错误"""
    console.print(Panel(
        f"[red]✗ {message}[/red]",
        title="错误",
        border_style="red"
    ))


def show_success(message: str):
    """显示成功"""
    console.print(Panel(
        f"[green]✓ {message}[/green]",
        title="成功",
        border_style="green"
    ))
