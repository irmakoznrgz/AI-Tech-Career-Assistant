import os
from google import genai
from google.genai import types
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

class AITechCareerChatbot:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.api_key = self.api_key.strip().strip("'").strip('"')
            
        if not self.api_key:
            raise ValueError("[ERROR] GEMINI_API_KEY not found in .env file!")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = 'gemini-3.5-flash'
        
        self.db_path = "data/chroma_db"
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.collection = self.chroma_client.get_collection(
            name="job_postings", embedding_function=self.sentence_transformer_ef
        )

        prompt_path = os.path.join("prompts", "system_instruction.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as file:
                self.system_instruction = file.read()
        except FileNotFoundError:
            self.system_instruction = "You are a helpful AI Career Assistant."
    
        self.chat_session = None
        self.reset_chat_session()
        
        self.ban_words = ["barmen", "barmaid", "hizmetleri", "büfeci", "garson", "komi", "aşçı", "temizlik", "kasiyer", "şoför", "kurye", "resepsiyon", "güvenlik", "maid"]
        self.valid_cities = {"Adana", "Adıyaman", "Afyon", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Remote", "Hybrid", "Multiple"}

    def reset_chat_session(self):
        self.chat_session = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.45, top_p=0.9        
            )
        )

    def search_jobs_for_ui(self, search_query="yazılım bilişim teknoloji veri", ui_filters=None, limit=None):
        total_docs = self.collection.count()
        fetch_limit = min(limit if limit else 50, total_docs) if total_docs > 0 else 10

        search_params = {
            "query_texts": [search_query], 
            "n_results": fetch_limit,
            "include": ["metadatas", "documents", "distances"]
        }
        
        if ui_filters:
            valid_filters = []
            for k, v in ui_filters.items():
                if v and str(v).strip() != "":
                    # Job Type verisi veritabanında type veya job_type olarak geçebilir
                    key = "type" if k == "job_type" else k
                    valid_filters.append({key: {"$eq": v}})
            
            if len(valid_filters) == 1: search_params["where"] = valid_filters[0]
            elif len(valid_filters) > 1: search_params["where"] = {"$and": valid_filters}

        results = self.collection.query(**search_params)
        
        job_list = []
        seen_jobs = set()
        
        if not results.get('ids') or not results['ids'][0]: return job_list

        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            title = str(metadata.get('title', 'Unknown'))
            company = str(metadata.get('company', 'Unknown'))
           
            if any(ban.lower() in title.lower() for ban in self.ban_words):
                continue
        
            job_identifier = f"{title.lower().strip()}-{company.lower().strip()}"
            if job_identifier in seen_jobs: continue
            seen_jobs.add(job_identifier)
            
            distance = results['distances'][0][i] if 'distances' in results else 1.0
            match_score = int(max(0, min(100, 100 - (distance * 35))))

            if match_score < 45 and not ui_filters: continue

            raw_logo = metadata.get('Logo_Link') or metadata.get('logo_link') or metadata.get('logo') or ""

            job_list.append({
                "id": job_identifier,
                "title": title,
                "company": company,
                "location": metadata.get('location', 'Unknown'),
                "work_model": metadata.get('work_model', 'Unknown'),
                "job_type": metadata.get('type') or metadata.get('job_type', 'Unknown'),
                "domain": metadata.get('domain', 'Unknown'),
                "experience": metadata.get('experience', 'Unknown'),
                "link": metadata.get('link', '#'),
                "logo": raw_logo,
                "description": document.strip(),
                "match_score": match_score
            })
            
        return job_list

    def generate_response_stream(self, user_message, job_list, cv_text=""):
        MAX_LLM_JOBS = 3
        job_context = ""
        for i, job in enumerate(job_list[:MAX_LLM_JOBS]):
            job_context += f"--- JOB {i+1} ---\nPosition: {job.get('title')} | Company: {job.get('company')}\nReq: {job.get('experience')} | {job.get('location')}\nDetails: {job.get('description', '')[:150]}...\n\n"
            
        prompt = f"[DATABASE CONTEXT]\n{job_context}\n"
        if cv_text:
            prompt += f"\n[USER CV DATA]\nThe user has uploaded a CV. Use this context if they ask for advice or matching.\n{cv_text}\n"
       
        prompt += f"\n[CRITICAL RULE]\nDetect the language of the USER MESSAGE below. You MUST reply entirely in that exact same language. Do NOT use English if the user speaks Turkish.\n\n[USER MESSAGE]\n{user_message}"

        try:
            response = self.chat_session.send_message_stream(prompt)
            for chunk in response:
                if chunk.text: yield chunk.text
        except Exception as e:
            yield f"\n[API ERROR] {str(e)}"

    def get_unique_filters(self):
        try:
            results = self.collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])
            
            locations, work_models, job_types, experiences, domains = set(), set(), set(), set(), set()
            
            for meta in metadatas:
                if meta:
                    title = str(meta.get("title", "")).lower()
                    if any(ban in title for ban in self.ban_words): continue # Filtre listesini de temizliyoruz

                    loc = str(meta.get("location") or "").strip().title()
                    wm = str(meta.get("work_model") or "").strip()
                    jt = str(meta.get("type") or meta.get("job_type") or "").strip()
                    exp = str(meta.get("experience") or "").strip()
                    dom = str(meta.get("domain") or "").strip()
                    
                    # ŞEHİR İSİMLERİNİ TEMİZLEME
                    if loc:
                        parts = loc.split()
                        if len(parts) >= 2 and parts[0] == parts[1]: loc = parts[0]
                    
                    if loc in self.valid_cities: locations.add(loc)
                    if wm and wm not in ["Unknown", "Not Specified", "None", ""]: work_models.add(wm)
                    if jt and jt not in ["Unknown", "Not Specified", "None", ""]: job_types.add(jt)
                    if exp and exp not in ["Unknown", "Not Specified", "None", ""]: experiences.add(exp)
                    if dom and dom not in ["Unknown", "Not Specified", "None", ""]: domains.add(dom)
            
            return {
                "locations": sorted(list(locations)),
                "work_models": sorted(list(work_models)),
                "job_types": sorted(list(job_types)),
                "experiences": sorted(list(experiences)),
                "domains": sorted(list(domains))
            }
        except Exception as e:
            return {"locations": [], "work_models": [], "job_types": [], "experiences": [], "domains": []}