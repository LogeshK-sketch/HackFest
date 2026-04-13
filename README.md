# Smart Placement Preparation & Guidance System

A complete, production-ready Flask web application to assess students, provide ML-driven readiness predictions, and offer personalized study recommendations.

## Features
- **Student & Admin Roles**: Role-based access control with Flask-Login.
- **Assessments**: Timed 15-minute assessments in Aptitude, Coding, and Core Subjects.
- **Machine Learning Integration**: Predicts placement readiness (High/Medium/Low) using a Random Forest model trained on synthetic student data.
- **Recommendations Engine**: Suggest topics and study resources based on weak performing areas.
- **Study Planner**: Add, view, and complete tasks with an AJAX-powered to-do list.
- **Analytics & Export**: Visual dashboards using Chart.js, and CSV export for Power BI integration.
- **Admin Dashboard**: Manage users and questions, generate reports, and retrain ML models.

## Technologies Used
- Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt
- Scikit-learn, Pandas, Numpy, Joblib
- Bootstrap 5, Chart.js

## Run Instructions

Follow these step-by-step instructions to run the application locally:

### 1. Clone + Create Virtual Environment
```bash
# Clone the repository (if not already local)
# git clone <repository-url>
cd HackFest

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize the Database
This application uses a custom Flask CLI command to seed the database, which also automates the creation of the SQL tables.
```bash
flask seed-db
```
*(This command runs `db.create_all()` and inserts seed data including the admin account, sample students, and 30 sample questions).*

### 4. Train the ML Model
Generate the synthetic dataset (500 records) and train the Scikit-Learn models.
```bash
python ml/train_model.py
```
*(This will save `model.pkl` and `label_encoder.pkl` in the `ml/` directory).*

### 5. Run the Application
```bash
flask run
```

### 6. Access the App
Open your browser and navigate to: http://127.0.0.1:5000/

### Default Credentials
- **Admin User**: `admin@placement.com` | Password: `Admin@123`
- **Student User**: `student1@placement.com` | Password: `student123` (up to student5)
