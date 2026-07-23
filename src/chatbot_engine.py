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

    def _get_relevant_jobs(self, user_message):
        """Retrieves and formats jobs into structured plain text for the LLM."""
        results = self.collection.query(
            query_texts=[user_message],
            n_results=100
        )
        
        MAX_DISTANCE_THRESHOLD = 1.2
        MAX_LLM_JOBS = 5
        job_context = ""
        valid_count = 0
        
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            if distance > MAX_DISTANCE_THRESHOLD:
                continue
                
            valid_count += 1
            if valid_count <= MAX_LLM_JOBS:
                metadata = results['metadatas'][0][i]
                document = results['documents'][0][i] 

            job_context += f"--- JOB {valid_count} ---\n"
            job_context += f"Position: {metadata.get('title')}\n"
            job_context += f"Company: {metadata.get('company')}\n"
            job_context += f"Location & Model: {metadata.get('location')} - {metadata.get('work_model')}\n"
            job_context += f"Domain: {metadata.get('domain')}\n"
            job_context += f"Experience Required: {metadata.get('experience')}\n"
            job_context += f"Application Link: {metadata.get('link')}\n"
            job_context += f"Full Description & Skills:\n{document.strip()}\n\n"

            if valid_count > MAX_LLM_JOBS:
                job_context += f"\n[SYSTEM NOTE: A total of {valid_count} suitable job postings were found in the database, but for speed optimization, I have only provided you with the details of the top {MAX_LLM_JOBS}. You may inform the user that a total of {valid_count} jobs were found.]\n"
            
        return job_context

    def generate_response_stream(self, user_message):
        """Generates a streamed response using RAG and Gemini's built-in chat memory."""
        context_jobs = self._get_relevant_jobs(user_message)
        
        if not context_jobs:
            context_jobs = "No suitable jobs found in the database for this specific query."

        prompt = f"[DATABASE CONTEXT (AVAILABLE JOBS)]\n{context_jobs}\n\n[USER MESSAGE]\n{user_message}"

        try:
            response = self.chat_session.send_message_stream(prompt)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"\n[API ERROR] An error occurred: {str(e)}"

# --- TEST BLOCK ---
if __name__ == "__main__":
    chatbot = AITechCareerChatbot()
    
    print("🤖 AI Tech Career Assistant Testing...")
    print("Type 'q' or 'quit' to exit.")
    print("Type 'temizle' or 'reset' to clear conversation memory.\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['q', 'quit', 'exit', 'çıkış']:
            print("Goodbye!")
            break
            
        if user_input.lower() in ['temizle', 'reset', 'clear']:
            chatbot.reset_chat_session()
            print("🔄 Memory cleared! Starting a fresh conversation.\n")
            continue
            
        print("\n🤖 Assistant:\n" + "-"*40)
        
        for chunk_text in chatbot.generate_response_stream(user_input):
            print(chunk_text, end="", flush=True)
            
        print("\n" + "-" * 40 + "\n")