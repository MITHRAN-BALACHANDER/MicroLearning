"""
Admin Dashboard for MicroLearning Bot
Web-based interface for managing users, videos, questions, and analytics
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from functools import wraps
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import func, Integer
from werkzeug.utils import secure_filename

from database.operations import SessionLocal
from database.models import User, Video, VideoProgress, Question, QuizAttempt, Document
from config.settings import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.video_processor import VideoProcessor
from utils.analytics_service import AnalyticsService
import csv
import io

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')
app.config['UPLOAD_FOLDER'] = 'data/videos'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize video processor
video_processor = VideoProcessor()

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
    """User management page with department-based grouping"""
    db = SessionLocal()
    try:
        all_users = db.query(User).order_by(User.created_at.desc()).all()
        
        # Group users by department (hr, sales, it)
        users_by_role = {
            'hr': [],
            'sales': [],
            'it': []
        }
        
        for user in all_users:
            role = user.role or 'hr'
            if role in users_by_role:
                users_by_role[role].append(user)
            else:
                # Default to HR if role not recognized
                users_by_role['hr'].append(user)
        
        return render_template('users_grouped.html', users=all_users, users_by_role=users_by_role)
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


@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """Add new user"""
    if request.method == 'POST':
        db = SessionLocal()
        try:
            # Get form data
            telegram_id = request.form.get('telegram_id')
            username = request.form.get('username')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            is_active = request.form.get('is_active') == 'on'
            
            # Validate required fields
            if not telegram_id or not username:
                flash('Telegram ID and Username are required!', 'error')
                return render_template('add_user.html')
            
            # Check if telegram_id already exists
            existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if existing_user:
                flash('A user with this Telegram ID already exists!', 'error')
                return render_template('add_user.html')
            
            # Create new user
            new_user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active
            )
            
            db.add(new_user)
            db.commit()
            flash(f'User {username} created successfully!', 'success')
            return redirect(url_for('users'))
            
        except Exception as e:
            db.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
            return render_template('add_user.html')
        finally:
            db.close()
    
    return render_template('add_user.html')


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit existing user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('users'))
        
        if request.method == 'POST':
            # Get form data
            telegram_id = request.form.get('telegram_id')
            username = request.form.get('username')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            is_active = request.form.get('is_active') == 'on'
            
            # Validate required fields
            if not telegram_id or not username:
                flash('Telegram ID and Username are required!', 'error')
                return render_template('edit_user.html', user=user)
            
            # Check if telegram_id is being changed to one that already exists
            if telegram_id != user.telegram_id:
                existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()
                if existing_user:
                    flash('A user with this Telegram ID already exists!', 'error')
                    return render_template('edit_user.html', user=user)
            
            # Update user
            user.telegram_id = telegram_id
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            
            db.commit()
            flash(f'User {username} updated successfully!', 'success')
            return redirect(url_for('user_detail', user_id=user_id))
        
        return render_template('edit_user.html', user=user)
        
    except Exception as e:
        db.rollback()
        flash(f'Error updating user: {str(e)}', 'error')
        return redirect(url_for('users'))
    finally:
        db.close()


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('users'))
        
        username = user.username
        
        # Delete related records first
        db.query(VideoProgress).filter(VideoProgress.user_id == user_id).delete()
        db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).delete()
        
        # Delete user
        db.delete(user)
        db.commit()
        
        flash(f'User {username} deleted successfully!', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        db.close()
    
    return redirect(url_for('users'))


@app.route('/videos')
@login_required
def videos():
    """Video management page with category-based grouping"""
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
        
        # Group videos by category
        videos_by_category = {
            'onboarding': [],
            'technical': [],
            'business': [],
            'general': []
        }
        
        for video in all_videos:
            category = video.category or 'general'
            if category in videos_by_category:
                videos_by_category[category].append(video)
            else:
                videos_by_category['general'].append(video)
        
        return render_template('videos_grouped.html', videos=all_videos, video_stats=video_stats, videos_by_category=videos_by_category)
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


@app.route('/videos/create', methods=['GET'])
@login_required
def create_video():
    """Video creation page with multi-clip upload"""
    # Generate unique session ID for this creation session
    session_id = str(uuid.uuid4())
    session['video_creation_session'] = session_id
    return render_template('create_video.html', session_id=session_id)


@app.route('/videos/create/upload-clip', methods=['POST'])
@login_required
def upload_video_clip():
    """Upload a video clip for compilation"""
    try:
        session_id = request.form.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID provided'}), 400
        
        if 'clip' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['clip']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save clip
        success, filepath, error = video_processor.save_uploaded_clip(
            file,
            secure_filename(file.filename),
            session_id
        )
        
        if not success:
            return jsonify({'success': False, 'error': error}), 400
        
        # Get clip info
        clip_info = video_processor.get_video_info(filepath)
        if not clip_info:
            return jsonify({'success': False, 'error': 'Could not read video file'}), 400
        
        return jsonify({
            'success': True,
            'clip': {
                'filename': os.path.basename(filepath),
                'path': filepath,
                'duration': round(clip_info['duration'], 2),
                'resolution': f"{clip_info['width']}x{clip_info['height']}",
                'fps': clip_info['fps'],
                'has_audio': clip_info['audio']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/videos/create/list-clips', methods=['GET'])
@login_required
def list_video_clips():
    """Get list of uploaded clips for current session"""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'No session ID'}), 400
    
    clips = video_processor.get_session_clips(session_id)
    return jsonify({'success': True, 'clips': clips})


@app.route('/videos/create/remove-clip', methods=['POST'])
@login_required
def remove_video_clip():
    """Remove a clip from the compilation"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        os.remove(filepath)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/videos/create/compile', methods=['POST'])
@login_required
def compile_video():
    """Compile uploaded clips into final video"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        title = data.get('title', 'Untitled Video')
        description = data.get('description', '')
        clip_order = data.get('clip_order', [])  # Array of clip paths in order
        add_title_screen = data.get('add_title_screen', False)
        add_transitions = data.get('add_transitions', True)
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'}), 400
        
        if not clip_order:
            return jsonify({'success': False, 'error': 'No clips to compile'}), 400
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"compiled_{timestamp}.mp4"
        
        # Compile clips
        success, output_path, error = video_processor.compile_clips(
            clip_paths=clip_order,
            output_filename=output_filename,
            title=title if add_title_screen else None,
            add_transitions=add_transitions,
            normalize_audio=True
        )
        
        if not success:
            return jsonify({'success': False, 'error': error}), 500
        
        # Generate thumbnail
        thumbnail_path = video_processor.generate_thumbnail(output_path)
        
        # Get video info
        video_info = video_processor.get_video_info(output_path)
        
        # Save to database
        db = SessionLocal()
        try:
            video = Video(
                title=title,
                description=description,
                file_id=output_path,  # Store local path for now
                file_path=output_path,
                duration=int(video_info['duration']) if video_info else None,
                is_active=False  # Inactive until admin reviews
            )
            db.add(video)
            db.commit()
            
            video_id = video.id
            
            # Clean up session files
            video_processor.cleanup_session(session_id)
            
            return jsonify({
                'success': True,
                'video_id': video_id,
                'output_path': output_path,
                'thumbnail': thumbnail_path,
                'duration': video_info['duration'] if video_info else 0
            })
            
        finally:
            db.close()
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/videos/create/cancel', methods=['POST'])
@login_required
def cancel_video_creation():
    """Cancel video creation and clean up files"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id:
            video_processor.cleanup_session(session_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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


# ============ Advanced Analytics Routes ============

@app.route('/analytics/dashboard')
@login_required
def analytics_dashboard():
    """Main analytics dashboard with real-time widgets"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        
        # Get all KPIs and data for initial load
        kpis = analytics.get_overview_kpis()
        user_activity = analytics.get_user_activity_breakdown()
        content_dist = analytics.get_content_distribution()
        system_health = analytics.get_system_health()
        
        return render_template('analytics_dashboard.html',
                             kpis=kpis,
                             user_activity=user_activity,
                             content_distribution=content_dist,
                             system_health=system_health)
    finally:
        db.close()


@app.route('/api/analytics/kpis')
@login_required
def api_analytics_kpis():
    """API endpoint for KPI widgets"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        kpis = analytics.get_overview_kpis()
        return jsonify(kpis)
    finally:
        db.close()


@app.route('/api/analytics/user-growth')
@login_required
def api_user_growth():
    """API endpoint for user growth trend"""
    days = request.args.get('days', 30, type=int)
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_user_growth_trend(days)
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/user-activity')
@login_required
def api_user_activity():
    """API endpoint for user activity breakdown"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_user_activity_breakdown()
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/top-users')
@login_required
def api_top_users():
    """API endpoint for top users"""
    limit = request.args.get('limit', 10, type=int)
    role_filter = request.args.get('role', 'all')
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_top_users(limit, role_filter)
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/video-performance')
@login_required
def api_video_performance():
    """API endpoint for video performance metrics"""
    category_filter = request.args.get('category', 'all')
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_video_performance(category_filter)
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/content-distribution')
@login_required
def api_content_distribution():
    """API endpoint for content distribution"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_content_distribution()
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/engagement-trends')
@login_required
def api_engagement_trends():
    """API endpoint for engagement trends"""
    days = request.args.get('days', 30, type=int)
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_engagement_trends(days)
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/quiz-performance')
@login_required
def api_quiz_performance():
    """API endpoint for quiz performance stats"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_quiz_performance_stats()
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/system-health')
@login_required
def api_system_health():
    """API endpoint for system health metrics"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_system_health()
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/users-by-role')
@login_required
def api_users_by_role():
    """API endpoint for users grouped by role"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_users_by_role()
        return jsonify(data)
    finally:
        db.close()


@app.route('/api/analytics/user/<int:user_id>')
@login_required
def api_user_detail(user_id):
    """API endpoint for detailed user analytics"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_user_detail(user_id)
        if data:
            return jsonify(data)
        return jsonify({'error': 'User not found'}), 404
    finally:
        db.close()


@app.route('/api/analytics/video/<int:video_id>')
@login_required
def api_video_detail(video_id):
    """API endpoint for detailed video analytics"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        data = analytics.get_video_detail(video_id)
        if data:
            return jsonify(data)
        return jsonify({'error': 'Video not found'}), 404
    finally:
        db.close()


@app.route('/api/analytics/export/<data_type>')
@login_required
def api_export_data(data_type):
    """API endpoint for exporting data as CSV"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        
        # Get filters from query params
        filters = {}
        if request.args.get('active_only') == 'true':
            filters['active_only'] = True
        if request.args.get('date_from'):
            filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
        if request.args.get('days'):
            filters['days'] = int(request.args.get('days'))
        
        # Export data
        data = analytics.export_data(data_type, filters)
        
        if not data:
            return jsonify({'error': 'Invalid data type or no data available'}), 400
        
        # Create CSV
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        # Prepare response
        response = send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{data_type}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
        return response
    finally:
        db.close()


@app.route('/api/analytics/clear-cache', methods=['POST'])
@login_required
def api_clear_cache():
    """API endpoint to clear analytics cache"""
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        analytics.clear_cache()
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
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
