import chromadb
from chromadb.utils import embedding_functions

def test_semantic_search_advanced():
    db_path = "data/chroma_db"
    
    chroma_client = chromadb.PersistentClient(path=db_path)
   
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
   
    collection = chroma_client.get_collection(
        name="job_postings",
        embedding_function=sentence_transformer_ef
    )
    
    query_text = "Üniversite 3. sınıf istatistik öğrencisiyim. Veri analizi, veri bilimi ve makine öğrenmesi alanlarında staj veya junior pozisyonlar arıyorum. Python ve SQL biliyorum."
    
    print(f"\n[SEARCH QUERY]: '{query_text}'")
    
    results = collection.query(
        query_texts=[query_text],
        n_results=100
    )
    
    MAX_DISTANCE_THRESHOLD = 0.42
    
    valid_match_count = 0
    
    print("="*70)
    print(f"RELEVANT POSTINGS")
    print("="*70)
    
    for i in range(len(results['ids'][0])):
        distance = results['distances'][0][i]
        if distance > MAX_DISTANCE_THRESHOLD:
            continue
            
        valid_match_count += 1
        metadata = results['metadatas'][0][i]
        document = results['documents'][0][i]
        
        print(f"\n Job ID: {results['ids'][0][i]} | Distance Score: {distance:.4f}")
        print(f"   Title & Company: {metadata.get('title')} at {metadata.get('company')}")
        print(f"   Location/Model: {metadata.get('location')} - {metadata.get('work_model')}")
        print(f"   Domain: {metadata.get('domain')} | Experience: {metadata.get('experience')}")
        print(f"   Apply Link: {metadata.get('link')}")
        print(f"   Snippet: {document[:120]}...")
        print("-" * 70)
        
    print(f"\n Total {valid_match_count} highly relevant postings found and listed!")

if __name__ == "__main__":
    test_semantic_search_advanced()