"""
AI智能推荐系统 - 基于阅读行为的个性化推荐
使用协同过滤和内容推荐算法
"""
import json
import sqlite3
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import random


@dataclass
class ReadingBehavior:
    """阅读行为数据"""
    book_id: str
    book_name: str
    author: str
    category: str
    read_duration: int = 0  # 阅读时长(分钟)
    read_chapters: int = 0
    completion_rate: float = 0.0  # 完成率
    last_read_time: str = ""
    reading_speed: float = 0.0  # 阅读速度(字/分钟)
    favorite_tags: List[str] = field(default_factory=list)


@dataclass
class BookFeature:
    """书籍特征向量"""
    book_id: str
    name: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    intro_vector: List[float] = field(default_factory=list)  # 简介语义向量
    popularity_score: float = 0.0  # 热度分数
    quality_score: float = 0.0  # 质量分数


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str = "default_user"
    preferred_categories: Dict[str, float] = field(default_factory=dict)  # 类别偏好权重
    preferred_authors: Dict[str, float] = field(default_factory=dict)  # 作者偏好
    preferred_tags: Dict[str, float] = field(default_factory=dict)  # 标签偏好
    reading_habits: Dict[str, Any] = field(default_factory=dict)  # 阅读习惯
    active_time_slots: List[int] = field(default_factory=list)  # 活跃时段
    avg_reading_speed: float = 300.0  # 平均阅读速度
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AIRecommendationEngine:
    """AI推荐引擎"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db_path = f"{data_dir}/recommendation.db"
        self._init_database()
        self.user_profile = self._load_user_profile()
        self.reading_history: List[ReadingBehavior] = []
        self.book_features: Dict[str, BookFeature] = {}
        
    def _init_database(self):
        """初始化推荐数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 用户画像表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT,
                    updated_at TEXT
                )
            ''')
            
            # 阅读行为表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reading_behaviors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT,
                    book_name TEXT,
                    author TEXT,
                    category TEXT,
                    read_duration INTEGER,
                    read_chapters INTEGER,
                    completion_rate REAL,
                    last_read_time TEXT,
                    reading_speed REAL,
                    favorite_tags TEXT
                )
            ''')
            
            # 推荐记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT,
                    book_name TEXT,
                    author TEXT,
                    reason TEXT,
                    confidence_score REAL,
                    recommended_at TEXT,
                    clicked INTEGER DEFAULT 0,
                    accepted INTEGER DEFAULT 0
                )
            ''')
            
            # 相似度矩阵表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS similarity_matrix (
                    book_id_1 TEXT,
                    book_id_2 TEXT,
                    similarity_score REAL,
                    PRIMARY KEY (book_id_1, book_id_2)
                )
            ''')
            
            conn.commit()
    
    def _load_user_profile(self) -> UserProfile:
        """加载用户画像"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT profile_data FROM user_profiles WHERE user_id = ?',
                ('default_user',)
            )
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row[0])
                return UserProfile(**data)
            
            return UserProfile()
    
    def save_user_profile(self):
        """保存用户画像"""
        profile_data = {
            'user_id': self.user_profile.user_id,
            'preferred_categories': self.user_profile.preferred_categories,
            'preferred_authors': self.user_profile.preferred_authors,
            'preferred_tags': self.user_profile.preferred_tags,
            'reading_habits': self.user_profile.reading_habits,
            'active_time_slots': self.user_profile.active_time_slots,
            'avg_reading_speed': self.user_profile.avg_reading_speed,
            'created_at': self.user_profile.created_at
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles (user_id, profile_data, updated_at)
                VALUES (?, ?, ?)
            ''', (
                self.user_profile.user_id,
                json.dumps(profile_data, ensure_ascii=False),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def record_reading_behavior(self, behavior: ReadingBehavior):
        """记录阅读行为"""
        self.reading_history.append(behavior)
        
        # 更新用户画像
        self._update_user_profile(behavior)
        
        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reading_behaviors 
                (book_id, book_name, author, category, read_duration, read_chapters,
                 completion_rate, last_read_time, reading_speed, favorite_tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                behavior.book_id, behavior.book_name, behavior.author,
                behavior.category, behavior.read_duration, behavior.read_chapters,
                behavior.completion_rate, behavior.last_read_time,
                behavior.reading_speed, json.dumps(behavior.favorite_tags, ensure_ascii=False)
            ))
            conn.commit()
    
    def _update_user_profile(self, behavior: ReadingBehavior):
        """根据阅读行为更新用户画像"""
        # 更新类别偏好
        if behavior.category:
            current_weight = self.user_profile.preferred_categories.get(behavior.category, 0)
            # 根据阅读时长和完成率计算权重
            weight_delta = (behavior.read_duration / 60) * behavior.completion_rate * 0.1
            self.user_profile.preferred_categories[behavior.category] = min(
                current_weight + weight_delta, 10.0
            )
        
        # 更新作者偏好
        if behavior.author:
            current_weight = self.user_profile.preferred_authors.get(behavior.author, 0)
            weight_delta = behavior.completion_rate * 0.5
            self.user_profile.preferred_authors[behavior.author] = min(
                current_weight + weight_delta, 10.0
            )
        
        # 更新标签偏好
        for tag in behavior.favorite_tags:
            current_weight = self.user_profile.preferred_tags.get(tag, 0)
            self.user_profile.preferred_tags[tag] = min(current_weight + 0.3, 10.0)
        
        # 更新平均阅读速度
        if behavior.reading_speed > 0:
            total_speed = self.user_profile.avg_reading_speed * len(self.reading_history)
            total_speed += behavior.reading_speed
            self.user_profile.avg_reading_speed = total_speed / (len(self.reading_history) + 1)
        
        self.save_user_profile()
    
    def calculate_book_similarity(self, book1: BookFeature, book2: BookFeature) -> float:
        """计算两本书的相似度"""
        similarity = 0.0
        
        # 类别相同加分
        if book1.category == book2.category:
            similarity += 0.3
        
        # 标签重叠度
        if book1.tags and book2.tags:
            common_tags = set(book1.tags) & set(book2.tags)
            all_tags = set(book1.tags) | set(book2.tags)
            if all_tags:
                similarity += 0.4 * (len(common_tags) / len(all_tags))
        
        # 作者相同加分
        if book1.author == book2.author:
            similarity += 0.2
        
        # 简介语义相似度（简化版，使用余弦相似度）
        if book1.intro_vector and book2.intro_vector:
            similarity += 0.1 * self._cosine_similarity(
                book1.intro_vector, book2.intro_vector
            )
        
        return min(similarity, 1.0)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_personalized_recommendations(
        self, 
        available_books: List[Dict],
        num_recommendations: int = 10
    ) -> List[Dict]:
        """获取个性化推荐"""
        if not available_books:
            return []
        
        # 构建书籍特征
        for book_data in available_books:
            book_id = book_data.get('id', '')
            if book_id not in self.book_features:
                self.book_features[book_id] = BookFeature(
                    book_id=book_id,
                    name=book_data.get('name', ''),
                    author=book_data.get('author', ''),
                    category=book_data.get('category', ''),
                    tags=book_data.get('tags', []),
                    popularity_score=book_data.get('popularity', 0),
                    quality_score=book_data.get('rating', 0)
                )
        
        # 计算推荐分数
        scored_books = []
        for book_data in available_books:
            book_id = book_data.get('id', '')
            book_feature = self.book_features.get(book_id)
            
            if not book_feature:
                continue
            
            score = self._calculate_recommendation_score(book_feature)
            scored_books.append((book_data, score))
        
        # 按分数排序
        scored_books.sort(key=lambda x: x[1], reverse=True)
        
        # 添加推荐理由
        recommendations = []
        for book_data, score in scored_books[:num_recommendations]:
            reason = self._generate_recommendation_reason(book_data)
            book_data['recommend_score'] = round(score, 2)
            book_data['recommend_reason'] = reason
            recommendations.append(book_data)
        
        return recommendations
    
    def _calculate_recommendation_score(self, book: BookFeature) -> float:
        """计算单本书的推荐分数"""
        score = 0.0
        
        # 基于用户画像的类别偏好
        category_weight = self.user_profile.preferred_categories.get(book.category, 0)
        score += category_weight * 2
        
        # 作者偏好
        author_weight = self.user_profile.preferred_authors.get(book.author, 0)
        score += author_weight * 1.5
        
        # 标签偏好
        tag_score = 0
        for tag in book.tags:
            tag_score += self.user_profile.preferred_tags.get(tag, 0)
        score += tag_score * 0.5
        
        # 热度加成
        score += book.popularity_score * 0.3
        
        # 质量加成
        score += book.quality_score * 0.5
        
        # 协同过滤：基于相似书籍
        for history in self.reading_history[-10:]:  # 最近10本
            if history.completion_rate > 0.7:  # 只考虑高完成率的书籍
                # 这里简化处理，实际应该查询相似度矩阵
                if book.author == history.author:
                    score += 1.0
                if book.category == history.category:
                    score += 0.5
        
        # 添加随机因子增加多样性
        score += random.uniform(0, 0.5)
        
        return score
    
    def _generate_recommendation_reason(self, book_data: Dict) -> str:
        """生成推荐理由"""
        reasons = []
        
        category = book_data.get('category', '')
        author = book_data.get('author', '')
        
        # 基于类别偏好
        if category in self.user_profile.preferred_categories:
            if self.user_profile.preferred_categories[category] > 5:
                reasons.append(f"你喜欢{category}类书籍")
        
        # 基于作者偏好
        if author in self.user_profile.preferred_authors:
            if self.user_profile.preferred_authors[author] > 3:
                reasons.append(f"你关注作者{author}")
        
        # 基于热度
        if book_data.get('popularity', 0) > 8:
            reasons.append("当前热门书籍")
        
        # 基于评分
        if book_data.get('rating', 0) > 4.5:
            reasons.append("高分好评")
        
        if reasons:
            return " · ".join(reasons[:2])
        return "为你推荐"
    
    def get_trending_books(self, available_books: List[Dict], num: int = 5) -> List[Dict]:
        """获取热门趋势书籍"""
        # 按热度排序
        sorted_books = sorted(
            available_books,
            key=lambda x: x.get('popularity', 0) * x.get('rating', 0),
            reverse=True
        )
        return sorted_books[:num]
    
    def get_similar_books(
        self, 
        book_id: str, 
        available_books: List[Dict], 
        num: int = 5
    ) -> List[Dict]:
        """获取相似书籍"""
        target_book = self.book_features.get(book_id)
        if not target_book:
            return []
        
        similarities = []
        for book_data in available_books:
            other_id = book_data.get('id', '')
            if other_id == book_id:
                continue
            
            other_book = self.book_features.get(other_id)
            if other_book:
                similarity = self.calculate_book_similarity(target_book, other_book)
                similarities.append((book_data, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [book for book, _ in similarities[:num]]
    
    def get_reading_insights(self) -> Dict[str, Any]:
        """获取阅读洞察"""
        if not self.reading_history:
            return {
                'total_books': 0,
                'total_reading_time': 0,
                'favorite_category': '暂无数据',
                'favorite_author': '暂无数据',
                'avg_completion_rate': 0,
                'reading_streak': 0
            }
        
        # 计算统计数据
        total_books = len(self.reading_history)
        total_time = sum(b.read_duration for b in self.reading_history)
        avg_completion = sum(b.completion_rate for b in self.reading_history) / total_books
        
        # 最喜欢的类别
        favorite_category = max(
            self.user_profile.preferred_categories.items(),
            key=lambda x: x[1],
            default=('暂无数据', 0)
        )[0]
        
        # 最喜欢的作者
        favorite_author = max(
            self.user_profile.preferred_authors.items(),
            key=lambda x: x[1],
            default=('暂无数据', 0)
        )[0]
        
        # 计算连续阅读天数（简化版）
        reading_dates = set()
        for behavior in self.reading_history:
            if behavior.last_read_time:
                date = behavior.last_read_time[:10]
                reading_dates.add(date)
        
        reading_streak = len(reading_dates)
        
        return {
            'total_books': total_books,
            'total_reading_time': total_time,
            'favorite_category': favorite_category,
            'favorite_author': favorite_author,
            'avg_completion_rate': round(avg_completion * 100, 1),
            'reading_streak': reading_streak,
            'avg_reading_speed': round(self.user_profile.avg_reading_speed, 0)
        }
