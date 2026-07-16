import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def generate_synthetic_data(num_records=10000):
    """Generates synthetic appointment data for modeling."""
    np.random.seed(42)
    
    # Features
    booking_lead_time = np.random.exponential(scale=7, size=num_records) # Days in advance
    previous_no_shows = np.random.poisson(lam=0.5, size=num_records)
    is_new_patient = np.random.choice([0, 1], p=[0.7, 0.3], size=num_records)
    reminder_sent = np.random.choice([0, 1], p=[0.2, 0.8], size=num_records)
    department_id = np.random.choice([1, 2, 3, 4, 5], size=num_records)
    distance_category = np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2], size=num_records) # 1=Close, 3=Far
    day_of_week = np.random.choice([0, 1, 2, 3, 4, 5, 6], size=num_records)
    
    df = pd.DataFrame({
        'lead_time_days': booking_lead_time,
        'previous_no_shows': previous_no_shows,
        'is_new_patient': is_new_patient,
        'reminder_sent': reminder_sent,
        'department_id': department_id,
        'distance_category': distance_category,
        'day_of_week': day_of_week
    })
    
    # Generate Target: No-show probability
    # Higher risk for: long lead times, past no-shows, new patients, no reminders, far distance, weekends
    base_risk = 0.05
    risk = base_risk + \
           (df['lead_time_days'] * 0.005) + \
           (df['previous_no_shows'] * 0.15) + \
           (df['is_new_patient'] * 0.05) - \
           (df['reminder_sent'] * 0.08) + \
           (df['distance_category'] * 0.02) + \
           (df['day_of_week'].isin([5, 6]) * 0.05)
           
    risk = np.clip(risk, 0, 1)
    
    # Sample actual outcomes based on probability
    df['is_no_show'] = np.random.binomial(1, risk)
    
    return df

def train_and_evaluate_model(df):
    """Trains a Logistic Regression and Random Forest model to predict no-shows."""
    print("--- Healthcare Operations: No-Show Prediction Model ---")
    
    # Prepare data
    X = df.drop('is_no_show', axis=1)
    y = df['is_no_show']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Dataset Size: {len(df)} records.")
    print(f"Overall No-Show Rate: {y.mean():.2%}\n")
    
    # 1. Logistic Regression
    print("--- Model: Logistic Regression ---")
    lr_model = LogisticRegression(max_iter=1000)
    lr_model.fit(X_train, y_train)
    lr_preds = lr_model.predict(X_test)
    lr_probs = lr_model.predict_proba(X_test)[:, 1]
    
    print("Classification Report:")
    print(classification_report(y_test, lr_preds))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, lr_probs):.4f}\n")
    
    # Feature Importance (Logistic Regression Coefficients)
    feature_importance_lr = pd.DataFrame({
        'Feature': X.columns,
        'Coefficient': lr_model.coef_[0]
    }).sort_values(by='Coefficient', ascending=False)
    print("Logistic Regression - Top Influential Features:")
    print(feature_importance_lr.to_string(index=False))
    print("\n")
    
    # 2. Random Forest
    print("--- Model: Random Forest ---")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_probs = rf_model.predict_proba(X_test)[:, 1]
    
    print("Classification Report:")
    print(classification_report(y_test, rf_preds))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, rf_probs):.4f}\n")
    
    # Feature Importance (Random Forest)
    feature_importance_rf = pd.DataFrame({
        'Feature': X.columns,
        'Importance': rf_model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    print("Random Forest - Feature Importance:")
    print(feature_importance_rf.to_string(index=False))
    
    # Decision Support Recommendation
    print("\n--- Operational Decision Support ---")
    print("Based on model insights:")
    print("1. Action: Implement automated 24hr reminders for appointments booked > 14 days in advance.")
    print("2. Action: Flag patients with >1 previous no-shows and require confirmation via SMS.")
    print("3. Action: Double-book highly likely no-show slots (probability > 80%) to maximize doctor utilization.")

if __name__ == "__main__":
    df = generate_synthetic_data()
    train_and_evaluate_model(df)
