import pandas as pd
import numpy as np
import optuna
import re
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from lightgbm import LGBMClassifier
from sklearn.metrics import f1_score
import warnings

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

def clean_seniority_words(text):
    text = str(text).lower()
    pattern = r'\b(senior|junior|mid-level|mid|lead|Middle|Leader|manager|Part time|Working|student|intern|Kıdemli|stajyer|uzman|specialist)\b'
    text = re.sub(pattern, '', text)

    return " ".join(text.split())

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    df['Cleaned_Title'] = df['Job_Title'].apply(clean_seniority_words)
    df['Combined_Text'] = df['Cleaned_Title'].astype(str) + " " + \
                          df['Required_Skills'].astype(str) + " " + \
                          df['Job_Description'].astype(str)
    
    le = LabelEncoder()
    y = le.fit_transform(df['Job_Domain'])
    
    tfidf = TfidfVectorizer(max_features=7000, stop_words='english')
    X = tfidf.fit_transform(df['Combined_Text'])

    return X, y

# --- 1. LightGBM Optimization ---
def lgbm_objective(trial, X, y):
    max_depth = trial.suggest_int('max_depth', 3, 12)
    max_leaves = (2 ** max_depth) - 1
    min_leaves = min(20, max_leaves)

    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'max_depth': max_depth,
        'num_leaves': trial.suggest_int('num_leaves', min_leaves, min(max_leaves, 3000)),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'class_weight': 'balanced',
        'random_state': 42,
        'verbose': -1
    }

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = []

    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        model = LGBMClassifier(**params)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        
        cv_scores.append(f1_score(y_val, y_pred, average='macro', zero_division=0))

        return np.mean(cv_scores)
    
# --- 2. Linear SVC Optimization ---
def svc_objective(trial, X, y):
    c_val = trial.suggest_float('C', 0.001, 10.0, log=True)

    tol_val = trial.suggest_float('tol', 1e-5, 1e-1, log=True)
    
    base_svc = LinearSVC(C=c_val, tol=tol_val, class_weight='balanced', random_state=42, dual=False)
    model = CalibratedClassifierCV(base_svc, method='sigmoid', cv=3)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = []

    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        
        cv_scores.append(f1_score(y_val, y_pred, average='macro', zero_division=0))
        
    return np.mean(cv_scores)

if __name__ == "__main__":
    filepath = "data/processed/labeled_domain_data.csv"
    X, y = load_and_prepare_data(filepath)
    
    lgbm_study = optuna.create_study(direction='maximize')
    lgbm_study.optimize(lambda trial: lgbm_objective(trial, X, y), n_trials=30)
    
    print(f"LightGBM Best F1 Score: {lgbm_study.best_value:.4f}")
    print(f"LightGBM Best Parameters: {lgbm_study.best_params}")
    
    svc_study = optuna.create_study(direction='maximize')
    svc_study.optimize(lambda trial: svc_objective(trial, X, y), n_trials=30)
    
    print(f"Linear SVC Best F1 Score: {svc_study.best_value:.4f}")
    print(f"Linear SVC Best Parameters: {svc_study.best_params}")