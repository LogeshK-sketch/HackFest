import os
import joblib
import pandas as pd
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.ml import ml_bp
from app.models import Prediction, db

def get_model():
    """Load the trained machine learning model."""
    try:
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ml', 'model.pkl')
        encoder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ml', 'label_encoder.pkl')
        model = joblib.load(model_path)
        le = joblib.load(encoder_path)
        return model, le
    except FileNotFoundError:
        return None, None

@ml_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    """Run ML prediction on current user scores."""
    model, le = get_model()
    if not model or not le:
        flash('Model is not trained yet. Please ask admin to train the model first.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    # Prepare data for prediction
    features = pd.DataFrame([{
        'aptitude_score': current_user.aptitude_score,
        'coding_score': current_user.coding_score,
        'core_score': current_user.core_score
    }])
    
    # Predict
    pred_encoded = model.predict(features)[0]
    pred_label = le.inverse_transform([pred_encoded])[0]
    
    # Confidence score (probability of the predicted class)
    probabilities = model.predict_proba(features)[0]
    confidence = max(probabilities) * 100
    
    # Save the prediction
    prediction = Prediction(
        user_id=current_user.id,
        readiness_level=pred_label,
        confidence_score=confidence
    )
    db.session.add(prediction)
    db.session.commit()
    
    flash(f'Readiness Prediction Complete: {pred_label} with {confidence:.2f}% confidence.', 'info')
    return render_template('ml/prediction.html', prediction=prediction)

@ml_bp.route('/history')
@login_required
def history():
    """View past predictions."""
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.predicted_at.desc()).all()
    return render_template('ml/history.html', predictions=predictions)

@ml_bp.route('/recommendations')
@login_required
def recommendations():
    """Rule-based Recommendation Engine."""
    recommendations = []
    
    if current_user.aptitude_score < 50:
        recommendations.append({
            'area': 'Aptitude Weakness Detected',
            'topics': ['Quantitative Aptitude', 'Logical Reasoning', 'Data Interpretation'],
            'resources': ['Prep India - Aptitude', 'GeeksForGeeks - Aptitude']
        })
    if current_user.coding_score < 50:
        recommendations.append({
            'area': 'Coding Weakness Detected',
            'topics': ['DSA', 'Problem Solving', 'OOP Concepts', 'SQL'],
            'resources': ['LeetCode', 'HackerRank Problem Solving']
        })
    if current_user.core_score < 50:
        recommendations.append({
            'area': 'Core Subjects Weakness Detected',
            'topics': ['OS', 'DBMS', 'Computer Networks', 'System Design'],
            'resources': ['GateSmasher Playlists', 'TutorialsPoint CS']
        })
        
    if not recommendations:
        if sum([current_user.aptitude_score, current_user.coding_score, current_user.core_score]) == 0:
            recommendations.append({
                'area': 'No Assessments Taken',
                'topics': ['Start by taking assessments to get personalized recommendations.'],
                'resources': []
            })
        else:
            recommendations.append({
                'area': 'Excellent Performance!',
                'topics': ['Advanced System Design', 'Competitive Programming Phase 2'],
                'resources': ['System Design Interview by Alex Xu', 'Codeforces']
            })
            
    return render_template('ml/recommendations.html', recommendations=recommendations)
