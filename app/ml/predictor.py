"""
Enhanced placement readiness predictor.
Model: RandomForestClassifier (scikit-learn)
Persisted to: app/ml/model.pkl via joblib
"""

import os, json, logging, numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')

FEATURE_NAMES = [
    'aptitude_avg',
    'coding_avg',
    'core_avg',
    'tests_taken',
    'resume_score',
    'consistency_score'
]

IMPROVEMENT_TIPS = {
    'Aptitude': [
        "Practice 20 aptitude questions daily on IndiaBix or PrepInsta.",
        "Focus on Time & Work, Percentages, and Number Series topics.",
        "Take timed mock tests to improve speed and accuracy."
    ],
    'Coding': [
        "Solve 2 DSA problems daily on LeetCode (start with Easy).",
        "Study Arrays, Strings, and Recursion fundamentals first.",
        "Practice SQL queries on HackerRank SQL track."
    ],
    'Core CS': [
        "Revise OS concepts: scheduling, memory management, deadlocks.",
        "Study DBMS: normalization, joins, transactions, indexing.",
        "Review Computer Networks: OSI model, TCP/IP, HTTP, DNS."
    ]
}

_clf = None
_le  = None

def generate_training_data():
    """
    Generate 180 synthetic training rows as (X, y).
    Rules (use numpy random with seed=42):
    """
    np.random.seed(42)
    
    # HIGH (60 rows)
    aptitude_high = np.random.uniform(70, 95, 60)
    coding_high = np.random.uniform(65, 95, 60)
    core_high = np.random.uniform(60, 95, 60)
    tests_high = np.random.randint(12, 25, 60)
    resume_high = np.random.uniform(65, 95, 60)
    consistency_high = np.random.uniform(0, 15, 60)
    
    X_high = np.column_stack((aptitude_high, coding_high, core_high, tests_high, resume_high, consistency_high))
    y_high = ['High'] * 60
    
    # MEDIUM (60 rows)
    aptitude_med = np.random.uniform(40, 70, 60)
    coding_med = np.random.uniform(35, 65, 60)
    core_med = np.random.uniform(35, 65, 60)
    tests_med = np.random.randint(5, 15, 60)
    resume_med = np.random.uniform(35, 65, 60)
    consistency_med = np.random.uniform(10, 30, 60)
    
    X_med = np.column_stack((aptitude_med, coding_med, core_med, tests_med, resume_med, consistency_med))
    y_med = ['Medium'] * 60
    
    # LOW (60 rows)
    aptitude_low = np.random.uniform(10, 40, 60)
    coding_low = np.random.uniform(10, 40, 60)
    core_low = np.random.uniform(10, 40, 60)
    tests_low = np.random.randint(0, 6, 60)
    resume_low = np.random.uniform(0, 40, 60)
    consistency_low = np.random.uniform(25, 50, 60)
    
    X_low = np.column_stack((aptitude_low, coding_low, core_low, tests_low, resume_low, consistency_low))
    y_low = ['Low'] * 60
    
    X = np.vstack((X_high, X_med, X_low))
    y = y_high + y_med + y_low
    
    return X, y

def train_model():
    """
    Train RandomForestClassifier and save to MODEL_PATH.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    import joblib
    
    X, y = generate_training_data()
    
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42)
        
    clf = RandomForestClassifier(
        n_estimators=100, random_state=42, max_depth=8)
    clf.fit(X_train, y_train)
    
    accuracy = clf.score(X_test, y_test)
    logger.info(f"Model trained. Accuracy: {accuracy:.2%}")
    
    joblib.dump({'model': clf, 'encoder': le}, MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")
    
    return clf, le

def load_model():
    """
    Load model from MODEL_PATH if it exists.
    If file missing, call train_model() first.
    Returns (clf, le) tuple.
    """
    global _clf, _le
    if _clf is not None and _le is not None:
        return _clf, _le
        
    import joblib
    if not os.path.exists(MODEL_PATH):
        _clf, _le = train_model()
    else:
        saved = joblib.load(MODEL_PATH)
        _clf = saved['model']
        _le = saved['encoder']
        
    return _clf, _le

def get_user_features(user_id: int) -> dict:
    from app.models import TestAttempt, Resume
    import numpy as np
    
    attempts = TestAttempt.query.filter_by(user_id=user_id)\
        .order_by(TestAttempt.attempted_at.asc()).all()
        
    aptitude_scores = [a.score for a in attempts
                       if a.category and 'aptitude' in a.category.lower()]
    coding_scores   = [a.score for a in attempts
                       if a.category and 'coding' in a.category.lower()]
    core_scores     = [a.score for a in attempts
                       if a.category and 'core' in a.category.lower()]
                       
    def safe_avg(lst): return round(sum(lst)/len(lst), 2) if lst else 0.0
    
    all_scores = [a.score for a in attempts]
    consistency_score = round(float(np.std(all_scores)), 2) if len(all_scores) > 1 else 0.0
    
    latest_resume = Resume.query.filter_by(user_id=user_id)\
        .order_by(Resume.uploaded_at.desc()).first()
    resume_score = latest_resume.score if latest_resume else 0
    
    return {
        'aptitude_avg':      safe_avg(aptitude_scores),
        'coding_avg':        safe_avg(coding_scores),
        'core_avg':          safe_avg(core_scores),
        'tests_taken':       len(attempts),
        'resume_score':      resume_score,
        'consistency_score': consistency_score
    }

def predict(user_id: int) -> dict:
    """
    Main prediction function called by the dashboard route.
    """
    try:
        clf, le = load_model()
        features = get_user_features(user_id)
        X = np.array([[features[f] for f in FEATURE_NAMES]])
        
        prediction_enc = clf.predict(X)[0]
        readiness = le.inverse_transform([prediction_enc])[0]
        proba = clf.predict_proba(X)[0]
        confidence = round(float(np.max(proba)) * 100, 1)
        
        weak_areas = []
        if features['aptitude_avg'] < 50: weak_areas.append('Aptitude')
        if features['coding_avg']   < 50: weak_areas.append('Coding')
        if features['core_avg']     < 50: weak_areas.append('Core CS')
        
        tips = []
        for area in weak_areas[:3]:
            tips.append(IMPROVEMENT_TIPS[area][0])
        if not tips:
            tips = ["Keep practising! Maintain your current performance."]
            
        return {
            'readiness':        readiness,
            'confidence':       confidence,
            'weak_areas':       weak_areas,
            'improvement_tips': tips,
            'features':         features
        }
    except Exception as e:
        logger.error(str(e))
        return {
            'readiness': 'Unknown', 'confidence': 0,
            'weak_areas': [], 'improvement_tips': [],
            'features': {}
        }
