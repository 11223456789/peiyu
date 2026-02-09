"""
并发搜索模块 - 提高搜索速度
"""
import asyncio
import aiohttp
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class AsyncBookSourceSearcher:
    """异步书源搜索器"""

    def __init__(self, max_workers: int = 5, timeout: int = 10):
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = None

    async def _init_session(self):
        """初始化aiohttp会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

    async def _close_session(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def search_single_source(self, source_manager, source_name: str,
                                   keyword: str) -> List[Dict[str, Any]]:
        """在单个书源搜索"""
        try:
            # 使用同步方法的线程池执行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                source_manager.search_book,
                source_name,
                keyword
            )
            return result if result else []
        except Exception as e:
            print(f"搜索失败 [{source_name}]: {e}")
            return []

    async def search_all_sources(self, source_manager, keyword: str,
                                  progress_callback: Callable = None) -> List[Dict[str, Any]]:
        """在所有书源并发搜索"""
        sources = source_manager.list_sources()
        if not sources:
            return []

        all_results = []
        completed = 0

        # 创建搜索任务
        tasks = []
        for source in sources:
            task = self.search_single_source(
                source_manager,
                source.bookSourceName,
                keyword
            )
            tasks.append((source.bookSourceName, task))

        # 并发执行
        for source_name, task in tasks:
            try:
                results = await task

                # 添加书源信息
                for r in results:
                    r['source_name'] = source_name

                all_results.extend(results)
                completed += 1

                if progress_callback:
                    progress_callback(completed, len(tasks), source_name, len(results))

            except Exception as e:
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(tasks), source_name, 0)

        return all_results


class ConcurrentSearcher:
    """线程池并发搜索器"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers

    def search_all_sources(self, source_manager, keyword: str,
                           progress_callback: Callable = None) -> List[Dict[str, Any]]:
        """在所有书源并发搜索"""
        sources = source_manager.list_sources()
        if not sources:
            return []

        all_results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有搜索任务
            future_to_source = {
                executor.submit(
                    source_manager.search_book,
                    source.bookSourceName,
                    keyword
                ): source
                for source in sources
            }

            # 收集结果
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    results = future.result()
                    if results:
                        for r in results:
                            r['source_name'] = source.bookSourceName
                        all_results.extend(results)

                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(sources),
                                        source.bookSourceName, len(results) if results else 0)

                except Exception as e:
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(sources),
                                        source.bookSourceName, 0)

        return all_results


class SearchHistory:
    """搜索历史管理"""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self):
        """从文件加载历史"""
        import json
        import os

        history_file = os.path.expanduser('~/.legado_reader/search_history.json')
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []

    def _save_history(self):
        """保存历史到文件"""
        import json
        import os

        history_dir = os.path.expanduser('~/.legado_reader')
        os.makedirs(history_dir, exist_ok=True)
        history_file = os.path.join(history_dir, 'search_history.json')

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def add(self, keyword: str, result_count: int):
        """添加搜索记录"""
        # 移除重复项
        self.history = [h for h in self.history if h['keyword'] != keyword]

        # 添加新记录
        self.history.insert(0, {
            'keyword': keyword,
            'result_count': result_count,
            'timestamp': time.time()
        })

        # 限制数量
        self.history = self.history[:self.max_history]

        self._save_history()

    def get_history(self, limit: int = 10) -> List[str]:
        """获取搜索历史关键词"""
        return [h['keyword'] for h in self.history[:limit]]

    def clear(self):
        """清空历史"""
        self.history = []
        self._save_history()

    def get_popular_keywords(self, limit: int = 5) -> List[str]:
        """获取热门搜索词"""
        from collections import Counter

        # 统计频率
        keywords = [h['keyword'] for h in self.history]
        counter = Counter(keywords)

        return [k for k, _ in counter.most_common(limit)]


class SourceHealthChecker:
    """书源健康检查器"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def check_source(self, source) -> Dict[str, Any]:
        """检查单个书源健康状态"""
        import requests
        import time

        result = {
            'source_name': source.bookSourceName,
            'url': source.bookSourceUrl,
            'status': 'unknown',
            'response_time': 0,
            'error': None
        }

        try:
            start_time = time.time()
            response = requests.get(
                source.bookSourceUrl,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            result['response_time'] = round(time.time() - start_time, 2)

            if response.status_code == 200:
                result['status'] = 'healthy'
            else:
                result['status'] = 'error'
                result['error'] = f"HTTP {response.status_code}"

        except requests.Timeout:
            result['status'] = 'timeout'
            result['error'] = '请求超时'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def check_all_sources(self, sources: List[Any],
                         progress_callback: Callable = None) -> List[Dict[str, Any]]:
        """检查所有书源"""
        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {
                executor.submit(self.check_source, source): source
                for source in sources
            }

            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'source_name': source.bookSourceName,
                        'url': source.bookSourceUrl,
                        'status': 'error',
                        'error': str(e)
                    })

                completed += 1
                if progress_callback:
                    progress_callback(completed, len(sources))

        return results
