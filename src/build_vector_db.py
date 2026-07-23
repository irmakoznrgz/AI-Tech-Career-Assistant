import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os

def create_vector_database():
    filepath = "data/processed/cleaned_data.csv"
    
    if not os.path.exists(filepath):
        print(f"[ERROR] Dataset not found at: {filepath}")
        print("Please ensure you run this script from the project root directory.")
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
      
    df['Combined_Text'] = df['Job_Title'] + " " + df['Required_Skills'] + " " + df['Job_Description']

    db_path = "data/chroma_db"
    os.makedirs(db_path, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=db_path)
   
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
  
    try:
        chroma_client.delete_collection(name="job_postings")
        print("-> Existing collection flushed.")
    except Exception:
        pass
        
    collection = chroma_client.create_collection(
        name="job_postings", 
        embedding_function=sentence_transformer_ef
    )
    
    total_jobs = len(df)
    print(f"-> Embedding {total_jobs} job postings into the vector space...")
  
    batch_size = 500
    for i in range(0, total_jobs, batch_size):
        batch_df = df.iloc[i:i+batch_size]
        
        documents = batch_df['Combined_Text'].tolist()
        ids = [f"job_{idx}" for idx in batch_df.index.tolist()]
        
        metadatas = []
        for _, row in batch_df.iterrows():
            metadatas.append({
                "title": str(row['Job_Title']),
                "company": str(row['Company']),
                "domain": str(row['Job_Domain']),
                "experience": str(row['Experience_Level']),
                "location": str(row['Location_Details']),
                "work_model": str(row['Work_Model']),
                "link": str(row['Job_Link'])
            })
            
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"   [{min(i + batch_size, total_jobs)}/{total_jobs}] postings successfully embedded.")
        
    print("\n[SUCCESS] Vector database build complete! Saved securely in 'data/chroma_db/'")

if __name__ == "__main__":
    create_vector_database()