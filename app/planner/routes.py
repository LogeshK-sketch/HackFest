from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.planner import planner_bp
from app.models import StudyTask, db
from datetime import datetime

@planner_bp.route('/')
@login_required
def index():
    """Display the study planner."""
    filter_by = request.args.get('filter', 'all')
    
    query = StudyTask.query.filter_by(user_id=current_user.id)
    if filter_by == 'pending':
        query = query.filter_by(is_completed=False)
    elif filter_by == 'completed':
        query = query.filter_by(is_completed=True)
        
    tasks = query.order_by(StudyTask.due_date.asc().nulls_last()).all()
    
    # Calculate progress
    all_tasks_count = StudyTask.query.filter_by(user_id=current_user.id).count()
    completed_count = StudyTask.query.filter_by(user_id=current_user.id, is_completed=True).count()
    progress = (completed_count / all_tasks_count * 100) if all_tasks_count > 0 else 0
    
    return render_template('planner/index.html', tasks=tasks, current_filter=filter_by, progress=progress)

@planner_bp.route('/add-task', methods=['POST'])
@login_required
def add_task():
    """Add a new study task."""
    title = request.form.get('title')
    description = request.form.get('description')
    due_date_str = request.form.get('due_date')
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            pass
            
    if title:
        task = StudyTask(
            user_id=current_user.id,
            title=title,
            description=description,
            due_date=due_date
        )
        db.session.add(task)
        db.session.commit()
        flash('Task added successfully!', 'success')
    else:
        flash('Task title is required.', 'danger')
        
    return redirect(url_for('planner.index'))

@planner_bp.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle completion status via AJAX."""
    task = StudyTask.query.filter_by(id=task_id, user_id=current_user.id).first()
    if task:
        task.is_completed = not task.is_completed
        db.session.commit()
        return jsonify({'success': True, 'is_completed': task.is_completed})
    return jsonify({'success': False, 'error': 'Task not found'}), 404
