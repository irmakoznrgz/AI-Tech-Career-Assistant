import pandas as pd
import numpy as np
import re
import optuna
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from lightgbm import LGBMClassifier
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
import warnings

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

def clean_seniority_words(text):
    text = str(text).lower()
    pattern = r'\b(senior|junior|mid-level|mid|lead|middle|leader|manager|part time|working|student|intern|kıdemli|stajyer|uzman|specialist)\b'
    text = re.sub(pattern, '', text)
    return " ".join(text.split())

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    df['Cleaned_Title'] = df['Job_Title'].apply(clean_seniority_words)
    df.fillna('', inplace=True)

    df['Combined_Text'] = df['Cleaned_Title'].astype(str) + " " + \
                          df['Required_Skills'].astype(str) + " " + \
                          df['Job_Description'].astype(str)
    
    le = LabelEncoder()
    y = le.fit_transform(df['Job_Domain'])
    
    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler', 'nan']
    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words

    tfidf = TfidfVectorizer(max_features=10000, stop_words=custom_stop_words, ngram_range=(1, 2))
    X = tfidf.fit_transform(df['Combined_Text'])
    return X, y

# --- 1. LightGBM Optimization ---
def lgbm_objective(trial, X, y):
    max_depth = trial.suggest_int('max_depth', 3, 12)
    max_leaves = (2 ** max_depth) - 1
    min_leaves = min(20, max_leaves)

    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 800, step=100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
        'max_depth': max_depth,
        'num_leaves': trial.suggest_int('num_leaves', min_leaves, min(max_leaves, 2048)),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
        'subsample': trial.suggest_float('subsample', 0.7, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 1.0),
        'class_weight': 'balanced',
        'random_state': 42,
        'verbose': -1
    }

    model = LGBMClassifier(**params)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring='f1_macro', n_jobs=-1)
    return scores.mean()

# --- 2. Linear SVC Optimization ---
def svc_objective(trial, X, y):
    params = {
        'C': trial.suggest_float('C', 0.01, 10.0, log=True),
        'penalty': 'l2',
        'loss': 'squared_hinge',
        'tol': trial.suggest_float('tol', 1e-5, 1e-2, log=True),
        'class_weight': 'balanced',
        'max_iter': 2000,
        'random_state': 42
    }
    
    model = LinearSVC(**params)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring='f1_macro', n_jobs=-1)
    return scores.mean()

if __name__ == "__main__":
    filepath = "data/processed/labeled_domain_data.csv"
    X, y = load_and_prepare_data(filepath)
    
    print("="*50)
    print("HYPERPARAMETER OPTIMIZATION STARTED...")
    print("="*50)

    # 1. LightGBM 
    print("\n-> Optimizing LightGBM...")
    lgbm_study = optuna.create_study(direction='maximize')
    lgbm_study.optimize(lambda trial: lgbm_objective(trial, X, y), n_trials=20)
    print(f"Best LightGBM F1: {lgbm_study.best_value:.4f}")
    print(f"Best Params: {lgbm_study.best_params}")
    
    # 2. Linear SVC
    print("\n-> Optimizing Linear SVC...")
    svc_study = optuna.create_study(direction='maximize')
    svc_study.optimize(lambda trial: svc_objective(trial, X, y), n_trials=30)
    print(f"Best Linear SVC F1: {svc_study.best_value:.4f}")
    print(f"Best Params: {svc_study.best_params}")
    
    
    
    