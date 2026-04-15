from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.company import company_bp
from app.models import Company, CompanyPost, PostLike, PostComment, CompanyFollow, SavedCompany
from app.extensions import db

@company_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    industry = request.args.get('industry', '')
    
    query = Company.query
    if search:
        query = query.filter(Company.name.ilike(f'%{search}%'))
    if industry:
        query = query.filter_by(industry=industry)
        
    companies = query.all()
    followed_ids = [f.company_id for f in CompanyFollow.query.filter_by(user_id=current_user.id).all()]
    
    # Get distinct industries for the pill filters
    industries = [r[0] for r in db.session.query(Company.industry).distinct() if r[0]]
    
    return render_template('company/companies.html', companies=companies, followed_ids=followed_ids, industries=industries, selected_industry=industry)

@company_bp.route('/<int:company_id>')
@login_required
def profile(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('company.index'))
    
    is_following = CompanyFollow.query.filter_by(user_id=current_user.id, company_id=company_id).first() is not None
    is_saved = SavedCompany.query.filter_by(user_id=current_user.id, company_id=company_id).first() is not None
    
    posts = CompanyPost.query.filter_by(company_id=company_id).order_by(CompanyPost.created_at.desc()).all()
    liked_post_ids = [like.post_id for like in PostLike.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('company/company_profile.html', company=company, posts=posts, is_following=is_following, is_saved=is_saved, liked_post_ids=liked_post_ids)

@company_bp.route('/feed')
@login_required
def feed():
    followed_companies = CompanyFollow.query.filter_by(user_id=current_user.id).all()
    followed_ids = [fc.company_id for fc in followed_companies]
    
    posts = CompanyPost.query.filter(CompanyPost.company_id.in_(followed_ids)).order_by(CompanyPost.created_at.desc()).all() if followed_ids else []
    
    # Recommended companies
    if followed_ids:
        recommended = Company.query.filter(~Company.id.in_(followed_ids)).limit(3).all()
    else:
        recommended = Company.query.limit(3).all()
    
    liked_post_ids = [like.post_id for like in PostLike.query.filter_by(user_id=current_user.id).all()]
    followed_company_list = Company.query.filter(Company.id.in_(followed_ids)).all() if followed_ids else []

    return render_template('company/feed.html', posts=posts, recommended=recommended, liked_post_ids=liked_post_ids, followed_companies=followed_company_list)

@company_bp.route('/api/follow/<int:company_id>', methods=['POST'])
@login_required
def api_follow(company_id):
    follow = CompanyFollow.query.filter_by(user_id=current_user.id, company_id=company_id).first()
    if follow:
        db.session.delete(follow)
        following = False
    else:
        new_follow = CompanyFollow(user_id=current_user.id, company_id=company_id)
        db.session.add(new_follow)
        following = True
    db.session.commit()
    count = CompanyFollow.query.filter_by(company_id=company_id).count()
    return jsonify({'following': following, 'count': count})

@company_bp.route('/api/save/<int:company_id>', methods=['POST'])
@login_required
def api_save(company_id):
    save = SavedCompany.query.filter_by(user_id=current_user.id, company_id=company_id).first()
    if save:
        db.session.delete(save)
        saved = False
    else:
        new_save = SavedCompany(user_id=current_user.id, company_id=company_id)
        db.session.add(new_save)
        saved = True
    db.session.commit()
    return jsonify({'saved': saved})

@company_bp.route('/api/like/<int:post_id>', methods=['POST'])
@login_required
def api_like(post_id):
    like = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if like:
        db.session.delete(like)
        liked = False
    else:
        new_like = PostLike(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        liked = True
    db.session.commit()
    count = PostLike.query.filter_by(post_id=post_id).count()
    return jsonify({'liked': liked, 'count': count})

@company_bp.route('/api/comment/<int:post_id>', methods=['POST'])
@login_required
def api_comment(post_id):
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'Comment cannot be empty'}), 400
        
    comment = PostComment(post_id=post_id, user_id=current_user.id, text=text)
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'comment_id': comment.id,
        'text': comment.text,
        'author': current_user.name,
        'time': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

# --- Placement Calendar Routes ---
from datetime import date, timedelta
from itertools import groupby
from app.models import PlacementEvent, EventApplication

@company_bp.route('/calendar')
@login_required
def calendar():
    query = PlacementEvent.query.filter_by(is_active=True)
    
    company_filter = request.args.get('company')
    if company_filter:
        query = query.filter(PlacementEvent.company_name.ilike(f"%{company_filter}%"))
        
    role_filter = request.args.get('role')
    if role_filter:
        query = query.filter(PlacementEvent.role == role_filter)
        
    timeframe_filter = request.args.get('timeframe')
    if timeframe_filter == 'upcoming':
        query = query.filter(PlacementEvent.event_date >= date.today())
    elif timeframe_filter == 'past':
        query = query.filter(PlacementEvent.event_date < date.today())
        
    location_filter = request.args.get('location')
    if location_filter:
        query = query.filter(PlacementEvent.location == location_filter)
        
    events = query.order_by(PlacementEvent.event_date.asc()).all()
    
    grouped = {k: list(v) for k, v in groupby(events, key=lambda e: e.event_date)}
    
    urgent_cutoff = date.today() + timedelta(days=3)
    urgent_ids = {e.id for e in events if date.today() <= e.event_date <= urgent_cutoff}
    
    applied_ids = {a.event_id for a in EventApplication.query.filter_by(user_id=current_user.id).all()}
    
    all_roles = [r[0] for r in db.session.query(PlacementEvent.role).distinct() if r[0]]
    all_companies = [c[0] for c in db.session.query(PlacementEvent.company_name).distinct() if c[0]]
    
    return render_template('company/company_calendar.html',
                           events=events,
                           grouped=grouped,
                           urgent_ids=urgent_ids,
                           applied_ids=applied_ids,
                           all_roles=all_roles,
                           all_companies=all_companies,
                           today_date=date.today())

@company_bp.route('/calendar/event/<int:id>')
@login_required
def event_detail(id):
    event = PlacementEvent.query.get_or_404(id)
    return jsonify({
        'id': event.id,
        'company_name': event.company_name,
        'role': event.role,
        'event_date': event.event_date.strftime('%Y-%m-%d'),
        'location': event.location,
        'venue': event.venue,
        'eligibility_cgpa': event.eligibility_cgpa,
        'eligibility_skills': event.eligibility_skills,
        'description': event.description,
        'registration_link': event.registration_link
    })

@company_bp.route('/calendar/apply/<int:id>', methods=['POST'])
@login_required
def apply_event(id):
    application = EventApplication.query.filter_by(event_id=id, user_id=current_user.id).first()
    if application:
        db.session.delete(application)
        applied = False
    else:
        new_app = EventApplication(event_id=id, user_id=current_user.id)
        db.session.add(new_app)
        applied = True
    db.session.commit()
    return jsonify({'applied': applied})
