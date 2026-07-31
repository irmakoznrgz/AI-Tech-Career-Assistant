import pandas as pd
import json
import joblib
import re
import hdbscan
import os
from tqdm import tqdm
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

        raw_combined_text = f"{job_title} {required_skills} {job_description}"
    
        cleaned_title = self._clean_text(job_title)
        cleaned_combined_text = f"{cleaned_title} {required_skills} {job_description}"
        
        # (Model 1)
        exp_features = self.exp_tfidf.transform([raw_combined_text])
        exp_pred_encoded = self.exp_model.predict(exp_features)
        exp_prediction = self.exp_le.inverse_transform(exp_pred_encoded)[0]
        exp_confidence = max(self.exp_model.predict_proba(exp_features)[0])
        
        # (Model 2)
        domain_features = self.domain_tfidf.transform([cleaned_combined_text])
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
                cluster_features = self.cluster_tfidf.transform([cleaned_combined_text])
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

    def process_entire_dataset(self, input_csv="data/processed/cleaned_data.csv", output_csv="data/processed/predicted_data.csv"):
        if not os.path.exists(input_csv):
            print(f"[ERROR] Input dataset not found at: {input_csv}")
            return False

        print(f"\n-> Reading dataset from {input_csv}...")
        df = pd.read_csv(input_csv)
        
        if df.empty:
            print("[WARNING] Dataset is empty.")
            return False

        print(f"-> Running AI predictions for {len(df)} job postings (Models 1, 2, 3)...")
        
        exp_levels = []
        domains = []
        cluster_ids = []
        coord_xs = []
        coord_ys = []

        for _, row in tqdm(df.iterrows(), total=len(df), desc="Predicting"):
            title = str(row.get('Job_Title', ''))
            skills = str(row.get('Required_Skills', ''))
            desc = str(row.get('Job_Description', ''))

            res = self.analyze_job_posting(job_title=title, required_skills=skills, job_description=desc)
            preds = res.get("Predictions", {})
            
            exp_levels.append(preds.get("Experience_Level", {}).get("Level", "Not specified"))
            domains.append(preds.get("Job_Domain", {}).get("Domain", "Other"))
            
            cluster_map = preds.get("Cluster_Map")
            if cluster_map:
                cluster_ids.append(cluster_map.get("Cluster_ID", -1))
                coords = cluster_map.get("Coordinates", {"X": 0.0, "Y": 0.0})
                coord_xs.append(coords.get("X", 0.0))
                coord_ys.append(coords.get("Y", 0.0))
            else:
                cluster_ids.append(-1)
                coord_xs.append(0.0)
                coord_ys.append(0.0)

        df['Experience_Level'] = exp_levels
        df['Job_Domain'] = domains
        df['Cluster_ID'] = cluster_ids
        df['Cluster_X'] = coord_xs
        df['Cluster_Y'] = coord_ys

        initial_count = len(df)
        df = df[df['Job_Domain'] != 'Other'].copy()
        filtered_count = initial_count - len(df)
        print(f"\n-> Filtering Complete: {filtered_count} non-IT jobs ('Other') removed.")
        print(f"-> Remaining Valid IT Jobs: {len(df)}")

        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        
        print(f"\n[SUCCESS] AI processing complete! Predicted dataset saved to: {output_csv}")
        return True

if __name__ == "__main__":
    predictor = AITechCareerPredictor()
    
    predictor.process_entire_dataset(
        input_csv="data/processed/cleaned_data.csv",
        output_csv="data/processed/predicted_data.csv"
    )