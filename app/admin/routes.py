import os
import subprocess
import csv
import io
from flask import render_template, request, flash, redirect, url_for, abort, make_response
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.models import User, Question, Prediction, db

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard overview."""
    total_students = User.query.filter_by(role='student').count()
    total_questions = Question.query.count()
    
    # Generate data for readiness doughnut chart
    high = Prediction.query.filter_by(readiness_level='High').count()
    medium = Prediction.query.filter_by(readiness_level='Medium').count()
    low = Prediction.query.filter_by(readiness_level='Low').count()
    
    # Just an approximation if multiple predictions per user
    readiness_dist = {'High': high, 'Medium': medium, 'Low': low}
    
    return render_template('admin/dashboard.html', 
                          total_students=total_students, 
                          total_questions=total_questions,
                          readiness_dist=readiness_dist)

@admin_bp.route('/students')
@admin_required
def students():
    """Manage students."""
    students = User.query.filter_by(role='student').all()
    # attach latest prediction
    for std in students:
        pred = Prediction.query.filter_by(user_id=std.id).order_by(Prediction.predicted_at.desc()).first()
        std.latest_readiness = pred.readiness_level if pred else "Unpredicted"
        
    return render_template('admin/students.html', students=students)

@admin_bp.route('/questions')
@admin_required
def questions():
    """Manage questions."""
    category_filter = request.args.get('category')
    if category_filter:
        questions = Question.query.filter_by(category=category_filter).all()
    else:
        questions = Question.query.all()
    return render_template('admin/questions.html', questions=questions, current_category=category_filter)

@admin_bp.route('/questions/add', methods=['POST'])
@admin_required
def add_question():
    """Add a new question."""
    category = request.form.get('category')
    difficulty = request.form.get('difficulty')
    text = request.form.get('text')
    opt_a = request.form.get('option_a')
    opt_b = request.form.get('option_b')
    opt_c = request.form.get('option_c')
    opt_d = request.form.get('option_d')
    correct = request.form.get('correct_answer')
    
    if all([category, text, opt_a, opt_b, opt_c, opt_d, correct]):
        q = Question(
            category=category, difficulty=difficulty, text=text,
            option_a=opt_a, option_b=opt_b, option_c=opt_c, option_d=opt_d,
            correct_answer=correct
        )
        db.session.add(q)
        db.session.commit()
        flash('Question added successfully!', 'success')
    else:
        flash('Please fill in all required fields.', 'danger')
        
    return redirect(url_for('admin.questions'))

@admin_bp.route('/questions/delete/<int:id>', methods=['POST'])
@admin_required
def delete_question(id):
    """Delete a question."""
    # Ensure this is a POST request explicitly intended to delete
    q = Question.query.get_or_404(id)
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted successfully.', 'info')
    return redirect(url_for('admin.questions'))

@admin_bp.route('/ml/train', methods=['POST'])
@admin_required
def trigger_training():
    """Trigger the ML model retraining script."""
    try:
        # Run train_model.py script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ml', 'train_model.py')
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        if result.returncode == 0:
            flash(f"Model retrained successfully! Output: {result.stdout}", 'success')
        else:
            flash(f"Error during training: {result.stderr}", 'danger')
    except Exception as e:
        flash(f"Failed to execute training script: {str(e)}", 'danger')
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/export')
@admin_required
def export():
    """Export full dataset stringified"""
    # Simply redirects to analytics export but passing admin context
    return redirect(url_for('analytics.export'))

# --- Placement Event Admin Routes ---
from datetime import datetime

@admin_bp.route('/events/add', methods=['GET', 'POST'])
@admin_required
def add_event():
    if request.method == 'POST':
        from app.models import PlacementEvent
        company_name = request.form.get('company_name')
        custom_role = request.form.get('custom_role')
        role = request.form.get('role')
        if role == 'other' and custom_role:
            role = custom_role
            
        event_date_str = request.form.get('event_date')
        location = request.form.get('location')
        venue = request.form.get('venue', '')
        eligibility_cgpa = request.form.get('eligibility_cgpa')
        eligibility_skills = request.form.get('eligibility_skills', '')
        description = request.form.get('description', '')
        registration_link = request.form.get('registration_link', '')
        
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            if eligibility_cgpa:
                eligibility_cgpa = float(eligibility_cgpa)
            else:
                eligibility_cgpa = None
                
            event = PlacementEvent(
                company_name=company_name,
                role=role,
                event_date=event_date,
                location=location,
                venue=venue,
                eligibility_cgpa=eligibility_cgpa,
                eligibility_skills=eligibility_skills,
                description=description,
                registration_link=registration_link
            )
            db.session.add(event)
            db.session.commit()
            flash('Event added successfully!', 'success')
            return redirect(url_for('company.calendar'))
        except Exception as e:
            flash(f"Error adding event: {str(e)}", 'danger')
            
    return render_template('company/add_event.html')

@admin_bp.route('/events/delete/<int:id>', methods=['POST'])
@admin_required
def delete_event(id):
    from app.models import PlacementEvent
    event = PlacementEvent.query.get_or_404(id)
    event.is_active = False
    db.session.commit()
    flash('Event deleted/deactivated successfully.', 'info')
    return redirect(url_for('company.calendar'))
