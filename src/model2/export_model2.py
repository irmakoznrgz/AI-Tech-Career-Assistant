import pandas as pd
import re
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
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
    
    df['Cleaned_Title'] = df['Job_Title'].fillna('').apply(clean_seniority_words)
    df['Combined_Text'] = df['Cleaned_Title'].astype(str) + " " + \
                          df['Required_Skills'].fillna('').astype(str) + " " + \
                          df['Job_Description'].fillna('').astype(str)
    le = LabelEncoder()
    y = le.fit_transform(df['Job_Domain'])

    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler', 'nan']

    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words

    tfidf = TfidfVectorizer(max_features=7000, stop_words=custom_stop_words, ngram_range=(1, 2))
    X = tfidf.fit_transform(df['Combined_Text'])
    
    best_params = {
        'max_depth': 11, 
        'n_estimators': 600, 
        'learning_rate': 0.03023277130991129, 
        'num_leaves': 1636, 
        'min_child_samples': 21, 
        'subsample': 0.8056965579865885, 
        'colsample_bytree': 0.8490213766408257,
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