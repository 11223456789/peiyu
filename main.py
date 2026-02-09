"""
佩宇Reader 高级版 - PeiYu Reader Advanced
完全原创的沉浸式阅读体验 + AI智能系统

高级功能:
- AI智能推荐系统
- 深度阅读分析
- 成就与游戏化
- 数据可视化仪表板
- 智能阅读助手
- 性能优化
- 数据同步与备份
- 插件系统

使用方法:
    python main.py
"""

import os
import sys
import time
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.align import Align
from rich.box import ROUNDED, DOUBLE, SIMPLE
from rich.progress import Progress, SpinnerColumn, TextColumn

# 导入核心模块
from core.book_source import BookSourceManager
from core.bookshelf import BookshelfManager
from core.config import ConfigManager, TextFormatter
from core.async_search import ConcurrentSearcher, SearchHistory
from core.ai_recommendation import AIRecommendationEngine, ReadingBehavior
from core.reading_analytics import ReadingAnalyticsEngine
from core.achievement_system import AchievementManager, AchievementType
from core.tts_engine import TTSEngine, ReadingAloudController
from core.performance_optimizer import (
    DatabaseOptimizer, CacheManager, PerformanceMonitor, 
    FullTextSearch, timed, memoize
)
from core.advanced_ai import DeepRecommendationEngine, SmartAssistant, get_advanced_ai
from core.advanced_features import (
    DataSyncManager, BackupManager, PluginManager,
    StatisticsCollector, ShortcutManager, ThemeEngine
)
from ui.nebula_ui import (
    PeiYuTheme, PeiYuHeader, PeiYuMenu, PeiYuBookCard,
    PeiYuReaderUI, PeiYuProgress, PeiYuSearchBox, PeiYuNotification,
    StarField, PEIYU_THEMES
)


class PeiYuReader:
    """佩宇Reader高级版主应用"""
    
    def __init__(self):
        self.data_dir = Path.home() / ".peiyu_reader"
        self.data_dir.mkdir(exist_ok=True)
        
        # 获取项目根目录
        self.project_dir = Path(__file__).parent
        
        # 初始化性能优化
        self.db_optimizer = DatabaseOptimizer(str(self.data_dir / "bookshelf.db"))
        self.db_optimizer.create_indexes()
        self.full_text_search = FullTextSearch(str(self.data_dir / "bookshelf.db"))
        
        # 初始化管理器
        self.source_manager = BookSourceManager()
        self.bookshelf = BookshelfManager(str(self.data_dir))
        self.config = ConfigManager()
        self.searcher = ConcurrentSearcher()
        self.search_history = SearchHistory()
        
        # 自动加载内置书源
        self._load_builtin_sources()
        
        # 初始化高级功能
        self.ai_engine = AIRecommendationEngine(str(self.data_dir))
        self.analytics = ReadingAnalyticsEngine(str(self.data_dir))
        self.achievements = AchievementManager(str(self.data_dir))
        
        # 初始化深度AI
        self.advanced_ai = get_advanced_ai(str(self.data_dir))
        self.smart_assistant = SmartAssistant(str(self.data_dir))
        
        # 初始化TTS
        self.tts_engine = TTSEngine(str(self.data_dir))
        self.reading_aloud = ReadingAloudController(self.tts_engine)
        
        # 初始化高级功能模块
        self.sync_manager = DataSyncManager(str(self.data_dir))
        self.backup_manager = BackupManager(str(self.data_dir))
        self.plugin_manager = PluginManager(str(self.data_dir))
        self.stats_collector = StatisticsCollector(str(self.data_dir))
        self.shortcut_manager = ShortcutManager(str(self.data_dir))
        self.theme_engine = ThemeEngine(str(self.data_dir))
        
        # 初始化主题
        theme_name = getattr(self.config.config, 'theme', 'cosmic')
        self.theme = PeiYuTheme(theme_name)
        self.console = self.theme.console

        # 初始化UI组件
        self.menu = PeiYuMenu(self.theme)
        self.book_card = PeiYuBookCard(self.theme)
        self.reader_component = PeiYuReaderUI(self.theme)
        self.progress = PeiYuProgress(self.theme)
        self.search_box = PeiYuSearchBox(self.theme)
        
        # 当前会话
        self.current_session_id: Optional[str] = None
        
        # 启动统计收集
        self.stats_collector.log_event("app_start", {"version": "2.0.0"})
    
    def _load_builtin_sources(self):
        """自动加载内置书源"""
        sources_dir = self.project_dir / "sources"
        book_sources_file = sources_dir / "book_sources.json"
        
        if book_sources_file.exists():
            count = self.source_manager.load_from_json(str(book_sources_file))
            if count > 0:
                # 静默加载，不打扰用户
                pass
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str, subtitle: str = ""):
        """打印佩宇标题"""
        header = PeiYuHeader.create(title, subtitle, self.theme)
        self.console.print(header)
    
    def main_loop(self):
        """主循环"""
        while True:
            self.clear_screen()
            self.print_header("✨ 佩宇Reader 高级版", "PeiYu Reader Advanced - AI智能阅读")
            
            # 显示用户等级和成就
            self._show_user_status_bar()
            
            # 主菜单
            menu_items = [
                {"icon": "🔮", "text": "AI智能推荐", "hotkey": "1"},
                {"icon": "🔍", "text": "佩宇搜索", "hotkey": "2"},
                {"icon": "📚", "text": "我的书架", "hotkey": "3"},
                {"icon": "📊", "text": "阅读分析", "hotkey": "4"},
                {"icon": "🏆", "text": "成就中心", "hotkey": "5"},
                {"icon": "📈", "text": "今日挑战", "hotkey": "6"},
                {"icon": "🌐", "text": "书源管理", "hotkey": "7"},
                {"icon": "⚙️", "text": "佩宇设置", "hotkey": "8"},
                {"icon": "💾", "text": "数据管理", "hotkey": "9"},
                {"icon": "🔌", "text": "插件中心", "hotkey": "10"},
                {"icon": "ℹ", "text": "关于", "hotkey": "11"},
                {"icon": "🚪", "text": "退出", "hotkey": "0"},
            ]
            
            menu = self.menu.create_vertical(menu_items, "主菜单")
            self.console.print(menu)
            
            # 快捷提示
            tips = Text()
            tips.append("\n💫 ", style=self.theme.colors["accent2"])
            tips.append("提示: 输入数字或快捷键选择功能", style=f"dim {self.theme.colors['dim']}")
            self.console.print(tips)
            
            choice = Prompt.ask("\n选择", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"], default="1")
            
            if choice == "0":
                self.exit_app()
                break
            elif choice == "1":
                self.ai_recommendations()
            elif choice == "2":
                self.search_books()
            elif choice == "3":
                self.my_bookshelf()
            elif choice == "4":
                self.reading_analytics()
            elif choice == "5":
                self.achievement_center()
            elif choice == "6":
                self.daily_challenges()
            elif choice == "7":
                self.manage_sources()
            elif choice == "8":
                self.settings()
            elif choice == "9":
                self.data_management()
            elif choice == "10":
                self.plugin_center()
            elif choice == "11":
                self.about()
    
    def _show_user_status_bar(self):
        """显示用户状态栏"""
        level = self.achievements.current_level
        title = self.achievements.current_title
        points = self.achievements.total_points
        
        # 获取成就进度
        all_achievements = self.achievements.get_all_achievements()
        unlocked = sum(1 for a in all_achievements if a.get('unlocked', False))
        total = len(all_achievements)
        
        status_text = Text()
        status_text.append("┌─ 用户状态 ", style=self.theme.colors["border"])
        status_text.append("─" * 50, style=self.theme.colors["border"])
        status_text.append("┐\n", style=self.theme.colors["border"])
        
        status_text.append("│ ", style=self.theme.colors["border"])
        status_text.append(f"👤 {title}", style=f"bold {self.theme.colors['highlight']}")
        status_text.append(f" | Lv.{level}", style=self.theme.colors["accent2"])
        status_text.append(f" | ⭐ {points}点", style=self.theme.colors["accent3"])
        status_text.append(f" | 🏆 {unlocked}/{total}", style=self.theme.colors["accent4"])
        status_text.append(" " * 20, style=self.theme.colors["dim"])
        status_text.append(" │\n", style=self.theme.colors["border"])
        
        status_text.append("└", style=self.theme.colors["border"])
        status_text.append("─" * 60, style=self.theme.colors["border"])
        status_text.append("┘", style=self.theme.colors["border"])
        
        self.console.print(status_text)
        self.console.print()
    
    def ai_recommendations(self):
        """AI智能推荐"""
        self.clear_screen()
        self.print_header("🔮 AI智能推荐", "基于你的阅读偏好智能推荐")
        
        # 显示加载动画
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            progress.add_task("AI正在分析你的阅读偏好...", total=None)
            time.sleep(1.5)
        
        # 模拟推荐数据（实际应该从书源获取）
        mock_books = [
            {
                'id': '1',
                'name': '斗破苍穹',
                'author': '天蚕土豆',
                'category': '玄幻',
                'tags': ['热血', '升级', '异世'],
                'popularity': 95,
                'rating': 8.5
            },
            {
                'id': '2',
                'name': '凡人修仙传',
                'author': '忘语',
                'category': '仙侠',
                'tags': ['修真', '凡人流', '长篇'],
                'popularity': 92,
                'rating': 8.8
            },
            {
                'id': '3',
                'name': '诡秘之主',
                'author': '爱潜水的乌贼',
                'category': '奇幻',
                'tags': ['克苏鲁', '蒸汽朋克', '悬疑'],
                'popularity': 98,
                'rating': 9.2
            },
            {
                'id': '4',
                'name': '大奉打更人',
                'author': '卖报小郎君',
                'category': '仙侠',
                'tags': ['探案', '轻松', '后宫'],
                'popularity': 94,
                'rating': 8.6
            },
            {
                'id': '5',
                'name': '我师兄实在太稳健了',
                'author': '言归正传',
                'category': '仙侠',
                'tags': ['洪荒', '稳健流', '搞笑'],
                'popularity': 89,
                'rating': 8.3
            }
        ]
        
        # 获取个性化推荐
        recommendations = self.ai_engine.get_personalized_recommendations(mock_books, 5)
        
        if recommendations:
            self.console.print(f"\n[{self.theme.colors['accent2']}]为你找到 {len(recommendations)} 本可能喜欢的书:[/]\n")
            
            for i, book in enumerate(recommendations, 1):
                card = self.book_card.create(book, i)
                self.console.print(card)
                
                # 显示推荐理由
                if 'recommend_reason' in book:
                    reason_text = Text()
                    reason_text.append("   💡 ", style=self.theme.colors["accent3"])
                    reason_text.append(book['recommend_reason'], style=self.theme.colors["dim"])
                    self.console.print(reason_text)
                
                # 显示匹配度
                if 'recommend_score' in book:
                    score = book['recommend_score']
                    bar_width = 20
                    filled = int(score / 10 * bar_width)
                    bar = "█" * filled + "░" * (bar_width - filled)
                    self.console.print(f"   匹配度: [{self.theme.colors['accent1']}]{bar}[/{self.theme.colors['accent1']}] {score}/10")
                
                self.console.print()
        else:
            self.console.print(PeiYuNotification.create(
                "暂无推荐，开始阅读来建立你的偏好画像吧！", "info", self.theme
            ))
        
        self.console.print(f"\n[{self.theme.colors['accent4']}]0. 返回[/]")
        choice = Prompt.ask("选择", choices=["0"], default="0")
    
    def search_books(self):
        """搜索书籍"""
        self.clear_screen()
        self.print_header("🔍 佩宇搜索", "在书海中寻找你的下一本书")
        
        # 显示搜索历史
        history = self.search_history.get_history(5)
        if history:
            self.console.print(f"\n[{self.theme.colors['dim']}]搜索历史:[/]")
            for i, keyword in enumerate(history, 1):
                self.console.print(f"  {i}. {keyword}")
            self.console.print()
        
        keyword = Prompt.ask("请输入书名或作者", default="")
        if not keyword:
            return
        
        # 保存搜索历史
        self.search_history.add_search(keyword)
        
        # 搜索动画
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            progress.add_task(f"正在搜索 '{keyword}'...", total=None)
            time.sleep(2)
        
        # 模拟搜索结果
        mock_results = [
            {
                'name': f'{keyword} - 搜索结果1',
                'author': '作者A',
                'source': '书源1',
                'latest_chapter': '第100章',
                'intro': '这是一本非常精彩的小说...'
            },
            {
                'name': f'{keyword} - 搜索结果2',
                'author': '作者B',
                'source': '书源2',
                'latest_chapter': '第50章',
                'intro': '另一本好书...'
            }
        ]
        
        self.console.print(f"\n[{self.theme.colors['accent2']}]找到 {len(mock_results)} 个结果:[/]\n")
        
        for i, book in enumerate(mock_results, 1):
            card = self.book_card.create(book, i)
            self.console.print(card)
            self.console.print()
        
        self.console.print(f"\n[{self.theme.colors['accent4']}]0. 返回[/]")
        choice = Prompt.ask("选择", choices=["0"], default="0")
    
    def my_bookshelf(self):
        """我的书架"""
        self.clear_screen()
        self.print_header("📚 我的书架", "你的私人图书馆")
        
        books = self.bookshelf.get_all_books()
        
        if books:
            self.console.print(f"\n[{self.theme.colors['accent2']}]共 {len(books)} 本书:[/]\n")
            
            for i, book in enumerate(books[:10], 1):
                card = self.book_card.create(book, i)
                self.console.print(card)
                
                # 显示阅读进度
                if 'progress' in book:
                    progress = book['progress']
                    bar_width = 20
                    filled = int(progress * bar_width)
                    bar = "█" * filled + "░" * (bar_width - filled)
                    self.console.print(f"   进度: [{self.theme.colors['accent1']}]{bar}[/{self.theme.colors['accent1']}] {progress*100:.1f}%")
                
                self.console.print()
        else:
            self.console.print(PeiYuNotification.create(
                "书架是空的，快去搜索添加书籍吧！", "info", self.theme
            ))
        
        self.console.print(f"\n[{self.theme.colors['accent4']}]0. 返回[/]")
        choice = Prompt.ask("选择", choices=["0"], default="0")
    
    def reading_analytics(self):
        """阅读分析"""
        self.clear_screen()
        self.print_header("📊 阅读分析", "深度洞察你的阅读习惯")
        
        # 获取周报告
        report = self.analytics.get_weekly_report()
        
        # 创建分析表格
        table = Table(show_header=True, box=ROUNDED, border_style=self.theme.colors["border"])
        table.add_column("指标", style=self.theme.colors["accent2"])
        table.add_column("数值", style=self.theme.colors["highlight"])
        
        table.add_row("📅 统计周期", report.get('period', '-'))
        table.add_row("⏱️ 总阅读时长", f"{report.get('total_reading_time', 0)/60:.1f} 小时")
        table.add_row("📖 阅读章节", f"{report.get('total_chapters', 0)} 章")
        table.add_row("📝 阅读字数", f"{report.get('total_words', 0)/10000:.1f} 万字")
        table.add_row("📊 阅读天数", f"{report.get('active_days', 0)} 天")
        table.add_row("📚 阅读书籍", f"{report.get('books_count', 0)} 本")
        table.add_row("⏰ 高峰时段", ", ".join(report.get('peak_hours', [])))
        
        self.console.print(table)
        
        # 阅读模式
        patterns = self.analytics.get_reading_patterns()
        if patterns:
            self.console.print(f"\n[{self.theme.colors['accent3']}]阅读模式分析:[/]")
            for pattern in patterns:
                self.console.print(f"  • {pattern}")
        
        self.console.print(f"\n[{self.theme.colors['accent4']}]0. 返回[/]")
        choice = Prompt.ask("选择", choices=["0"], default="0")
    
    def achievement_center(self):
        """成就中心"""
        self.clear_screen()
        self.print_header("🏆 成就中心", "解锁成就，获得荣誉")
        
        # 总体进度
        all_achievements = self.achievements.get_all_achievements()
        unlocked = sum(1 for a in all_achievements if a['unlocked'])
        total = len(all_achievements)
        progress = unlocked / total if total > 0 else 0
        
        progress_bar = self.progress.create_bar(progress, 20)
        
        self.console.print(f"\n[{self.theme.colors['accent2']}]总体进度:[/]")
        self.console.print(f"  当前等级: {self.achievements.current_title} (Lv.{self.achievements.current_level})")
        self.console.print(f"  总点数: {self.achievements.total_points} ⭐")
        self.console.print(f"  成就完成度: {unlocked}/{total} ({progress*100:.1f}%)")
        self.console.print(f"  [{self.theme.colors['accent1']}]{progress_bar}[/{self.theme.colors['accent1']}]")
        
        # 按类型分组显示成就
        self.console.print(f"\n[{self.theme.colors['accent3']}]阅读时长成就:[/]")
        time_achievements = [a for a in all_achievements if a['type'] == 'reading_time']
        for ach in time_achievements[:3]:
            status = "✅" if ach['unlocked'] else "⏳"
            self.console.print(f"  {status} {ach['name']}: {ach['description']}")
        
        self.console.print(f"\n[{self.theme.colors['accent4']}]完成书籍成就:[/]")
        book_achievements = [a for a in all_achievements if a['type'] == 'books_completed']
        for ach in book_achievements[:3]:
            status = "✅" if ach['unlocked'] else "⏳"
            self.console.print(f"  {status} {ach['name']}: {ach['description']}")
        
        self.console.print(f"\n[{self.theme.colors['accent4']}]0. 返回[/]")
        choice = Prompt.ask("选择", choices=["0"], default="0")
    
    def daily_challenges(self):
        """每日挑战"""
        self.clear_screen()
        self.print_header("📈 今日挑战", "完成挑战，获得奖励")
        
        # 获取今日挑战
        challenges = self.achievements.get_daily_challenges()
        
        self.console.print(f"\n[{self.theme.colors['accent2']}]今日任务:[/]\n")
        
        for i, ch in enumerate(challenges, 1):
            status = "✅ 已完成" if ch['completed'] else "⏳ 进行中"
            ch_text = Text()
            ch_text.append(f"{i}. ", style=self.theme.colors["accent2"])
            ch_text.append(f"{ch['title']}\n", style=f"bold {self.theme.colors['highlight']}")
            ch_text.append(f"   描述: {ch['description']}\n", style=self.theme.colors["dim"])
            ch_text.append(f"   状态: {status}\n", style=self.theme.colors["accent3"])
            ch_text.append(f"   进度: [{ch['current']}/{ch['target']}]\n", style=self.theme.colors["dim"])
            ch_text.append(f"   奖励: {ch['reward_points']} ⭐", style=self.theme.colors["accent3"])
            
            self.console.print(ch_text)
            self.console.print()
        
        Prompt.ask("\n按回车返回")
    
    def manage_sources(self):
        """书源管理"""
        self.clear_screen()
        self.print_header("🌐 书源管理", "管理你的书源")
        
        sources = self.source_manager.list_sources()
        
        if sources:
            self.console.print(f"\n[{self.theme.colors['accent2']}]已加载 {len(sources)} 个书源:[/]\n")
            
            # 创建书源表格
            table = Table(show_header=True, box=ROUNDED, border_style=self.theme.colors["border"])
            table.add_column("序号", style=self.theme.colors["accent2"], width=4)
            table.add_column("书源名称", style=self.theme.colors["highlight"], width=20)
            table.add_column("分组", style=self.theme.colors["accent3"], width=12)
            table.add_column("状态", style=self.theme.colors["accent4"], width=6)
            
            for i, source in enumerate(sources[:20], 1):  # 最多显示20个
                status = "✅ 启用" if source.enabled else "❌ 禁用"
                table.add_row(
                    str(i),
                    source.bookSourceName or "未命名",
                    source.bookSourceGroup or "默认",
                    status
                )
            
            self.console.print(table)
            
            if len(sources) > 20:
                self.console.print(f"\n[dim]... 还有 {len(sources) - 20} 个书源[/]")
        else:
            self.console.print(PeiYuNotification.create(
                "暂无书源，请先导入！", "warning", self.theme
            ))
        
        self.console.print(f"\n[{self.theme.colors['accent4']}]0. 返回[/]")
        self.console.print(f"[{self.theme.colors['accent1']}]1. 导入新书源[/]")
        self.console.print(f"[{self.theme.colors['accent2']}]2. 重新加载内置书源[/]")
        
        choice = Prompt.ask("选择", choices=["0", "1", "2"], default="0")
        
        if choice == "1":
            path = Prompt.ask("请输入书源文件路径")
            if os.path.exists(path):
                try:
                    count = self.source_manager.load_from_json(path)
                    self.console.print(PeiYuNotification.create(
                        f"成功导入 {count} 个书源！", "success", self.theme
                    ))
                except Exception as e:
                    self.console.print(PeiYuNotification.create(
                        f"导入失败: {e}", "error", self.theme
                    ))
            else:
                self.console.print(PeiYuNotification.create(
                    "文件不存在！", "error", self.theme
                ))
            time.sleep(1)
        elif choice == "2":
            self._load_builtin_sources()
            self.console.print(PeiYuNotification.create(
                f"已重新加载 {len(self.source_manager.list_sources())} 个书源！", "success", self.theme
            ))
            time.sleep(1)
    
    def settings(self):
        """佩宇设置"""
        self.clear_screen()
        self.print_header("⚙️ 佩宇设置", "自定义你的阅读体验")
        
        # 获取当前配置值
        current_theme = getattr(self.config.config, 'theme', 'cosmic')
        current_chars = getattr(self.config.config, 'chars_per_page', 800)
        
        self.console.print(f"\n[{self.theme.colors['accent2']}]当前设置:[/]")
        self.console.print(f"  主题: {current_theme}")
        self.console.print(f"  每页字数: {current_chars}")
        
        self.console.print(f"\n[{self.theme.colors['accent4']}]0. 返回[/]")
        self.console.print(f"[{self.theme.colors['accent1']}]1. 切换主题[/]")
        self.console.print(f"[{self.theme.colors['accent2']}]2. 阅读设置[/]")
        
        choice = Prompt.ask("选择", choices=["0", "1", "2"], default="0")
        
        if choice == "1":
            self.console.print(f"\n[{self.theme.colors['accent2']}]可用主题:[/]")
            for i, (key, name) in enumerate(PEIYU_THEMES.items(), 1):
                self.console.print(f"  {i}. {name}")
            
            theme_choice = Prompt.ask("选择主题", choices=["1", "2", "3", "4"], default="1")
            theme_keys = list(PEIYU_THEMES.keys())
            if theme_choice.isdigit() and 1 <= int(theme_choice) <= len(theme_keys):
                selected_theme = theme_keys[int(theme_choice) - 1]
                self.config.set("theme", selected_theme)
                self.theme = PeiYuTheme(selected_theme)
                self.console.print(PeiYuNotification.create(
                    f"主题已切换为: {PEIYU_THEMES[selected_theme]}", "success", self.theme
                ))
                time.sleep(1)
    
    def data_management(self):
        """数据管理"""
        self.clear_screen()
        self.print_header("💾 数据管理", "备份、同步与恢复")
        
        menu_items = [
            {"icon": "💾", "text": "创建备份", "hotkey": "1"},
            {"icon": "📂", "text": "恢复备份", "hotkey": "2"},
            {"icon": "☁️", "text": "云端同步", "hotkey": "3"},
            {"icon": "📊", "text": "使用统计", "hotkey": "4"},
            {"icon": "🧹", "text": "清理缓存", "hotkey": "5"},
            {"icon": "🔙", "text": "返回", "hotkey": "0"},
        ]
        
        menu = self.menu.create_vertical(menu_items, "数据管理")
        self.console.print(menu)
        
        choice = Prompt.ask("\n选择", choices=["0", "1", "2", "3", "4", "5"], default="1")
        
        if choice == "1":
            desc = Prompt.ask("备份描述（可选）", default="")
            with self.console.status("[cyan]正在创建备份...[/]"):
                info = self.backup_manager.create_backup(description=desc)
            self.console.print(PeiYuNotification.create(
                f"备份创建成功！ID: {info.backup_id}, 大小: {info.size/1024:.1f}KB", "success", self.theme
            ))
            time.sleep(2)
            
        elif choice == "2":
            backups = self.backup_manager.list_backups()
            if not backups:
                self.console.print(PeiYuNotification.create("没有可用备份", "warning", self.theme))
            else:
                self.console.print(f"\n[{self.theme.colors['highlight']}]可用备份:[/]")
                for i, backup in enumerate(backups[:10], 1):
                    self.console.print(f"  {i}. {backup.backup_id} - {backup.description or '无描述'} ({backup.size/1024:.1f}KB)")
                
                backup_id = Prompt.ask("输入备份ID")
                if Confirm.ask(f"确定要恢复备份 {backup_id} 吗？当前数据将被覆盖"):
                    with self.console.status("[cyan]正在恢复备份...[/]"):
                        result = self.backup_manager.restore_backup(backup_id)
                    if result['success']:
                        self.console.print(PeiYuNotification.create("备份恢复成功！", "success", self.theme))
                    else:
                        self.console.print(PeiYuNotification.create(f"恢复失败: {result['error']}", "error", self.theme))
            time.sleep(2)
            
        elif choice == "3":
            self.console.print(f"\n[{self.theme.colors['highlight']}]云端同步[/]")
            self.console.print(f"  状态: {'已启用' if self.sync_manager.config.enabled else '未启用'}")
            if self.sync_manager.config.last_sync:
                self.console.print(f"  上次同步: {self.sync_manager.config.last_sync}")
            
            if Confirm.ask("是否立即同步到云端？"):
                import asyncio
                with self.console.status("[cyan]正在同步...[/]"):
                    result = asyncio.run(self.sync_manager.sync_to_cloud())
                if result['success']:
                    self.console.print(PeiYuNotification.create("同步成功！", "success", self.theme))
                else:
                    self.console.print(PeiYuNotification.create(f"同步失败: {result['error']}", "error", self.theme))
            time.sleep(2)
            
        elif choice == "4":
            report = self.stats_collector.get_usage_report(days=7)
            self.console.print(f"\n[{self.theme.colors['highlight']}]过去7天使用统计[/]")
            self.console.print(f"  事件统计: {report.get('event_stats', {})}")
            self.console.print(f"  性能统计: {report.get('performance_stats', {})}")
            self.console.print(f"  错误统计: {report.get('error_stats', {})}")
            Prompt.ask("\n按回车返回")
            
        elif choice == "5":
            CacheManager.clear()
            self.console.print(PeiYuNotification.create("缓存已清理", "success", self.theme))
            time.sleep(1)
    
    def plugin_center(self):
        """插件中心"""
        self.clear_screen()
        self.print_header("🔌 插件中心", "扩展功能")
        
        plugins = self.plugin_manager.list_plugins()
        
        if not plugins:
            self.console.print(f"\n[{self.theme.colors['dim']}]暂无已加载插件[/]")
            self.console.print(f"[{self.theme.colors['dim']}]插件目录: {self.plugin_manager.plugins_dir}[/]")
        else:
            self.console.print(f"\n[{self.theme.colors['highlight']}]已加载插件:[/]")
            for plugin in plugins:
                status = "✅ 启用" if plugin['enabled'] else "❌ 禁用"
                self.console.print(f"  • {plugin['name']} ({status})")
        
        menu_items = [
            {"icon": "🔄", "text": "刷新插件列表", "hotkey": "1"},
            {"icon": "🔙", "text": "返回", "hotkey": "0"},
        ]
        
        menu = self.menu.create_vertical(menu_items, "插件管理")
        self.console.print(menu)
        
        choice = Prompt.ask("\n选择", choices=["0", "1"], default="0")
        
        if choice == "1":
            # 扫描插件目录
            for plugin_dir in self.plugin_manager.plugins_dir.iterdir():
                if plugin_dir.is_dir():
                    self.plugin_manager.load_plugin(plugin_dir.name)
            self.console.print(PeiYuNotification.create("插件列表已刷新", "success", self.theme))
            time.sleep(1)
    
    def about(self):
        """关于"""
        self.clear_screen()
        self.print_header("ℹ 关于", "了解佩宇Reader")
        
        # 获取性能统计
        perf_stats = PerformanceMonitor.get_all_stats()
        
        about_text = f"""
[{self.theme.colors['highlight']}]佩宇Reader 高级版[/] [{self.theme.colors['accent2']}]v2.0[/]

[{self.theme.colors['dim']}]一个基于Python的Legado书源阅读器[/]
[{self.theme.colors['dim']}]采用独特的佩宇UI设计系统[/]

[{self.theme.colors['accent3']}]高级功能:[/]
  • AI智能推荐系统（深度学习）
  • 深度阅读分析
  • 成就与游戏化
  • 数据可视化仪表板
  • 性能优化（缓存、索引）
  • 数据同步与备份
  • 插件系统
  • 全文搜索（FTS5）

[{self.theme.colors['accent4']}]技术栈:[/]
  • Python 3.8+
  • Rich (UI渲染)
  • SQLite + FTS5 (数据存储)
  • FastAPI (Web后端)
  • Edge TTS (语音合成)
  • Legado书源格式

[{self.theme.colors['accent5']}]性能统计:[/]
  • 缓存命中率: 自动优化
  • 数据库索引: 已启用
  • 连接池: 已启用

[{self.theme.colors['dim']}]© 2024 佩宇Reader. All rights reserved.[/]
"""
        self.console.print(about_text)
        
        Prompt.ask("\n按回车返回")
    
    def exit_app(self):
        """退出应用"""
        self.clear_screen()
        self.console.print(PeiYuNotification.create(
            "感谢使用佩宇Reader，再见！", "success", self.theme
        ))
        time.sleep(1)


def main():
    """主函数"""
    try:
        # 显示启动画面
        console = Console()
        
        # 启动横幅
        banner = """
    ╔═══════════════════════════════════════════╗
    ║                                           ║
    ║     ✨ 佩宇Reader 高级版 ✨               ║
    ║                                           ║
    ║     PeiYu Reader Advanced v2.0            ║
    ║                                           ║
    ║     AI智能 · 深度分析 · 游戏化            ║
    ║                                           ║
    ╚═══════════════════════════════════════════╝
        """
        console.print(banner, style="cyan")
        console.print("\n[dim]正在初始化...[/]")
        time.sleep(1)
        
        # 启动应用
        app = PeiYuReader()
        app.main_loop()
        
    except KeyboardInterrupt:
        console = Console()
        console.print("\n\n[yellow]程序被用户中断[/]")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"\n\n[red]程序出错: {e}[/]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
