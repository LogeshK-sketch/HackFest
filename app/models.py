from app.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return db.session.get(User, int(user_id))

class User(db.Model, UserMixin):
    """User model for students and admins."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    
    # Scores
    aptitude_score = db.Column(db.Float, default=0.0)
    coding_score = db.Column(db.Float, default=0.0)
    core_score = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tests = db.relationship('TestAttempt', backref='user', lazy=True)
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    tasks = db.relationship('StudyTask', backref='user', lazy=True)

class Question(db.Model):
    __tablename__ = 'question'
    id             = db.Column(db.Integer, primary_key=True)
    question_text  = db.Column(db.Text, nullable=False, unique=True)
    option_a       = db.Column(db.String(500), nullable=False)
    option_b       = db.Column(db.String(500), nullable=False)
    option_c       = db.Column(db.String(500), nullable=False)
    option_d       = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    category       = db.Column(db.String(50), nullable=False, 
                               default='aptitude')
    difficulty     = db.Column(db.String(10), nullable=False, 
                               default='medium')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

class TestAttempt(db.Model):
    """Record of a user's test attempt."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    time_taken = db.Column(db.Integer, nullable=False) # in seconds
    question_ids = db.Column(db.Text, nullable=True) # JSON string
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Prediction(db.Model):
    """Record of ML readiness prediction."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    readiness_level = db.Column(db.String(20), nullable=False) # High/Medium/Low
    confidence_score = db.Column(db.Float, nullable=False)
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class StudyTask(db.Model):
    """To-do tasks for the study planner."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
