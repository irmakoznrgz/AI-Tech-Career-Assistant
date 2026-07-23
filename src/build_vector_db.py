import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os

def create_vector_database():
    print("-> Veri yükleniyor...")
    # Çalıştırma dizinine göre yolu ayarlıyoruz
    filepath = "data/processed/cleaned_data.csv"
    if not os.path.exists(filepath):
        print(f"Hata: {filepath} bulunamadı. Lütfen kodu projenin ana dizininden çalıştırın.")
        return

    df = pd.read_csv(filepath)
    
    # Olası boşlukları (NaN) temizleme garantisi
    df['Job_Title'] = df['Job_Title'].fillna('')
    df['Required_Skills'] = df['Required_Skills'].fillna('')
    df['Job_Description'] = df['Job_Description'].fillna('')
    df['Job_Domain'] = 'Belirtilmemiş'
    df['Experience_Level'] = df['Experience_Level'].fillna('Not specified')
    
    # Vektörleştirilecek ana metni birleştiriyoruz (Chunking yapmadan, tek parça)
    df['Combined_Text'] = df['Job_Title'] + " " + df['Required_Skills'] + " " + df['Job_Description']
    
    print("-> ChromaDB başlatılıyor (Kalıcı disk modu)...")
    # Veritabanını diske kaydetmek için PersistentClient kullanıyoruz
    db_path = "data/chroma_db"
    os.makedirs(db_path, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    # Geliştirme aşamasında lokal, hızlı ve ücretsiz olan varsayılan modeli kullanıyoruz.
    sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()
    
    # Koleksiyon oluşturma (Çakışmayı önlemek için varsa önce siliyoruz)
    try:
        chroma_client.delete_collection(name="job_postings")
    except Exception:
        pass
        
    collection = chroma_client.create_collection(
        name="job_postings", 
        embedding_function=sentence_transformer_ef
    )
    
    print(f"-> Toplam {len(df)} adet ilan vektörleştirilip veritabanına ekleniyor...")
    print("   (Bu işlem bilgisayarının hızına göre birkaç dakika sürebilir)")
    
    # RAM'i şişirmemek için verileri 500'lük paketler (batch) halinde işliyoruz
    batch_size = 500
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i+batch_size]
        
        documents = batch_df['Combined_Text'].tolist()
        # Her ilana benzersiz bir ID atıyoruz
        ids = [f"job_{idx}" for idx in batch_df.index.tolist()]
        
        # Filtreleme (Örn: Sadece Junior ilanları getir) yapabilmek için metadata ekliyoruz
        metadatas = []
        for _, row in batch_df.iterrows():
            metadatas.append({
                "title": row['Job_Title'],
                "domain": row['Job_Domain'],
                "experience": row['Experience_Level']
            })
            
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"   [{min(i + batch_size, len(df))}/{len(df)}] ilan başarıyla eklendi...")
        
    print("\n[BAŞARILI] Vektör veritabanı oluşturuldu ve 'data/chroma_db/' klasörüne kilitlendi!")

if __name__ == "__main__":
    create_vector_database()