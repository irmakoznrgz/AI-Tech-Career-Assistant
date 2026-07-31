import pandas as pd
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
import umap
import hdbscan
import warnings

warnings.filterwarnings('ignore')

def clean_seniority_words(text):
    text = str(text).lower()

    pattern = r'\b(senior|junior|mid-level|mid|lead|Middle|Leader|manager|Part time|Working|student|intern|Kıdemli|stajyer|uzman|specialist)\b'

    text = re.sub(pattern, '', text)

    return " ".join(text.split())

def export_final_model3():
    filepath = "data/processed/cleaned_data.csv"
    df = pd.read_csv(filepath)
    
    df['Cleaned_Title'] = df['Job_Title'].apply(clean_seniority_words)
    df['Combined_Text'] = df['Cleaned_Title'].fillna('').astype(str) + " " + \
                          df['Required_Skills'].fillna('').astype(str) + " " + \
                          df['Job_Description'].fillna('').astype(str)
    
    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'nan', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler']
    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words
    
    tfidf = TfidfVectorizer(max_features=10000, stop_words=custom_stop_words)
    X_tfidf = tfidf.fit_transform(df['Combined_Text'])
    
    reducer = umap.UMAP(n_neighbors=15, n_components=2, metric='cosine', random_state=42)
    X_umap = reducer.fit_transform(X_tfidf)
  
    best_mcs = 15
    best_ms = 15
    clusterer = hdbscan.HDBSCAN(min_cluster_size=best_mcs, min_samples=best_ms, metric='euclidean', prediction_data=True)
    clusterer.fit(X_umap)
    
    joblib.dump(tfidf, 'models/model3_tfidf.pkl')
    joblib.dump(reducer, 'models/model3_umap.pkl')
    joblib.dump(clusterer, 'models/model3_hdbscan.pkl')
    
if __name__ == "__main__":
    export_final_model3()




    