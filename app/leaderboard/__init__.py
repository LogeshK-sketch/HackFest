from flask import Blueprint

leaderboard_bp = Blueprint('leaderboard', __name__)

from app.leaderboard import routes
