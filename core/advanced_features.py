"""
高级功能模块 - 数据同步、备份恢复、云存储、插件系统
"""
import json
import sqlite3
import zipfile
import shutil
import hashlib
import threading
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import os
import time


@dataclass
class SyncConfig:
    """同步配置"""
    enabled: bool = False
    sync_interval: int = 3600  # 秒
    last_sync: str = ""
    sync_server: str = ""  # 同步服务器地址
    api_key: str = ""
    auto_sync: bool = True
    sync_bookshelf: bool = True
    sync_reading_progress: bool = True
    sync_settings: bool = True


@dataclass
class BackupInfo:
    """备份信息"""
    backup_id: str
    created_at: str
    size: int
    description: str
    includes: List[str]
    checksum: str


class DataSyncManager:
    """数据同步管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / "sync_config.json"
        self.config = self._load_config()
        self._sync_lock = threading.Lock()
        self._sync_task: Optional[asyncio.Task] = None
    
    def _load_config(self) -> SyncConfig:
        """加载同步配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return SyncConfig(**data)
            except:
                pass
        return SyncConfig()
    
    def save_config(self):
        """保存同步配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
    
    async def sync_to_cloud(self) -> Dict:
        """同步数据到云端"""
        if not self.config.enabled or not self.config.sync_server:
            return {'success': False, 'error': '同步未启用'}
        
        with self._sync_lock:
            try:
                # 准备同步数据
                sync_data = self._prepare_sync_data()
                
                # 这里应该实现实际的HTTP请求
                # 简化示例
                self.config.last_sync = datetime.now().isoformat()
                self.save_config()
                
                return {
                    'success': True,
                    'timestamp': self.config.last_sync,
                    'data_size': len(json.dumps(sync_data))
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    async def sync_from_cloud(self) -> Dict:
        """从云端同步数据"""
        if not self.config.enabled:
            return {'success': False, 'error': '同步未启用'}
        
        with self._sync_lock:
            try:
                # 这里应该实现实际的HTTP请求获取数据
                # 简化示例
                return {'success': True, 'message': '数据已同步'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def _prepare_sync_data(self) -> Dict:
        """准备同步数据"""
        data = {}
        
        if self.config.sync_bookshelf:
            # 读取书架数据
            db_path = self.data_dir / "bookshelf.db"
            if db_path.exists():
                data['bookshelf'] = self._export_database(str(db_path))
        
        if self.config.sync_reading_progress:
            # 读取进度数据
            progress_file = self.data_dir / "reading_progress.json"
            if progress_file.exists():
                with open(progress_file, 'r', encoding='utf-8') as f:
                    data['reading_progress'] = json.load(f)
        
        if self.config.sync_settings:
            # 读取设置
            config_file = self.data_dir / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    data['settings'] = json.load(f)
        
        return data
    
    def _export_database(self, db_path: str) -> List[Dict]:
        """导出数据库为JSON"""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        data = {}
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            data[table] = [dict(row) for row in rows]
        
        conn.close()
        return data
    
    def start_auto_sync(self):
        """启动自动同步"""
        if self.config.auto_sync and self.config.enabled:
            asyncio.create_task(self._auto_sync_loop())
    
    async def _auto_sync_loop(self):
        """自动同步循环"""
        while True:
            await asyncio.sleep(self.config.sync_interval)
            if self.config.auto_sync:
                await self.sync_to_cloud()


class BackupManager:
    """备份管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, description: str = "", 
                     includes: List[str] = None) -> BackupInfo:
        """创建备份"""
        backup_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"backup_{backup_id}.zip"
        
        if includes is None:
            includes = ['bookshelf', 'config', 'cache', 'sources']
        
        # 创建ZIP文件
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 备份书架数据库
            if 'bookshelf' in includes:
                db_path = self.data_dir / "bookshelf.db"
                if db_path.exists():
                    zf.write(db_path, 'bookshelf.db')
            
            # 备份配置
            if 'config' in includes:
                config_path = self.data_dir / "config.json"
                if config_path.exists():
                    zf.write(config_path, 'config.json')
            
            # 备份书源
            if 'sources' in includes:
                sources_dir = self.data_dir / "sources"
                if sources_dir.exists():
                    for file in sources_dir.rglob('*'):
                        if file.is_file():
                            arcname = f"sources/{file.relative_to(sources_dir)}"
                            zf.write(file, arcname)
            
            # 备份缓存（可选）
            if 'cache' in includes:
                cache_dir = self.data_dir / "cache"
                if cache_dir.exists():
                    for file in cache_dir.rglob('*'):
                        if file.is_file():
                            arcname = f"cache/{file.relative_to(cache_dir)}"
                            zf.write(file, arcname)
        
        # 计算校验和
        checksum = self._calculate_checksum(backup_path)
        
        # 创建备份信息
        info = BackupInfo(
            backup_id=backup_id,
            created_at=datetime.now().isoformat(),
            size=backup_path.stat().st_size,
            description=description,
            includes=includes,
            checksum=checksum
        )
        
        # 保存备份信息
        info_path = self.backup_dir / f"backup_{backup_id}.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(info), f, ensure_ascii=False, indent=2)
        
        return info
    
    def restore_backup(self, backup_id: str) -> Dict:
        """恢复备份"""
        backup_path = self.backup_dir / f"backup_{backup_id}.zip"
        
        if not backup_path.exists():
            return {'success': False, 'error': '备份不存在'}
        
        # 验证校验和
        info_path = self.backup_dir / f"backup_{backup_id}.json"
        if info_path.exists():
            with open(info_path, 'r', encoding='utf-8') as f:
                info = BackupInfo(**json.load(f))
            
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != info.checksum:
                return {'success': False, 'error': '备份文件已损坏'}
        
        # 解压备份
        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                # 先备份当前数据
                self._backup_current_data()
                
                # 解压
                zf.extractall(self.data_dir)
            
            return {'success': True, 'message': '恢复成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_backups(self) -> List[BackupInfo]:
        """列出所有备份"""
        backups = []
        
        for info_file in self.backup_dir.glob("backup_*.json"):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    backups.append(BackupInfo(**json.load(f)))
            except:
                pass
        
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        backup_path = self.backup_dir / f"backup_{backup_id}.zip"
        info_path = self.backup_dir / f"backup_{backup_id}.json"
        
        try:
            if backup_path.exists():
                backup_path.unlink()
            if info_path.exists():
                info_path.unlink()
            return True
        except:
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _backup_current_data(self):
        """备份当前数据（用于恢复失败时回滚）"""
        rollback_dir = self.data_dir / "rollback"
        rollback_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rollback_path = rollback_dir / f"rollback_{timestamp}.zip"
        
        with zipfile.ZipFile(rollback_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in self.data_dir.rglob('*'):
                if file.is_file() and 'backups' not in str(file) and 'rollback' not in str(file):
                    arcname = str(file.relative_to(self.data_dir))
                    zf.write(file, arcname)


class PluginManager:
    """插件管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.plugins_dir = self.data_dir / "plugins"
        self.plugins_dir.mkdir(exist_ok=True)
        
        self.plugins: Dict[str, Any] = {}
        self.hooks: Dict[str, List[Callable]] = defaultdict(list)
    
    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        plugin_path = self.plugins_dir / plugin_name
        
        if not plugin_path.exists():
            return False
        
        try:
            # 读取插件配置
            config_path = plugin_path / "plugin.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {'name': plugin_name, 'version': '1.0.0'}
            
            # 加载插件模块
            init_file = plugin_path / "__init__.py"
            if init_file.exists():
                # 动态导入插件
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    plugin_name, str(init_file)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                self.plugins[plugin_name] = {
                    'config': config,
                    'module': module,
                    'enabled': True
                }
                
                # 调用插件初始化
                if hasattr(module, 'initialize'):
                    module.initialize(self)
                
                return True
        except Exception as e:
            print(f"加载插件 {plugin_name} 失败: {e}")
        
        return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        # 调用插件清理
        if hasattr(plugin['module'], 'cleanup'):
            try:
                plugin['module'].cleanup()
            except:
                pass
        
        del self.plugins[plugin_name]
        return True
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name]['enabled'] = True
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name]['enabled'] = False
            return True
        return False
    
    def register_hook(self, hook_name: str, callback: Callable):
        """注册钩子"""
        self.hooks[hook_name].append(callback)
    
    def unregister_hook(self, hook_name: str, callback: Callable):
        """注销钩子"""
        if hook_name in self.hooks:
            self.hooks[hook_name] = [
                cb for cb in self.hooks[hook_name] if cb != callback
            ]
    
    def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """触发钩子"""
        results = []
        for callback in self.hooks.get(hook_name, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"钩子 {hook_name} 执行失败: {e}")
        return results
    
    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        result = []
        
        for plugin_name, plugin in self.plugins.items():
            result.append({
                'name': plugin_name,
                'config': plugin['config'],
                'enabled': plugin['enabled']
            })
        
        return result


class StatisticsCollector:
    """统计收集器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "statistics.db"
        self._init_database()
    
    def _init_database(self):
        """初始化统计数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 使用统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    event_data TEXT,
                    timestamp TEXT,
                    session_id TEXT
                )
            ''')
            
            # 性能统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT,
                    duration_ms REAL,
                    timestamp TEXT
                )
            ''')
            
            # 错误日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    timestamp TEXT
                )
            ''')
            
            conn.commit()
    
    def log_event(self, event_type: str, event_data: Dict, session_id: str = ""):
        """记录事件"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO usage_stats (event_type, event_data, timestamp, session_id)
                VALUES (?, ?, ?, ?)
            ''', (
                event_type,
                json.dumps(event_data, ensure_ascii=False),
                datetime.now().isoformat(),
                session_id
            ))
            conn.commit()
    
    def log_performance(self, operation: str, duration_ms: float):
        """记录性能数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO performance_stats (operation, duration_ms, timestamp)
                VALUES (?, ?, ?)
            ''', (operation, duration_ms, datetime.now().isoformat()))
            conn.commit()
    
    def log_error(self, error_type: str, error_message: str, stack_trace: str = ""):
        """记录错误"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO error_logs (error_type, error_message, stack_trace, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (error_type, error_message, stack_trace, datetime.now().isoformat()))
            conn.commit()
    
    def get_usage_report(self, days: int = 7) -> Dict:
        """生成使用报告"""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 事件统计
            cursor.execute('''
                SELECT event_type, COUNT(*) as count
                FROM usage_stats
                WHERE timestamp > ?
                GROUP BY event_type
            ''', (since,))
            event_stats = dict(cursor.fetchall())
            
            # 性能统计
            cursor.execute('''
                SELECT operation, AVG(duration_ms) as avg_duration
                FROM performance_stats
                WHERE timestamp > ?
                GROUP BY operation
            ''', (since,))
            perf_stats = dict(cursor.fetchall())
            
            # 错误统计
            cursor.execute('''
                SELECT error_type, COUNT(*) as count
                FROM error_logs
                WHERE timestamp > ?
                GROUP BY error_type
            ''', (since,))
            error_stats = dict(cursor.fetchall())
            
            return {
                'period_days': days,
                'event_stats': event_stats,
                'performance_stats': perf_stats,
                'error_stats': error_stats
            }


class ShortcutManager:
    """快捷键管理器"""
    
    DEFAULT_SHORTCUTS = {
        'open_book': {'key': 'o', 'ctrl': True, 'description': '打开书籍'},
        'search': {'key': 'f', 'ctrl': True, 'description': '搜索'},
        'next_chapter': {'key': 'pagedown', 'ctrl': False, 'description': '下一章'},
        'prev_chapter': {'key': 'pageup', 'ctrl': False, 'description': '上一章'},
        'bookmark': {'key': 'b', 'ctrl': True, 'description': '添加书签'},
        'fullscreen': {'key': 'f11', 'ctrl': False, 'description': '全屏'},
        'settings': {'key': 's', 'ctrl': True, 'description': '设置'},
        'quit': {'key': 'q', 'ctrl': True, 'description': '退出'},
    }
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / "shortcuts.json"
        self.shortcuts = self._load_shortcuts()
    
    def _load_shortcuts(self) -> Dict:
        """加载快捷键配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return self.DEFAULT_SHORTCUTS.copy()
    
    def save_shortcuts(self):
        """保存快捷键配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.shortcuts, f, ensure_ascii=False, indent=2)
    
    def get_shortcut(self, action: str) -> Optional[Dict]:
        """获取快捷键"""
        return self.shortcuts.get(action)
    
    def set_shortcut(self, action: str, key: str, ctrl: bool = False):
        """设置快捷键"""
        if action in self.shortcuts:
            self.shortcuts[action]['key'] = key
            self.shortcuts[action]['ctrl'] = ctrl
            self.save_shortcuts()
            return True
        return False
    
    def reset_to_default(self):
        """重置为默认快捷键"""
        self.shortcuts = self.DEFAULT_SHORTCUTS.copy()
        self.save_shortcuts()
    
    def list_shortcuts(self) -> Dict:
        """列出所有快捷键"""
        return self.shortcuts.copy()


class ThemeEngine:
    """主题引擎 - 支持自定义主题"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.themes_dir = self.data_dir / "themes"
        self.themes_dir.mkdir(exist_ok=True)
        
        self.current_theme = "default"
        self.themes: Dict[str, Dict] = {}
        
        self._load_builtin_themes()
        self._load_custom_themes()
    
    def _load_builtin_themes(self):
        """加载内置主题"""
        self.themes['default'] = {
            'name': '默认',
            'background': '#1e1e1e',
            'foreground': '#d4d4d4',
            'accent': '#007acc',
            'font_family': 'Consolas',
            'font_size': 14,
            'line_height': 1.6
        }
        
        self.themes['light'] = {
            'name': '明亮',
            'background': '#ffffff',
            'foreground': '#333333',
            'accent': '#0066cc',
            'font_family': 'Consolas',
            'font_size': 14,
            'line_height': 1.6
        }
        
        self.themes['sepia'] = {
            'name': '护眼',
            'background': '#f4ecd8',
            'foreground': '#5b4636',
            'accent': '#8b6914',
            'font_family': 'Georgia',
            'font_size': 16,
            'line_height': 1.8
        }
    
    def _load_custom_themes(self):
        """加载自定义主题"""
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme = json.load(f)
                    theme_name = theme_file.stem
                    self.themes[theme_name] = theme
            except:
                pass
    
    def create_theme(self, name: str, theme_data: Dict) -> bool:
        """创建自定义主题"""
        theme_id = name.lower().replace(' ', '_')
        
        theme_file = self.themes_dir / f"{theme_id}.json"
        with open(theme_file, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, ensure_ascii=False, indent=2)
        
        self.themes[theme_id] = theme_data
        return True
    
    def delete_theme(self, theme_id: str) -> bool:
        """删除主题"""
        if theme_id in ['default', 'light', 'sepia']:
            return False  # 不能删除内置主题
        
        theme_file = self.themes_dir / f"{theme_id}.json"
        if theme_file.exists():
            theme_file.unlink()
        
        if theme_id in self.themes:
            del self.themes[theme_id]
        
        return True
    
    def set_theme(self, theme_id: str) -> bool:
        """设置当前主题"""
        if theme_id in self.themes:
            self.current_theme = theme_id
            return True
        return False
    
    def get_current_theme(self) -> Dict:
        """获取当前主题"""
        return self.themes.get(self.current_theme, self.themes['default'])
    
    def list_themes(self) -> List[Dict]:
        """列出所有主题"""
        return [
            {'id': k, 'name': v.get('name', k), 'custom': k not in ['default', 'light', 'sepia']}
            for k, v in self.themes.items()
        ]
