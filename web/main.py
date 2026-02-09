"""
佩宇Reader Web版本 - FastAPI后端
提供RESTful API供Web、iOS、Android调用
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys
import os
import json
import asyncio
from datetime import datetime

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from core.book_source import BookSourceManager, BookSource
from core.bookshelf import BookshelfManager, Book
from core.ai_recommendation import AIRecommendationEngine
from core.reading_analytics import ReadingAnalyticsEngine
from core.achievement_system import AchievementManager
from core.tts_engine import TTSEngine, ReadingAloudController
from core.config import ConfigManager

app = FastAPI(
    title="佩宇Reader API",
    description="佩宇Reader后端API服务",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据目录
DATA_DIR = Path.home() / ".peiyu_reader"
DATA_DIR.mkdir(exist_ok=True)

# 初始化管理器
source_manager = BookSourceManager()
bookshelf = BookshelfManager(str(DATA_DIR))
ai_engine = AIRecommendationEngine(str(DATA_DIR))
analytics = ReadingAnalyticsEngine(str(DATA_DIR))
achievements = AchievementManager(str(DATA_DIR))
tts_engine = TTSEngine(str(DATA_DIR))
config_manager = ConfigManager()

# 加载书源
sources_file = Path(__file__).parent.parent / "sources" / "book_sources.json"
if sources_file.exists():
    source_manager.load_from_json(str(sources_file))


# ============ 数据模型 ============

class BookSourceModel(BaseModel):
    bookSourceName: str
    bookSourceUrl: str
    bookSourceGroup: str = ""
    enabled: bool = True


class BookModel(BaseModel):
    id: str
    name: str
    author: str
    cover: str = ""
    intro: str = ""
    source: str = ""
    latest_chapter: str = ""
    progress: float = 0.0


class SearchRequest(BaseModel):
    keyword: str
    sources: Optional[List[str]] = None


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    speed: Optional[float] = 1.0


class ReadingProgress(BaseModel):
    book_id: str
    chapter_id: str
    position: float


class UserStats(BaseModel):
    level: int
    title: str
    points: int
    achievements_unlocked: int
    achievements_total: int


# ============ API路由 ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "佩宇Reader API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


# ============ 书源管理 ============

@app.get("/api/sources", response_model=List[Dict])
async def get_sources():
    """获取所有书源"""
    sources = source_manager.list_sources()
    return [
        {
            "name": s.bookSourceName,
            "url": s.bookSourceUrl,
            "group": s.bookSourceGroup,
            "enabled": s.enabled
        }
        for s in sources
    ]


@app.post("/api/sources/import")
async def import_sources(file_path: str):
    """导入书源"""
    try:
        count = source_manager.load_from_json(file_path)
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ 书籍搜索 ============

@app.post("/api/search")
async def search_books(request: SearchRequest):
    """搜索书籍"""
    # 这里简化处理，实际应该调用书源搜索
    results = []
    sources = source_manager.list_sources()
    
    for source in sources[:3]:  # 限制搜索前3个书源
        try:
            # 模拟搜索结果
            results.append({
                "name": f"{request.keyword} - 来自{source.bookSourceName}",
                "author": "作者",
                "source": source.bookSourceName,
                "cover": "",
                "intro": f"从{source.bookSourceName}搜索到的书籍"
            })
        except:
            pass
    
    return {"results": results, "total": len(results)}


# ============ 书架管理 ============

@app.get("/api/bookshelf", response_model=List[Dict])
async def get_bookshelf():
    """获取书架"""
    books = bookshelf.get_all_books()
    return [
        {
            "id": b.get("id", ""),
            "name": b.get("name", ""),
            "author": b.get("author", ""),
            "cover": b.get("cover", ""),
            "progress": b.get("progress", 0),
            "current_chapter": b.get("current_chapter", ""),
            "source": b.get("source", "")
        }
        for b in books
    ]


@app.post("/api/bookshelf/add")
async def add_to_bookshelf(book: BookModel):
    """添加书籍到书架"""
    try:
        bookshelf.add_book(book.dict())
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/bookshelf/{book_id}")
async def remove_from_bookshelf(book_id: str):
    """从书架移除书籍"""
    try:
        bookshelf.remove_book(book_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/bookshelf/{book_id}/progress")
async def get_reading_progress(book_id: str):
    """获取阅读进度"""
    progress = bookshelf.get_reading_progress(book_id)
    return progress


@app.post("/api/bookshelf/progress")
async def update_reading_progress(progress: ReadingProgress):
    """更新阅读进度"""
    try:
        bookshelf.update_progress(
            progress.book_id,
            progress.chapter_id,
            progress.position
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ AI推荐 ============

@app.get("/api/recommendations")
async def get_recommendations(limit: int = 10):
    """获取AI推荐"""
    # 模拟书籍数据
    mock_books = [
        {
            "id": str(i),
            "name": f"推荐书籍{i}",
            "author": f"作者{i}",
            "category": "玄幻",
            "tags": ["热血", "升级"],
            "popularity": 90 - i,
            "rating": 8.5
        }
        for i in range(1, 11)
    ]
    
    recommendations = ai_engine.get_personalized_recommendations(mock_books, limit)
    return {"recommendations": recommendations}


@app.get("/api/recommendations/user-profile")
async def get_user_profile():
    """获取用户画像"""
    profile = ai_engine.user_profile
    return {
        "favorite_categories": profile.favorite_categories,
        "favorite_authors": profile.favorite_authors,
        "avg_reading_speed": profile.avg_reading_speed,
        "preferred_times": profile.preferred_times
    }


# ============ 阅读分析 ============

@app.get("/api/analytics/weekly-report")
async def get_weekly_report():
    """获取周阅读报告"""
    report = analytics.get_weekly_report()
    return report


@app.get("/api/analytics/reading-patterns")
async def get_reading_patterns():
    """获取阅读模式"""
    patterns = analytics.get_reading_patterns()
    return {"patterns": patterns}


@app.get("/api/analytics/stats")
async def get_reading_stats():
    """获取阅读统计"""
    return {
        "total_books": len(bookshelf.get_all_books()),
        "total_time": 0,
        "total_words": 0,
        "current_streak": 0
    }


# ============ 成就系统 ============

@app.get("/api/achievements")
async def get_achievements():
    """获取所有成就"""
    all_achievements = achievements.get_all_achievements()
    return {"achievements": all_achievements}


@app.get("/api/achievements/daily-challenges")
async def get_daily_challenges():
    """获取每日挑战"""
    challenges = achievements.get_daily_challenges()
    return {"challenges": challenges}


@app.get("/api/achievements/user-stats")
async def get_user_stats():
    """获取用户统计"""
    all_achievements = achievements.get_all_achievements()
    unlocked = sum(1 for a in all_achievements if a['unlocked'])
    
    return {
        "level": achievements.current_level,
        "title": achievements.current_title,
        "points": achievements.total_points,
        "achievements_unlocked": unlocked,
        "achievements_total": len(all_achievements),
        "progress": unlocked / len(all_achievements) if all_achievements else 0
    }


@app.post("/api/achievements/update/{achievement_type}")
async def update_achievement_progress(achievement_type: str, value: int):
    """更新成就进度"""
    from core.achievement_system import AchievementType
    
    try:
        ach_type = AchievementType(achievement_type)
        unlocked = achievements.update_progress(ach_type, value)
        return {
            "success": True,
            "newly_unlocked": unlocked
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ TTS语音 ============

@app.get("/api/tts/voices")
async def get_tts_voices():
    """获取可用语音列表"""
    voices = tts_engine.get_available_voices("zh")
    return {
        "voices": [
            {
                "id": v.id,
                "name": v.name,
                "gender": v.gender,
                "description": v.description,
                "is_neural": v.is_neural
            }
            for v in voices
        ]
    }


@app.post("/api/tts/synthesize")
async def synthesize_speech(request: TTSRequest):
    """合成语音"""
    try:
        # 更新配置
        if request.voice_id:
            tts_engine.set_voice(request.voice_id)
        if request.speed:
            tts_engine.set_speed(request.speed)
        
        # 合成语音
        audio_path = await tts_engine.synthesize(request.text)
        
        return {
            "success": True,
            "audio_url": f"/api/tts/audio/{Path(audio_path).name}",
            "text": request.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tts/audio/{filename}")
async def get_audio_file(filename: str):
    """获取音频文件"""
    audio_path = DATA_DIR / "tts_cache" / filename
    if audio_path.exists():
        return FileResponse(str(audio_path), media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="音频文件不存在")


@app.get("/api/tts/cache-stats")
async def get_tts_cache_stats():
    """获取TTS缓存统计"""
    stats = tts_engine.get_cache_stats()
    return stats


@app.delete("/api/tts/clear-cache")
async def clear_tts_cache():
    """清除TTS缓存"""
    tts_engine.clear_cache()
    return {"success": True}


# ============ 配置管理 ============

@app.get("/api/config")
async def get_config():
    """获取配置"""
    return config_manager.config


@app.post("/api/config")
async def update_config(config: Dict[str, Any]):
    """更新配置"""
    for key, value in config.items():
        config_manager.set(key, value)
    return {"success": True}


# ============ 启动服务 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
