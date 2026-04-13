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
        
    # MODIFIED: Calculate category scores using utils
    current_user.aptitude_score = get_category_score(current_user.id, 'aptitude')
    current_user.coding_score = get_category_score(current_user.id, 'coding')
    current_user.core_score = get_category_score(current_user.id, 'core')
    db.session.commit()
    
    recent_tests = TestAttempt.query.filter_by(user_id=current_user.id).order_by(TestAttempt.attempted_at.desc()).limit(5).all()
    latest_prediction = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.predicted_at.desc()).first()
    
    test_counts = {
        'aptitude': TestAttempt.query.filter_by(user_id=current_user.id, category='aptitude').count(),
        'coding': TestAttempt.query.filter_by(user_id=current_user.id, category='coding').count(),
        'core': TestAttempt.query.filter_by(user_id=current_user.id, category='core').count(),
    }
    
    question_counts = {
        'aptitude': Question.query.filter_by(category='aptitude').count(),
        'coding': Question.query.filter_by(category='coding').count(),
        'core': Question.query.filter_by(category='core').count(),
    }
    
    readiness_label = get_readiness_label(current_user.aptitude_score, current_user.coding_score, current_user.core_score)
    
    return render_template('main/dashboard.html',
        aptitude_score=current_user.aptitude_score,
        coding_score=current_user.coding_score,
        core_score=current_user.core_score,
        recent_tests=recent_tests,
        latest_prediction=latest_prediction,
        test_counts=test_counts,
        question_counts=question_counts,
        readiness_label=readiness_label
    )
