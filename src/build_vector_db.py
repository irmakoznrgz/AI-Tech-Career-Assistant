import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os
import hashlib
from datetime import datetime, timedelta

def generate_stable_id(url, location):
    unique_string = f"{str(url).strip()}_{str(location).strip()}"
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

def create_vector_database():
    filepath = "data/processed/predicted_data.csv"
    
    if not os.path.exists(filepath):
        print(f"[ERROR] Dataset not found at: {filepath}")
        return

    df = pd.read_csv(filepath)
    df = df.reset_index(drop=True)
   
    df['Job_Title'] = df['Job_Title'].fillna('Not specified')
    df['Required_Skills'] = df['Required_Skills'].fillna('')
    df['Job_Description'] = df['Job_Description'].fillna('')
    df['Job_Domain'] = df['Job_Domain'].fillna('Not specified') if 'Job_Domain' in df.columns else 'Not specified'
    df['Experience_Level'] = df['Experience_Level'].fillna('Not specified') if 'Experience_Level' in df.columns else 'Not specified'
    df['Company'] = df['Company'].fillna('Not specified') if 'Company' in df.columns else 'Not specified'
    df['Job_Link'] = df['Job_Link'].fillna('No link available') if 'Job_Link' in df.columns else 'No link available'
    df['Location_Details'] = df['Location_Details'].fillna('Not specified') if 'Location_Details' in df.columns else 'Not specified'
    df['Work_Model'] = df['Work_Model'].fillna('Not specified') if 'Work_Model' in df.columns else 'Not specified'

    df['Cluster_ID'] = df['Cluster_ID'].fillna(-1) if 'Cluster_ID' in df.columns else -1
    df['Cluster_X'] = df['Cluster_X'].fillna(0.0) if 'Cluster_X' in df.columns else 0.0
    df['Cluster_Y'] = df['Cluster_Y'].fillna(0.0) if 'Cluster_Y' in df.columns else 0.0
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    df['first_seen'] = df['first_seen'] if 'first_seen' in df.columns else today_str
    df['last_seen'] = df['last_seen'] if 'last_seen' in df.columns else today_str
      
    df['Combined_Text'] = df['Job_Title'] + " " + df['Required_Skills'] + " " + df['Job_Description']

    db_path = "data/chroma_db"
    os.makedirs(db_path, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=db_path)
   
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
  
    collection = chroma_client.get_or_create_collection(
        name="job_postings", 
        embedding_function=sentence_transformer_ef
    )
    
    total_jobs = len(df)
    print(f"-> Upserting (Inserting/Updating) {total_jobs} job postings into the vector space...")
  
    batch_size = 500
    for i in range(0, total_jobs, batch_size):
        batch_df = df.iloc[i:i+batch_size]
        
        documents = batch_df['Combined_Text'].tolist()
        
        ids = []
        metadatas = []
        
        for _, row in batch_df.iterrows():
            ids.append(generate_stable_id(row['Job_Link'], row['Location_Details']))
          
            try:
                date_only = str(row['last_seen'])[:10]
                last_seen_str = str(row['last_seen']).replace('-', '')
                last_seen_int = int(last_seen_str)
            except ValueError:
                last_seen_int = int(datetime.now().strftime("%Y%m%d"))

            metadatas.append({
                "title": str(row['Job_Title']),
                "company": str(row['Company']),
                "domain": str(row['Job_Domain']),
                "experience": str(row['Experience_Level']),
                "location": str(row['Location_Details']),
                "work_model": str(row['Work_Model']),
                "link": str(row['Job_Link']),
                "first_seen": str(row['first_seen']),
                "last_seen": str(row['last_seen']),
                "last_seen_int": last_seen_int,
                "cluster_id": int(row['Cluster_ID']),
                "cluster_x": float(row['Cluster_X']),
                "cluster_y": float(row['Cluster_Y'])
            })
            
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"   [{min(i + batch_size, total_jobs)}/{total_jobs}] postings successfully upserted.")

    print("\n-> Running Garbage Collector for expired job postings...")
   
    cutoff_date = datetime.now() - timedelta(days=3)
    cutoff_int = int(cutoff_date.strftime("%Y%m%d"))
    
    try:
        collection.delete(
            where={"last_seen_int": {"$lt": cutoff_int}}
        )
        print(f"-> Expired jobs (older than {cutoff_date.strftime('%Y-%m-%d')}) have been completely removed from the database.")
    except Exception as e:
        print(f"-> No old jobs to clean or an issue occurred during deletion: {e}")

    print("\n[SUCCESS] Vector database update & cleanup complete! Saved securely in 'data/chroma_db/'")

if __name__ == "__main__":
    create_vector_database()