import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    
    df_train = df[df['Experience_Level'] != 'Not specified'].copy()
    print(f"Number of suitable job postings for training: {len(df_train)}")
    
    df_train['Combined_Text'] = df_train['Required_Skills'].astype(str) + " " + df_train['Job_Description'].astype(str)
    
    X_raw = df_train['Combined_Text']
    y_raw = df_train['Experience_Level']
    
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    
    print("Class matches:", dict(zip(le.classes_, le.transform(le.classes_))))
    
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    X = tfidf.fit_transform(X_raw)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    return X_train, X_test, y_train, y_test, le, tfidf

def train_and_evaluate_models(X_train, X_test, y_train, y_test, label_encoder):
    target_names = label_encoder.classes_

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Linear SVC (SVM)": LinearSVC(random_state=42, dual=False),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)
    }
    
    results = {}

    print("\n=======================================================")
    print("THE ALGORITHM COMPETITION BEGINS...")
    print("=======================================================\n")

    for name, model in models.items():
        print(f"-> {name} is being trained...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        results[name] = acc
        print(f"   Accuracy: {acc * 100:.2f}%\n")

        best_model_name = max(results, key=results.get)
    print("=======================================================")
    print(f"🏆 CHAMPION MODEL: {best_model_name} (Accuracy: {results[best_model_name] * 100:.2f}%)")
    print("=======================================================")

    print("\nChampion Model's Class-wise Performance:")
    best_model = models[best_model_name]
    y_pred_best = best_model.predict(X_test)
    print(classification_report(y_test, y_pred_best, target_names=target_names))
    
    return best_model, best_model_name

if __name__ == "__main__":
    csv_path = "data/processed/cleaned_data.csv"
    
    X_train, X_test, y_train, y_test, label_encoder, tfidf_vectorizer = load_and_prepare_data(csv_path)
    
    best_model, best_name = train_and_evaluate_models(X_train, X_test, y_train, y_test, label_encoder)
