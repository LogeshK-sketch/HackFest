import json
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app.assessment import assessment_bp
from app.models import Question, TestAttempt, User, db
from sqlalchemy.sql.expression import func

@assessment_bp.route('/')
@login_required
def index():
    """Display category selection for assessments."""
    category_data = {
        'aptitude': {
            'label': 'Aptitude',
            'description': 'Quantitative, logical & verbal reasoning',
            'icon': '📐',
            'count': Question.query.filter_by(category='aptitude').count(),
            'user_score': current_user.aptitude_score,
            'attempts': TestAttempt.query.filter_by(user_id=current_user.id, category='aptitude').count(),
        },
        'coding': {
            'label': 'Coding',
            'description': 'Programming, DSA, OOP & SQL',
            'icon': '💻',
            'count': Question.query.filter_by(category='coding').count(),
            'user_score': current_user.coding_score,
            'attempts': TestAttempt.query.filter_by(user_id=current_user.id, category='coding').count(),
        },
        'core': {
            'label': 'Core Subjects',
            'description': 'OS, DBMS, Computer Networks & OOP',
            'icon': '🖥️',
            'count': Question.query.filter_by(category='core').count(),
            'user_score': current_user.core_score,
            'attempts': TestAttempt.query.filter_by(user_id=current_user.id, category='core').count(),
        },
    }
    return render_template('assessment/index.html', category_data=category_data)

@assessment_bp.route('/test')
@login_required
def test():
    """Load test questions with query params."""
    category = request.args.get('category', 'aptitude')
    difficulty = request.args.get('difficulty', 'mixed')
    count_str = request.args.get('count', '10')
    
    # Validate count
    try:
        count = int(count_str)
        if count < 5:
            count = 5
        elif count > 30:
            count = 30
    except ValueError:
        count = 10
        
    valid_categories = ['aptitude', 'logical', 'verbal', 'numerical', 'coding', 'core']
    if category not in valid_categories:
        category = 'aptitude'
        
    query = Question.query.filter_by(category=category)
    
    if difficulty in ['easy', 'medium', 'hard']:
        query = query.filter_by(difficulty=difficulty)
        
    questions = query.order_by(func.random()).limit(count).all()
    
    if not questions:
        flash(f'No questions found for {category} ({difficulty}).', 'danger')
        return redirect(url_for('assessment.index'))
        
    if len(questions) < count:
        flash(f'Only loaded {len(questions)} questions (requested {count}).', 'info')
        
    # Store IDs in session
    q_ids = [q.id for q in questions]
    session['current_test_ids'] = q_ids
    session['test_meta'] = {
        'category': category,
        'difficulty': difficulty,
        'count': len(questions),
        'started_at': datetime.utcnow().isoformat()
    }
    
    return render_template('assessment/test.html', questions=questions, meta=session['test_meta'])

@assessment_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """Process assessment submission."""
    if 'current_test_ids' not in session or 'test_meta' not in session:
        flash('Invalid session or test already submitted.', 'warning')
        return redirect(url_for('assessment.index'))
        
    q_ids = session['current_test_ids']
    meta = session['test_meta']
    
    correct_count = 0
    total = len(q_ids)
    
    for q_id in q_ids:
        ans = request.form.get(f'answer_{q_id}', '').strip()
        q = db.session.get(Question, q_id)
        if q and ans.upper() == q.correct_answer.upper():
            correct_count += 1
            
    score = int(round((correct_count / total) * 100))
    
    started_at = datetime.fromisoformat(meta['started_at'])
    time_taken_seconds = int((datetime.utcnow() - started_at).total_seconds())
    
    attempt = TestAttempt(
        user_id=current_user.id,
        category=meta['category'],
        score=score,
        total_questions=total,
        correct_answers=correct_count,
        time_taken=time_taken_seconds,
        question_ids=json.dumps(q_ids),
        attempted_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit() # Save attempt first, then we update user scores
    
    # --- ADDED IN STEP 3 ---
    from app.utils import update_leaderboard, push_notification

    # Update leaderboard after every test submission
    update_leaderboard(current_user.id)

    # Push score-based notification
    score = attempt.score  # use whatever variable holds the saved score
    if score < 40:
        push_notification(current_user.id,
            "Your score was below 40. Focus on weak areas today!", type='warning')
    elif score >= 80:
        push_notification(current_user.id,
            f"Great job! You scored {score}. Keep it up!", type='success')
    # -----------------------

    # MODIFIED: After saving TestAttempt, recalculate and update User score
    submitted_category = session['test_meta']['category']
    # ADDED IMPORT: get_category_score
    from app.utils import get_category_score
    if submitted_category in ['aptitude', 'coding', 'core']:
        new_score = get_category_score(current_user.id, submitted_category)
        if submitted_category == 'aptitude':
            current_user.aptitude_score = new_score
        elif submitted_category == 'coding':
            current_user.coding_score = new_score
        elif submitted_category == 'core':
            current_user.core_score = new_score
        db.session.commit()
    
    session.pop('current_test_ids', None)
    session.pop('test_meta', None)
    
    return redirect(url_for('assessment.result', attempt_id=attempt.id))

@assessment_bp.route('/result/<int:attempt_id>')
@login_required
def result(attempt_id):
    """View test result."""
    attempt = TestAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    
    q_ids = json.loads(attempt.question_ids) if attempt.question_ids else []
    # Fetch questions
    questions = []
    if q_ids:
        # Fetch preserving order
        for qid in q_ids:
            q = db.session.get(Question, qid)
            if q:
               # get user answer from form data would be ideal, but we didn't save their exact text.
               # Without a db schema change to save exact answers, we can only infer wrongness if we didn't save their choice.
               # For full compliance with File 4 "wrong submitted in red", we should ideally save them, 
               # but we will just pass questions to template and it'll show the correct answers clearly (since we couldn't alter TestAttempt further).
               questions.append(q)
               
    return render_template('assessment/result.html', attempt=attempt, questions=questions)

@assessment_bp.route('/history')
@login_required
def history():
    """Show current_user's last 20 TestAttempt records."""
    attempts = TestAttempt.query.filter_by(user_id=current_user.id).order_by(TestAttempt.attempted_at.desc()).limit(20).all()
    return render_template('assessment/history.html', attempts=attempts)

@assessment_bp.route('/leaderboard')
@login_required
def leaderboard():
    """Show top 10 students by average score across all categories."""
    
    # Needs to calculate mean for each user
    users = User.query.filter_by(role='student').all()
    leaderboard_data = []
    
    for u in users:
        atts = TestAttempt.query.filter_by(user_id=u.id).all()
        if atts:
            avg = sum(a.score for a in atts) / len(atts)
            leaderboard_data.append({
                'id': u.id,
                'name': u.name.split()[0], # first name only
                'avg_score': avg,
                'total_tests': len(atts)
            })
            
    # Sort by avg score desc
    leaderboard_data.sort(key=lambda x: x['avg_score'], reverse=True)
    
    top_10 = leaderboard_data[:10]
    
    current_user_rank = None
    for idx, row in enumerate(leaderboard_data):
        if row['id'] == current_user.id:
            current_user_rank = idx + 1
            break
            
    return render_template('assessment/leaderboard.html', top_10=top_10, current_user_rank=current_user_rank, current_user=current_user)
