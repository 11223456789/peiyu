"""
智能阅读分析系统 - 深度分析阅读行为和习惯
提供可视化数据、阅读报告和智能建议
"""
import json
import sqlite3
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class DailyReadingStats:
    """每日阅读统计"""
    date: str
    total_time: int = 0  # 分钟
    books_read: int = 0
    chapters_read: int = 0
    words_read: int = 0
    peak_hour: int = 0  # 阅读高峰时段
    session_count: int = 0  # 阅读次数


@dataclass
class ReadingSession:
    """单次阅读会话"""
    session_id: str
    book_id: str
    book_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: int = 0  # 分钟
    chapters_read: int = 0
    words_read: int = 0
    reading_speed: float = 0.0  # 字/分钟
    focus_score: float = 0.0  # 专注度分数(0-100)


@dataclass
class BookAnalytics:
    """单本书的分析数据"""
    book_id: str
    book_name: str
    total_reading_time: int = 0
    completion_percentage: float = 0.0
    average_speed: float = 0.0
    reading_pattern: str = ""  # 阅读模式：快速/慢读/间歇
    estimated_finish_time: Optional[datetime] = None
    difficulty_score: float = 0.0  # 难度分数
    engagement_score: float = 0.0  # 参与度分数


class ReadingAnalyticsEngine:
    """阅读分析引擎"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db_path = f"{data_dir}/analytics.db"
        self._init_database()
        
        # 内存缓存
        self.daily_stats: Dict[str, DailyReadingStats] = {}
        self.sessions: List[ReadingSession] = []
        self.book_analytics: Dict[str, BookAnalytics] = {}
        
    def _init_database(self):
        """初始化分析数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 每日统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_time INTEGER,
                    books_read INTEGER,
                    chapters_read INTEGER,
                    words_read INTEGER,
                    peak_hour INTEGER,
                    session_count INTEGER
                )
            ''')
            
            # 阅读会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reading_sessions (
                    session_id TEXT PRIMARY KEY,
                    book_id TEXT,
                    book_name TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration INTEGER,
                    chapters_read INTEGER,
                    words_read INTEGER,
                    reading_speed REAL,
                    focus_score REAL
                )
            ''')
            
            # 书籍分析表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS book_analytics (
                    book_id TEXT PRIMARY KEY,
                    book_name TEXT,
                    total_reading_time INTEGER,
                    completion_percentage REAL,
                    average_speed REAL,
                    reading_pattern TEXT,
                    estimated_finish_time TEXT,
                    difficulty_score REAL,
                    engagement_score REAL,
                    updated_at TEXT
                )
            ''')
            
            # 阅读时段分布表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hour_distribution (
                    hour INTEGER PRIMARY KEY,
                    total_time INTEGER,
                    session_count INTEGER
                )
            ''')
            
            conn.commit()
    
    def start_reading_session(self, book_id: str, book_name: str) -> str:
        """开始新的阅读会话"""
        session_id = f"{book_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        session = ReadingSession(
            session_id=session_id,
            book_id=book_id,
            book_name=book_name,
            start_time=datetime.now()
        )
        
        self.sessions.append(session)
        return session_id
    
    def end_reading_session(
        self, 
        session_id: str, 
        chapters_read: int = 0, 
        words_read: int = 0
    ):
        """结束阅读会话"""
        # 查找会话
        session = None
        for s in self.sessions:
            if s.session_id == session_id:
                session = s
                break
        
        if not session:
            return
        
        # 计算统计数据
        session.end_time = datetime.now()
        session.duration = int((session.end_time - session.start_time).total_seconds() / 60)
        session.chapters_read = chapters_read
        session.words_read = words_read
        
        if session.duration > 0:
            session.reading_speed = words_read / session.duration
        
        # 计算专注度分数
        session.focus_score = self._calculate_focus_score(session)
        
        # 保存到数据库
        self._save_session(session)
        self._update_daily_stats(session)
        self._update_hour_distribution(session)
    
    def _calculate_focus_score(self, session: ReadingSession) -> float:
        """计算专注度分数"""
        score = 50.0  # 基础分
        
        # 根据阅读速度稳定性
        if session.reading_speed > 0:
            # 正常阅读速度范围：200-600字/分钟
            if 200 <= session.reading_speed <= 600:
                score += 20
            elif 100 <= session.reading_speed < 200 or 600 < session.reading_speed <= 800:
                score += 10
        
        # 根据阅读时长
        if session.duration >= 30:  # 连续阅读30分钟以上
            score += 15
        elif session.duration >= 15:
            score += 10
        
        # 根据章节完成度
        if session.chapters_read > 0:
            score += min(session.chapters_read * 5, 15)
        
        return min(score, 100)
    
    def _save_session(self, session: ReadingSession):
        """保存会话到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reading_sessions 
                (session_id, book_id, book_name, start_time, end_time, duration,
                 chapters_read, words_read, reading_speed, focus_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id, session.book_id, session.book_name,
                session.start_time.isoformat(),
                session.end_time.isoformat() if session.end_time else None,
                session.duration, session.chapters_read, session.words_read,
                session.reading_speed, session.focus_score
            ))
            conn.commit()
    
    def _update_daily_stats(self, session: ReadingSession):
        """更新每日统计"""
        date = session.start_time.strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 查询现有数据
            cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (date,))
            row = cursor.fetchone()
            
            if row:
                # 更新
                cursor.execute('''
                    UPDATE daily_stats SET
                        total_time = total_time + ?,
                        chapters_read = chapters_read + ?,
                        words_read = words_read + ?,
                        session_count = session_count + 1
                    WHERE date = ?
                ''', (session.duration, session.chapters_read, session.words_read, date))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO daily_stats 
                    (date, total_time, books_read, chapters_read, words_read, peak_hour, session_count)
                    VALUES (?, ?, 1, ?, ?, 0, 1)
                ''', (date, session.duration, session.chapters_read, session.words_read))
            
            conn.commit()
    
    def _update_hour_distribution(self, session: ReadingSession):
        """更新时段分布"""
        hour = session.start_time.hour
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM hour_distribution WHERE hour = ?', (hour,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute('''
                    UPDATE hour_distribution 
                    SET total_time = total_time + ?, session_count = session_count + 1
                    WHERE hour = ?
                ''', (session.duration, hour))
            else:
                cursor.execute('''
                    INSERT INTO hour_distribution (hour, total_time, session_count)
                    VALUES (?, ?, 1)
                ''', (hour, session.duration))
            
            conn.commit()
    
    def get_weekly_report(self) -> Dict[str, Any]:
        """生成周阅读报告"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取周统计数据
            cursor.execute('''
                SELECT * FROM daily_stats 
                WHERE date >= ? AND date <= ?
                ORDER BY date
            ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            
            daily_data = cursor.fetchall()
            
            # 计算周总计
            total_time = sum(row[1] for row in daily_data)
            total_chapters = sum(row[3] for row in daily_data)
            total_words = sum(row[4] for row in daily_data)
            total_sessions = sum(row[6] for row in daily_data)
            
            # 计算日均
            days_with_data = len(daily_data) if daily_data else 1
            avg_daily_time = total_time / days_with_data
            
            # 获取阅读时段分布
            cursor.execute('''
                SELECT hour, total_time FROM hour_distribution
                ORDER BY hour
            ''')
            hour_data = cursor.fetchall()
            
            # 找出高峰时段
            peak_hours = sorted(hour_data, key=lambda x: x[1], reverse=True)[:3] if hour_data else []
            
            # 获取本周阅读的书籍
            cursor.execute('''
                SELECT DISTINCT book_id, book_name FROM reading_sessions
                WHERE start_time >= ? AND start_time <= ?
            ''', (start_date.isoformat(), end_date.isoformat()))
            
            books_this_week = cursor.fetchall()
            
            return {
                'period': f"{start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}",
                'total_reading_time': total_time,
                'total_chapters': total_chapters,
                'total_words': total_words,
                'total_sessions': total_sessions,
                'avg_daily_time': round(avg_daily_time, 1),
                'active_days': len(daily_data),
                'books_count': len(books_this_week),
                'peak_hours': [f"{h[0]}:00" for h in peak_hours],
                'daily_breakdown': [
                    {
                        'date': row[0],
                        'time': row[1],
                        'chapters': row[3],
                        'words': row[4]
                    }
                    for row in daily_data
                ]
            }
    
    def get_reading_patterns(self) -> Dict[str, Any]:
        """分析阅读模式"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取所有会话
            cursor.execute('''
                SELECT duration, reading_speed, focus_score, chapters_read
                FROM reading_sessions
                ORDER BY start_time DESC
                LIMIT 100
            ''')
            
            sessions = cursor.fetchall()
            
            if not sessions:
                return {
                    'pattern_type': '暂无数据',
                    'avg_session_duration': 0,
                    'avg_reading_speed': 0,
                    'avg_focus_score': 0,
                    'consistency_score': 0
                }
            
            # 计算统计数据
            durations = [s[0] for s in sessions]
            speeds = [s[1] for s in sessions if s[1] > 0]
            focus_scores = [s[2] for s in sessions]
            
            avg_duration = statistics.mean(durations)
            avg_speed = statistics.mean(speeds) if speeds else 0
            avg_focus = statistics.mean(focus_scores)
            
            # 判断阅读模式
            if avg_duration >= 45 and avg_focus >= 70:
                pattern_type = "深度阅读者"
            elif avg_duration >= 30:
                pattern_type = "规律阅读者"
            elif avg_speed > 500:
                pattern_type = "快速浏览者"
            else:
                pattern_type = "休闲阅读者"
            
            # 计算一致性分数（基于标准差）
            if len(durations) > 1:
                consistency = 100 - min(statistics.stdev(durations) / avg_duration * 50, 100)
            else:
                consistency = 50
            
            return {
                'pattern_type': pattern_type,
                'avg_session_duration': round(avg_duration, 1),
                'avg_reading_speed': round(avg_speed, 0),
                'avg_focus_score': round(avg_focus, 1),
                'consistency_score': round(consistency, 1),
                'total_sessions_analyzed': len(sessions)
            }
    
    def get_productivity_insights(self) -> Dict[str, Any]:
        """获取效率洞察"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取最近30天的数据
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT * FROM daily_stats WHERE date >= ? ORDER BY date
            ''', (start_date,))
            
            daily_data = cursor.fetchall()
            
            if len(daily_data) < 7:
                return {
                    'status': '数据不足',
                    'message': '需要至少7天的阅读数据才能生成效率洞察'
                }
            
            # 计算趋势
            times = [row[1] for row in daily_data]
            
            # 简单线性回归计算趋势
            n = len(times)
            x = list(range(n))
            
            if n > 1:
                slope = (n * sum(x[i] * times[i] for i in range(n)) - sum(x) * sum(times)) / \
                       (n * sum(xi * xi for xi in x) - sum(x) ** 2)
            else:
                slope = 0
            
            # 判断趋势
            if slope > 5:
                trend = '上升'
                trend_emoji = '📈'
            elif slope < -5:
                trend = '下降'
                trend_emoji = '📉'
            else:
                trend = '稳定'
                trend_emoji = '➡️'
            
            # 找出最佳阅读日
            best_day = max(daily_data, key=lambda x: x[1])
            
            # 计算阅读频率
            active_days = len([t for t in times if t > 0])
            frequency = active_days / n * 100
            
            return {
                'trend': trend,
                'trend_emoji': trend_emoji,
                'trend_slope': round(slope, 2),
                'best_day': {
                    'date': best_day[0],
                    'time': best_day[1]
                },
                'reading_frequency': round(frequency, 1),
                'active_days': active_days,
                'total_days': n,
                'recommendation': self._generate_productivity_recommendation(
                    trend, frequency, active_days, n
                )
            }
    
    def _generate_productivity_recommendation(
        self, 
        trend: str, 
        frequency: float, 
        active_days: int, 
        total_days: int
    ) -> str:
        """生成效率建议"""
        recommendations = []
        
        if trend == '下降':
            recommendations.append("你的阅读时间呈下降趋势，建议设定每日阅读目标")
        elif trend == '上升':
            recommendations.append("很好！你的阅读习惯正在改善，继续保持！")
        
        if frequency < 50:
            recommendations.append(f"你的阅读频率为{frequency:.0f}%，建议尝试每天阅读15分钟")
        elif frequency >= 80:
            recommendations.append("你的阅读频率很高，是个优秀的习惯！")
        
        if active_days < 7:
            recommendations.append("建议建立固定的阅读时间，培养阅读习惯")
        
        return " ".join(recommendations) if recommendations else "继续保持良好的阅读习惯！"
    
    def generate_ascii_chart(self, data: List[float], width: int = 40, height: int = 10) -> str:
        """生成ASCII图表"""
        if not data:
            return "暂无数据"
        
        max_val = max(data) if max(data) > 0 else 1
        min_val = min(data)
        
        chart_lines = []
        
        for i in range(height, 0, -1):
            threshold = min_val + (max_val - min_val) * (i - 1) / height
            line = ""
            for val in data:
                if val >= threshold:
                    line += "█"
                else:
                    line += " "
            chart_lines.append(line)
        
        return "\n".join(chart_lines)
    
    def get_reading_goals(self) -> Dict[str, Any]:
        """获取阅读目标和建议"""
        # 基于历史数据设定合理目标
        patterns = self.get_reading_patterns()
        weekly = self.get_weekly_report()
        
        current_avg_daily = weekly.get('avg_daily_time', 0)
        
        # 设定渐进式目标
        if current_avg_daily < 15:
            target_daily = 20
            goal_level = "初级"
        elif current_avg_daily < 30:
            target_daily = 45
            goal_level = "中级"
        elif current_avg_daily < 60:
            target_daily = 90
            goal_level = "高级"
        else:
            target_daily = 120
            goal_level = "专家"
        
        weekly_target = target_daily * 7
        monthly_target = target_daily * 30
        
        return {
            'current_level': patterns.get('pattern_type', '未知'),
            'goal_level': goal_level,
            'daily_target': target_daily,
            'weekly_target': weekly_target,
            'monthly_target_hours': round(monthly_target / 60, 1),
            'progress_percentage': round(
                min(current_avg_daily / target_daily * 100, 100), 1
            ),
            'next_milestone': self._get_next_milestone(current_avg_daily)
        }
    
    def _get_next_milestone(self, current_avg: float) -> Dict[str, Any]:
        """获取下一个里程碑"""
        milestones = [
            {'name': '阅读新手', 'time': 15, 'reward': '📚'},
            {'name': '阅读爱好者', 'time': 30, 'reward': '📖'},
            {'name': '阅读达人', 'time': 60, 'reward': '📜'},
            {'name': '阅读专家', 'time': 120, 'reward': '🏆'},
            {'name': '阅读大师', 'time': 180, 'reward': '👑'}
        ]
        
        for milestone in milestones:
            if current_avg < milestone['time']:
                remaining = milestone['time'] - current_avg
                return {
                    'name': milestone['name'],
                    'required_time': milestone['time'],
                    'remaining': round(remaining, 1),
                    'reward': milestone['reward']
                }
        
        return {
            'name': '阅读大师',
            'required_time': 180,
            'remaining': 0,
            'reward': '👑',
            'message': '你已达到最高级别！'
        }
