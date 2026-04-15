from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import Leaderboard, User
from app.extensions import db

leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/leaderboard')

@leaderboard_bp.route('/')
@login_required
def index():
    rows = db.session.query(Leaderboard, User)\
        .join(User, Leaderboard.user_id == User.id)\
        .order_by(Leaderboard.total_score.desc())\
        .limit(50).all()

    entries = []
    for rank, (lb, user) in enumerate(rows, start=1):
        initials = ''.join(w[0].upper() for w in user.name.split()[:2])
        entries.append({
            'rank':        rank,
            'username':    user.name,
            'initials':    initials,
            'total_score': lb.total_score,
            'tests_taken': lb.tests_taken,
            'badge':       lb.badge,
            'last_updated': lb.last_updated.strftime('%d %b %Y') if lb.last_updated else '-'
        })

    current_rank = next((e['rank'] for e in entries if e['username'] == current_user.name), None)

    return render_template('leaderboard/index.html', entries=entries, current_rank=current_rank, current_username=current_user.name)

@leaderboard_bp.route('/api')
@login_required
def api():
    rows = db.session.query(Leaderboard, User)\
        .join(User, Leaderboard.user_id == User.id)\
        .order_by(Leaderboard.total_score.desc())\
        .limit(50).all()

    entries = []
    for rank, (lb, user) in enumerate(rows, start=1):
        initials = ''.join(w[0].upper() for w in user.name.split()[:2])
        entries.append({
            'rank':        rank,
            'username':    user.name,
            'initials':    initials,
            'total_score': lb.total_score,
            'tests_taken': lb.tests_taken,
            'badge':       lb.badge,
            'last_updated': lb.last_updated.strftime('%d %b %Y') if lb.last_updated else '-'
        })

    current_rank = next((e['rank'] for e in entries if e['username'] == current_user.name), None)
    
    return jsonify({'entries': entries, 'current_rank': current_rank}), 200
