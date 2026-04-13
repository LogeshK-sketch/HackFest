from app.coding import coding_bp

@coding_bp.route('/')
def index():
    return "Coding Blueprint"
