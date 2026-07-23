import pandas as pd
import joblib
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from lightgbm import LGBMClassifier

def export_champion_model():
    df = pd.read_csv("data/processed/cleaned_data.csv")

    df_train = df[df['Experience_Level'] != 'Not specified'].copy()

    df_train.fillna('', inplace=True)

    df_train['Combined_Text'] = df_train['Required_Skills'].astype(str) + " " + df_train['Job_Description'].astype(str)
    X_raw = df_train['Combined_Text']
    y_raw = df_train['Experience_Level']
    
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    
    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler', 'nan']
    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words
    
    tfidf = TfidfVectorizer(max_features=7000, stop_words=custom_stop_words, ngram_range=(1, 2))
    X = tfidf.fit_transform(X_raw)
    
    best_params = {
        'n_estimators': 100, 
        'learning_rate': 0.043581617022279084, 'max_depth': 4, 
        'subsample': 0.8485423210969325, 'colsample_bytree': 0.716892743749649,
        'class_weight': 'balanced',
        'random_state': 42,
        'verbose': -1
    }
    
    champion_model = LGBMClassifier(**best_params)
    champion_model.fit(X, y)
    os.makedirs("models", exist_ok=True)
    
    joblib.dump(champion_model, "models/experience_model.pkl")
    joblib.dump(tfidf, "models/tfidf_vectorizer.pkl")
    joblib.dump(le, "models/label_encoder.pkl")
    
    print("\n[SUCCESSFUL] All files have been saved to the 'models/' folder! Model 1 is complete.")

if __name__ == "__main__":
    export_champion_model()