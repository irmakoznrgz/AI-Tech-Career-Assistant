import os
import re
import random
from collections import Counter 
from datetime import datetime
from google import genai
from google.genai import types
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

os.environ["HF_HUB_OFFLINE"] = "1"

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
                base_instruction = file.read()
        except FileNotFoundError:
            base_instruction = "You are a helpful AI Career Assistant."
            
        bugunun_tarihi = datetime.now().strftime("%B %d, %Y")
        self.system_instruction = f"{base_instruction}\n\n[CRITICAL SYSTEM UPDATE]: The current date is {bugunun_tarihi}. You MUST evaluate all timelines, ongoing university degrees, bootcamp dates, and job postings based on this current date. Do not assume any year other than {bugunun_tarihi[:4]} as the present."
    
        self.chat_session = None
        self.reset_chat_session()
        
        self.ban_words = ["barmen", "barmaid", "hizmetleri", "büfeci", "garson", "komi", "aşçı", "temizlik", "kasiyer", "şoför", "kurye", "resepsiyon", "güvenlik", "maid", "sekreter"]
        self.valid_cities = {"Adana", "Adıyaman", "Afyon", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Remote", "Hybrid", "Multiple"}

    def reset_chat_session(self):
        self.chat_session = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.45, top_p=0.9        
            )
        )

    def clean_val(self, val):
        if not val: return ""
        return str(val).lower().replace("-", "").replace(" ", "").strip()

    def extract_cv_skills(self, cv_text):
        if not cv_text or not str(cv_text).strip():
            return []

        cv_text_lower = str(cv_text).lower()
        tech_pool = [
            'python', 'java', 'c#', '.net', 'c++', 'javascript', 'typescript', 'react',
            'angular', 'vue', 'node', 'sql', 'mysql', 'postgresql', 'mongodb', 'nosql',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux', 'git', 'ci/cd',
            'machine learning', 'deep learning', 'yapay zeka', 'nlp', 'data science',
            'hadoop', 'spark', 'pytorch', 'tensorflow', 'excel', 'power bi', 'tableau',
            'html', 'css', 'spring boot', 'django', 'flask', 'golang', 'rust', 'ruby', 'swift', 'kotlin'
        ]

        found_skills = []
        for skill in tech_pool:
            if re.search(rf'\b{re.escape(skill)}\b', cv_text_lower):
                found_skills.append(skill)

        return found_skills

    def search_jobs_for_ui(self, search_query="yazılım bilişim teknoloji veri", ui_filters=None, limit=None, cv_text=None):
        total_docs = self.collection.count()
        fetch_limit = total_docs if total_docs > 0 else 10000
        cv_skills = self.extract_cv_skills(cv_text) if cv_text else []
        query_text = search_query or "yazılım bilişim teknoloji veri"

        if cv_skills:
            query_text = f"{query_text} {' '.join(cv_skills)}"

        search_params = {
            "query_texts": [query_text], 
            "n_results": fetch_limit,
            "include": ["metadatas", "documents", "distances"]
        }
        
        results = self.collection.query(**search_params)
        
        job_list = []
        seen_jobs = set()
        
        if not results.get('ids') or not results['ids'][0]: return job_list

        for i in range(len(results['ids'][0])):
            real_db_id = results['ids'][0][i]
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            title = str(metadata.get('title', 'Unknown'))
            company = str(metadata.get('company', 'Unknown'))
            
            if any(ban.lower() in title.lower() for ban in self.ban_words): continue
        
            job_identifier = f"{title.lower().strip()}-{company.lower().strip()}"
            if job_identifier in seen_jobs: continue
            
            loc = str(metadata.get('Location') or metadata.get('location') or 'Unknown').strip()
            wm = str(metadata.get('Work_Model') or metadata.get('work_model') or 'Unknown').strip()
            jt = str(metadata.get('Job_Type') or metadata.get('job_type') or metadata.get('type') or 'Unknown').strip()
            dom = str(metadata.get('Domain') or metadata.get('domain') or 'Unknown').strip()
            exp = str(metadata.get('Experience') or metadata.get('experience') or 'Unknown').strip()

            if ui_filters:
                skip_job = False
                if "location" in ui_filters and self.clean_val(ui_filters["location"]) not in self.clean_val(loc): skip_job = True
                if "work_model" in ui_filters and self.clean_val(ui_filters["work_model"]) not in self.clean_val(wm): skip_job = True
                if "job_type" in ui_filters and self.clean_val(ui_filters["job_type"]) not in self.clean_val(jt): skip_job = True
                if "experience" in ui_filters and self.clean_val(ui_filters["experience"]) not in self.clean_val(exp): skip_job = True
                if "domain" in ui_filters and self.clean_val(ui_filters["domain"]) not in self.clean_val(dom): skip_job = True
                
                if skip_job: continue 

            job_text = f"{title} {company} {document} {loc} {wm} {jt} {dom} {exp}".lower()
            cv_overlap = sum(1 for skill in cv_skills if skill in job_text)
            distance = results['distances'][0][i] if 'distances' in results else 1.0
            base_score = int(max(0, min(100, 100 - (distance * 35))))

            if cv_skills:
                cv_strength = int((cv_overlap / max(len(cv_skills), 1)) * 100)
                match_score = int(round((base_score * 0.55) + (cv_strength * 0.45)))
                if cv_overlap < 1:
                    continue
            else:
                match_score = base_score

            if match_score < 45 and not ui_filters and not cv_skills: continue
            if cv_skills and match_score < 55:
                continue

            seen_jobs.add(job_identifier)
            job_list.append({
                "id": real_db_id,
                "title": title,
                "company": company,
                "location": loc,
                "work_model": wm,
                "job_type": jt,
                "domain": dom,
                "experience": exp,
                "link": metadata.get('link', '#'),
                "description": document.strip(),
                "match_score": match_score,
                "last_seen_int": metadata.get('last_seen_int', 0),
                "first_seen": metadata.get('first_seen', 'Unknown')
            })
            
        job_list.sort(key=lambda item: item["match_score"], reverse=True)

        if not ui_filters and search_query == "yazılım bilişim teknoloji veri":
            random.shuffle(job_list)

        display_limit = limit if limit else len(job_list)
        return job_list[:display_limit]

    def generate_response_stream(self, user_message, job_list, cv_text=""):
        MAX_LLM_JOBS = 3
        job_context = ""
        for i, job in enumerate(job_list[:MAX_LLM_JOBS]):
            job_context += f"--- JOB {i+1} ---\nPosition: {job.get('title')} | Company: {job.get('company')}\nReq: {job.get('experience')} | {job.get('location')}\nDetails: {job.get('description', '')[:150]}...\n\n"
            
        prompt = f"[DATABASE CONTEXT]\n{job_context}\n"
        if cv_text:
            prompt += f"\n[USER CV DATA]\nThe user has uploaded a CV. Use this context if they ask for advice or matching.\n{cv_text}\n"
            
        prompt += f"\n[CRITICAL RULE]\nDetect the language of the USER MESSAGE below. You MUST reply entirely in that exact same language. Also, format your answer beautifully using Markdown (bullet points, bold text) for readability.\n\n[USER MESSAGE]\n{user_message}"

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
            
            loc_counter = Counter()
            work_models, job_types, experiences, domains = set(), set(), set(), set()
            
            for meta in metadatas:
                if meta:
                    title = str(meta.get("title", "")).lower()
                    if any(ban in title for ban in self.ban_words): continue

                    loc = str(meta.get("Location") or meta.get("location") or "").strip().title()
                    wm = str(meta.get("Work_Model") or meta.get("work_model") or "").strip()
                    jt = str(meta.get("Job_Type") or meta.get("job_type") or meta.get("type") or meta.get("Job_type") or "").strip()
                    exp = str(meta.get("Experience") or meta.get("experience") or "").strip()
                    dom = str(meta.get("Domain") or meta.get("domain") or "").strip()
                    
                    if loc:
                        parts = loc.split()
                        if len(parts) >= 2 and parts[0] == parts[1]: loc = parts[0]
                    
                    if loc in self.valid_cities: loc_counter[loc] += 1
                    if wm and wm not in ["Unknown", "Not Specified", "None", ""]: work_models.add(wm)
                    if jt and jt not in ["Unknown", "Not Specified", "None", ""]: job_types.add(jt)
                    if exp and exp not in ["Unknown", "Not Specified", "None", ""]: experiences.add(exp)
                    if dom and dom not in ["Unknown", "Not Specified", "None", ""]: domains.add(dom)
            
            sorted_locations = [city for city, count in loc_counter.most_common()]

            return {
                "locations": sorted_locations,
                "work_models": sorted(list(work_models)),
                "job_types": sorted(list(job_types)),
                "experiences": sorted(list(experiences)),
                "domains": sorted(list(domains))
            }
        except Exception as e:
            return {"locations": [], "work_models": [], "job_types": [], "experiences": [], "domains": []}

    def get_dashboard_stats(self):
        try:
            results = self.collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])
            
            stats = {
                "work_models": Counter(), "experiences": Counter(),
                "locations": Counter(), "domains": Counter(),
                "timeline": Counter()
            }
            
            for meta in metadatas:
                if not meta: continue
                title = str(meta.get("title", "")).lower()
                if any(ban in title for ban in self.ban_words): continue
                
                wm = str(meta.get("Work_Model") or meta.get("work_model") or "Not Specified").strip()
                exp = str(meta.get("Experience") or meta.get("experience") or "Not Specified").strip()
                loc = str(meta.get("Location") or meta.get("location") or "Not Specified").strip().title()
                dom = str(meta.get("Domain") or meta.get("domain") or "Not Specified").strip()
                fs = str(meta.get("first_seen") or meta.get("First_Seen") or "").strip()

                if loc:
                    parts = loc.split()
                    if len(parts) >= 2 and parts[0] == parts[1]: loc = parts[0]
                    if loc in self.valid_cities: stats["locations"][loc] += 1
                    
                if wm and wm not in ["Unknown", "Not Specified", "", "None"]: stats["work_models"][wm] += 1
                if exp and exp not in ["Unknown", "Not Specified", "", "None"]: stats["experiences"][exp] += 1
                if dom and dom not in ["Unknown", "Not Specified", "", "None"]: stats["domains"][dom] += 1
                
                if fs and fs not in ["Unknown", "None", ""]: 
                    stats["timeline"][fs] += 1

            sorted_timeline = sorted([{"name": k, "value": v} for k, v in stats["timeline"].items()], key=lambda x: x["name"])

            return {
                "work_models": [{"name": k, "value": v} for k, v in stats["work_models"].items()],
                "experiences": [{"name": k, "value": v} for k, v in stats["experiences"].items()],
                "locations": [{"name": k, "value": v} for k, v in stats["locations"].most_common(10)],
                "domains": [{"name": k, "value": v} for k, v in stats["domains"].most_common(6)],
                "timeline": sorted_timeline
            }
        except Exception as e:
            return {"work_models": [], "experiences": [], "locations": [], "domains": [], "timeline": []}

    def get_expired_job_ids(self, job_ids: list):
        if not job_ids: return []
        try:
            results = self.collection.get(ids=job_ids, include=[])
            existing_ids = set(results.get("ids", []))
            expired_ids = [jid for jid in job_ids if jid not in existing_ids]
            return expired_ids
        except Exception as e:
            print(f"[ERROR] Expired jobs check failed: {e}")
            return []