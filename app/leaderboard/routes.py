from app.leaderboard import leaderboard_bp

@leaderboard_bp.route('/')
def index():
    return "Leaderboard Blueprint"
