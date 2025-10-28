"""
Admin Dashboard for MicroLearning Bot
Web-based interface for managing users, videos, questions, and analytics
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from functools import wraps
import os
from datetime import datetime, timedelta
from sqlalchemy import func, Integer
from werkzeug.utils import secure_filename

from database.operations import SessionLocal
from database.models import User, Video, VideoProgress, Question, QuizAttempt, Document
from config.settings import ADMIN_USERNAME, ADMIN_PASSWORD

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')
app.config['UPLOAD_FOLDER'] = 'data/videos'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Successfully logged out!', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    """Main dashboard with overview stats"""
    db = SessionLocal()
    try:
        # Get statistics
        stats = {
            'total_users': db.query(User).count(),
            'active_users': db.query(User).filter(User.is_active == True).count(),
            'total_videos': db.query(Video).count(),
            'active_videos': db.query(Video).filter(Video.is_active == True).count(),
            'total_questions': db.query(Question).count(),
            'total_quiz_attempts': db.query(QuizAttempt).count(),
            'total_documents': db.query(Document).count(),
            'videos_watched': db.query(VideoProgress).filter(VideoProgress.completed == True).count(),
        }
        
        # Recent activity
        recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
        recent_videos = db.query(Video).order_by(Video.created_at.desc()).limit(5).all()
        recent_attempts = db.query(QuizAttempt).order_by(QuizAttempt.attempted_at.desc()).limit(10).all()
        
        # User engagement stats
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        active_today = db.query(User).filter(
            func.date(User.last_active) == today
        ).count()
        
        active_this_week = db.query(User).filter(
            func.date(User.last_active) >= week_ago
        ).count()
        
        stats['active_today'] = active_today
        stats['active_this_week'] = active_this_week
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_users=recent_users,
                             recent_videos=recent_videos,
                             recent_attempts=recent_attempts)
    finally:
        db.close()


@app.route('/users')
@login_required
def users():
    """User management page"""
    db = SessionLocal()
    try:
        all_users = db.query(User).order_by(User.created_at.desc()).all()
        # Render clean template to avoid previously corrupted file
        return render_template('users_clean.html', users=all_users)
    finally:
        db.close()


@app.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    """User detail page with progress and activity"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('users'))
        
        # Get user's video progress
        progress = db.query(VideoProgress).filter(
            VideoProgress.user_id == user_id
        ).all()
        
        # Get quiz attempts
        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id
        ).order_by(QuizAttempt.attempted_at.desc()).all()
        
        # Calculate stats
        total_videos = db.query(Video).filter(Video.is_active == True).count()
        completed_videos = len([p for p in progress if p.completed])
        completion_rate = (completed_videos / total_videos * 100) if total_videos > 0 else 0
        
        avg_rating = db.query(func.avg(QuizAttempt.rating)).filter(
            QuizAttempt.user_id == user_id
        ).scalar() or 0
        
        user_stats = {
            'total_videos': total_videos,
            'completed_videos': completed_videos,
            'completion_rate': round(completion_rate, 1),
            'quiz_attempts': len(attempts),
            'avg_rating': round(avg_rating, 2)
        }
        
        return render_template('user_detail.html', 
                             user=user, 
                             progress=progress,
                             attempts=attempts,
                             user_stats=user_stats)
    finally:
        db.close()


@app.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    """Activate/Deactivate user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = not user.is_active
            db.commit()
            status = 'activated' if user.is_active else 'deactivated'
            flash(f'User {user.username} {status} successfully!', 'success')
        else:
            flash('User not found!', 'danger')
    finally:
        db.close()
    
    return redirect(url_for('users'))


@app.route('/videos')
@login_required
def videos():
    """Video management page"""
    db = SessionLocal()
    try:
        all_videos = db.query(Video).order_by(Video.order_index, Video.created_at.desc()).all()
        
        # Get watch stats for each video
        video_stats = {}
        for video in all_videos:
            total_watches = db.query(VideoProgress).filter(
                VideoProgress.video_id == video.id
            ).count()
            completed_watches = db.query(VideoProgress).filter(
                VideoProgress.video_id == video.id,
                VideoProgress.completed == True
            ).count()
            
            video_stats[video.id] = {
                'total_watches': total_watches,
                'completed_watches': completed_watches
            }
        
        return render_template('videos.html', videos=all_videos, video_stats=video_stats)
    finally:
        db.close()


@app.route('/videos/add', methods=['GET', 'POST'])
@login_required
def add_video():
    """Add new video"""
    if request.method == 'POST':
        db = SessionLocal()
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            file_id = request.form.get('file_id')
            duration = request.form.get('duration', type=int)
            difficulty = request.form.get('difficulty', 1, type=int)
            
            # Handle file upload
            if 'video_file' in request.files:
                file = request.files['video_file']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    file_id = os.path.abspath(filepath)
            
            # Create video
            video = Video(
                title=title,
                description=description,
                file_id=file_id,
                duration=duration,
                difficulty_level=difficulty,
                is_active=True
            )
            
            db.add(video)
            db.commit()
            
            flash(f'Video "{title}" added successfully!', 'success')
            return redirect(url_for('videos'))
        except Exception as e:
            flash(f'Error adding video: {str(e)}', 'danger')
        finally:
            db.close()
    
    return render_template('add_video.html')


@app.route('/videos/<int:video_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    """Edit video"""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            flash('Video not found!', 'danger')
            return redirect(url_for('videos'))
        
        if request.method == 'POST':
            video.title = request.form.get('title')
            video.description = request.form.get('description')
            video.duration = request.form.get('duration', type=int)
            video.difficulty_level = request.form.get('difficulty', type=int)
            
            # Update file_id if provided
            new_file_id = request.form.get('file_id')
            if new_file_id:
                video.file_id = new_file_id
            
            db.commit()
            flash(f'Video "{video.title}" updated successfully!', 'success')
            return redirect(url_for('videos'))
        
        return render_template('edit_video.html', video=video)
    finally:
        db.close()


@app.route('/videos/<int:video_id>/toggle', methods=['POST'])
@login_required
def toggle_video(video_id):
    """Activate/Deactivate video"""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.is_active = not video.is_active
            db.commit()
            status = 'activated' if video.is_active else 'deactivated'
            flash(f'Video "{video.title}" {status} successfully!', 'success')
        else:
            flash('Video not found!', 'danger')
    finally:
        db.close()
    
    return redirect(url_for('videos'))


@app.route('/videos/<int:video_id>/delete', methods=['POST'])
@login_required
def delete_video(video_id):
    """Delete video"""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            title = video.title
            db.delete(video)
            db.commit()
            flash(f'Video "{title}" deleted successfully!', 'warning')
        else:
            flash('Video not found!', 'danger')
    finally:
        db.close()
    
    return redirect(url_for('videos'))


@app.route('/questions')
@login_required
def questions():
    """Questions management page"""
    db = SessionLocal()
    try:
        all_questions = db.query(Question).order_by(Question.created_at.desc()).all()
        return render_template('questions.html', questions=all_questions)
    finally:
        db.close()


@app.route('/analytics')
@login_required
def analytics():
    """Analytics page with charts and insights"""
    db = SessionLocal()
    try:
        # User growth over time
        users_by_date_raw = db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).group_by(func.date(User.created_at)).all()
        
        # Convert to serializable format
        users_by_date = [[str(row.date), row.count] for row in users_by_date_raw]
        
        # Quiz performance
        quiz_stats = db.query(
            func.avg(QuizAttempt.rating).label('avg_rating'),
            func.count(QuizAttempt.id).label('total_attempts')
        ).first()
        
        # Video completion rates
        video_completion_raw = db.query(
            Video.title,
            func.count(VideoProgress.id).label('total_watches'),
            func.sum(func.cast(VideoProgress.completed, Integer)).label('completed')
        ).join(VideoProgress, Video.id == VideoProgress.video_id, isouter=True
        ).group_by(Video.id, Video.title).all()
        
        # Convert to serializable format
        video_completion = [[row.title, row.total_watches, row.completed or 0] for row in video_completion_raw]
        
        # Top performers
        top_users = db.query(
            User.username,
            User.first_name,
            func.avg(QuizAttempt.rating).label('avg_score')
        ).join(QuizAttempt, User.id == QuizAttempt.user_id
        ).group_by(User.id, User.username, User.first_name
        ).order_by(func.avg(QuizAttempt.rating).desc()
        ).limit(10).all()
        
        return render_template('analytics.html',
                             users_by_date=users_by_date,
                             quiz_stats=quiz_stats,
                             video_completion=video_completion,
                             top_users=top_users)
    finally:
        db.close()


@app.route('/documents')
@login_required
def documents():
    """Documents management for RAG"""
    db = SessionLocal()
    try:
        all_documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()
        return render_template('documents.html', documents=all_documents)
    finally:
        db.close()


@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for real-time stats"""
    db = SessionLocal()
    try:
        stats = {
            'users': {
                'total': db.query(User).count(),
                'active': db.query(User).filter(User.is_active == True).count()
            },
            'videos': {
                'total': db.query(Video).count(),
                'active': db.query(Video).filter(Video.is_active == True).count()
            },
            'activity': {
                'quiz_attempts': db.query(QuizAttempt).count(),
                'videos_watched': db.query(VideoProgress).filter(VideoProgress.completed == True).count()
            }
        }
        return jsonify(stats)
    finally:
        db.close()


if __name__ == '__main__':
    # Create upload folder if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("="*60)
    print("MicroLearning Bot - Admin Dashboard")
    print("="*60)
    print(f"Access the dashboard at: http://localhost:5000")
    print(f"Username: {ADMIN_USERNAME}")
    print(f"Password: {ADMIN_PASSWORD}")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
