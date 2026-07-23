import pandas as pd
import time
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score,precision_score, recall_score, f1_score, classification_report
from sklearn.metrics import log_loss, roc_auc_score
import warnings

warnings.filterwarnings('ignore')


def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    
    df_train = df[df['Experience_Level'] != 'Not specified'].copy()
    df_train.fillna('', inplace=True)

    print(f"Number of suitable job postings for training: {len(df_train)}")
    
    df_train['Combined_Text'] = df_train['Required_Skills'].astype(str) + " " + df_train['Job_Description'].astype(str)
    
    X_raw = df_train['Combined_Text']
    y_raw = df_train['Experience_Level']
    
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    
    print("Class matches:", dict(zip(le.classes_, le.transform(le.classes_))))

    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler', 'nan']
    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words
    
    tfidf = TfidfVectorizer(max_features=7000, stop_words=custom_stop_words, ngram_range=(1, 2))
    X = tfidf.fit_transform(X_raw)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    return X_train, X_test, y_train, y_test, le, tfidf

def train_and_evaluate_models(X_train, X_test, y_train, y_test, label_encoder):
    target_names = label_encoder.classes_

    models = {
        "Naive Bayes (Multinomial)": MultinomialNB(),

        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),

        "Linear SVC (Calibrated)": CalibratedClassifierCV(LinearSVC(random_state=42, dual=False), method='sigmoid', cv=3),

        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),

        "XGBoost": XGBClassifier(eval_metric='mlogloss', random_state=42),

        "LightGBM": LGBMClassifier(random_state=42, verbose=-1, class_weight='balanced'),

        "CatBoost": CatBoostClassifier(verbose=0, random_state=42, allow_writing_files=False, auto_class_weights='Balanced')
    }
    
    results = {}

    print("="*50)
    print("THE ALGORITHM COMPETITION BEGINS...")
    print("="*50)

    for name, model in models.items():
        print(f"-> {name} is being trained...")

        start_time = time.time()
        model.fit(X_train, y_train)
        training_time = time.time() - start_time

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)
        
        acc = accuracy_score(y_test, y_pred)

        prec = precision_score(y_test, y_pred, average='macro', zero_division=0)

        rec = recall_score(y_test, y_pred, average='macro', zero_division=0)

        f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)

        loss = log_loss(y_test, y_prob)

        roc_auc = roc_auc_score(y_test, y_prob, multi_class='ovr', average='macro')

        results[name] = {
            'Accuracy': acc, 
            'F1-Score': f1,
            'Log-Loss': loss,
            'ROC-AUC': roc_auc,
            'Time (s)': training_time}

        print(f"   Time: {training_time:.2f} seconds")
        print(f"   Accuracy: {acc * 100:.2f}%")
        print(f"   Precision: {prec:.3f}")
        print(f"   Recall: {rec:.3f}")
        print(f"   F1-Score: {f1:.3f}")
        print(f"   Log-Loss: {loss:.3f}")
        print(f"   ROC-AUC: {roc_auc:.3f}")

    sorted_results = sorted(results.items(), key=lambda x: x[1]['F1-Score'], reverse=True)

    top_2_names = [sorted_results[0][0], sorted_results[1][0]]
    
    print("="*50)
    print("FINAL ALGORITHMS")
    print("="*50)

    top_2_models = {}
    for i, name in enumerate(top_2_names, 1):
        metrics = results[name]
        top_2_models[name] = models[name]
        print(f"{i}. {name}")
        print(f"   PERFORMANCE -> F1: {metrics['F1-Score']:.3f} | ROC-AUC: {metrics['ROC-AUC']:.3f} | Acc: {metrics['Accuracy']*100:.2f}% | Log-Loss: {metrics['Log-Loss']:.3f}")
        
        y_pred_finalist = models[name].predict(X_test)
        print(f"\n [{name}] Champion Models Class-wise Performance:")
        print(classification_report(y_test, y_pred_finalist, target_names=target_names))
        print("-" * 50)
    
    return top_2_models

if __name__ == "__main__":
    csv_path = "data/processed/cleaned_data.csv"
    
    X_train, X_test, y_train, y_test, label_encoder, tfidf_vectorizer = load_and_prepare_data(csv_path)
    
    top_2_models = train_and_evaluate_models(X_train, X_test, y_train, y_test, label_encoder)
