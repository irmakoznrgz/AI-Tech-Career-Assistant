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
            name="job_postings",
            embedding_function=self.sentence_transformer_ef
        )

        prompt_path = os.path.join("prompts", "system_instruction.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as file:
                self.system_instruction = file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"[ERROR] Could not find {prompt_path}. Make sure the folder and file exist.")
    
        self.chat_session = None
        self.reset_chat_session()

    def reset_chat_session(self):
        """Creates or resets the isolated chat memory for a user."""
        self.chat_session = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.45,  
                top_p=0.9       
            )
        )

    def search_jobs_for_ui(self, search_query="yazılım bilişim teknoloji veri uzman geliştirici mühendis", ui_filters=None, limit=None):

        total_docs = self.collection.count()

        if limit is not None:
            fetch_limit = min(limit, total_docs) if total_docs > 0 else 10
        else:
            fetch_limit = total_docs if total_docs > 0 else 10

        search_params = {
            "query_texts": [search_query], 
            "n_results": fetch_limit,
            "include": ["metadatas", "documents", "embeddings", "distances"]
        }
        
        if ui_filters:
            search_params["where"] = ui_filters

        results = self.collection.query(**search_params)
        
        job_list = []
        seen_jobs = set()
        
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]

            title = metadata.get('title', 'Unknown')
            company = metadata.get('company', 'Unknown')
        
            job_identifier = f"{title.lower().strip()}-{company.lower().strip()}"
           
            if job_identifier in seen_jobs:
                continue
                
            seen_jobs.add(job_identifier)
            
            distance = results['distances'][0][i] if 'distances' in results else 1.0
            match_score = int(max(0, min(100, 100 - (distance * 35))))

            if match_score < 55:
                continue

            raw_logo = metadata.get('Logo_Link') or metadata.get('logo_link') or metadata.get('logo') or metadata.get('Logo_link') or ""

            job_list.append({
                "id": job_identifier,
                "title": metadata.get('title', 'Unknown'),
                "company": metadata.get('company', 'Unknown'),
                "location": metadata.get('location', 'Unknown'),
                "work_model": metadata.get('work_model', 'Unknown'),
                "domain": metadata.get('domain', 'Unknown'),
                "experience": metadata.get('experience', 'Unknown'),
                "link": metadata.get('link', '#'),
                "logo": raw_logo,
                "description": document.strip(),
                "match_score": match_score,
                "embedding": results['embeddings'][0][i] if 'embeddings' in results else None
            })
            
        return job_list

    def generate_response_stream(self, user_message, job_list, cv_text=""):
        MAX_LLM_JOBS = 3
        job_context = ""
        
        for i, job in enumerate(job_list[:MAX_LLM_JOBS]):
            job_context += f"--- JOB {i+1} ---\n"
            job_context += f"Position: {job['title']} | Company: {job['company']}\n"
            job_context += f"Req: {job['experience']} | {job['location']}\n"
            job_context += f"Details: {job['description'][:150]}...\n\n"
            
        if len(job_list) > MAX_LLM_JOBS:
            job_context += f"\n[SYSTEM NOTE: The database found {len(job_list)} jobs, but I provided you with the top {MAX_LLM_JOBS}. Mention to the user that {len(job_list)} jobs were found.]\n"

        prompt = f"[DATABASE CONTEXT]\n{job_context}\n\n[USER MESSAGE]\n{user_message}"

        if cv_text:
            prompt += f"\n[USER CV DATA]\nThe user has uploaded a CV. Use this to give personalized advice:\n{cv_text}\n"
            
        prompt += f"\n[USER MESSAGE]\n{user_message}"

        try:
            response = self.chat_session.send_message_stream(prompt)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[API ERROR] {str(e)}"