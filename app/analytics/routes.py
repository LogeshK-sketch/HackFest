import csv
import io
from flask import render_template, make_response, request
from flask_login import login_required, current_user
from app.analytics import analytics_bp
from app.models import User, TestAttempt, Prediction

@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    """View personal analytics dashboard."""
    # Data for the bar chart
    scores = {
        'Aptitude': current_user.aptitude_score,
        'Coding': current_user.coding_score,
        'Core': current_user.core_score
    }
    
    # Data for the line chart (last 5 tests)
    recent_tests = TestAttempt.query.filter_by(user_id=current_user.id).order_by(TestAttempt.attempted_at.desc()).limit(5).all()
    test_history = [{
        'date': t.attempted_at.strftime('%m-%d'),
        'score': t.score,
        'category': t.category
    } for t in reversed(recent_tests)]
    
    return render_template('analytics/dashboard.html', scores=scores, test_history=test_history)

@analytics_bp.route('/export')
@login_required
def export():
    """Export analytics to CSV. Admin exports all, student exports themselves."""
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['student_name', 'email', 'aptitude_score', 'coding_score', 'core_score', 'readiness_level', 'total_tests'])
    
    if current_user.role == 'admin':
        level_filter = request.args.get('level')
        users_query = User.query.filter_by(role='student')
        
        users = users_query.all()
    else:
        users = [current_user]
        
    for user in users:
        # Get latest prediction
        latest_pred = Prediction.query.filter_by(user_id=user.id).order_by(Prediction.predicted_at.desc()).first()
        readiness = latest_pred.readiness_level if latest_pred else 'N/A'
        
        # Apply admin filter logic in py
        if current_user.role == 'admin' and level_filter and readiness != level_filter:
            continue
            
        total_tests = len(user.tests)
        cw.writerow([
            user.name, user.email, 
            user.aptitude_score, user.coding_score, user.core_score,
            readiness, total_tests
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=student_performance.csv"
    output.headers["Content-type"] = "text/csv"
    return output
