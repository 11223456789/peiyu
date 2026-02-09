"""
高级AI系统 - 深度学习推荐、自然语言处理、情感分析
"""
import json
import sqlite3
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import re
import math
import random


@dataclass
class SemanticVector:
    """语义向量"""
    vector: List[float]
    text_hash: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def cosine_similarity(self, other: 'SemanticVector') -> float:
        """计算余弦相似度"""
        v1 = np.array(self.vector)
        v2 = np.array(other.vector)
        
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(v1, v2) / (norm1 * norm2))


@dataclass
class SentimentScore:
    """情感分析分数"""
    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 1.0
    compound: float = 0.0
    
    def get_dominant(self) -> str:
        """获取主导情感"""
        scores = {
            'positive': self.positive,
            'negative': self.negative,
            'neutral': self.neutral
        }
        return max(scores, key=scores.get)


@dataclass
class ReadingPattern:
    """阅读模式分析"""
    time_distribution: Dict[int, float] = field(default_factory=dict)  # 24小时分布
    day_distribution: Dict[str, float] = field(default_factory=dict)  # 星期分布
    session_length_avg: float = 0.0  # 平均阅读时长
    session_length_std: float = 0.0  # 标准差
    preferred_categories: List[str] = field(default_factory=list)
    reading_speed_trend: List[float] = field(default_factory=list)
    completion_rate_by_category: Dict[str, float] = field(default_factory=dict)


class TextPreprocessor:
    """文本预处理器"""
    
    # 停用词
    STOP_WORDS = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也',
        '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那'
    }
    
    # 情感词典
    POSITIVE_WORDS = {
        '精彩', '优秀', '喜欢', '推荐', '好看', '棒', '赞', '完美', '优秀', '出色',
        '感动', '震撼', '惊喜', '满意', '享受', '愉快', '开心', '兴奋', '激动', '热爱'
    }
    
    NEGATIVE_WORDS = {
        '无聊', '差', '烂', '失望', '难看', '糟糕', '垃圾', '坑', '后悔', '浪费时间',
        '拖沓', '平淡', '乏味', '枯燥', '冗长', '混乱', '不合理', 'bug', '错误'
    }
    
    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """简单分词"""
        # 使用正则表达式分词
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]+', text.lower())
        return [w for w in words if w not in cls.STOP_WORDS and len(w) > 1]
    
    @classmethod
    def extract_keywords(cls, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """提取关键词（基于词频）"""
        words = cls.tokenize(text)
        word_freq = defaultdict(int)
        
        for word in words:
            word_freq[word] += 1
        
        # 计算TF-IDF（简化版）
        total_words = len(words)
        keywords = []
        
        for word, freq in word_freq.items():
            tf = freq / total_words
            # 这里简化处理，实际应该使用IDF
            score = tf * (1 + math.log(freq + 1))
            keywords.append((word, score))
        
        keywords.sort(key=lambda x: x[1], reverse=True)
        return keywords[:top_k]
    
    @classmethod
    def analyze_sentiment(cls, text: str) -> SentimentScore:
        """情感分析"""
        words = cls.tokenize(text)
        
        positive_count = sum(1 for w in words if w in cls.POSITIVE_WORDS)
        negative_count = sum(1 for w in words if w in cls.NEGATIVE_WORDS)
        total_count = len(words)
        
        if total_count == 0:
            return SentimentScore()
        
        positive = positive_count / total_count
        negative = negative_count / total_count
        neutral = 1 - positive - negative
        
        # 复合分数
        compound = (positive - negative) / (positive + negative + 1e-8)
        
        return SentimentScore(
            positive=positive,
            negative=negative,
            neutral=max(0, neutral),
            compound=compound
        )
    
    @classmethod
    def create_semantic_vector(cls, text: str, dim: int = 128) -> SemanticVector:
        """创建语义向量（简化版词袋模型）"""
        words = cls.tokenize(text)
        word_freq = defaultdict(int)
        
        for word in words:
            word_freq[word] += 1
        
        # 使用哈希技巧创建固定维度向量
        vector = [0.0] * dim
        for word, freq in word_freq.items():
            hash_val = hash(word) % dim
            vector[hash_val] += freq
        
        # 归一化
        norm = math.sqrt(sum(v**2 for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        
        text_hash = str(hash(text))
        return SemanticVector(vector=vector, text_hash=text_hash)


class DeepRecommendationEngine:
    """深度推荐引擎"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db_path = f"{data_dir}/advanced_ai.db"
        self._init_database()
        
        # 语义向量缓存
        self._vector_cache: Dict[str, SemanticVector] = {}
        
        # 相似度矩阵缓存
        self._similarity_cache: Dict[str, float] = {}
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 语义向量表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS semantic_vectors (
                    book_id TEXT PRIMARY KEY,
                    vector_data TEXT,
                    text_hash TEXT,
                    created_at TEXT
                )
            ''')
            
            # 情感分析表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sentiment_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id TEXT,
                    content_type TEXT,
                    positive REAL,
                    negative REAL,
                    neutral REAL,
                    compound REAL,
                    analyzed_at TEXT
                )
            ''')
            
            # 阅读模式表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reading_patterns (
                    user_id TEXT PRIMARY KEY,
                    pattern_data TEXT,
                    updated_at TEXT
                )
            ''')
            
            # 用户-书籍交互表（用于协同过滤）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_book_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    book_id TEXT,
                    interaction_type TEXT,
                    weight REAL,
                    created_at TEXT,
                    UNIQUE(user_id, book_id, interaction_type)
                )
            ''')
            
            conn.commit()
    
    def index_book(self, book_id: str, name: str, intro: str, 
                   category: str = "", tags: List[str] = None):
        """索引书籍 - 创建语义向量"""
        # 合并文本
        text = f"{name}。{intro}。{' '.join(tags or [])}"
        
        # 创建语义向量
        vector = TextPreprocessor.create_semantic_vector(text)
        
        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO semantic_vectors 
                (book_id, vector_data, text_hash, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                book_id,
                json.dumps(vector.vector),
                vector.text_hash,
                vector.created_at
            ))
            conn.commit()
        
        # 更新缓存
        self._vector_cache[book_id] = vector
    
    def get_book_vector(self, book_id: str) -> Optional[SemanticVector]:
        """获取书籍语义向量"""
        # 检查缓存
        if book_id in self._vector_cache:
            return self._vector_cache[book_id]
        
        # 从数据库加载
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT vector_data, text_hash, created_at FROM semantic_vectors WHERE book_id = ?',
                (book_id,)
            )
            row = cursor.fetchone()
            
            if row:
                vector = SemanticVector(
                    vector=json.loads(row[0]),
                    text_hash=row[1],
                    created_at=row[2]
                )
                self._vector_cache[book_id] = vector
                return vector
        
        return None
    
    def content_based_recommend(self, book_id: str, top_k: int = 10) -> List[Dict]:
        """基于内容的推荐"""
        target_vector = self.get_book_vector(book_id)
        if not target_vector:
            return []
        
        # 计算与所有书籍的相似度
        similarities = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT book_id, vector_data FROM semantic_vectors')
            
            for row in cursor.fetchall():
                other_id = row[0]
                if other_id == book_id:
                    continue
                
                other_vector = SemanticVector(
                    vector=json.loads(row[1]),
                    text_hash=""
                )
                
                similarity = target_vector.cosine_similarity(other_vector)
                similarities.append((other_id, similarity))
        
        # 排序并返回Top-K
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for book_id, score in similarities[:top_k]:
            results.append({
                'book_id': book_id,
                'similarity': score,
                'reason': '内容相似'
            })
        
        return results
    
    def collaborative_filtering(self, user_id: str, top_k: int = 10) -> List[Dict]:
        """协同过滤推荐"""
        # 获取用户交互记录
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取当前用户的偏好
            cursor.execute('''
                SELECT book_id, interaction_type, weight
                FROM user_book_interactions
                WHERE user_id = ?
            ''', (user_id,))
            user_interactions = cursor.fetchall()
            
            if not user_interactions:
                return []
            
            # 找到相似用户
            user_book_weights = {row[0]: row[2] for row in user_interactions}
            
            # 获取其他用户的交互
            cursor.execute('''
                SELECT user_id, book_id, weight
                FROM user_book_interactions
                WHERE user_id != ?
            ''', (user_id,))
            other_interactions = cursor.fetchall()
            
            # 计算用户相似度
            user_similarities = defaultdict(float)
            user_books = defaultdict(dict)
            
            for other_id, book_id, weight in other_interactions:
                user_books[other_id][book_id] = weight
            
            for other_id, books in user_books.items():
                # 计算余弦相似度
                common_books = set(user_book_weights.keys()) & set(books.keys())
                if not common_books:
                    continue
                
                dot_product = sum(user_book_weights[b] * books[b] for b in common_books)
                norm1 = math.sqrt(sum(w**2 for w in user_book_weights.values()))
                norm2 = math.sqrt(sum(w**2 for w in books.values()))
                
                if norm1 > 0 and norm2 > 0:
                    similarity = dot_product / (norm1 * norm2)
                    user_similarities[other_id] = similarity
            
            # 基于相似用户推荐
            book_scores = defaultdict(float)
            
            for other_id, similarity in sorted(user_similarities.items(), 
                                               key=lambda x: x[1], reverse=True)[:20]:
                for book_id, weight in user_books[other_id].items():
                    if book_id not in user_book_weights:
                        book_scores[book_id] += similarity * weight
            
            # 排序并返回
            sorted_books = sorted(book_scores.items(), key=lambda x: x[1], reverse=True)
            
            results = []
            for book_id, score in sorted_books[:top_k]:
                results.append({
                    'book_id': book_id,
                    'score': score,
                    'reason': '相似用户喜欢'
                })
            
            return results
    
    def record_interaction(self, user_id: str, book_id: str, 
                          interaction_type: str, weight: float = 1.0):
        """记录用户-书籍交互"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_book_interactions
                (user_id, book_id, interaction_type, weight, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, book_id, interaction_type, weight, datetime.now().isoformat()))
            conn.commit()
    
    def analyze_reading_pattern(self, user_id: str) -> ReadingPattern:
        """分析用户阅读模式"""
        # 从主数据库获取阅读历史
        main_db = f"{self.data_dir}/bookshelf.db"
        
        with sqlite3.connect(main_db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT read_time, position 
                FROM reading_history
                WHERE book_id IN (
                    SELECT id FROM books WHERE last_read_time != ""
                )
                ORDER BY read_time
            ''')
            history = cursor.fetchall()
        
        if not history:
            return ReadingPattern()
        
        # 分析时间分布
        time_dist = defaultdict(int)
        day_dist = defaultdict(int)
        session_lengths = []
        
        prev_time = None
        session_start = None
        
        for read_time_str, position in history:
            try:
                read_time = datetime.fromisoformat(read_time_str)
                hour = read_time.hour
                day = read_time.strftime('%A')
                
                time_dist[hour] += 1
                day_dist[day] += 1
                
                # 会话检测（间隔超过30分钟算新会话）
                if prev_time and (read_time - prev_time).total_seconds() > 1800:
                    if session_start:
                        session_lengths.append((prev_time - session_start).total_seconds() / 60)
                    session_start = read_time
                elif session_start is None:
                    session_start = read_time
                
                prev_time = read_time
            except:
                continue
        
        # 计算统计
        total = sum(time_dist.values())
        time_distribution = {h: c/total for h, c in time_dist.items()} if total > 0 else {}
        
        total_days = sum(day_dist.values())
        day_distribution = {d: c/total_days for d, c in day_dist.items()} if total_days > 0 else {}
        
        if session_lengths:
            avg_length = sum(session_lengths) / len(session_lengths)
            std_length = math.sqrt(sum((x - avg_length)**2 for x in session_lengths) / len(session_lengths))
        else:
            avg_length = 0
            std_length = 0
        
        pattern = ReadingPattern(
            time_distribution=time_distribution,
            day_distribution=day_distribution,
            session_length_avg=avg_length,
            session_length_std=std_length
        )
        
        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO reading_patterns
                (user_id, pattern_data, updated_at)
                VALUES (?, ?, ?)
            ''', (
                user_id,
                json.dumps({
                    'time_distribution': time_distribution,
                    'day_distribution': day_distribution,
                    'session_length_avg': avg_length,
                    'session_length_std': std_length
                }),
                datetime.now().isoformat()
            ))
            conn.commit()
        
        return pattern
    
    def hybrid_recommend(self, user_id: str, book_id: str = None, 
                        top_k: int = 10) -> List[Dict]:
        """混合推荐 - 结合多种算法"""
        recommendations = []
        
        # 1. 基于内容的推荐
        if book_id:
            content_recs = self.content_based_recommend(book_id, top_k=top_k//2)
            for rec in content_recs:
                rec['algorithm'] = 'content'
                rec['final_score'] = rec['similarity'] * 0.4
            recommendations.extend(content_recs)
        
        # 2. 协同过滤推荐
        collab_recs = self.collaborative_filtering(user_id, top_k=top_k//2)
        for rec in collab_recs:
            rec['algorithm'] = 'collaborative'
            rec['final_score'] = rec['score'] * 0.4
        recommendations.extend(collab_recs)
        
        # 3. 热门推荐（补充）
        if len(recommendations) < top_k:
            # 这里简化处理，实际应该查询热门书籍
            pass
        
        # 去重并排序
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec['book_id'] not in seen:
                seen.add(rec['book_id'])
                unique_recs.append(rec)
        
        unique_recs.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return unique_recs[:top_k]


class SmartAssistant:
    """智能阅读助手"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.ai_engine = DeepRecommendationEngine(data_dir)
    
    def generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成内容摘要"""
        # 简单摘要：提取前几句
        sentences = re.split(r'[。！？]', content)
        summary = ""
        
        for sentence in sentences[:3]:
            if len(summary) + len(sentence) < max_length:
                summary += sentence + "。"
            else:
                break
        
        return summary
    
    def extract_key_points(self, content: str, num_points: int = 5) -> List[str]:
        """提取关键要点"""
        # 基于关键词提取
        keywords = TextPreprocessor.extract_keywords(content, top_k=num_points * 2)
        
        sentences = re.split(r'[。！？]', content)
        key_points = []
        
        keyword_set = set(k[0] for k in keywords)
        
        for sentence in sentences:
            if len(key_points) >= num_points:
                break
            
            # 检查句子是否包含关键词
            if any(kw in sentence for kw in keyword_set):
                if len(sentence) > 10:  # 过滤太短句子
                    key_points.append(sentence.strip())
        
        return key_points
    
    def predict_reading_time(self, content: str, reading_speed: float = 300) -> Dict:
        """预测阅读时间"""
        # 统计字数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', content))
        english_words = len(re.findall(r'[a-zA-Z]+', content))
        
        total_words = chinese_chars + english_words
        
        # 计算时间（分钟）
        minutes = total_words / reading_speed
        
        return {
            'total_words': total_words,
            'chinese_chars': chinese_chars,
            'english_words': english_words,
            'estimated_minutes': round(minutes, 1),
            'estimated_time_str': f"{int(minutes)}分{int((minutes % 1) * 60)}秒"
        }
    
    def suggest_break_point(self, content: str, current_position: int) -> Optional[int]:
        """建议休息点（章节结束、段落结束等）"""
        # 查找下一个段落结束点
        next_para = content.find('\n\n', current_position)
        if next_para != -1 and next_para - current_position < 500:
            return next_para
        
        # 查找下一个句号
        next_period = content.find('。', current_position)
        if next_period != -1 and next_period - current_position < 200:
            return next_period + 1
        
        return None
    
    def analyze_book_quality(self, intro: str, sample_chapter: str = "") -> Dict:
        """分析书籍质量"""
        sentiment = TextPreprocessor.analyze_sentiment(intro)
        
        # 基于简介长度和情感分析评分
        intro_length = len(intro)
        length_score = min(intro_length / 500, 1.0)  # 简介越长分越高，最高1.0
        
        sentiment_score = (sentiment.positive + 1) / 2  # 归一化到0-1
        
        # 综合评分
        overall_score = (length_score * 0.3 + sentiment_score * 0.7)
        
        return {
            'overall_score': round(overall_score * 10, 1),
            'intro_quality': round(length_score * 10, 1),
            'sentiment_score': round(sentiment_score * 10, 1),
            'sentiment': sentiment.get_dominant(),
            'recommendation': '强烈推荐' if overall_score > 0.8 else '推荐' if overall_score > 0.6 else '一般'
        }


# 全局实例
_advanced_ai_instance: Optional[DeepRecommendationEngine] = None

def get_advanced_ai(data_dir: str) -> DeepRecommendationEngine:
    """获取高级AI引擎实例"""
    global _advanced_ai_instance
    if _advanced_ai_instance is None:
        _advanced_ai_instance = DeepRecommendationEngine(data_dir)
    return _advanced_ai_instance
