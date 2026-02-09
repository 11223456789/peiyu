"""
真人语音TTS引擎 - 支持多种语音合成服务
支持: Edge TTS (免费)、Azure TTS、百度TTS、讯飞TTS
"""

import asyncio
import edge_tts
import pygame
import tempfile
import os
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import sqlite3
from datetime import datetime


class TTSService(Enum):
    """TTS服务类型"""
    EDGE = "edge"           # Edge TTS (免费，质量高)
    AZURE = "azure"         # Azure TTS (付费，质量最高)
    BAIDU = "baidu"         # 百度TTS
    XUNFEI = "xunfei"       # 讯飞TTS
    SYSTEM = "system"       # 系统TTS


@dataclass
class Voice:
    """语音角色"""
    id: str
    name: str
    gender: str
    language: str
    service: TTSService
    description: str = ""
    is_neural: bool = False


@dataclass
class TTSConfig:
    """TTS配置"""
    service: TTSService = TTSService.EDGE
    voice_id: str = "zh-CN-XiaoxiaoNeural"
    speed: float = 1.0      # 语速 0.5-2.0
    pitch: float = 1.0      # 音调 0.5-2.0
    volume: float = 1.0     # 音量 0.0-1.0
    auto_play: bool = True
    cache_enabled: bool = True


class TTSEngine:
    """TTS引擎主类"""
    
    # Edge TTS 中文语音列表
    EDGE_VOICES = {
        "zh-CN-XiaoxiaoNeural": Voice("zh-CN-XiaoxiaoNeural", "晓晓", "Female", "zh-CN", TTSService.EDGE, "活泼年轻女声", True),
        "zh-CN-XiaoyiNeural": Voice("zh-CN-XiaoyiNeural", "晓伊", "Female", "zh-CN", TTSService.EDGE, "温柔女声", True),
        "zh-CN-YunjianNeural": Voice("zh-CN-YunjianNeural", "云健", "Male", "zh-CN", TTSService.EDGE, "新闻男声", True),
        "zh-CN-YunxiNeural": Voice("zh-CN-YunxiNeural", "云希", "Male", "zh-CN", TTSService.EDGE, "活泼男声", True),
        "zh-CN-YunxiaNeural": Voice("zh-CN-YunxiaNeural", "云夏", "Male", "zh-CN", TTSService.EDGE, "年轻男声", True),
        "zh-CN-YunyangNeural": Voice("zh-CN-YunyangNeural", "云扬", "Male", "zh-CN", TTSService.EDGE, "成熟男声", True),
        "zh-CN-liaoning-XiaobeiNeural": Voice("zh-CN-liaoning-XiaobeiNeural", "晓北", "Female", "zh-CN", TTSService.EDGE, "东北话女声", True),
        "zh-CN-shaanxi-XiaoniNeural": Voice("zh-CN-shaanxi-XiaoniNeural", "晓妮", "Female", "zh-CN", TTSService.EDGE, "陕西话女声", True),
        "zh-HK-HiuMaanNeural": Voice("zh-HK-HiuMaanNeural", "晓曼", "Female", "zh-HK", TTSService.EDGE, "粤语女声", True),
        "zh-HK-HiuGaaiNeural": Voice("zh-HK-HiuGaaiNeural", "晓佳", "Female", "zh-HK", TTSService.EDGE, "粤语女声2", True),
        "zh-HK-WanLungNeural": Voice("zh-HK-WanLungNeural", "云龙", "Male", "zh-HK", TTSService.EDGE, "粤语男声", True),
        "zh-TW-HsiaoChenNeural": Voice("zh-TW-HsiaoChenNeural", "晓晨", "Female", "zh-TW", TTSService.EDGE, "台湾话女声", True),
        "zh-TW-YunJheNeural": Voice("zh-TW-YunJheNeural", "云哲", "Male", "zh-TW", TTSService.EDGE, "台湾话男声", True),
    }
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.cache_dir = Path(data_dir) / "tts_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # 初始化音频播放
        pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=4096)
        
        # 配置
        self.config = self._load_config()
        
        # 状态
        self.is_playing = False
        self.current_task: Optional[asyncio.Task] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None
        self.on_complete: Optional[Callable[[], None]] = None
        
        # 数据库
        self._init_database()
    
    def _init_database(self):
        """初始化TTS数据库"""
        db_path = Path(self.data_dir) / "tts.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tts_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_hash TEXT UNIQUE,
                    text_content TEXT,
                    voice_id TEXT,
                    audio_path TEXT,
                    duration REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    play_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tts_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT,
                    chapter_id TEXT,
                    text_content TEXT,
                    voice_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def _load_config(self) -> TTSConfig:
        """加载配置"""
        config_path = Path(self.data_dir) / "tts_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return TTSConfig(
                    service=TTSService(data.get('service', 'edge')),
                    voice_id=data.get('voice_id', 'zh-CN-XiaoxiaoNeural'),
                    speed=data.get('speed', 1.0),
                    pitch=data.get('pitch', 1.0),
                    volume=data.get('volume', 1.0),
                    auto_play=data.get('auto_play', True),
                    cache_enabled=data.get('cache_enabled', True)
                )
        return TTSConfig()
    
    def save_config(self):
        """保存配置"""
        config_path = Path(self.data_dir) / "tts_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({
                'service': self.config.service.value,
                'voice_id': self.config.voice_id,
                'speed': self.config.speed,
                'pitch': self.config.pitch,
                'volume': self.config.volume,
                'auto_play': self.config.auto_play,
                'cache_enabled': self.config.cache_enabled
            }, f, ensure_ascii=False, indent=2)
    
    def get_available_voices(self, language: str = "zh") -> List[Voice]:
        """获取可用语音列表"""
        voices = []
        for voice in self.EDGE_VOICES.values():
            if language in voice.language.lower():
                voices.append(voice)
        return voices
    
    def _get_cache_path(self, text: str, voice_id: str) -> Optional[str]:
        """获取缓存路径"""
        import hashlib
        text_hash = hashlib.md5(f"{text}:{voice_id}".encode()).hexdigest()
        
        db_path = Path(self.data_dir) / "tts.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT audio_path FROM tts_cache WHERE text_hash = ?",
                (text_hash,)
            )
            result = cursor.fetchone()
            if result and os.path.exists(result[0]):
                # 更新播放计数
                cursor.execute(
                    "UPDATE tts_cache SET play_count = play_count + 1 WHERE text_hash = ?",
                    (text_hash,)
                )
                conn.commit()
                return result[0]
        return None
    
    def _save_cache(self, text: str, voice_id: str, audio_path: str, duration: float):
        """保存缓存"""
        import hashlib
        text_hash = hashlib.md5(f"{text}:{voice_id}".encode()).hexdigest()
        
        db_path = Path(self.data_dir) / "tts.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO tts_cache 
                (text_hash, text_content, voice_id, audio_path, duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (text_hash, text[:500], voice_id, audio_path, duration))
            conn.commit()
    
    async def _synthesize_edge(self, text: str, voice_id: str) -> str:
        """使用Edge TTS合成语音"""
        # 检查缓存
        if self.config.cache_enabled:
            cached_path = self._get_cache_path(text, voice_id)
            if cached_path:
                return cached_path
        
        # 生成临时文件
        temp_file = self.cache_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text)}.mp3"
        
        # 调整语速参数
        rate = f"{int((self.config.speed - 1) * 100):+d}%"
        
        # 合成语音
        communicate = edge_tts.Communicate(text, voice_id, rate=rate)
        await communicate.save(str(temp_file))
        
        # 保存缓存
        if self.config.cache_enabled:
            self._save_cache(text, voice_id, str(temp_file), 0.0)
        
        return str(temp_file)
    
    async def synthesize(self, text: str) -> str:
        """合成语音"""
        if self.config.service == TTSService.EDGE:
            return await self._synthesize_edge(text, self.config.voice_id)
        else:
            raise NotImplementedError(f"TTS服务 {self.config.service} 尚未实现")
    
    def play_audio(self, audio_path: str):
        """播放音频"""
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.set_volume(self.config.volume)
            pygame.mixer.music.play()
            self.is_playing = True
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            self.is_playing = False
            if self.on_complete:
                self.on_complete()
                
        except Exception as e:
            print(f"播放音频失败: {e}")
            self.is_playing = False
    
    async def speak(self, text: str, auto_play: bool = True) -> str:
        """合成并播放语音"""
        audio_path = await self.synthesize(text)
        
        if auto_play and self.config.auto_play:
            self.play_audio(audio_path)
        
        return audio_path
    
    def stop(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_playing = False
    
    def pause(self):
        """暂停播放"""
        pygame.mixer.music.pause()
    
    def resume(self):
        """恢复播放"""
        pygame.mixer.music.unpause()
    
    def set_voice(self, voice_id: str):
        """设置语音"""
        self.config.voice_id = voice_id
        self.save_config()
    
    def set_speed(self, speed: float):
        """设置语速"""
        self.config.speed = max(0.5, min(2.0, speed))
        self.save_config()
    
    def set_volume(self, volume: float):
        """设置音量"""
        self.config.volume = max(0.0, min(1.0, volume))
        self.save_config()
    
    def clear_cache(self):
        """清理缓存"""
        # 删除旧缓存文件
        for file in self.cache_dir.glob("*.mp3"):
            try:
                file.unlink()
            except:
                pass
        
        # 清空数据库
        db_path = Path(self.data_dir) / "tts.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tts_cache")
            conn.commit()
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        db_path = Path(self.data_dir) / "tts.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(play_count) FROM tts_cache")
            count, plays = cursor.fetchone()
            return {
                "cache_count": count or 0,
                "total_plays": plays or 0
            }


class ReadingAloudController:
    """朗读控制器 - 控制书籍朗读"""
    
    def __init__(self, tts_engine: TTSEngine):
        self.tts = tts_engine
        self.is_reading = False
        self.current_book_id: Optional[str] = None
        self.current_chapter_id: Optional[str] = None
        self.current_paragraph: int = 0
        self.paragraphs: List[str] = []
        self.on_paragraph_start: Optional[Callable[[int, str], None]] = None
        self.on_reading_complete: Optional[Callable[[], None]] = None
    
    def load_chapter(self, book_id: str, chapter_id: str, content: str):
        """加载章节内容"""
        self.current_book_id = book_id
        self.current_chapter_id = chapter_id
        # 将内容分段
        self.paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        self.current_paragraph = 0
    
    async def start_reading(self, from_paragraph: int = 0):
        """开始朗读"""
        if not self.paragraphs:
            return
        
        self.is_reading = True
        self.current_paragraph = from_paragraph
        
        while self.is_reading and self.current_paragraph < len(self.paragraphs):
            paragraph = self.paragraphs[self.current_paragraph]
            
            # 回调通知
            if self.on_paragraph_start:
                self.on_paragraph_start(self.current_paragraph, paragraph)
            
            # 合成并播放
            await self.tts.speak(paragraph)
            
            self.current_paragraph += 1
        
        self.is_reading = False
        
        if self.on_reading_complete:
            self.on_reading_complete()
    
    def stop_reading(self):
        """停止朗读"""
        self.is_reading = False
        self.tts.stop()
    
    def next_paragraph(self):
        """下一段"""
        self.tts.stop()
        self.current_paragraph = min(len(self.paragraphs) - 1, self.current_paragraph + 1)
    
    def previous_paragraph(self):
        """上一段"""
        self.tts.stop()
        self.current_paragraph = max(0, self.current_paragraph - 1)
    
    def get_progress(self) -> Dict:
        """获取朗读进度"""
        return {
            "current": self.current_paragraph,
            "total": len(self.paragraphs),
            "percentage": (self.current_paragraph / len(self.paragraphs) * 100) if self.paragraphs else 0
        }
