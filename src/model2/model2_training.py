import pandas as pd
import re
import time
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, log_loss, roc_auc_score, classification_report
import warnings

warnings.filterwarnings('ignore')

def clean_seniority_words(text):
    text = str(text).lower()
    pattern = r'\b(senior|junior|mid-level|mid|lead|Middle|Leader|manager|Part time|Working|student|intern|Kıdemli|stajyer|uzman|specialist)\b'
    text = re.sub(pattern, '', text)

    return " ".join(text.split())

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    
    df['Cleaned_Title'] = df['Job_Title'].fillna('').apply(clean_seniority_words)
    
    df['Combined_Text'] = df['Cleaned_Title'].astype(str) + " " + \
                          df['Required_Skills'].astype(str) + " " + \
                          df['Job_Description'].astype(str)
    
    le = LabelEncoder()
    y = le.fit_transform(df['Job_Domain'])
    
    print("Category Matches:", dict(zip(le.classes_, le.transform(le.classes_))))

    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler', 'nan']
    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words

    tfidf = TfidfVectorizer(max_features=7000, stop_words=custom_stop_words, ngram_range=(1, 2))
    X = tfidf.fit_transform(df['Combined_Text'])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    return X_train, X_test, y_train, y_test, le

def train_domain_models(X_train, X_test, y_train, y_test, label_encoder):
    target_names = label_encoder.classes_
    
    svc_base = LinearSVC(random_state=42, dual=False, class_weight='balanced')
    calibrated_svc = CalibratedClassifierCV(svc_base, method='sigmoid', cv=3)

    models = {
        "Naive Bayes": MultinomialNB(),

        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),

        "Linear SVC": calibrated_svc,

        "XGBoost": XGBClassifier(eval_metric='mlogloss', random_state=42),

        "LightGBM": LGBMClassifier(random_state=42, verbose=-1, class_weight='balanced')
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
            'Precision': prec,
            'Recall': rec,
            'F1-Score': f1,
            'Log-Loss': loss,
            'ROC-AUC': roc_auc,
            'Time': training_time
        }
        
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
    
    for i, name in enumerate(top_2_names, 1):
        metrics = results[name]
        print(f"{i}. {name}")
        print(f"   PERFORMANCE -> F1: {metrics['F1-Score']:.3f} | ROC-AUC: {metrics['ROC-AUC']:.3f} | Acc: {metrics['Accuracy']*100:.2f}% | Log-Loss: {metrics['Log-Loss']:.3f}")
        
        best_model = models[name]
        y_pred_finalist = best_model.predict(X_test)
        print(f"\n [{name}] Champion Models Class-wise Performance:")

        report_dict = classification_report(y_test, y_pred_finalist, target_names=target_names, zero_division=0, output_dict=True)
        report_df = pd.DataFrame(report_dict).transpose()
        report_df['support'] = report_df['support'].astype(int)
        print(report_df.round(3).to_string())

if __name__ == "__main__":
    filepath = "data/processed/labeled_domain_data.csv"
    X_train, X_test, y_train, y_test, le = load_and_prepare_data(filepath)
    train_domain_models(X_train, X_test, y_train, y_test, le)