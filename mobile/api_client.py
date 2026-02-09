"""
移动端API客户端 - 为iOS/Android提供统一的API接口
支持: iOS (Swift), Android (Kotlin/Java), Flutter, React Native
"""

import requests
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class Platform(Enum):
    """平台类型"""
    IOS = "ios"
    ANDROID = "android"
    FLUTTER = "flutter"
    REACT_NATIVE = "react_native"
    WEB = "web"


@dataclass
class APIResponse:
    """API响应"""
    success: bool
    data: Any
    message: str = ""
    error_code: int = 0


class PeiYuAPIClient:
    """
    佩宇Reader API客户端
    
    使用示例:
        client = PeiYuAPIClient("http://localhost:8000")
        
        # 搜索书籍
        results = client.search_books("斗破苍穹")
        
        # 获取书架
        books = client.get_bookshelf()
        
        # 获取AI推荐
        recommendations = client.get_recommendations()
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", platform: Platform = Platform.WEB):
        self.base_url = base_url.rstrip("/")
        self.platform = platform
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Platform": platform.value,
            "Accept": "application/json"
        })
        
        # 认证token
        self._token: Optional[str] = None
        
        # 回调函数
        self.on_error: Optional[Callable[[str], None]] = None
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            
            data = response.json()
            return APIResponse(
                success=True,
                data=data,
                message=data.get("message", "")
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求失败: {str(e)}"
            if self.on_error:
                self.on_error(error_msg)
            return APIResponse(success=False, data=None, message=error_msg)
        
        except json.JSONDecodeError:
            error_msg = "响应解析失败"
            if self.on_error:
                self.on_error(error_msg)
            return APIResponse(success=False, data=None, message=error_msg)
    
    # ============ 书源管理 ============
    
    def get_sources(self) -> APIResponse:
        """获取所有书源"""
        return self._make_request("GET", "/api/sources")
    
    def import_sources(self, file_path: str) -> APIResponse:
        """导入书源"""
        return self._make_request("POST", "/api/sources/import", 
                                  params={"file_path": file_path})
    
    # ============ 书籍搜索 ============
    
    def search_books(self, keyword: str, sources: Optional[List[str]] = None) -> APIResponse:
        """
        搜索书籍
        
        Args:
            keyword: 搜索关键词
            sources: 指定书源列表，None表示搜索所有
        """
        data = {"keyword": keyword}
        if sources:
            data["sources"] = sources
        
        return self._make_request("POST", "/api/search", json=data)
    
    # ============ 书架管理 ============
    
    def get_bookshelf(self) -> APIResponse:
        """获取书架列表"""
        return self._make_request("GET", "/api/bookshelf")
    
    def add_to_bookshelf(self, book: Dict[str, Any]) -> APIResponse:
        """
        添加书籍到书架
        
        Args:
            book: 书籍信息字典
                {
                    "id": "书籍ID",
                    "name": "书名",
                    "author": "作者",
                    "cover": "封面URL",
                    "intro": "简介",
                    "source": "书源"
                }
        """
        return self._make_request("POST", "/api/bookshelf/add", json=book)
    
    def remove_from_bookshelf(self, book_id: str) -> APIResponse:
        """从书架移除书籍"""
        return self._make_request("DELETE", f"/api/bookshelf/{book_id}")
    
    def get_reading_progress(self, book_id: str) -> APIResponse:
        """获取阅读进度"""
        return self._make_request("GET", f"/api/bookshelf/{book_id}/progress")
    
    def update_reading_progress(self, book_id: str, chapter_id: str, position: float) -> APIResponse:
        """
        更新阅读进度
        
        Args:
            book_id: 书籍ID
            chapter_id: 章节ID
            position: 阅读位置 (0.0-1.0)
        """
        data = {
            "book_id": book_id,
            "chapter_id": chapter_id,
            "position": position
        }
        return self._make_request("POST", "/api/bookshelf/progress", json=data)
    
    # ============ AI推荐 ============
    
    def get_recommendations(self, limit: int = 10) -> APIResponse:
        """
        获取AI推荐书籍
        
        Args:
            limit: 返回数量
        """
        return self._make_request("GET", "/api/recommendations", 
                                  params={"limit": limit})
    
    def get_user_profile(self) -> APIResponse:
        """获取用户画像"""
        return self._make_request("GET", "/api/recommendations/user-profile")
    
    # ============ 阅读分析 ============
    
    def get_weekly_report(self) -> APIResponse:
        """获取周阅读报告"""
        return self._make_request("GET", "/api/analytics/weekly-report")
    
    def get_reading_patterns(self) -> APIResponse:
        """获取阅读模式分析"""
        return self._make_request("GET", "/api/analytics/reading-patterns")
    
    def get_reading_stats(self) -> APIResponse:
        """获取阅读统计"""
        return self._make_request("GET", "/api/analytics/stats")
    
    # ============ 成就系统 ============
    
    def get_achievements(self) -> APIResponse:
        """获取所有成就"""
        return self._make_request("GET", "/api/achievements")
    
    def get_daily_challenges(self) -> APIResponse:
        """获取每日挑战"""
        return self._make_request("GET", "/api/achievements/daily-challenges")
    
    def get_user_stats(self) -> APIResponse:
        """获取用户统计"""
        return self._make_request("GET", "/api/achievements/user-stats")
    
    def update_achievement_progress(self, achievement_type: str, value: int) -> APIResponse:
        """更新成就进度"""
        return self._make_request("POST", 
                                  f"/api/achievements/update/{achievement_type}",
                                  params={"value": value})
    
    # ============ TTS语音 ============
    
    def get_tts_voices(self) -> APIResponse:
        """获取可用语音列表"""
        return self._make_request("GET", "/api/tts/voices")
    
    def synthesize_speech(self, text: str, voice_id: Optional[str] = None, 
                          speed: float = 1.0) -> APIResponse:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            voice_id: 语音ID，None使用默认
            speed: 语速 (0.5-2.0)
        """
        data = {"text": text}
        if voice_id:
            data["voice_id"] = voice_id
        data["speed"] = speed
        
        return self._make_request("POST", "/api/tts/synthesize", json=data)
    
    def get_tts_cache_stats(self) -> APIResponse:
        """获取TTS缓存统计"""
        return self._make_request("GET", "/api/tts/cache-stats")
    
    def clear_tts_cache(self) -> APIResponse:
        """清除TTS缓存"""
        return self._make_request("DELETE", "/api/tts/clear-cache")
    
    # ============ 配置管理 ============
    
    def get_config(self) -> APIResponse:
        """获取配置"""
        return self._make_request("GET", "/api/config")
    
    def update_config(self, config: Dict[str, Any]) -> APIResponse:
        """更新配置"""
        return self._make_request("POST", "/api/config", json=config)


# ============ 平台特定适配器 ============

class iOSAPIClient(PeiYuAPIClient):
    """iOS专用API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url, Platform.IOS)
        # iOS特定配置
        self.session.headers.update({
            "X-iOS-Version": "16.0",
            "X-Device": "iPhone"
        })
    
    def sync_with_icloud(self) -> APIResponse:
        """与iCloud同步"""
        # iCloud同步逻辑
        pass


class AndroidAPIClient(PeiYuAPIClient):
    """Android专用API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url, Platform.ANDROID)
        # Android特定配置
        self.session.headers.update({
            "X-Android-Version": "13",
            "X-Device": "Android"
        })
    
    def sync_with_google_drive(self) -> APIResponse:
        """与Google Drive同步"""
        # Google Drive同步逻辑
        pass


class FlutterAPIClient(PeiYuAPIClient):
    """Flutter跨平台API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url, Platform.FLUTTER)


class ReactNativeAPIClient(PeiYuAPIClient):
    """React Native跨平台API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url, Platform.REACT_NATIVE)


# ============ 使用示例 ============

if __name__ == "__main__":
    # 创建客户端
    client = PeiYuAPIClient("http://localhost:8000")
    
    # 设置错误回调
    def on_error(message: str):
        print(f"错误: {message}")
    
    client.on_error = on_error
    
    # 示例: 搜索书籍
    print("=== 搜索书籍 ===")
    response = client.search_books("斗破苍穹")
    if response.success:
        print(f"找到 {len(response.data.get('results', []))} 本书")
    else:
        print(f"搜索失败: {response.message}")
    
    # 示例: 获取书架
    print("\n=== 获取书架 ===")
    response = client.get_bookshelf()
    if response.success:
        print(f"书架有 {len(response.data)} 本书")
    
    # 示例: 获取AI推荐
    print("\n=== AI推荐 ===")
    response = client.get_recommendations(5)
    if response.success:
        recommendations = response.data.get("recommendations", [])
        for book in recommendations:
            print(f"- {book.get('name')} (匹配度: {book.get('recommend_score')})")
    
    # 示例: 获取成就
    print("\n=== 成就系统 ===")
    response = client.get_achievements()
    if response.success:
        achievements = response.data.get("achievements", [])
        unlocked = sum(1 for a in achievements if a.get("unlocked"))
        print(f"已解锁 {unlocked}/{len(achievements)} 个成就")
