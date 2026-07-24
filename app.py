import streamlit as st
import base64
from src.chatbot_engine import AITechCareerChatbot
import math
import PyPDF2 # PDF okumak için ekledik

# --- PAGE CONFIG ---
st.set_page_config(page_title="AITechCareer", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

# --- BACKGROUND & CSS ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

bg_base64 = get_base64_of_bin_file("img/pic.jpg")

st.markdown(f"""
    <style>
    [data-testid="stHeader"] {{ display: none; }}
    [data-testid="stStatusWidget"] {{ display: none; }}
    
    .stApp {{
        background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.95)), 
                    url("data:image/jpeg;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: white;
    }}
    
    .custom-header {{
        font-size: 32px; font-weight: 800; color: #10B981;
        margin-bottom: 20px; margin-top: 20px;
    }}
    
    [data-testid="stExpander"] {{
        background-color: rgba(30, 41, 59, 0.9);
        border: 1px solid #10B981;
        border-radius: 20px !important;
        overflow: hidden;
    }}
    
    .job-card {{
        background-color: rgba(30, 41, 59, 0.7);
        border-left: 4px solid #10B981;
        padding: 20px; border-radius: 12px; margin-bottom: 15px;
        backdrop-filter: blur(10px);
    }}
    .job-title {{ font-size: 20px; font-weight: bold; color: #F8FAFC; }}
    .job-company {{ font-size: 16px; color: #94A3B8; margin-bottom: 10px; }}
    .job-tags span {{
        background-color: #334155; padding: 4px 8px; border-radius: 6px;
        font-size: 12px; margin-right: 5px; color: #CBD5E1;
    }}
    </style>
""", unsafe_allow_html=True)

# --- SYSTEM INIT ---
@st.cache_resource(show_spinner="Loading... Please wait!")
def init_bot():
    return AITechCareerChatbot()

chatbot = init_bot()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello, how can I help your career today? 😊"}]
if "jobs" not in st.session_state:
    st.session_state.jobs = st.session_state.jobs = [] 
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# --- HEADER & FILTERS ---
st.markdown('<div class="custom-header">AI Tech Career</div>', unsafe_allow_html=True)

with st.container():
    col1, col2, col3 = st.columns(3)
    
    cities = ["Any", "İstanbul", "Ankara", "İzmir", "Antalya", "Bursa", "Kocaeli", "Eskişehir"]
    city_filter = col1.selectbox("Location", cities) 
    
    job_types = ["Any", "Full-time", "Part-time", "Freelance", "Contract", "Remote", "Hybrid", "On-site"]
    job_type_filter = col2.selectbox("Job Type", job_types)
    
    exp_level = col3.selectbox("Experience Level", ["Any", "Junior", "Mid-Level", "Senior", "Lead/Manager"])

def build_filters():
    conditions = []
    if job_type_filter != "Any": conditions.append({"work_model": job_type_filter})
    if exp_level != "Any": conditions.append({"experience": exp_level})
    if city_filter != "Any": conditions.append({"location": city_filter})
    
    if not conditions: return None
    elif len(conditions) == 1: return conditions[0]
    else: return {"$and": conditions}

# Buton ve CV Yükleme Alanını Yanyana Koyduk
st.write("") # Boşluk
btn_col, cv_col, empty_col = st.columns([1.5, 2, 3])
search_btn = btn_col.button("🔍 Search Jobs", use_container_width=True)
cv_file = cv_col.file_uploader("📄 Magic Search with CV (PDF)", type=["pdf"], label_visibility="collapsed")

# Arama Butonuna Basılırsa veya CV Yüklenirse (Otomatik Tetikleme)
if search_btn or cv_file:
    ui_filters = build_filters()
    search_query = "yazılım bilişim teknoloji veri uzman geliştirici mühendis" # Varsayılan
    
    if cv_file is not None:
        # PDF'i Oku ve Metne Çevir
        pdf_reader = PyPDF2.PdfReader(cv_file)
        cv_text = " ".join([page.extract_text() for page in pdf_reader.pages])
        
        # Vektör araması için CV'nin ilk 1000 karakterini kullanmak yeterlidir
        search_query = cv_text[:1000] 
        st.toast("CV Analyzed! Displaying tailored jobs...", icon="✨")
        
        # Chatbot'un ilk mesajını dinamik olarak CV'ye göre değiştirelim!
        if len(st.session_state.messages) <= 1:
            st.session_state.messages = [{"role": "assistant", "content": "I've analyzed your CV! 🚀 I've listed the most suitable jobs on the left based on your skills. Should we do a mock interview for the first one? 😊"}]

    # İlanları güncelle ve 1. sayfaya dön
    st.session_state.jobs = chatbot.search_jobs_for_ui(search_query=search_query, ui_filters=ui_filters)
    st.session_state.current_page = 1


# --- SPLIT SCREEN (LEFT: Jobs | RIGHT: Chatbot Widget) ---
st.write("---")
main_col, chat_col = st.columns([2, 1], gap="large")

# --- LEFT PANEL: JOBS ---
with main_col:
    st.subheader(f"Found Jobs ({len(st.session_state.jobs)})")
    
    jobs = st.session_state.jobs
    items_per_page = 5
    total_pages = math.ceil(len(jobs) / items_per_page) if jobs else 1
    
    if jobs:
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        for job in jobs[start_idx:end_idx]:
            st.markdown(f"""
                <div class="job-card">
                    <div class="job-title">{job['title']}</div>
                    <div class="job-company">{job['company']}</div>
                    <div class="job-tags">
                        <span>📍 {job['location']}</span>
                        <span>💼 {job['work_model']}</span>
                        <span>⭐ {job['experience']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Job Details"):
                st.write(job['description'])
                st.markdown(f"[Apply Here]({job['link']})")
                
        # Pagination
        st.write("")
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        if p_col1.button("⬅️ Previous") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
            st.rerun()
        p_col2.markdown(f"<div style='text-align: center'>Page {st.session_state.current_page} / {total_pages}</div>", unsafe_allow_html=True)
        if p_col3.button("Next ➡️") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.rerun()
    else:
        st.info("Welcome! Upload your resume (PDF) or click 'Search Jobs' to explore the best career opportunities.")

# --- RIGHT PANEL: FLOATING CHATBOT WIDGET ---
with chat_col:
    st.write("") 
    st.write("")
    
    # Kullanıcı CV yüklediyse chat otomatik açılsın, yoksa kapalı dursun
    is_chat_expanded = True if cv_file else False
    
    with st.expander("💬 Chat with AI Career Assistant", expanded=is_chat_expanded):
        chat_container = st.container(height=400)
        with chat_container:
            for message in st.session_state.messages:
                avatar = "💬" if message["role"] == "assistant" else "👤"
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

        user_input = st.chat_input("Ask for career advice...")
        
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with chat_container:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(user_input)
                
                with st.chat_message("assistant", avatar="💬"):
                    response_placeholder = st.empty()
                    full_response = ""
                    for chunk in chatbot.generate_response_stream(user_input, st.session_state.jobs):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()