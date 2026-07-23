import pandas as pd
import optuna
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics import f1_score
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
import warnings

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)

    df_train = df[df['Experience_Level'] != 'Not specified'].copy()

    df_train.fillna('', inplace=True)

    df_train['Combined_Text'] = df_train['Required_Skills'].astype(str) + " " + df_train['Job_Description'].astype(str)
    
    le = LabelEncoder()
    y = le.fit_transform(df_train['Experience_Level'])

    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler', 'nan']
    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words
    
    tfidf = TfidfVectorizer(max_features=7000, stop_words=custom_stop_words, ngram_range=(1, 2))
    X = tfidf.fit_transform(df_train['Combined_Text'])
    
    return X, y

# --- 1. LightGBM Optimization  ---
def lgbm_objective(trial, X, y):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
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
        'n_estimators': trial.suggest_int('n_estimators', 100, 500, step=100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 8),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'eval_metric': 'mlogloss',
        'random_state': 42,
        'n_jobs': 1
    }
    
    model = XGBClassifier(**params)

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring='f1_macro', n_jobs=-1)
    
    return scores.mean()

if __name__ == "__main__":
    csv_path = "data/processed/cleaned_data.csv"
    X, y = load_and_prepare_data(csv_path)
    
    lgbm_study = optuna.create_study(direction='maximize')
    lgbm_study.optimize(lambda trial: lgbm_objective(trial, X, y), n_trials=20)

    print(f"LightGBM Best F1 Score: {lgbm_study.best_value:.4f}")

    print(f"LightGBM Best Parameters: {lgbm_study.best_params}")
    
    xgb_study = optuna.create_study(direction='maximize')
    xgb_study.optimize(lambda trial: xgb_objective(trial, X, y), n_trials=20)
    
    print(f"XGBoost Best F1 Score: {xgb_study.best_value:.4f}")
    print(f"XGBoost Best Parameters: {xgb_study.best_params}")