import chromadb
from chromadb.utils import embedding_functions

def test_semantic_search_debug():
    print("-> ChromaDB'ye bağlanılıyor...")
    db_path = "data/chroma_db"
    chroma_client = chromadb.PersistentClient(path=db_path)
    sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()
    
    collection = chroma_client.get_collection(
        name="job_postings",
        embedding_function=sentence_transformer_ef
    )
    
    query_text = "React, Vue ve JavaScript konularında uzmanım. Kullanıcı arayüzleri geliştiriyorum."
    
    print(f"\n🔍 Arama: '{query_text}'")
    print("-> Tüm uygun eşleşmeler aranıyor (Filtreler Kapalı)...\n")
    
    # 1. DEĞİŞİKLİK: 'where' filtresini tamamen kaldırdık ki tüm veritabanında arasın
    results = collection.query(
        query_texts=[query_text],
        n_results=10 # En iyi 10 sonucu görelim
    )
    
    # 2. DEĞİŞİKLİK: Eşiği 2.0'a çektik (Gevşettik)
    MAX_DISTANCE_THRESHOLD = 2.0 
    
    uygun_ilan_sayisi = 0
    
    for i in range(len(results['ids'][0])):
        distance = results['distances'][0][i]
        
        # 3. DEĞİŞİKLİK: Elenen ilanların da neden elendiğini (mesafesini) görelim
        if distance > MAX_DISTANCE_THRESHOLD:
            print(f"❌ Elendi (Mesafe çok yüksek: {distance:.4f}) - İlan ID: {results['ids'][0][i]}")
            continue
            
        uygun_ilan_sayisi += 1
        metadata = results['metadatas'][0][i]
        
        print(f"✅ İlan ID: {results['ids'][0][i]} | Mesafe: {distance:.4f}")
        print(f"   Pozisyon: {metadata.get('title')}")
        print(f"   Alan: {metadata.get('domain')} | Seviye: {metadata.get('experience')}")
        print("-" * 50)
        
    print(f"\n🎉 Toplam {uygun_ilan_sayisi} adet uygun ilan bulundu!")

if __name__ == "__main__":
    test_semantic_search_debug()