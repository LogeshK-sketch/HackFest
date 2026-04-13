from flask import render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app.assessment import assessment_bp
from app.models import Question, TestAttempt, db
from sqlalchemy.sql.expression import func

@assessment_bp.route('/')
@login_required
def index():
    """Display category selection for assessments."""
    return render_template('assessment/select.html')

@assessment_bp.route('/test/<category>')
@login_required
def test(category):
    """Load test questions for a specific category."""
    if category not in ['aptitude', 'coding', 'core']:
        flash('Invalid assessment category selected.', 'danger')
        return redirect(url_for('assessment.index'))
    
    # Load 10 random questions
    questions = Question.query.filter_by(category=category).order_by(func.random()).limit(10).all()
    if not questions:
        flash('No questions available in this category yet.', 'warning')
        return redirect(url_for('assessment.index'))
        
    # Store order of question IDs to verify later
    session[f'{category}_questions'] = [q.id for q in questions]
    
    return render_template('assessment/test.html', category=category, questions=questions)

@assessment_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """Process assessment submission."""
    category = request.form.get('category')
    question_ids = session.get(f'{category}_questions', [])
    
    if not question_ids:
        flash('Invalid session. Please restart your test.', 'danger')
        return redirect(url_for('assessment.index'))
        
    correct_count = 0
    total_count = len(question_ids)
    
    for q_id in question_ids:
        answer = request.form.get(f'q_{q_id}')
        question = db.session.get(Question, q_id)
        if question and answer and question.correct_answer.upper() == answer.upper():
            correct_count += 1
            
    score_percentage = (correct_count / total_count) * 100
    
    # Update user score logic (simplistic: taking the latest score)
    if category == 'aptitude':
        current_user.aptitude_score = score_percentage
    elif category == 'coding':
        current_user.coding_score = score_percentage
    elif category == 'core':
        current_user.core_score = score_percentage
        
    # Save the attempt
    time_taken = request.form.get('time_taken', 0) # in seconds (from JS)
    try:
        time_taken = int(time_taken)
    except ValueError:
        time_taken = 0
        
    attempt = TestAttempt(
        user_id=current_user.id,
        category=category,
        score=score_percentage,
        total_questions=total_count,
        time_taken=time_taken
    )
    db.session.add(attempt)
    db.session.commit()
    
    session.pop(f'{category}_questions', None)
    
    flash(f'Test completed! You scored {correct_count}/{total_count}.', 'success')
    return redirect(url_for('assessment.result', id=attempt.id))

@assessment_bp.route('/result/<int:id>')
@login_required
def result(id):
    """View test result."""
    attempt = TestAttempt.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('assessment/result.html', attempt=attempt)
