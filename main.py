import os
import io
import PyPDF2
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sklearn.decomposition import PCA
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.chatbot_engine import AITechCareerChatbot

app = FastAPI(title="TechCareer API")

global_db_bot = AITechCareerChatbot()

chat_sessions: Dict[str, AITechCareerChatbot] = {}

stateless_engine = AITechCareerChatbot()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # UPDATED
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_sessions: Dict[str, Dict[str, Any]] = {}

def get_chatbot(session_id: str) -> AITechCareerChatbot:
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required.")
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "bot": AITechCareerChatbot(),
            "last_active": datetime.now()
        }
    else:
        chat_sessions[session_id]["last_active"] = datetime.now()
        
    return chat_sessions[session_id]["bot"]

async def cleanup_inactive_sessions():
    while True:
        await asyncio.sleep(3600) 
        now = datetime.now()
        expired_sessions = [
            sid for sid, data in chat_sessions.items()
            if now - data["last_active"] > timedelta(hours=2)
        ]
        for sid in expired_sessions:
            del chat_sessions[sid]

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_inactive_sessions())


# --- REQUEST MODELS ---
class SearchRequest(BaseModel):
    search_query: str = "yazılım bilişim teknoloji veri uzman geliştirici mühendis"
    ui_filters: Optional[Dict[str, Any]] = None
    limit: int = 50

class ChatRequest(BaseModel):
    session_id: str  
    user_message: str
    job_list: List[Dict[str, Any]]
    cv_text: str = ""

class MapRequest(BaseModel):
    jobs: List[Dict[str, Any]]
    cv_text: str = ""

class ResetRequest(BaseModel):
    session_id: str


# --- ENDPOINTS ---

@app.get("/api/jobs/filters")
async def get_filters():
    temp_bot = AITechCareerChatbot()
    try:
        filters = global_db_bot.get_unique_filters()
        return {"status": "success", "data": filters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/search")
async def search_jobs(request: SearchRequest):
    """Retrieves job postings from ChromaDB based on filters from React."""
    try:
        jobs = stateless_engine.search_jobs_for_ui(
            search_query=request.search_query, 
            ui_filters=request.ui_filters, 
            limit=request.limit
        )
        
        clean_jobs = []
        for job in jobs:
            clean_job = {k: v for k, v in job.items() if k != "embedding"}
            clean_jobs.append(clean_job)
                
        return {"status": "success", "data": clean_jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    """Reads the PDF from React, converts it to text, and extracts capabilities."""

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    try:
        contents = await file.read()
        
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Max 5MB.")

        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        cv_text = " ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        
        cv_text_lower = cv_text.lower()
        tech_keywords = ['python', 'java', 'c#', '.net', 'c++', 'javascript', 'typescript', 'react', 'angular', 'vue', 'node', 'sql', 'mysql', 'postgresql', 'mongodb', 'nosql',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux', 'git', 'ci/cd',
        'machine learning', 'deep learning', 'yapay zeka', 'nlp', 'data science', 
        'hadoop', 'spark', 'pytorch', 'tensorflow', 'excel', 'power bi', 'tableau',
        'html', 'css', 'spring boot', 'django', 'flask', 'golang', 'rust', 'ruby', 'swift', 'kotlin']
        found_skills = [skill for skill in tech_keywords if skill in cv_text_lower]
        
        return {
            "status": "success", 
            "cv_text": cv_text, 
            "found_skills": found_skills
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/galaxy-map")
def generate_galaxy_map(request: MapRequest):
    """Calculates PCA based on job postings and CV text and returns X, Y coordinates."""
    if len(request.jobs) < 3:
        raise HTTPException(status_code=400, detail="You need at least 3 listings to create a map.")
        
    try:
        texts_for_map = [j.get('description', '') for j in request.jobs]
        labels = [j.get('experience', 'Unknown') for j in request.jobs]
        titles = [j.get('title', 'Unknown') for j in request.jobs]
        companies = [j.get('company', 'Unknown') for j in request.jobs]
        links = [j.get('link', '#') for j in request.jobs]
        
        if request.cv_text:
            texts_for_map.append(request.cv_text)
            labels.append("MY CV")
            titles.append("Your Profile")
            companies.append("You")
            links.append("N/A")

        embeddings = stateless_engine.sentence_transformer_ef(texts_for_map)
        
        pca = PCA(n_components=2)
        coords = pca.fit_transform(embeddings)
        
        map_data = []
        for i in range(len(coords)):
            map_data.append({
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
                "title": titles[i],
                "company": companies[i],
                "category": labels[i],
                "link": links[i]
            })
            
        return {"status": "success", "map_data": map_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
@limiter.limit("5/minute")
async def chat_with_bot(request: Request, body: ChatRequest):
    """Passes the streaming response from the specific user's chatbot to React."""
    try:
        user_bot = get_chatbot(body.session_id)
        
        return StreamingResponse(
            user_bot.generate_response_stream(
                body.user_message, 
                body.job_list, 
                body.cv_text
            ), 
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/reset")
async def reset_chat(request: ResetRequest):
    """Resets the memory for a specific user session."""
    if request.session_id in chat_sessions:
        chat_sessions[request.session_id]["bot"].reset_chat_session()
        chat_sessions[request.session_id]["last_active"] = datetime.now()
        return {"status": "success", "message": "Memory has been reset for this session."}
    
    return {"status": "success", "message": "No active session found to reset."}