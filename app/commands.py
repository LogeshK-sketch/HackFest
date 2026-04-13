from flask import Flask
from app.extensions import db, bcrypt
from app.models import User, Question
import random

def register_commands(app: Flask):
    """Register custom CLI commands."""

    @app.cli.command('seed-db')
    def seed_db():
        """Seed the database with initial users and questions."""
        db.create_all()

        # Seed admin user
        if not User.query.filter_by(email='admin@placement.com').first():
            hashed_pw = bcrypt.generate_password_hash('Admin@123').decode('utf-8')
            admin = User(name='Admin', email='admin@placement.com', password_hash=hashed_pw, role='admin')
            db.session.add(admin)

        # Seed 5 sample students
        for i in range(1, 6):
            student_email = f'student{i}@placement.com'
            if not User.query.filter_by(email=student_email).first():
                hashed_pw = bcrypt.generate_password_hash('student123').decode('utf-8')
                student = User(
                    name=f'Student {i}',
                    email=student_email,
                    password_hash=hashed_pw,
                    role='student',
                    aptitude_score=random.randint(30, 95),
                    coding_score=random.randint(30, 95),
                    core_score=random.randint(30, 95)
                )
                db.session.add(student)

        # Seed 30 sample questions (10 per category)
        if Question.query.count() == 0:
            categories = ['aptitude', 'coding', 'core']
            for cat in categories:
                for i in range(1, 11):
                    q = Question(
                        category=cat,
                        text=f"Sample {cat.capitalize()} Question {i}?",
                        option_a=f"Option A for Q{i}",
                        option_b=f"Option B for Q{i}",
                        option_c=f"Option C for Q{i}",
                        option_d=f"Option D for Q{i}",
                        correct_answer=random.choice(['A', 'B', 'C', 'D']),
                        difficulty=random.choice(['easy', 'medium', 'hard'])
                    )
                    db.session.add(q)

        db.session.commit()
        print("Database seeded successfully with users and questions!")
