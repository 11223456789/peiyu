"""
成就系统 - 游戏化阅读体验
提供徽章、等级、挑战和奖励机制
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import random


class AchievementType(Enum):
    """成就类型"""
    READING_TIME = "reading_time"  # 阅读时长
    BOOKS_COMPLETED = "books_completed"  # 完成书籍
    CHAPTERS_READ = "chapters_read"  # 阅读章节
    STREAK_DAYS = "streak_days"  # 连续阅读
    SPEED_MASTERY = "speed_mastery"  # 阅读速度
    GENRE_EXPLORER = "genre_explorer"  # 类型探索
    COLLECTION = "collection"  # 收藏成就
    SPECIAL = "special"  # 特殊成就


@dataclass
class Achievement:
    """成就定义"""
    id: str
    name: str
    description: str
    icon: str
    type: AchievementType
    requirement: int  # 达成条件数值
    points: int  # 成就点数
    rarity: str  # 稀有度: common, rare, epic, legendary
    hidden: bool = False  # 是否为隐藏成就
    prerequisite: Optional[str] = None  # 前置成就


@dataclass
class UserAchievement:
    """用户获得的成就"""
    achievement_id: str
    unlocked_at: str
    progress: int = 0  # 当前进度
    completed: bool = False


@dataclass
class DailyChallenge:
    """每日挑战"""
    id: str
    title: str
    description: str
    target: int
    current: int = 0
    reward_points: int = 0
    completed: bool = False
    expires_at: str = ""


class AchievementManager:
    """成就管理器"""
    
    # 预定义成就列表
    ACHIEVEMENTS = [
        # 阅读时长成就
        Achievement("time_1", "初窥门径", "累计阅读1小时", "⏱️", AchievementType.READING_TIME, 60, 10, "common"),
        Achievement("time_2", "渐入佳境", "累计阅读5小时", "⏳", AchievementType.READING_TIME, 300, 25, "common"),
        Achievement("time_3", "书虫养成", "累计阅读24小时", "📚", AchievementType.READING_TIME, 1440, 50, "rare"),
        Achievement("time_4", "阅读达人", "累计阅读100小时", "📖", AchievementType.READING_TIME, 6000, 100, "epic"),
        Achievement("time_5", "阅读大师", "累计阅读500小时", "📜", AchievementType.READING_TIME, 30000, 250, "legendary"),
        
        # 完成书籍成就
        Achievement("book_1", "开卷有益", "完成阅读1本书", "📕", AchievementType.BOOKS_COMPLETED, 1, 15, "common"),
        Achievement("book_2", "博览群书", "完成阅读5本书", "📗", AchievementType.BOOKS_COMPLETED, 5, 40, "common"),
        Achievement("book_3", "学富五车", "完成阅读20本书", "📘", AchievementType.BOOKS_COMPLETED, 20, 80, "rare"),
        Achievement("book_4", "藏书万卷", "完成阅读50本书", "📙", AchievementType.BOOKS_COMPLETED, 50, 150, "epic"),
        Achievement("book_5", "书海无涯", "完成阅读100本书", "🏛️", AchievementType.BOOKS_COMPLETED, 100, 300, "legendary"),
        
        # 章节成就
        Achievement("chapter_1", "小试牛刀", "阅读10个章节", "📄", AchievementType.CHAPTERS_READ, 10, 10, "common"),
        Achievement("chapter_2", "循序渐进", "阅读50个章节", "📃", AchievementType.CHAPTERS_READ, 50, 25, "common"),
        Achievement("chapter_3", "章节猎手", "阅读200个章节", "📑", AchievementType.CHAPTERS_READ, 200, 60, "rare"),
        Achievement("chapter_4", "章节大师", "阅读500个章节", "📋", AchievementType.CHAPTERS_READ, 500, 120, "epic"),
        Achievement("chapter_5", "章节之王", "阅读1000个章节", "👑", AchievementType.CHAPTERS_READ, 1000, 250, "legendary"),
        
        # 连续阅读成就
        Achievement("streak_1", "坚持不懈", "连续阅读3天", "🔥", AchievementType.STREAK_DAYS, 3, 20, "common"),
        Achievement("streak_2", "习惯养成", "连续阅读7天", "🔥🔥", AchievementType.STREAK_DAYS, 7, 40, "rare"),
        Achievement("streak_3", "持之以恒", "连续阅读30天", "🔥🔥🔥", AchievementType.STREAK_DAYS, 30, 100, "epic"),
        Achievement("streak_4", "终身习惯", "连续阅读100天", "🌟", AchievementType.STREAK_DAYS, 100, 300, "legendary"),
        
        # 阅读速度成就
        Achievement("speed_1", "一目十行", "达到300字/分钟", "⚡", AchievementType.SPEED_MASTERY, 300, 30, "rare"),
        Achievement("speed_2", "速读高手", "达到500字/分钟", "🚀", AchievementType.SPEED_MASTERY, 500, 60, "epic"),
        Achievement("speed_3", "闪电阅读", "达到800字/分钟", "💫", AchievementType.SPEED_MASTERY, 800, 150, "legendary"),
        
        # 类型探索成就
        Achievement("genre_1", "类型探索者", "阅读3种不同类型", "🎭", AchievementType.GENRE_EXPLORER, 3, 25, "rare"),
        Achievement("genre_2", "类型大师", "阅读5种不同类型", "🎨", AchievementType.GENRE_EXPLORER, 5, 50, "epic"),
        Achievement("genre_3", "全类型通吃", "阅读10种不同类型", "🌈", AchievementType.GENRE_EXPLORER, 10, 100, "legendary"),
        
        # 特殊成就
        Achievement("night_owl", "夜猫子", "在凌晨12点后阅读", "🦉", AchievementType.SPECIAL, 1, 15, "rare", True),
        Achievement("early_bird", "早起的鸟儿", "在早上6点前阅读", "🐦", AchievementType.SPECIAL, 1, 15, "rare", True),
        Achievement("marathon", "阅读马拉松", "单次阅读超过2小时", "🏃", AchievementType.SPECIAL, 120, 50, "epic", True),
        Achievement("collector", "收藏家", "收藏50本书", "💎", AchievementType.COLLECTION, 50, 40, "rare"),
        Achievement("completionist", "完美主义者", "完成一本书并达到100%", "✨", AchievementType.SPECIAL, 1, 30, "epic", True),
    ]
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db_path = f"{data_dir}/achievements.db"
        self._init_database()
        
        # 成就索引
        self.achievement_map: Dict[str, Achievement] = {
            a.id: a for a in self.ACHIEVEMENTS
        }
        
        # 用户数据
        self.user_achievements: Dict[str, UserAchievement] = {}
        self.total_points: int = 0
        self.current_level: int = 1
        self.current_title: str = "阅读新手"
        
        self._load_user_data()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 用户成就表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_achievements (
                    achievement_id TEXT PRIMARY KEY,
                    unlocked_at TEXT,
                    progress INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0
                )
            ''')
            
            # 用户统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    id INTEGER PRIMARY KEY,
                    total_points INTEGER DEFAULT 0,
                    current_level INTEGER DEFAULT 1,
                    current_title TEXT DEFAULT '阅读新手'
                )
            ''')
            
            # 每日挑战表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_challenges (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    target INTEGER,
                    current INTEGER DEFAULT 0,
                    reward_points INTEGER,
                    completed INTEGER DEFAULT 0,
                    expires_at TEXT
                )
            ''')
            
            conn.commit()
    
    def _load_user_data(self):
        """加载用户数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 加载成就
            cursor.execute('SELECT * FROM user_achievements')
            for row in cursor.fetchall():
                self.user_achievements[row[0]] = UserAchievement(
                    achievement_id=row[0],
                    unlocked_at=row[1],
                    progress=row[2],
                    completed=bool(row[3])
                )
            
            # 加载统计
            cursor.execute('SELECT * FROM user_stats WHERE id = 1')
            row = cursor.fetchone()
            if row:
                self.total_points = row[1]
                self.current_level = row[2]
                self.current_title = row[3]
    
    def _save_user_data(self):
        """保存用户数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 保存统计
            cursor.execute('''
                INSERT OR REPLACE INTO user_stats (id, total_points, current_level, current_title)
                VALUES (1, ?, ?, ?)
            ''', (self.total_points, self.current_level, self.current_title))
            
            conn.commit()
    
    def check_achievement(self, achievement_id: str, current_value: int) -> Optional[Dict]:
        """检查并更新成就进度"""
        achievement = self.achievement_map.get(achievement_id)
        if not achievement:
            return None
        
        # 检查前置条件
        if achievement.prerequisite:
            prereq = self.user_achievements.get(achievement.prerequisite)
            if not prereq or not prereq.completed:
                return None
        
        # 检查是否已完成
        user_achievement = self.user_achievements.get(achievement_id)
        if user_achievement and user_achievement.completed:
            return None
        
        # 更新进度
        if not user_achievement:
            user_achievement = UserAchievement(
                achievement_id=achievement_id,
                unlocked_at="",
                progress=current_value,
                completed=False
            )
            self.user_achievements[achievement_id] = user_achievement
        else:
            user_achievement.progress = max(user_achievement.progress, current_value)
        
        # 检查是否达成
        if current_value >= achievement.requirement and not user_achievement.completed:
            return self._unlock_achievement(achievement_id)
        
        # 保存进度
        self._save_achievement_progress(achievement_id)
        return None
    
    def _unlock_achievement(self, achievement_id: str) -> Dict:
        """解锁成就"""
        achievement = self.achievement_map[achievement_id]
        user_achievement = self.user_achievements[achievement_id]
        
        user_achievement.completed = True
        user_achievement.unlocked_at = datetime.now().isoformat()
        user_achievement.progress = achievement.requirement
        
        # 增加点数
        self.total_points += achievement.points
        
        # 检查升级
        self._check_level_up()
        
        # 保存
        self._save_achievement_progress(achievement_id)
        self._save_user_data()
        
        return {
            'id': achievement_id,
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon,
            'points': achievement.points,
            'rarity': achievement.rarity,
            'message': f"🎉 解锁成就: {achievement.name}! +{achievement.points}点"
        }
    
    def _save_achievement_progress(self, achievement_id: str):
        """保存成就进度"""
        user_achievement = self.user_achievements[achievement_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_achievements 
                (achievement_id, unlocked_at, progress, completed)
                VALUES (?, ?, ?, ?)
            ''', (
                achievement_id,
                user_achievement.unlocked_at,
                user_achievement.progress,
                int(user_achievement.completed)
            ))
            conn.commit()
    
    def _check_level_up(self):
        """检查是否升级"""
        # 等级阈值
        level_thresholds = [
            (0, "阅读新手"),
            (100, "阅读学徒"),
            (300, "阅读爱好者"),
            (600, "阅读达人"),
            (1000, "阅读专家"),
            (1500, "阅读大师"),
            (2500, "阅读宗师"),
            (4000, "阅读传奇"),
            (6000, "阅读神话"),
            (10000, "阅读之神")
        ]
        
        new_level = 1
        new_title = "阅读新手"
        
        for threshold, title in level_thresholds:
            if self.total_points >= threshold:
                new_level = level_thresholds.index((threshold, title)) + 1
                new_title = title
            else:
                break
        
        if new_level > self.current_level:
            self.current_level = new_level
            self.current_title = new_title
    
    def get_user_stats(self) -> Dict[str, Any]:
        """获取用户统计"""
        completed_count = sum(1 for ua in self.user_achievements.values() if ua.completed)
        total_count = len(self.ACHIEVEMENTS)
        
        # 计算下一个等级所需点数
        level_thresholds = [0, 100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000]
        next_level_points = 0
        for threshold in level_thresholds:
            if self.total_points < threshold:
                next_level_points = threshold
                break
        
        progress_to_next = 0
        if next_level_points > 0:
            prev_threshold = level_thresholds[self.current_level - 1] if self.current_level > 1 else 0
            progress_to_next = (self.total_points - prev_threshold) / (next_level_points - prev_threshold) * 100
        
        return {
            'total_points': self.total_points,
            'current_level': self.current_level,
            'current_title': self.current_title,
            'completed_achievements': completed_count,
            'total_achievements': total_count,
            'completion_percentage': round(completed_count / total_count * 100, 1),
            'next_level_points': next_level_points,
            'progress_to_next_level': round(progress_to_next, 1)
        }
    
    def get_achievements_by_type(self, achievement_type: AchievementType) -> List[Dict]:
        """按类型获取成就"""
        achievements = []
        
        for achievement in self.ACHIEVEMENTS:
            if achievement.type == achievement_type:
                user_achievement = self.user_achievements.get(achievement.id)
                achievements.append({
                    'id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'icon': achievement.icon,
                    'points': achievement.points,
                    'rarity': achievement.rarity,
                    'requirement': achievement.requirement,
                    'progress': user_achievement.progress if user_achievement else 0,
                    'completed': user_achievement.completed if user_achievement else False,
                    'hidden': achievement.hidden and not (user_achievement and user_achievement.completed)
                })
        
        return achievements
    
    def get_all_achievements(self) -> List[Dict]:
        """获取所有成就"""
        all_achievements = []
        
        for achievement in self.ACHIEVEMENTS:
            user_achievement = self.user_achievements.get(achievement.id)
            
            # 隐藏未解锁的隐藏成就
            if achievement.hidden and not (user_achievement and user_achievement.completed):
                all_achievements.append({
                    'id': achievement.id,
                    'name': "???",
                    'description': "这是一个隐藏成就",
                    'icon': "🔒",
                    'points': achievement.points,
                    'rarity': achievement.rarity,
                    'hidden': True,
                    'completed': False
                })
            else:
                all_achievements.append({
                    'id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'icon': achievement.icon,
                    'points': achievement.points,
                    'rarity': achievement.rarity,
                    'requirement': achievement.requirement,
                    'progress': user_achievement.progress if user_achievement else 0,
                    'completed': user_achievement.completed if user_achievement else False,
                    'hidden': False
                })
        
        return all_achievements
    
    def generate_daily_challenges(self) -> List[DailyChallenge]:
        """生成每日挑战"""
        # 挑战池
        challenge_pool = [
            {"title": "每日阅读", "description": "今天阅读30分钟", "target": 30, "points": 20},
            {"title": "章节挑战", "description": "今天阅读5个章节", "target": 5, "points": 15},
            {"title": "专注阅读", "description": "进行一次45分钟以上的阅读", "target": 45, "points": 25},
            {"title": "探索新书", "description": "开始阅读一本新书", "target": 1, "points": 10},
            {"title": "速度挑战", "description": "达到400字/分钟的阅读速度", "target": 400, "points": 30},
        ]
        
        # 随机选择3个挑战
        selected = random.sample(challenge_pool, min(3, len(challenge_pool)))
        
        challenges = []
        expires_at = (datetime.now() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        
        for i, ch in enumerate(selected):
            challenge = DailyChallenge(
                id=f"daily_{datetime.now().strftime('%Y%m%d')}_{i}",
                title=ch["title"],
                description=ch["description"],
                target=ch["target"],
                reward_points=ch["points"],
                expires_at=expires_at
            )
            challenges.append(challenge)
        
        # 保存到数据库
        self._save_daily_challenges(challenges)
        
        return challenges
    
    def _save_daily_challenges(self, challenges: List[DailyChallenge]):
        """保存每日挑战"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 清除旧挑战
            cursor.execute('DELETE FROM daily_challenges')
            
            # 插入新挑战
            for ch in challenges:
                cursor.execute('''
                    INSERT INTO daily_challenges 
                    (id, title, description, target, current, reward_points, completed, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ch.id, ch.title, ch.description, ch.target, ch.current,
                    ch.reward_points, int(ch.completed), ch.expires_at
                ))
            
            conn.commit()
    
    def get_daily_challenges(self) -> List[Dict]:
        """获取今日挑战"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM daily_challenges')
            rows = cursor.fetchall()
            
            if not rows:
                # 生成新挑战
                challenges = self.generate_daily_challenges()
                return [
                    {
                        'id': ch.id,
                        'title': ch.title,
                        'description': ch.description,
                        'target': ch.target,
                        'current': ch.current,
                        'reward_points': ch.reward_points,
                        'completed': ch.completed,
                        'progress_percentage': 0
                    }
                    for ch in challenges
                ]
            
            # 检查是否过期
            expires_at = datetime.fromisoformat(rows[0][7])
            if datetime.now() > expires_at:
                # 生成新挑战
                challenges = self.generate_daily_challenges()
                return [
                    {
                        'id': ch.id,
                        'title': ch.title,
                        'description': ch.description,
                        'target': ch.target,
                        'current': ch.current,
                        'reward_points': ch.reward_points,
                        'completed': ch.completed,
                        'progress_percentage': 0
                    }
                    for ch in challenges
                ]
            
            return [
                {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'target': row[3],
                    'current': row[4],
                    'reward_points': row[5],
                    'completed': bool(row[6]),
                    'progress_percentage': round(row[4] / row[3] * 100, 1) if row[3] > 0 else 0
                }
                for row in rows
            ]
    
    def update_challenge_progress(self, challenge_id: str, current: int):
        """更新挑战进度"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT target, reward_points FROM daily_challenges WHERE id = ?',
                (challenge_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            target, reward_points = row
            completed = current >= target
            
            cursor.execute('''
                UPDATE daily_challenges 
                SET current = ?, completed = ?
                WHERE id = ?
            ''', (current, int(completed), challenge_id))
            
            conn.commit()
            
            if completed:
                self.total_points += reward_points
                self._save_user_data()
                return {
                    'completed': True,
                    'message': f"🎉 完成挑战! +{reward_points}点",
                    'points_earned': reward_points
                }
            
            return {'completed': False}
    
    def get_leaderboard_position(self) -> Dict[str, Any]:
        """获取排行榜位置（模拟）"""
        # 模拟排行榜数据
        mock_users = [
            {"name": "阅读达人", "points": 5000},
            {"name": "书虫小王", "points": 3500},
            {"name": "夜读君", "points": 2800},
            {"name": "你", "points": self.total_points},
            {"name": "新手小白", "points": 500},
        ]
        
        # 排序
        mock_users.sort(key=lambda x: x["points"], reverse=True)
        
        # 找到用户位置
        position = next(
            (i + 1 for i, u in enumerate(mock_users) if u["name"] == "你"),
            len(mock_users)
        )
        
        return {
            'position': position,
            'total_users': len(mock_users),
            'top_users': mock_users[:3],
            'points': self.total_points
        }
