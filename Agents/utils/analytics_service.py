"""
Analytics Service for Real-time Dashboard
Provides aggregated metrics, KPIs, trends, and export capabilities
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc, case, distinct
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
import json
from collections import defaultdict

from database.models import (
    User, Video, VideoProgress, Question, QuizAttempt, 
    Document, UserSession
)


class AnalyticsService:
    """Service for generating analytics and insights"""
    
    def __init__(self, db: Session):
        self.db = db
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    # ============ KPI Cards ============
    
    def get_overview_kpis(self) -> Dict:
        """Get high-level KPI metrics for dashboard cards"""
        cache_key = 'overview_kpis'
        if self._check_cache(cache_key):
            return self._cache[cache_key]['data']
        
        now = datetime.utcnow()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # User metrics
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        new_users_week = self.db.query(User).filter(
            func.date(User.created_at) >= week_ago
        ).count()
        active_today = self.db.query(User).filter(
            func.date(User.last_active) == today
        ).count()
        
        # Content metrics
        total_videos = self.db.query(Video).count()
        active_videos = self.db.query(Video).filter(Video.is_active == True).count()
        total_questions = self.db.query(Question).filter(Question.is_active == True).count()
        total_documents = self.db.query(Document).filter(Document.is_active == True).count()
        
        # Engagement metrics
        total_video_views = self.db.query(VideoProgress).count()
        completed_videos = self.db.query(VideoProgress).filter(
            VideoProgress.completed == True
        ).count()
        total_quiz_attempts = self.db.query(QuizAttempt).count()
        quiz_attempts_week = self.db.query(QuizAttempt).filter(
            func.date(QuizAttempt.attempted_at) >= week_ago
        ).count()
        
        # Calculate completion rate
        completion_rate = (completed_videos / total_video_views * 100) if total_video_views > 0 else 0
        
        # Average quiz score
        avg_rating = self.db.query(func.avg(QuizAttempt.rating)).filter(
            QuizAttempt.rating.isnot(None)
        ).scalar() or 0
        
        # Session metrics
        active_sessions = self.db.query(UserSession).filter(
            UserSession.is_active == True
        ).count()
        
        kpis = {
            'users': {
                'total': total_users,
                'active': active_users,
                'new_this_week': new_users_week,
                'active_today': active_today,
                'inactive': total_users - active_users
            },
            'content': {
                'total_videos': total_videos,
                'active_videos': active_videos,
                'total_questions': total_questions,
                'total_documents': total_documents,
                'avg_questions_per_video': round(total_questions / total_videos, 1) if total_videos > 0 else 0
            },
            'engagement': {
                'total_views': total_video_views,
                'completed_videos': completed_videos,
                'completion_rate': round(completion_rate, 1),
                'total_quiz_attempts': total_quiz_attempts,
                'quiz_attempts_week': quiz_attempts_week,
                'avg_quiz_score': round(avg_rating, 1),
                'active_sessions': active_sessions
            },
            'system': {
                'uptime_days': (now - datetime(2025, 1, 1)).days,
                'avg_response_time': 1.2,  # Mock - implement actual tracking
                'cache_hit_rate': 85.3  # Mock - implement actual tracking
            }
        }
        
        self._set_cache(cache_key, kpis)
        return kpis
    
    # ============ User Analytics ============
    
    def get_user_growth_trend(self, days: int = 30) -> List[Dict]:
        """Get user growth trend over time"""
        cache_key = f'user_growth_{days}'
        if self._check_cache(cache_key):
            return self._cache[cache_key]['data']
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Daily user registrations
        daily_users = self.db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            func.date(User.created_at) >= start_date
        ).group_by(
            func.date(User.created_at)
        ).order_by('date').all()
        
        # Fill missing dates
        result = []
        current_total = self.db.query(User).filter(
            func.date(User.created_at) < start_date
        ).count()
        
        date_map = {str(row.date): row.count for row in daily_users}
        
        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            new_users = date_map.get(str(date), 0)
            current_total += new_users
            
            result.append({
                'date': str(date),
                'new_users': new_users,
                'total_users': current_total
            })
        
        self._set_cache(cache_key, result)
        return result
    
    def get_user_activity_breakdown(self) -> Dict:
        """Get user activity segmentation"""
        now = datetime.utcnow().date()
        
        # Active users by recency
        active_today = self.db.query(User).filter(
            func.date(User.last_active) == now
        ).count()
        
        active_week = self.db.query(User).filter(
            func.date(User.last_active) >= now - timedelta(days=7),
            func.date(User.last_active) < now
        ).count()
        
        active_month = self.db.query(User).filter(
            func.date(User.last_active) >= now - timedelta(days=30),
            func.date(User.last_active) < now - timedelta(days=7)
        ).count()
        
        inactive = self.db.query(User).filter(
            or_(
                func.date(User.last_active) < now - timedelta(days=30),
                User.last_active.is_(None)
            )
        ).count()
        
        return {
            'active_today': active_today,
            'active_this_week': active_week,
            'active_this_month': active_month,
            'inactive': inactive,
            'segments': [
                {'label': 'Today', 'value': active_today, 'color': '#10b981'},
                {'label': 'This Week', 'value': active_week, 'color': '#3b82f6'},
                {'label': 'This Month', 'value': active_month, 'color': '#f59e0b'},
                {'label': 'Inactive', 'value': inactive, 'color': '#6b7280'}
            ]
        }
    
    def get_top_users(self, limit: int = 10, role_filter: Optional[str] = None) -> List[Dict]:
        """Get top performing users by various metrics"""
        # Users with most completed videos
        query = self.db.query(
            User,
            func.count(VideoProgress.id).label('completed_count'),
            func.avg(QuizAttempt.rating).label('avg_rating')
        ).outerjoin(
            VideoProgress, and_(
                VideoProgress.user_id == User.id,
                VideoProgress.completed == True
            )
        ).outerjoin(
            QuizAttempt, QuizAttempt.user_id == User.id
        )
        
        if role_filter and role_filter != 'all':
            query = query.filter(User.role == role_filter)
        
        top_completions = query.group_by(User.id).order_by(
            desc('completed_count')
        ).limit(limit).all()
        
        return [{
            'user_id': user.id,
            'telegram_id': user.telegram_id,
            'username': user.username or user.first_name or 'Unknown',
            'role': user.role or 'learner',
            'completed_videos': completed_count,
            'avg_quiz_score': round(avg_rating, 1) if avg_rating else 0,
            'member_since': user.created_at.strftime('%Y-%m-%d')
        } for user, completed_count, avg_rating in top_completions]
    
    def get_users_by_role(self) -> Dict:
        """Get users grouped by role"""
        roles = self.db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role).all()
        
        return {
            'by_role': [
                {'role': role or 'learner', 'count': count}
                for role, count in roles
            ],
            'total': sum(count for _, count in roles)
        }
    
    # ============ Content Analytics ============
    
    def get_video_performance(self, category_filter: Optional[str] = None) -> List[Dict]:
        """Get video performance metrics"""
        cache_key = f'video_performance_{category_filter or "all"}'
        if self._check_cache(cache_key):
            return self._cache[cache_key]['data']
        
        query = self.db.query(
            Video,
            func.count(VideoProgress.id).label('view_count'),
            func.count(case((VideoProgress.completed == True, 1))).label('completion_count'),
            func.avg(QuizAttempt.rating).label('avg_rating'),
            func.count(distinct(Question.id)).label('question_count')
        ).outerjoin(
            VideoProgress, VideoProgress.video_id == Video.id
        ).outerjoin(
            Question, Question.video_id == Video.id
        ).outerjoin(
            QuizAttempt, QuizAttempt.question_id == Question.id
        ).filter(
            Video.is_active == True
        )
        
        if category_filter and category_filter != 'all':
            query = query.filter(Video.category == category_filter)
        
        videos = query.group_by(Video.id).all()
        
        result = []
        for video, views, completions, avg_rating, questions in videos:
            completion_rate = (completions / views * 100) if views > 0 else 0
            
            result.append({
                'video_id': video.id,
                'title': video.title,
                'category': video.category or 'general',
                'views': views,
                'completions': completions,
                'completion_rate': round(completion_rate, 1),
                'avg_rating': round(avg_rating, 1) if avg_rating else 0,
                'questions': questions,
                'difficulty': video.difficulty_level,
                'created_at': video.created_at.strftime('%Y-%m-%d')
            })
        
        self._set_cache(cache_key, result)
        return result
    
    def get_content_distribution(self) -> Dict:
        """Get content distribution by type and difficulty"""
        # Videos by difficulty
        difficulty_dist = self.db.query(
            Video.difficulty_level,
            func.count(Video.id).label('count')
        ).filter(
            Video.is_active == True
        ).group_by(Video.difficulty_level).all()
        
        # Videos by category
        category_dist = self.db.query(
            Video.category,
            func.count(Video.id).label('count')
        ).filter(
            Video.is_active == True
        ).group_by(Video.category).all()
        
        # Questions by type
        question_types = self.db.query(
            Question.question_type,
            func.count(Question.id).label('count')
        ).filter(
            Question.is_active == True
        ).group_by(Question.question_type).all()
        
        # Documents by type
        doc_types = self.db.query(
            Document.doc_type,
            func.count(Document.id).label('count')
        ).filter(
            Document.is_active == True
        ).group_by(Document.doc_type).all()
        
        return {
            'videos_by_difficulty': [
                {'level': level, 'count': count} 
                for level, count in difficulty_dist
            ],
            'videos_by_category': [
                {'category': cat or 'general', 'count': count}
                for cat, count in category_dist
            ],
            'questions_by_type': [
                {'type': qtype, 'count': count} 
                for qtype, count in question_types
            ],
            'documents_by_type': [
                {'type': dtype, 'count': count} 
                for dtype, count in doc_types
            ]
        }
    
    # ============ Engagement Analytics ============
    
    def get_engagement_trends(self, days: int = 30) -> Dict:
        """Get daily engagement trends"""
        cache_key = f'engagement_trends_{days}'
        if self._check_cache(cache_key):
            return self._cache[cache_key]['data']
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Daily video views
        daily_views = self.db.query(
            func.date(VideoProgress.watched_at).label('date'),
            func.count(VideoProgress.id).label('count')
        ).filter(
            func.date(VideoProgress.watched_at) >= start_date
        ).group_by('date').order_by('date').all()
        
        # Daily quiz attempts
        daily_quizzes = self.db.query(
            func.date(QuizAttempt.attempted_at).label('date'),
            func.count(QuizAttempt.id).label('count')
        ).filter(
            func.date(QuizAttempt.attempted_at) >= start_date
        ).group_by('date').order_by('date').all()
        
        # Build time series
        views_map = {str(row.date): row.count for row in daily_views}
        quizzes_map = {str(row.date): row.count for row in daily_quizzes}
        
        result = {
            'dates': [],
            'video_views': [],
            'quiz_attempts': [],
            'total_engagement': []
        }
        
        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            date_str = str(date)
            
            views = views_map.get(date_str, 0)
            quizzes = quizzes_map.get(date_str, 0)
            
            result['dates'].append(date_str)
            result['video_views'].append(views)
            result['quiz_attempts'].append(quizzes)
            result['total_engagement'].append(views + quizzes)
        
        self._set_cache(cache_key, result)
        return result
    
    def get_quiz_performance_stats(self) -> Dict:
        """Get detailed quiz performance statistics"""
        # Overall stats
        total_attempts = self.db.query(QuizAttempt).count()
        
        avg_rating = self.db.query(func.avg(QuizAttempt.rating)).filter(
            QuizAttempt.rating.isnot(None)
        ).scalar() or 0
        
        correct_answers = self.db.query(QuizAttempt).filter(
            QuizAttempt.is_correct == True
        ).count()
        
        accuracy = (correct_answers / total_attempts * 100) if total_attempts > 0 else 0
        
        # Rating distribution
        rating_ranges = [
            (0, 3, 'Poor'),
            (3, 5, 'Fair'),
            (5, 7, 'Good'),
            (7, 9, 'Very Good'),
            (9, 11, 'Excellent')
        ]
        
        distribution = []
        for min_r, max_r, label in rating_ranges:
            count = self.db.query(QuizAttempt).filter(
                QuizAttempt.rating >= min_r,
                QuizAttempt.rating < max_r
            ).count()
            distribution.append({'label': label, 'count': count})
        
        return {
            'total_attempts': total_attempts,
            'avg_rating': round(avg_rating, 2),
            'accuracy': round(accuracy, 1),
            'correct_answers': correct_answers,
            'incorrect_answers': total_attempts - correct_answers,
            'rating_distribution': distribution
        }
    
    # ============ System Analytics ============
    
    def get_system_health(self) -> Dict:
        """Get system health metrics"""
        # Database statistics
        total_records = (
            self.db.query(User).count() +
            self.db.query(Video).count() +
            self.db.query(VideoProgress).count() +
            self.db.query(Question).count() +
            self.db.query(QuizAttempt).count() +
            self.db.query(Document).count()
        )
        
        # Active vs inactive content
        active_content = self.db.query(Video).filter(Video.is_active == True).count()
        inactive_content = self.db.query(Video).filter(Video.is_active == False).count()
        
        return {
            'database': {
                'total_records': total_records,
                'tables': 6,
                'status': 'healthy'
            },
            'content': {
                'active': active_content,
                'inactive': inactive_content,
                'active_percentage': round(active_content / (active_content + inactive_content) * 100, 1) if (active_content + inactive_content) > 0 else 0
            },
            'sessions': {
                'active': self.db.query(UserSession).filter(UserSession.is_active == True).count(),
                'total_today': self.db.query(UserSession).filter(
                    func.date(UserSession.started_at) == datetime.utcnow().date()
                ).count()
            }
        }
    
    # ============ Drill-down Methods ============
    
    def get_user_detail(self, user_id: int) -> Optional[Dict]:
        """Get detailed analytics for specific user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Video progress
        videos_watched = self.db.query(VideoProgress).filter(
            VideoProgress.user_id == user_id
        ).count()
        
        completed_videos = self.db.query(VideoProgress).filter(
            VideoProgress.user_id == user_id,
            VideoProgress.completed == True
        ).count()
        
        # Quiz performance
        quiz_attempts = self.db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id
        ).count()
        
        avg_score = self.db.query(func.avg(QuizAttempt.rating)).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.rating.isnot(None)
        ).scalar() or 0
        
        correct_answers = self.db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.is_correct == True
        ).count()
        
        return {
            'user': {
                'id': user.id,
                'telegram_id': user.telegram_id,
                'username': user.username,
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
                'created_at': user.created_at,
                'last_active': user.last_active,
                'is_active': user.is_active
            },
            'video_stats': {
                'watched': videos_watched,
                'completed': completed_videos,
                'completion_rate': round(completed_videos / videos_watched * 100, 1) if videos_watched > 0 else 0
            },
            'quiz_stats': {
                'attempts': quiz_attempts,
                'avg_score': round(avg_score, 1),
                'correct': correct_answers,
                'accuracy': round(correct_answers / quiz_attempts * 100, 1) if quiz_attempts > 0 else 0
            }
        }
    
    def get_video_detail(self, video_id: int) -> Optional[Dict]:
        """Get detailed analytics for specific video"""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return None
        
        # View statistics
        total_views = self.db.query(VideoProgress).filter(
            VideoProgress.video_id == video_id
        ).count()
        
        unique_viewers = self.db.query(
            func.count(distinct(VideoProgress.user_id))
        ).filter(
            VideoProgress.video_id == video_id
        ).scalar()
        
        completions = self.db.query(VideoProgress).filter(
            VideoProgress.video_id == video_id,
            VideoProgress.completed == True
        ).count()
        
        avg_watch_time = self.db.query(func.avg(VideoProgress.watch_time)).filter(
            VideoProgress.video_id == video_id
        ).scalar() or 0
        
        # Quiz statistics
        questions = self.db.query(Question).filter(
            Question.video_id == video_id
        ).all()
        
        quiz_attempts = self.db.query(QuizAttempt).join(
            Question, QuizAttempt.question_id == Question.id
        ).filter(
            Question.video_id == video_id
        ).count()
        
        avg_rating = self.db.query(func.avg(QuizAttempt.rating)).join(
            Question, QuizAttempt.question_id == Question.id
        ).filter(
            Question.video_id == video_id,
            QuizAttempt.rating.isnot(None)
        ).scalar() or 0
        
        return {
            'video': {
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'duration': video.duration,
                'difficulty': video.difficulty_level,
                'created_at': video.created_at,
                'is_active': video.is_active
            },
            'view_stats': {
                'total_views': total_views,
                'unique_viewers': unique_viewers,
                'completions': completions,
                'completion_rate': round(completions / total_views * 100, 1) if total_views > 0 else 0,
                'avg_watch_time': int(avg_watch_time)
            },
            'quiz_stats': {
                'total_questions': len(questions),
                'total_attempts': quiz_attempts,
                'avg_rating': round(avg_rating, 1),
                'questions': [{
                    'id': q.id,
                    'text': q.question_text[:100],
                    'type': q.question_type,
                    'difficulty': q.difficulty
                } for q in questions]
            }
        }
    
    # ============ Export Methods ============
    
    def export_data(self, data_type: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Export data for CSV/Excel download"""
        if data_type == 'users':
            return self._export_users(filters)
        elif data_type == 'videos':
            return self._export_videos(filters)
        elif data_type == 'quiz_attempts':
            return self._export_quiz_attempts(filters)
        elif data_type == 'engagement':
            return self._export_engagement(filters)
        else:
            return []
    
    def _export_users(self, filters: Optional[Dict]) -> List[Dict]:
        """Export user data"""
        query = self.db.query(User)
        
        if filters:
            if filters.get('active_only'):
                query = query.filter(User.is_active == True)
            if filters.get('date_from'):
                query = query.filter(User.created_at >= filters['date_from'])
        
        users = query.all()
        
        return [{
            'ID': u.id,
            'Telegram ID': u.telegram_id,
            'Username': u.username or '',
            'First Name': u.first_name or '',
            'Last Name': u.last_name or '',
            'Created At': u.created_at.strftime('%Y-%m-%d %H:%M'),
            'Last Active': u.last_active.strftime('%Y-%m-%d %H:%M') if u.last_active else '',
            'Is Active': 'Yes' if u.is_active else 'No'
        } for u in users]
    
    def _export_videos(self, filters: Optional[Dict]) -> List[Dict]:
        """Export video data"""
        query = self.db.query(Video)
        
        if filters:
            if filters.get('active_only'):
                query = query.filter(Video.is_active == True)
        
        videos = query.all()
        
        return [{
            'ID': v.id,
            'Title': v.title,
            'Description': v.description or '',
            'Duration': v.duration or 0,
            'Difficulty': v.difficulty_level,
            'Created At': v.created_at.strftime('%Y-%m-%d %H:%M'),
            'Is Active': 'Yes' if v.is_active else 'No'
        } for v in videos]
    
    def _export_quiz_attempts(self, filters: Optional[Dict]) -> List[Dict]:
        """Export quiz attempt data"""
        query = self.db.query(QuizAttempt).join(User).join(Question).join(Video)
        
        if filters:
            if filters.get('date_from'):
                query = query.filter(QuizAttempt.attempted_at >= filters['date_from'])
        
        attempts = query.all()
        
        return [{
            'Attempt ID': a.id,
            'User': a.user.username or a.user.telegram_id,
            'Video': a.question.video.title,
            'Question': a.question.question_text[:100],
            'Rating': a.rating or 0,
            'Correct': 'Yes' if a.is_correct else 'No',
            'Attempted At': a.attempted_at.strftime('%Y-%m-%d %H:%M')
        } for a in attempts]
    
    def _export_engagement(self, filters: Optional[Dict]) -> List[Dict]:
        """Export engagement data"""
        days = filters.get('days', 30) if filters else 30
        trends = self.get_engagement_trends(days)
        
        result = []
        for i in range(len(trends['dates'])):
            result.append({
                'Date': trends['dates'][i],
                'Video Views': trends['video_views'][i],
                'Quiz Attempts': trends['quiz_attempts'][i],
                'Total Engagement': trends['total_engagement'][i]
            })
        
        return result
    
    # ============ Cache Helpers ============
    
    def _check_cache(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache:
            return False
        
        cache_entry = self._cache[key]
        age = (datetime.utcnow() - cache_entry['timestamp']).seconds
        
        return age < self._cache_ttl
    
    def _set_cache(self, key: str, data: any):
        """Set cache entry"""
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.utcnow()
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache = {}
