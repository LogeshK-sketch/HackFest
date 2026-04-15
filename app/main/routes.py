from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp
from app.models import TestAttempt, Prediction, Question
from app.extensions import db
# ADDED IMPORT: Utility functions
from app.utils import get_category_score, get_readiness_label

@main_bp.route('/')
def index():
    """Redirect to dashboard or login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Display the student or admin dashboard."""
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
        
    # MODIFIED: Calculate category scores using utils for aptitude and core
    current_user.aptitude_score = get_category_score(current_user.id, 'aptitude')
    current_user.core_score = get_category_score(current_user.id, 'core')
    
    # NEW: Calculate coding metrics and score from Submissions
    from app.models import Submission, CodingProblem
    from sqlalchemy import distinct
    from sqlalchemy.sql import func
    
    # 1. total_solved
    total_solved = db.session.query(func.count(distinct(Submission.problem_id)))\
        .filter(Submission.user_id == current_user.id, Submission.result == 'passed').scalar() or 0
        
    # 2. total_attempted
    total_attempted = db.session.query(func.count(distinct(Submission.problem_id)))\
        .filter(Submission.user_id == current_user.id).scalar() or 0
        
    # 3. accuracy
    accuracy = round((total_solved / total_attempted * 100), 1) if total_attempted > 0 else 0
    
    # 4. recent_submissions
    recent_submissions = Submission.query.filter_by(user_id=current_user.id)\
        .order_by(Submission.created_at.desc()).limit(5).all()
        
    # 5. coding_score
    solved_problems = db.session.query(CodingProblem.difficulty, func.count(distinct(Submission.problem_id)))\
        .join(Submission, CodingProblem.id == Submission.problem_id)\
        .filter(Submission.user_id == current_user.id, Submission.result == 'passed')\
        .group_by(CodingProblem.difficulty).all()
        
    c_score = 0
    dif_breakdown = {'Easy': 0, 'Medium': 0, 'Hard': 0}
    for diff, count in solved_problems:
        if diff == 'Easy': 
            c_score += count * 10
            dif_breakdown['Easy'] = count
        elif diff == 'Medium': 
            c_score += count * 20
            dif_breakdown['Medium'] = count
        elif diff == 'Hard': 
            c_score += count * 30
            dif_breakdown['Hard'] = count
            
    current_user.coding_score = c_score
    db.session.commit()
    
    # --- UPDATED IN STEP 4 ---
    from app.ml.predictor import predict
    from app.models import TestAttempt, Leaderboard, Notification, Resume
    import json

    # ML prediction
    ml_result = predict(current_user.id)

    # Category averages for radar chart
    all_attempts = TestAttempt.query.filter_by(
        user_id=current_user.id).all()

    def cat_avg(category):
        scores = [a.score for a in all_attempts
                  if a.category and category in a.category.lower()]
        return round(sum(scores)/len(scores), 1) if scores else 0

    category_scores = {
        'Aptitude': cat_avg('aptitude'),
        'Coding':   c_score if c_score <= 100 else 100, # Normalize for chart visualization if needed, but previously it was an avg 0-100
        'Core CS':  cat_avg('core')
    }

    # Score history for line chart (last 10 attempts, any category)
    recent_attempts = TestAttempt.query\
        .filter_by(user_id=current_user.id)\
        .order_by(TestAttempt.id.desc()).limit(10).all()
    recent_attempts = list(reversed(recent_attempts))

    score_history = [{
        'date':     a.attempted_at.strftime('%d %b') if hasattr(a, 'attempted_at') and a.attempted_at else f'Test {i+1}',
        'score':    a.score,
        'category': a.category or 'General'
    } for i, a in enumerate(recent_attempts)]

    # Leaderboard entry for badge display
    lb_entry = Leaderboard.query.filter_by(
        user_id=current_user.id).first()
    current_badge  = lb_entry.badge if lb_entry else 'Beginner'
    tests_taken    = lb_entry.tests_taken if lb_entry else 0
    overall_avg    = round(lb_entry.total_score / tests_taken, 1) \
                     if lb_entry and tests_taken > 0 else 0

    # Latest resume score
    latest_resume = Resume.query.filter_by(
        user_id=current_user.id)\
        .order_by(Resume.uploaded_at.desc()).first()
    resume_score = latest_resume.score if latest_resume else 0

    # Unread notifications count
    notif_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).count()
        
    recent_tests = TestAttempt.query.filter_by(user_id=current_user.id).order_by(TestAttempt.attempted_at.desc()).limit(5).all()
    latest_prediction = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.predicted_at.desc()).first()
    
    test_counts = {
        'aptitude': TestAttempt.query.filter_by(user_id=current_user.id, category='aptitude').count(),
        'coding': total_attempted,
        'core': TestAttempt.query.filter_by(user_id=current_user.id, category='core').count(),
    }
    
    question_counts = {
        'aptitude': Question.query.filter_by(category='aptitude').count(),
        'coding': CodingProblem.query.count(),
        'core': Question.query.filter_by(category='core').count(),
    }
    
    # Normalize c_score for the readiness model which expects a 0-100 range.
    norm_coding = (c_score / (question_counts['coding'] * 10)) * 100 if question_counts['coding'] > 0 else c_score
    if norm_coding > 100: norm_coding = 100
    
    readiness_label = get_readiness_label(current_user.aptitude_score, norm_coding, current_user.core_score)
    
    from app.models import Company, CompanyFollow, CompanyPost, StudyTask, StudyStreak, PlacementEvent, EventApplication
    from datetime import date
    
    followed_follows = CompanyFollow.query.filter_by(user_id=current_user.id).all()
    followed_c_ids = [f.company_id for f in followed_follows]
    followed_companies = Company.query.filter(Company.id.in_(followed_c_ids)).all() if followed_c_ids else []
    
    recent_company_updates = CompanyPost.query.filter(CompanyPost.company_id.in_(followed_c_ids)).order_by(CompanyPost.created_at.desc()).limit(3).all() if followed_c_ids else []
    
    if followed_c_ids:
        recommended_companies = Company.query.filter(~Company.id.in_(followed_c_ids)).limit(3).all()
    else:
        recommended_companies = Company.query.limit(3).all()
        
    # Study Planner Context
    user_tasks = StudyTask.query.filter_by(user_id=current_user.id).all()
    planner_total = len(user_tasks)
    planner_completed = len([t for t in user_tasks if t.is_completed])
    planner_progress = (planner_completed / planner_total * 100) if planner_total > 0 else 0
    top_pending_tasks = StudyTask.query.filter_by(user_id=current_user.id, is_completed=False).order_by(StudyTask.due_date.asc().nulls_last()).limit(3).all()
    
    streak_obj = StudyStreak.query.filter_by(user_id=current_user.id).first()
    current_streak = streak_obj.current_streak if streak_obj else 0
    
    # Upcoming Drives Context
    upcoming_drives = PlacementEvent.query.filter(PlacementEvent.is_active == True, PlacementEvent.event_date >= date.today()).order_by(PlacementEvent.event_date.asc()).limit(3).all()
    applied_events = EventApplication.query.filter_by(user_id=current_user.id).all()
    total_applied = len(applied_events)
    applied_event_ids = [app.event_id for app in applied_events]
    
    return render_template('main/dashboard.html',
        aptitude_score=current_user.aptitude_score,
        coding_score=current_user.coding_score,
        core_score=current_user.core_score,
        recent_tests=recent_tests,
        latest_prediction=latest_prediction,
        test_counts=test_counts,
        question_counts=question_counts,
        readiness_label=readiness_label,
        ml_result=ml_result,
        category_scores=category_scores,
        score_history=json.dumps(score_history),
        current_badge=current_badge,
        tests_taken=tests_taken,
        overall_avg=overall_avg,
        resume_score=resume_score,
        notif_count=notif_count,
        total_solved=total_solved,
        total_attempted=total_attempted,
        accuracy=accuracy,
        recent_submissions=recent_submissions,
        dif_breakdown=dif_breakdown,
        followed_companies=followed_companies,
        recent_company_updates=recent_company_updates,
        recommended_companies=recommended_companies,
        planner_total=planner_total,
        planner_completed=planner_completed,
        planner_progress=planner_progress,
        top_pending_tasks=top_pending_tasks,
        current_streak=current_streak,
        upcoming_drives=upcoming_drives,
        total_applied=total_applied,
        applied_event_ids=applied_event_ids
    )

from flask import jsonify
from app.models import Notification

@main_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

@main_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def read_all():
    Notification.query.filter_by(
        user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'ok'})

@main_bp.route('/notifications/list')
@login_required
def notification_list():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(10).all()
    return jsonify({'notifications': [{
        'id':      n.id,
        'message': n.message,
        'type':    n.type,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%d %b, %I:%M %p')
    } for n in notifs]})
