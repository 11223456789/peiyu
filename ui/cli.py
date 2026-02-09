"""
佩宇Reader - 命令行界面模块
提供基础的CLI交互功能
"""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
import time

console = Console()


class ReaderUI:
    """阅读器UI基类"""
    
    def __init__(self):
        self.console = Console()
    
    def show_header(self, title: str = "佩宇Reader"):
        """显示标题头"""
        header = Panel(
            Text(title, style="bold cyan", justify="center"),
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(header)
    
    def show_menu(self, options: List[str], title: str = "菜单"):
        """显示菜单选项"""
        table = Table(title=title, show_header=False, border_style="cyan")
        table.add_column("选项", style="cyan")
        table.add_column("描述", style="white")
        
        for i, option in enumerate(options, 1):
            table.add_row(f"[{i}]", option)
        
        self.console.print(table)
    
    def get_choice(self, prompt: str = "请选择") -> str:
        """获取用户选择"""
        return Prompt.ask(f"\n[bold cyan]{prompt}[/bold cyan]")
    
    def show_message(self, message: str, style: str = "info"):
        """显示消息"""
        styles = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red"
        }
        color = styles.get(style, "white")
        self.console.print(f"[{color}]{message}[/{color}]")
    
    def show_progress(self, description: str = "处理中..."):
        """显示进度条"""
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{description}"),
            console=self.console
        )


class ContentReader:
    """内容阅读器"""
    
    def __init__(self, content: str = "", title: str = ""):
        self.content = content
        self.title = title
        self.console = Console()
        self.page_size = 20  # 每页行数
    
    def read(self) -> bool:
        """开始阅读"""
        if not self.content:
            self.console.print("[yellow]内容为空[/yellow]")
            return False
        
        lines = self.content.split('\n')
        total_pages = (len(lines) + self.page_size - 1) // self.page_size
        current_page = 0
        
        while current_page < total_pages:
            self.console.clear()
            
            # 显示标题
            if self.title:
                self.console.print(Panel(
                    Text(self.title, style="bold cyan", justify="center"),
                    border_style="cyan"
                ))
            
            # 显示内容
            start = current_page * self.page_size
            end = min(start + self.page_size, len(lines))
            page_content = '\n'.join(lines[start:end])
            
            self.console.print(Panel(
                page_content,
                border_style="dim cyan",
                title=f"第 {current_page + 1}/{total_pages} 页"
            ))
            
            # 显示操作提示
            self.console.print("\n[dim]操作: [n]下一页 [p]上一页 [q]退出[/dim]")
            
            choice = Prompt.ask("选择", choices=["n", "p", "q"], default="n")
            
            if choice == "q":
                return True
            elif choice == "n" and current_page < total_pages - 1:
                current_page += 1
            elif choice == "p" and current_page > 0:
                current_page -= 1
        
        return True
    
    def set_content(self, content: str, title: str = ""):
        """设置内容"""
        self.content = content
        if title:
            self.title = title


class BookSelector:
    """书籍选择器"""
    
    def __init__(self, books: List[Dict[str, Any]] = None):
        self.books = books or []
        self.console = Console()
    
    def select(self) -> Optional[Dict[str, Any]]:
        """选择书籍"""
        if not self.books:
            self.console.print("[yellow]没有可用的书籍[/yellow]")
            return None
        
        table = Table(title="书籍列表", border_style="cyan")
        table.add_column("序号", style="cyan", width=6)
        table.add_column("书名", style="white")
        table.add_column("作者", style="green")
        table.add_column("状态", style="yellow")
        
        for i, book in enumerate(self.books, 1):
            status = "在读" if book.get('reading', False) else "未读"
            table.add_row(
                str(i),
                book.get('name', '未知'),
                book.get('author', '未知'),
                status
            )
        
        self.console.print(table)
        
        choice = Prompt.ask(
            "\n选择书籍编号 (或输入0取消)",
            default="0"
        )
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.books):
                return self.books[idx]
        except ValueError:
            pass
        
        return None
    
    def set_books(self, books: List[Dict[str, Any]]):
        """设置书籍列表"""
        self.books = books


class SearchInterface:
    """搜索界面"""
    
    def __init__(self):
        self.console = Console()
    
    def get_keyword(self) -> str:
        """获取搜索关键词"""
        return Prompt.ask("\n[bold cyan]请输入搜索关键词[/bold cyan]")
    
    def show_results(self, results: List[Dict[str, Any]], keyword: str = ""):
        """显示搜索结果"""
        if not results:
            self.console.print(f"[yellow]未找到与 '{keyword}' 相关的结果[/yellow]")
            return
        
        table = Table(title=f"搜索结果: {keyword}" if keyword else "搜索结果", border_style="cyan")
        table.add_column("序号", style="cyan", width=6)
        table.add_column("书名", style="white")
        table.add_column("作者", style="green")
        table.add_column("来源", style="yellow")
        
        for i, result in enumerate(results, 1):
            table.add_row(
                str(i),
                result.get('name', '未知'),
                result.get('author', '未知'),
                result.get('source', '未知')
            )
        
        self.console.print(table)
        
        # 选择结果
        choice = Prompt.ask(
            "\n选择书籍编号添加到书架 (或输入0取消)",
            default="0"
        )
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                return results[idx]
        except ValueError:
            pass
        
        return None


class SettingsInterface:
    """设置界面"""
    
    def __init__(self):
        self.console = Console()
    
    def show_settings(self, settings: Dict[str, Any]):
        """显示设置"""
        table = Table(title="阅读设置", border_style="cyan")
        table.add_column("设置项", style="cyan")
        table.add_column("当前值", style="white")
        
        for key, value in settings.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
    
    def edit_setting(self, name: str, current_value: Any) -> Any:
        """编辑设置"""
        new_value = Prompt.ask(
            f"设置 {name} (当前: {current_value})",
            default=str(current_value)
        )
        
        # 尝试转换类型
        try:
            if isinstance(current_value, int):
                return int(new_value)
            elif isinstance(current_value, float):
                return float(new_value)
            elif isinstance(current_value, bool):
                return new_value.lower() in ('true', 'yes', '1', 'y')
        except ValueError:
            pass
        
        return new_value


# 便捷函数
def print_success(message: str):
    """打印成功消息"""
    console.print(f"[green]✓ {message}[/green]")


def print_error(message: str):
    """打印错误消息"""
    console.print(f"[red]✗ {message}[/red]")


def print_warning(message: str):
    """打印警告消息"""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def print_info(message: str):
    """打印信息消息"""
    console.print(f"[blue]ℹ {message}[/blue]")


def wait_for_key(message: str = "按回车键继续..."):
    """等待用户按键"""
    Prompt.ask(f"\n[dim]{message}[/dim]", default="")
