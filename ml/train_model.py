import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score

def generate_synthetic_data(num_samples=500):
    """Generate synthetic student records."""
    np.random.seed(42)
    
    # Generate features
    aptitude = np.clip(np.random.normal(65, 15, num_samples), 0, 100)
    coding = np.clip(np.random.normal(60, 20, num_samples), 0, 100)
    core = np.clip(np.random.normal(70, 15, num_samples), 0, 100)
    
    # Calculate weighted average
    weighted_avg = 0.4 * aptitude + 0.4 * coding + 0.2 * core
    
    # Add some noise to the weighted average before classification
    noise = np.random.normal(0, 5, num_samples)
    final_score = weighted_avg + noise
    
    # Generate labels
    labels = []
    for score in final_score:
        if score >= 70:
            labels.append('High')
        elif score >= 40:
            labels.append('Medium')
        else:
            labels.append('Low')
            
    # Create DataFrame
    df = pd.DataFrame({
        'aptitude_score': aptitude,
        'coding_score': coding,
        'core_score': core,
        'readiness_level': labels
    })
    
    return df

def train_and_save_model():
    """Train ML models and save the best one."""
    print("Generating synthetic data (500 records)...")
    df = generate_synthetic_data(500)
    
    X = df[['aptitude_score', 'coding_score', 'core_score']]
    y = df['readiness_level']
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
    
    print("Training Logistic Regression (Baseline)...")
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    print(f"Logistic Regression Accuracy: {accuracy_score(y_test, lr_preds):.4f}")
    
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_preds)
    print(f"Random Forest Accuracy: {rf_acc:.4f}")
    print("\nClassification Report (Random Forest):")
    print(classification_report(y_test, rf_preds, target_names=le.classes_))
    
    # Ensure ml directory exists
    ml_dir = os.path.dirname(__file__)
    if not os.path.exists(ml_dir):
        os.makedirs(ml_dir)
        
    model_path = os.path.join(ml_dir, 'model.pkl')
    encoder_path = os.path.join(ml_dir, 'label_encoder.pkl')
    
    # Save the better model (usually Random Forest for this)
    joblib.dump(rf, model_path)
    joblib.dump(le, encoder_path)
    print(f"Model saved to {model_path}")
    print(f"Label encoder saved to {encoder_path}")

if __name__ == '__main__':
    train_and_save_model()
