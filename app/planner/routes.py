from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.planner import planner_bp
from app.models import StudyTask, StudyStreak, db
from datetime import datetime, timedelta, date

def get_category_label(score):
    if score < 50: return "WEAK"
    if score <= 70: return "MODERATE"
    return "STRONG"

def generate_suggestions(user):
    suggestions = []
    
    apt = get_category_label(user.aptitude_score)
    cod = get_category_label(user.coding_score)
    cor = get_category_label(user.core_score)
    
    if cod == "WEAK":
        suggestions.append("Solve 2 LeetCode Easy problems today.")
    if apt == "WEAK":
        suggestions.append("Practice 20 aptitude questions on IndiaBix.")
    if cor == "WEAK":
        suggestions.append("Read one OS/DBMS chapter and summarize.")
        
    return suggestions

@planner_bp.route('/generate', methods=['POST'])
@login_required
def generate_study_plan():
    """Generates a study plan based on user scores."""
    
    # Classify
    apt = get_category_label(current_user.aptitude_score)
    cod = get_category_label(current_user.coding_score)
    cor = get_category_label(current_user.core_score)
    
    # Delete existing pending tasks
    StudyTask.query.filter_by(user_id=current_user.id, is_completed=False).delete()
    
    tasks_to_add = []
    
    # Mappings
    if apt == "WEAK":
        tasks_to_add.extend([
            ("Quantitative Aptitude – Percentages & Ratios", "aptitude", "Easy"),
            ("Quantitative Aptitude – Time, Speed & Distance", "aptitude", "Easy"),
            ("Logical Reasoning – Puzzles", "aptitude", "Medium"),
            ("Logical Reasoning – Syllogisms", "aptitude", "Medium")
        ])
    elif apt == "MODERATE":
        tasks_to_add.extend([
            ("Quantitative Aptitude – Permutation & Combination", "aptitude", "Medium"),
            ("Logical Reasoning – Data Interpretation", "aptitude", "Medium")
        ])
        
    if cod == "WEAK":
        tasks_to_add.extend([
            ("Arrays – Basics & Traversal", "coding", "Easy"),
            ("Strings – Manipulation Problems", "coding", "Easy"),
            ("Basic DSA – Sorting Algorithms", "coding", "Easy"),
            ("Basic DSA – Recursion", "coding", "Medium")
        ])
    elif cod == "MODERATE":
        tasks_to_add.extend([
            ("Linked Lists – Reversal & Merge", "coding", "Medium"),
            ("Binary Search – Practice Problems", "coding", "Medium")
        ])
        
    if cor == "WEAK":
        tasks_to_add.extend([
            ("DBMS – Normalization & ER Model", "core", "Easy"),
            ("DBMS – SQL Queries Practice", "core", "Easy"),
            ("OS – Process Scheduling", "core", "Medium"),
            ("CN – OSI Model & TCP/IP", "core", "Easy")
        ])
    elif cor == "MODERATE":
        tasks_to_add.extend([
            ("OS – Memory Management", "core", "Medium"),
            ("CN – Routing Protocols", "core", "Medium")
        ])
        
    # Cap at 10 prioritizing WEAK first (already appended sequentially)
    tasks_to_add = tasks_to_add[:10]
    
    # Bulk create
    now = datetime.utcnow()
    for i, t in enumerate(tasks_to_add):
        task = StudyTask(
            user_id=current_user.id,
            title=t[0],
            category=t[1],
            difficulty=t[2],
            due_date=now + timedelta(days=i+1)
        )
        db.session.add(task)
        
    db.session.commit()
    flash('Study Plan generated correctly!', 'success')
    return redirect(url_for('planner.study_plan'))

@planner_bp.route('/study_plan')
@login_required
def study_plan():
    """Display the detailed study plan UI with suggestions."""
    tasks = StudyTask.query.filter_by(user_id=current_user.id).order_by(StudyTask.due_date.asc().nulls_last()).all()
    suggestions = generate_suggestions(current_user)
    
    total = len(tasks)
    completed = len([t for t in tasks if t.is_completed])
    progress = (completed / total * 100) if total > 0 else 0
    
    # Categorize tasks
    aptitude_tasks = [t for t in tasks if t.category == 'aptitude']
    coding_tasks = [t for t in tasks if t.category == 'coding']
    core_tasks = [t for t in tasks if t.category == 'core']
    
    return render_template('planner/study_plan.html', 
        tasks=tasks, 
        suggestions=suggestions,
        progress=progress,
        completed=completed,
        total=total,
        aptitude_tasks=aptitude_tasks,
        coding_tasks=coding_tasks,
        core_tasks=core_tasks
    )

@planner_bp.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle completion status and handle study streak."""
    task = StudyTask.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
        
    task.is_completed = not task.is_completed
    db.session.commit()
    
    if task.is_completed:
        # User completed a task. Update valid streak logic.
        streak = StudyStreak.query.filter_by(user_id=current_user.id).first()
        if not streak:
            streak = StudyStreak(user_id=current_user.id, current_streak=0, longest_streak=0)
            db.session.add(streak)
            
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if streak.last_completed_date == yesterday:
            streak.current_streak += 1
        elif streak.last_completed_date != today:
            streak.current_streak = 1
            
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
            
        streak.last_completed_date = today
        db.session.commit()
        
    return jsonify({'success': True, 'is_completed': task.is_completed})

@planner_bp.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = StudyTask.query.filter_by(id=task_id, user_id=current_user.id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404
