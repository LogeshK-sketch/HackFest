import os
from flask import Flask, render_template
from dotenv import load_dotenv

from app.config import DevelopmentConfig, ProductionConfig
from app.extensions import db, login_manager, bcrypt, migrate

# Load environment variables
load_dotenv()

def create_app(config_class=DevelopmentConfig):
    """Flask application factory."""
    app = Flask(__name__)
    
    import os
    app.config.setdefault('UPLOAD_FOLDER', 'uploads/resumes')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    

    # Configure app based on FLASK_ENV
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.assessment.routes import assessment_bp
    from app.ml.routes import ml_bp
    from app.planner.routes import planner_bp
    from app.analytics.routes import analytics_bp
    from app.admin.routes import admin_bp
    from app.resume.routes import resume_bp
    from app.company_prep.routes import company_prep_bp
    from app.leaderboard.routes import leaderboard_bp
    from app.coding.routes import coding_bp
    

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp) # Includes dashboard, mapped to /
    app.register_blueprint(assessment_bp, url_prefix='/assessment')
    app.register_blueprint(ml_bp, url_prefix='/ml')
    app.register_blueprint(planner_bp, url_prefix='/planner')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(resume_bp, url_prefix='/resume')
    app.register_blueprint(company_prep_bp, url_prefix='/company_prep')
    app.register_blueprint(leaderboard_bp, url_prefix='/leaderboard')
    app.register_blueprint(coding_bp, url_prefix='/coding')

    # Register custom CLI commands
    from app.cli import cli_bp
    app.register_blueprint(cli_bp)

    # ADDED IMPORT: format_seconds filter
    from app.utils import format_seconds
    app.jinja_env.filters['format_seconds'] = format_seconds

    # Error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
