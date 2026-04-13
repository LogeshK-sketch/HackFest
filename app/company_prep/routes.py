from app.company_prep import company_prep_bp

@company_prep_bp.route('/')
def index():
    return "Company Prep Blueprint"
