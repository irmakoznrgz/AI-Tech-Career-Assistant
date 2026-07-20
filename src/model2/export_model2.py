import pandas as pd
import re
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from lightgbm import LGBMClassifier
import warnings

warnings.filterwarnings('ignore')

def clean_seniority_words(text):
    text = str(text).lower()
    pattern = r'\b(senior|junior|mid-level|mid|lead|Middle|Leader|manager|Part time|Working|student|intern|Kıdemli|stajyer|uzman|specialist)\b'
    text = re.sub(pattern, '', text)
    return " ".join(text.split())

def export_final_model():
    filepath = "data/processed/labeled_domain_data.csv"
    df = pd.read_csv(filepath)
    
    df['Cleaned_Title'] = df['Job_Title'].apply(clean_seniority_words)
    df['Combined_Text'] = df['Cleaned_Title'].astype(str) + " " + \
                          df['Required_Skills'].astype(str) + " " + \
                          df['Job_Description'].astype(str)
    le = LabelEncoder()
    y = le.fit_transform(df['Job_Domain'])

    tfidf = TfidfVectorizer(max_features=7000, stop_words='english')
    X = tfidf.fit_transform(df['Combined_Text'])
    
    best_params = {
        'max_depth': 6, 
        'n_estimators': 700, 
        'learning_rate': 0.014598046257479147, 
        'num_leaves': 35, 
        'min_child_samples': 36, 
        'subsample': 0.6375098575982161, 
        'colsample_bytree': 0.694426954320492,
        'class_weight': 'balanced',
        'random_state': 42,
        'verbose': -1
    }
    
    model = LGBMClassifier(**best_params)
    model.fit(X, y)
   
    joblib.dump(model, 'models/domain_model.pkl')
    joblib.dump(tfidf, 'models/domain_tfidf_vectorizer.pkl')
    joblib.dump(le, 'models/domain_label_encoder.pkl')

if __name__ == "__main__":
    export_final_model()