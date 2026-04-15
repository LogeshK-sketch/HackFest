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
    category = db.Column(db.String(50), nullable=True)
    difficulty = db.Column(db.String(20), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudyStreak(db.Model):
    """Tracks daily study streaks."""
    __tablename__ = 'study_streak'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_completed_date = db.Column(db.Date, nullable=True)

class Resume(db.Model):
    __tablename__ = 'resume'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at   = db.Column(db.DateTime, default=datetime.utcnow)
    filename      = db.Column(db.String(200))
    score         = db.Column(db.Integer, default=0)
    extracted_skills = db.Column(db.Text)   # JSON list
    missing_skills   = db.Column(db.Text)   # JSON list
    suggestions      = db.Column(db.Text)   # JSON list
    projects_detected = db.Column(db.Text)  # JSON list
    experience_level  = db.Column(db.String(50))

class Company(db.Model):
    __tablename__ = 'company'
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), nullable=False)
    description     = db.Column(db.Text)
    industry        = db.Column(db.String(50))
    hiring_roles    = db.Column(db.String(200)) # comma-sep
    required_skills = db.Column(db.String(300)) # comma-sep
    package_range   = db.Column(db.String(50))
    logo_url        = db.Column(db.String(300))
    website         = db.Column(db.String(200))
    headquarters    = db.Column(db.String(100))
    hiring_process  = db.Column(db.String(500)) # pipe-sep
    prep_topics     = db.Column(db.String(500)) # pipe-sep

class CompanyPost(db.Model):
    __tablename__ = 'company_post'
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    post_type   = db.Column(db.String(50)) # experience/tip/question
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    
    company = db.relationship('Company', backref='posts')
    user = db.relationship('User', backref='company_posts')

class PostLike(db.Model):
    __tablename__ = 'post_like'
    id          = db.Column(db.Integer, primary_key=True)
    post_id     = db.Column(db.Integer, db.ForeignKey('company_post.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id'),)

class PostComment(db.Model):
    __tablename__ = 'post_comment'
    id          = db.Column(db.Integer, primary_key=True)
    post_id     = db.Column(db.Integer, db.ForeignKey('company_post.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text        = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('CompanyPost', backref='comments')
    user = db.relationship('User')

class CompanyFollow(db.Model):
    __tablename__ = 'company_follow'
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('company_id', 'user_id'),)

class SavedCompany(db.Model):
    __tablename__ = 'saved_company'
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('company_id', 'user_id'),)

class PlacementEvent(db.Model):
    __tablename__ = 'placement_events'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(50), nullable=False)
    venue = db.Column(db.String(200), nullable=True)
    eligibility_cgpa = db.Column(db.Float, nullable=True)
    eligibility_skills = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
    registration_link = db.Column(db.String(300), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventApplication(db.Model):
    __tablename__ = 'event_applications'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('placement_events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='applied')
    
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='_event_user_uc'),)
    
    event = db.relationship('PlacementEvent', backref=db.backref('applications', lazy=True))
    user = db.relationship('User', backref=db.backref('event_applications', lazy=True))

class CompanyQuestion(db.Model):
    __tablename__ = 'company_question'
    id         = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    question   = db.Column(db.Text, nullable=False)
    answer     = db.Column(db.Text)
    difficulty = db.Column(db.String(10))
    category   = db.Column(db.String(50))

class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    total_score  = db.Column(db.Integer, default=0)
    tests_taken  = db.Column(db.Integer, default=0)
    badge        = db.Column(db.String(20), default='Beginner')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    user         = db.relationship('User', backref='leaderboard_entry')

class Notification(db.Model):
    __tablename__ = 'notification'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'))
    message    = db.Column(db.Text)
    is_read    = db.Column(db.Boolean, default=False)
    type       = db.Column(db.String(30))  # info/warning/success
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class StudyResource(db.Model):
    __tablename__ = 'study_resource'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(50)) 
    url = db.Column(db.String(300))

class StudentStudyProgress(db.Model):
    __tablename__ = 'student_study_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('study_resource.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    resource = db.relationship('StudyResource')

class CodingProblem(db.Model):
    __tablename__ = 'coding_problem'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    input_format = db.Column(db.Text)
    output_format = db.Column(db.Text)
    constraints = db.Column(db.Text)
    sample_input = db.Column(db.Text)
    sample_output = db.Column(db.Text)
    explanation = db.Column(db.Text)
    test_cases = db.Column(db.Text) # JSON field mapping
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Submission(db.Model):
    __tablename__ = 'submission'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('coding_problem.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(30), default='python')
    result = db.Column(db.String(20))
    execution_time = db.Column(db.Float)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    problem = db.relationship('CodingProblem', backref='submissions')
