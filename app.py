import streamlit as st
import base64
from src.chatbot_engine import AITechCareerChatbot
import math
import PyPDF2
import plotly.express as px
from sklearn.decomposition import PCA
import pandas as pd

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
        background: linear-gradient(rgba(15, 23, 42, 0.60), rgba(15, 23, 42, 0.85)), 
                    url("data:image/jpeg;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
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
    
    /* YENİ: LOGO VE İLAN KARTI TASARIMI */
    .job-card {{
        background-color: rgba(30, 41, 59, 0.7);
        border-left: 4px solid #10B981;
        padding: 20px; border-radius: 12px; margin-bottom: 15px;
        backdrop-filter: blur(10px);
        display: flex;
        flex-direction: column;
    }}
    
    .job-header-container {{
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 15px;
    }}
    
    .job-logo {{
        width: 50px;
        height: 50px;
        object-fit: contain;
        background-color: white; /* Logolar genelde şeffaftır, arkası beyaz olsun */
        border-radius: 8px;
        padding: 4px;
        border: 1px solid #334155;
    }}
    
    .job-logo-fallback {{
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #334155;
        border-radius: 8px;
        font-size: 24px;
    }}
    
    .job-title {{ font-size: 20px; font-weight: bold; color: #F8FAFC; line-height: 1.2; }}
    .job-company {{ font-size: 15px; color: #94A3B8; margin-top: 4px; }}
    
    .job-tags span {{
        background-color: #334155; padding: 4px 8px; border-radius: 6px;
        font-size: 12px; margin-right: 5px; color: #CBD5E1; display: inline-block; margin-bottom: 5px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- SYSTEM INIT ---
@st.cache_resource(show_spinner="Loading AI Engine... Please wait!")
def init_bot():
    return AITechCareerChatbot()

chatbot = init_bot()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello, how can I help your career today? 😊"}]
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "cv_text" not in st.session_state:
    st.session_state.cv_text = ""
if "last_cv_name" not in st.session_state:
    st.session_state.last_cv_name = ""
if "search_performed" not in st.session_state:
    st.session_state.search_performed = False

if "jobs" not in st.session_state:
    st.session_state.jobs = chatbot.search_jobs_for_ui()

# --- HEADER & FILTERS ---
st.markdown('<div class="custom-header">AI Tech Career</div>', unsafe_allow_html=True)

with st.container():
    col1, col2, col3, col4 = st.columns(4)
    
    cities = ["All Locations", "İstanbul", "Ankara", "İzmir", "Antalya", "Bursa", "Kocaeli", "Eskişehir", "Adana", "Gaziantep", "Kayseri", "Samsun", "Trabzon", "Tekirdağ"]
    city_filter = col1.selectbox("Location", cities) 
    
    job_types = ["All Types", "Full-time", "Part-time", "Freelance", "Contract", "Remote", "Hybrid", "On-site"]
    job_type_filter = col2.selectbox("Job Type", job_types)
    
    exp_levels = ["All Levels", "Junior", "Mid-Level", "Senior", "Lead/Manager"]
    exp_level = col3.selectbox("Experience Level", exp_levels)

    domains = ["All Domains", "Product & Business Analysis", "Cybersecurity", "System, Network & IT Ops", "Data & AI", "DevOps & Cloud", "Mobile", "QA & Testing", "Frontend", "Backend", "Full Stack"]
    domain_filter = col4.selectbox("Job Domain", domains)

def build_filters(forced_exp=None):
    conditions = []
    if job_type_filter != "All Types": conditions.append({"work_model": job_type_filter})
    if city_filter != "All Locations": conditions.append({"location": city_filter})
    if domain_filter != "All Domains": conditions.append({"domain": domain_filter})
    
    final_exp = forced_exp if forced_exp else (exp_level if exp_level != "All Levels" else None)
    if final_exp:
        conditions.append({"experience": final_exp})
    
    if not conditions: return None
    elif len(conditions) == 1: return conditions[0]
    else: return {"$and": conditions}

st.write("") 
btn_col, cv_col, empty_col = st.columns([1.5, 2, 3])
search_btn = btn_col.button("🔍 Search Jobs", use_container_width=True)
cv_file = cv_col.file_uploader("📄 Magic Search with CV (PDF)", type=["pdf"], label_visibility="collapsed")

if search_btn or (cv_file and cv_file.name != st.session_state.last_cv_name):
    st.session_state.search_performed = True
    forced_exp = None
    search_query = "yazılım bilişim teknoloji veri uzman geliştirici mühendis" 
    
    if cv_file is not None:
        st.session_state.last_cv_name = cv_file.name
        pdf_reader = PyPDF2.PdfReader(cv_file)
        cv_text = " ".join([page.extract_text() for page in pdf_reader.pages])
        st.session_state.cv_text = cv_text 
        
        cv_text_lower = cv_text.lower()
        student_keywords = ["öğrenci", "student", "stajyer", "intern", "bachelor", "lisans öğrencisi", "devam ediyor"]
        if any(keyword in cv_text_lower for keyword in student_keywords):
            forced_exp = "Junior"
            st.toast("Student profile detected! Forcing Junior/Intern roles.", icon="🎓")
            
        tech_keywords = ["python", "java", "c#", "c++", "sql", "react", "node", "aws", "azure", "docker", "kubernetes", "machine learning", "data science", "excel", "powerbi", "javascript"]
        found_skills = [skill for skill in tech_keywords if skill in cv_text_lower]
        
        if found_skills:
            search_query = " ".join(found_skills) + " " + cv_text[:500]
        else:
            search_query = cv_text[:1000] 
            
        st.toast("CV Analyzed! Displaying tailored jobs...", icon="✨")
        
        if len(st.session_state.messages) <= 1:
            st.session_state.messages = [{"role": "assistant", "content": f"I've analyzed your CV! 🚀 I noticed your skills in **{', '.join(found_skills[:3])}**. I've listed the most suitable jobs on the left."}]

    ui_filters = build_filters(forced_exp=forced_exp)
    st.session_state.jobs = chatbot.search_jobs_for_ui(search_query=search_query, ui_filters=ui_filters)
    st.session_state.current_page = 1

# --- SPLIT SCREEN ---
st.write("---")
main_col, chat_col = st.columns([2, 1], gap="large")

with main_col:
    jobs = st.session_state.jobs
    
    if len(jobs) == 0 and st.session_state.search_performed:
        st.warning("⚠️ No jobs found matching your selected criteria. Please try broadening your filters.")
    else:
        st.subheader(f"Found Jobs ({len(jobs)})")
        
        items_per_page = 5
        total_pages = math.ceil(len(jobs) / items_per_page) if jobs else 1
        
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        for job in jobs[start_idx:end_idx]:
            logo_url = str(job.get('logo', '')).strip()
            if logo_url and len(logo_url) > 5 and logo_url.lower() != "none":
                logo_html = f'<img src="{logo_url}" class="job-logo">'
            else:
                logo_html = '<div class="job-logo-fallback">🏢</div>'
            
            st.markdown(f"""
                <div class="job-card">
                    <div class="job-header-container">
                        {logo_html}
                        <div>
                            <div class="job-title">{job['title']}</div>
                            <div class="job-company">{job['company']}</div>
                        </div>
                    </div>
                    <div class="job-tags">
                        <span>📍 {job['location']}</span>
                        <span>💼 {job['work_model']}</span>
                        <span>⭐ {job['experience']}</span>
                        <span>🏷️ {job.get('domain', 'Unknown')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Job Details"):
                st.write(job['description'])
                st.markdown(f"[Apply Here]({job['link']})")
                
        st.write("")
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        if p_col1.button("⬅️ Previous") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
            st.rerun()
        if jobs:
            p_col2.markdown(f"<div style='text-align: center'>Page {st.session_state.current_page} / {total_pages}</div>", unsafe_allow_html=True)
        if p_col3.button("Next ➡️") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.rerun()
            
        # MODEL 3: 2D KARIYER GALAKSISI
        st.write("---")
        with st.expander("🌌 View Career Galaxy (Job Clustering Map)", expanded=False):
            if len(jobs) > 3:
                with st.spinner("Mapping your CV in the AI Galaxy..."):
                    try:
                        texts_for_map = [j['description'] for j in jobs]
                        labels = [j['experience'] for j in jobs]
                        titles = [j['title'] for j in jobs]
                        companies = [j['company'] for j in jobs]
                        links = [j['link'] for j in jobs] # YENİ: Linkleri de grafiğe yolluyoruz
                        
                        if st.session_state.cv_text:
                            texts_for_map.append(st.session_state.cv_text[:1000])
                            labels.append("🎯 MY CV")
                            titles.append("Your Profile")
                            companies.append("You")
                            links.append("N/A")

                        embeddings = chatbot.sentence_transformer_ef(texts_for_map)
                        
                        pca = PCA(n_components=2)
                        coords = pca.fit_transform(embeddings)
                        
                        df_plot = pd.DataFrame({
                            'X': coords[:, 0],
                            'Y': coords[:, 1],
                            'Title': titles,
                            'Company': companies,
                            'Category': labels,
                            'Link': links # YENİ: Grafiğin içine gömüyoruz
                        })
                        
                        # Hover (Üzerine gelince çıkacak yazılar) güncellendi
                        fig = px.scatter(df_plot, x='X', y='Y', color='Category', 
                                         hover_data={'Title': True, 'Company': True, 'Link': True, 'X': False, 'Y': False}, 
                                         title="Semantic Similarity Map (You vs. Market)", 
                                         template="plotly_dark",
                                         color_discrete_map={"🎯 MY CV": "#ef4444"}) 
                        
                        fig.update_traces(marker=dict(size=12, opacity=0.85, line=dict(width=1, color='DarkSlateGrey')))
                        
                        for i, trace in enumerate(fig.data):
                            if trace.name == "🎯 MY CV":
                                trace.marker.symbol = 'star'
                                trace.marker.size = 20
                        
                        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=350, 
                                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)') 
                        
                        st.plotly_chart(fig, use_container_width=True)
                        # Kullanıcıya ufak bir ipucu:
                        st.caption("💡 *Tip: Hover over a dot to see the job title and apply link!*")
                    except Exception as e:
                        st.error(f"Galaxy map could not be generated: {e}")
            else:
                st.info("Not enough jobs found to generate the Galaxy Map. Try a broader search.")

# --- RIGHT PANEL: CHATBOT WIDGET ---
with chat_col:
    is_chat_expanded = True if cv_file else False
    
    with st.expander("💬 Chat with AI Career Assistant", expanded=is_chat_expanded):
        
        c1, c2 = st.columns([3, 1])
        if c2.button("🗑️ Clear", help="Reset Memory"):
            st.session_state.messages = [{"role": "assistant", "content": "Memory cleared! How can I help your career today? 😊"}]
            chatbot.reset_chat_session()
            st.session_state.cv_text = ""
            st.session_state.last_cv_name = ""
            st.rerun()

        chat_container = st.container(height=450)
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    user_html = f"""
                    <div style='display: flex; justify-content: flex-end; align-items: center; margin-bottom: 15px;'>
                        <div style='background-color: #10B981; color: white; padding: 12px 18px; border-radius: 18px 18px 0px 18px; margin-right: 10px; max-width: 80%; word-wrap: break-word;'>
                            {message['content']}
                        </div>
                        <div style='font-size: 24px;'>👤</div>
                    </div>
                    """
                    st.markdown(user_html, unsafe_allow_html=True)
                else:
                    with st.chat_message("assistant", avatar="💬"):
                        st.markdown(message["content"])

        user_input = st.chat_input("Ask for career advice...")
        
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with chat_container:
                
                user_html = f"""
                <div style='display: flex; justify-content: flex-end; align-items: center; margin-bottom: 15px;'>
                    <div style='background-color: #10B981; color: white; padding: 12px 18px; border-radius: 18px 18px 0px 18px; margin-right: 10px; max-width: 80%; word-wrap: break-word;'>
                        {user_input}
                    </div>
                    <div style='font-size: 24px;'>👤</div>
                </div>
                """
                st.markdown(user_html, unsafe_allow_html=True)
                
                with st.chat_message("assistant", avatar="💬"):
                    response_placeholder = st.empty()
                    full_response = ""
                    for chunk in chatbot.generate_response_stream(user_input, st.session_state.jobs, st.session_state.cv_text):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()