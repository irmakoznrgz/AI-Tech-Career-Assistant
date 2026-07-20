import pandas as pd
import joblib
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from lightgbm import LGBMClassifier

def export_champion_model():
    df = pd.read_csv("data/processed/cleaned_data.csv")
    df_train = df[df['Experience_Level'] != 'Not specified'].copy()
    
    df_train['Combined_Text'] = df_train['Required_Skills'].astype(str) + " " + df_train['Job_Description'].astype(str)
    X_raw = df_train['Combined_Text']
    y_raw = df_train['Experience_Level']
    
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    X = tfidf.fit_transform(X_raw)
    
    best_params = {
        'n_estimators': 400, 
        'learning_rate': 0.07325655640104782, 
        'max_depth': 6, 
        'subsample': 0.8135212784498054, 
        'colsample_bytree': 0.8120899556307981,
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