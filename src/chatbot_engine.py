import os
from google import genai
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

class AITechCareerChatbot:
    def __init__(self):
        # 1. API Anahtarını Güvenli Bir Şekilde Yükle
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # Boşluk veya tırnak işareti hatalarını temizleme
        if self.api_key:
            self.api_key = self.api_key.strip().strip("'").strip('"')
            
        if not self.api_key or self.api_key == "senin_kopyaladigin_uzun_api_anahtarin_buraya_gelecek":
            raise ValueError("HATA: .env dosyasında geçerli bir GEMINI_API_KEY bulunamadı! Lütfen kontrol edin.")
        
        # Yeni nesil Google GenAI Client Kurulumu
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = 'gemini-2-flash'
        
        # 2. ChromaDB (Vektör Veritabanı) Bağlantısını Kur
        print("-> Chatbot Motoru: ChromaDB'ye bağlanılıyor...")
        self.db_path = "data/chroma_db"
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.chroma_client.get_collection(
            name="job_postings",
            embedding_function=self.sentence_transformer_ef
        )
        print("-> Chatbot Motoru Hazır! Zeka devrede. 🧠\n")

    def _get_relevant_jobs(self, user_message, n_results=3):
        """Kullanıcının mesajına en uygun ilanları ChromaDB'den çeker."""
        results = self.collection.query(
            query_texts=[user_message],
            n_results=n_results
        )
        
        job_context = ""
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            # Çok alakasız ilanları Gemini'a göndermemek için sınır
            if distance > 1.5: 
                continue
                
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            
            job_context += f"İLAN {i+1}:\n"
            job_context += f"- Pozisyon: {metadata.get('title')}\n"
            job_context += f"- Alan: {metadata.get('domain')} | Seviye: {metadata.get('experience')}\n"
            job_context += f"- Detaylar: {document[:500]}...\n\n"
            
        return job_context

    def generate_response(self, user_message, chat_history=None):
        """RAG Mimarisi: ChromaDB verisini Gemini'a bağlayıp cevap üretir."""
        
        # 1. Kullanıcının mesajına uygun ilanları bul
        context_jobs = self._get_relevant_jobs(user_message)
        
        if not context_jobs:
            context_jobs = "Maalesef şu anki veritabanında kullanıcının profiline tam uyan bir ilan bulunamadı."

        # 2. Sistem Prompt'unu Hazırla
        system_prompt = f"""
        Sen 'AI Tech Career' isimli bir platformun baş yapay zeka kariyer asistanısın. 
        Görevin, BT (IT) sektöründeki adaylara kariyer tavsiyesi vermek, CV'lerini yorumlamak ve onlara uygun iş ilanları sunmaktır.
        
        Aşağıda, kullanıcının mesajına en uygun olduğu tespit edilen güncel iş ilanları yer almaktadır:
        --- İLANLAR BAŞLANGICI ---
        {context_jobs}
        --- İLANLAR BİTİŞİ ---
        
        KURALLAR:
        1. Kullanıcıya her zaman profesyonel, cesaretlendirici ve yapıcı bir dille hitap et.
        2. Eğer kullanıcı iş soruyorsa, YALNIZCA yukarıda sana verilen ilanlar listesinden öneriler yap. Hayali bir ilan uydurma.
        3. Yukarıdaki ilanlar kullanıcının yetenekleriyle eşleşiyorsa, neden uygun olduklarını açıkla.
        4. İlan yoksa, yeteneklerini nasıl geliştirebileceği konusunda tavsiyeler ver.
        5. Cevabın çok uzun destanlar şeklinde olmasın, okunaklı ve madde işaretli olsun.
        
        Kullanıcının Mesajı: {user_message}
        """

        # 3. Yeni nesil API ile Gemini'a soruyu sor ve cevabı al
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=system_prompt
            )
            return response.text
        except Exception as e:
            return f"Gemini API ile iletişim kurarken bir hata oluştu: {str(e)}"

# --- TEST BLOĞU ---
if __name__ == "__main__":
    try:
        chatbot = AITechCareerChatbot()
        
        print("🤖 AI Tech Career Asistanı Test Ediliyor...")
        print("Çıkmak için 'q' veya 'quit' yazın.\n")
        
        while True:
            user_input = input("Sen: ")
            if user_input.lower() in ['q', 'quit', 'çıkış']:
                print("Görüşmek üzere!")
                break
                
            print("\n🤖 Asistan (Düşünüyor...)\n" + "-"*40)
            answer = chatbot.generate_response(user_input)
            print(answer)
            print("-" * 40 + "\n")
            
    except Exception as error:
        print(f"\n[BAŞLATMA HATASI] {error}")