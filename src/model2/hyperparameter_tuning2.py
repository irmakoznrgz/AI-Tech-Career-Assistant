import pandas as pd
import numpy as np
import re
import optuna
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from xgboost import XGBClassifier
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

    df.fillna('', inplace=True)

    df['Combined_Text'] = df['Cleaned_Title'].astype(str) + " " + \
                          df['Required_Skills'].astype(str) + " " + \
                          df['Job_Description'].astype(str)
    
    le = LabelEncoder()
    y = le.fit_transform(df['Job_Domain'])
    
    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler', 'nan']
    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words

    tfidf = TfidfVectorizer(max_features=7000, stop_words=custom_stop_words, ngram_range=(1, 2))
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

    model = LGBMClassifier(**params)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring='f1_macro', n_jobs=-1)
    
    return scores.mean()
    
# --- 2. XGBoost Optimization ---
def xgb_objective(trial, X, y):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'eval_metric': 'mlogloss',
        'random_state': 42
    }
    
    model = XGBClassifier(**params)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring='f1_macro', n_jobs=-1)
    
    return scores.mean()

if __name__ == "__main__":
    filepath = "data/processed/labeled_domain_data.csv"
    X, y = load_and_prepare_data(filepath)
    
    lgbm_study = optuna.create_study(direction='maximize')
    lgbm_study.optimize(lambda trial: lgbm_objective(trial, X, y), n_trials=20)
    
    print(f"LightGBM Best F1 Score: {lgbm_study.best_value:.4f}")
    print(f"LightGBM Best Parameters: {lgbm_study.best_params}")
    
    xgb_study = optuna.create_study(direction='maximize')
    xgb_study.optimize(lambda trial: xgb_objective(trial, X, y), n_trials=20)
    
    print(f"\nXGBoost Best F1 Score: {xgb_study.best_value:.4f}")
    print(f"XGBoost Best Parameters: {xgb_study.best_params}")