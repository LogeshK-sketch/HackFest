from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.study import study_bp
from app.models import StudyResource, StudentStudyProgress
from app.extensions import db

@study_bp.route('/')
@login_required
def index():
    topic_filter = request.args.get('topic')
    
    query = StudyResource.query
    if topic_filter:
        query = query.filter_by(topic=topic_filter)
        
    resources = query.all()
    
    # Get completed resource IDs for the current user
    progress_records = StudentStudyProgress.query.filter_by(user_id=current_user.id).all()
    completed_ids = [p.resource_id for p in progress_records if p.completed]
    
    # Calculate progress for topics
    all_topics = db.session.query(StudyResource.topic).distinct().all()
    progress_stats = {}
    
    for t in all_topics:
        topic_name = t[0]
        topic_resources = StudyResource.query.filter_by(topic=topic_name).all()
        topic_resource_ids = [r.id for r in topic_resources]
        
        if not topic_resource_ids:
            progress_stats[topic_name] = 0
            continue
            
        completed_in_topic = len([rid for rid in completed_ids if rid in topic_resource_ids])
        progress_pct = int((completed_in_topic / len(topic_resource_ids)) * 100)
        progress_stats[topic_name] = progress_pct
    
    return render_template('study/index.html', 
                           resources=resources, 
                           completed_ids=completed_ids, 
                           topic_filter=topic_filter,
                           progress_stats=progress_stats)

@study_bp.route('/<int:resource_id>/toggle', methods=['POST'])
@login_required
def toggle_progress(resource_id):
    resource = db.session.get(StudyResource, resource_id)
    if not resource:
        return redirect(url_for('study.index'))
    
    progress = StudentStudyProgress.query.filter_by(user_id=current_user.id, resource_id=resource_id).first()
    if progress:
        progress.completed = not progress.completed
    else:
        progress = StudentStudyProgress(user_id=current_user.id, resource_id=resource_id, completed=True)
        db.session.add(progress)
        
    db.session.commit()
    return redirect(url_for('study.index'))
