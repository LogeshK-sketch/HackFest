from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp
from app.models import TestAttempt, Prediction

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
        
    recent_tests = TestAttempt.query.filter_by(user_id=current_user.id).order_by(TestAttempt.attempted_at.desc()).limit(5).all()
    latest_prediction = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.predicted_at.desc()).first()
    
    return render_template('main/dashboard.html', recent_tests=recent_tests, latest_prediction=latest_prediction)
