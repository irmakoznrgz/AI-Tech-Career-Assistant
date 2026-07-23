import pandas as pd
import json
import joblib
import re
import hdbscan
import warnings

warnings.filterwarnings('ignore')

class AITechCareerPredictor:
    def __init__(self, model_dir='models/'):
        self.model_dir = model_dir
        self.models_loaded = False
        self._load_models()

    def _load_models(self):
        
        try:
            # Model 1: Experience Level
            self.exp_model = joblib.load(f'{self.model_dir}experience_model.pkl')
            self.exp_tfidf = joblib.load(f'{self.model_dir}tfidf_vectorizer.pkl')
            self.exp_le = joblib.load(f'{self.model_dir}label_encoder.pkl')

            # Model 2: Job Domain 
            self.domain_model = joblib.load(f'{self.model_dir}domain_model.pkl')
            self.domain_tfidf = joblib.load(f'{self.model_dir}domain_tfidf_vectorizer.pkl')
            self.domain_le = joblib.load(f'{self.model_dir}domain_label_encoder.pkl')

            try:
                # Model 3: Similarity & Clustering (HDBSCAN & UMAP)
                self.cluster_hdbscan = joblib.load(f'{self.model_dir}model3_hdbscan.pkl')
                self.cluster_umap = joblib.load(f'{self.model_dir}model3_umap.pkl')
                self.cluster_tfidf = joblib.load(f'{self.model_dir}model3_tfidf.pkl')
                self.model3_available = True
            except FileNotFoundError:
                print("Warning: Model 3 files could not be found.")
                self.model3_available = False

            self.models_loaded = True
            print("All models were successfully uploaded.")

        except FileNotFoundError as e:
            print(f"Model1 and Model2 files could not be found! {e}")
            self.models_loaded = False


    def _clean_text(self, text):
        if not text or pd.isna(text):
            return ""

        text = str(text).lower()
    
        pattern = r'\b(senior|junior|mid-level|mid|lead|middle|leader|manager|part time|working|student|intern|kıdemli|stajyer|uzman|specialist)\b'

        text = re.sub(pattern, '', text)

        return " ".join(text.split())

    def analyze_job_posting(self, job_title="", required_skills="", job_description=""):

        if not self.models_loaded:
            return {"Error": "Predictions cannot be made because the models could not be loaded."}
    
        cleaned_title = self._clean_text(job_title)
        combined_text = f"{cleaned_title} {required_skills} {job_description}"
        
        # (Model 1)
        exp_features = self.exp_tfidf.transform([combined_text])
        exp_pred_encoded = self.exp_model.predict(exp_features)
        exp_prediction = self.exp_le.inverse_transform(exp_pred_encoded)[0]
        exp_confidence = max(self.exp_model.predict_proba(exp_features)[0])
        
        # (Model 2)
        domain_features = self.domain_tfidf.transform([combined_text])
        domain_pred_encoded = self.domain_model.predict(domain_features)
        domain_prediction = self.domain_le.inverse_transform(domain_pred_encoded)[0]
        domain_confidence = max(self.domain_model.predict_proba(domain_features)[0])
        
        response = {
            "Input": {
                "Title": job_title
            },
            "Predictions": {
                "Experience_Level": {
                    "Level": exp_prediction,
                    "Confidence": round(exp_confidence * 100, 2)
                },
                "Job_Domain": {
                    "Domain": domain_prediction,
                    "Confidence": round(domain_confidence * 100, 2)
                },
                "Cluster_Map":None
            }
        }

         # (Model 3)
        if self.model3_available:

            try:
                cluster_features = self.cluster_tfidf.transform([combined_text])
                umap_coords = self.cluster_umap.transform(cluster_features)

                cluster_labels, cluster_strengths = hdbscan.approximate_predict(self.cluster_hdbscan, umap_coords)
                cluster_id = int(cluster_labels[0])
        

                response["Predictions"]["Cluster_Map"] = {
                "Cluster_ID": cluster_id,
                "Coordinates": {"X": round(float(umap_coords[0][0]), 4), "Y": round(float(umap_coords[0][1]), 4)}
            }

            except Exception as e:
                print(f"Warning: Model 3 prediction failed: {e}")
                response["Predictions"]["Cluster_Map"] = {
                    "Cluster_ID": -1,
                    "Coordinates": {"X": 0.0, "Y": 0.0}
                }
        return response

if __name__ == "__main__":
     
    predictor = AITechCareerPredictor()
    
    # TEST
    test_title = "Data Scientist"
    test_skills = "Python, SQL, Machine Learning, Deep Learning, Pandas, Scikit-Learn"
    test_desc = "We are looking for someone to build predictive models and analyze large datasets. Must be an expert in Python."
    
    results = predictor.analyze_job_posting(test_title, test_skills, test_desc)
    
    print(json.dumps(results, indent=4, ensure_ascii=False))