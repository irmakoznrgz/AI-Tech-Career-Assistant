import pandas as pd
import optuna
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
import warnings

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    df_train = df[df['Experience_Level'] != 'Not specified'].copy()
    df_train['Combined_Text'] = df_train['Required_Skills'].astype(str) + " " + df_train['Job_Description'].astype(str)
    
    le = LabelEncoder()
    y = le.fit_transform(df_train['Experience_Level'])
    
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    X = tfidf.fit_transform(df_train['Combined_Text'])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    return X_train, X_test, y_train, y_test

# --- 1. LightGBM Optimization ---
def lgbm_objective(trial, X_train, X_test, y_train, y_test):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'random_state': 42,
        'verbose': -1
    }
    
    model = LGBMClassifier(**params)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    return f1_score(y_test, y_pred, average='macro', zero_division=0)

# --- 2. XGBoost Optimization ---
def xgb_objective(trial, X_train, X_test, y_train, y_test):
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
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    return f1_score(y_test, y_pred, average='macro', zero_division=0)

if __name__ == "__main__":
    csv_path = "data/processed/cleaned_data.csv"
    X_train, X_test, y_train, y_test = load_and_prepare_data(csv_path)
    
    lgbm_study = optuna.create_study(direction='maximize') 
    lgbm_study.optimize(lambda trial: lgbm_objective(trial, X_train, X_test, y_train, y_test), n_trials=30)
    
    print(f"LightGBM Best F1 Score: {lgbm_study.best_value:.4f}")
    print(f"LightGBM Best Parameters: {lgbm_study.best_params}")
    
    xgb_study = optuna.create_study(direction='maximize')
    xgb_study.optimize(lambda trial: xgb_objective(trial, X_train, X_test, y_train, y_test), n_trials=30)
    
    print(f"XGBoost Best F1 Score: {xgb_study.best_value:.4f}")
    print(f"XGBoost Best Parameters: {xgb_study.best_params}")