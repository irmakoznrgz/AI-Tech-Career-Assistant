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
        background-color: white; 
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
    
    div[data-testid="column"] button {{
        width: 100%;
        padding: 0.25rem 0.5rem;
    }}
    </style>
""", unsafe_allow_html=True)

# --- SYSTEM INIT ---
@st.cache_resource(show_spinner="Loading AI Engine... Please wait!")
def init_bot():
    return AITechCareerChatbot()

chatbot = init_bot()

# --- OTURUM YÖNETİMİ ---
if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "Hello, how can I help your career today? 😊"}]
if "current_page" not in st.session_state: st.session_state.current_page = 1
if "cv_text" not in st.session_state: st.session_state.cv_text = ""
if "last_cv_name" not in st.session_state: st.session_state.last_cv_name = ""
if "search_performed" not in st.session_state: st.session_state.search_performed = False
if "file_uploader_key" not in st.session_state: st.session_state.file_uploader_key = 0

# YENİ: Favoriler için değişkenler
if "saved_jobs" not in st.session_state: st.session_state.saved_jobs = {} # Kaydedilen ilanları tutan sözlük
if "view_mode" not in st.session_state: st.session_state.view_mode = "search" # 'search' veya 'saved' modu

if "jobs" not in st.session_state:
    st.session_state.jobs = chatbot.search_jobs_for_ui(limit=50)

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

domain_keywords = {
    'Product & Business Analysis': 'product ürün business analyst iş analisti scrum agile project proje owner',
    'Cybersecurity': 'security cyber güvenlik siber penetration pentest soc',
    'System, Network & IT Ops': 'system sistem network ağ it ops support helpdesk help desk altyapı infrastructure',
    'Data & AI': 'data veri machine learning ai yapay zeka bi sql analytics scientist',
    'DevOps & Cloud': 'devops cloud aws azure gcp kubernetes docker ci cd',
    'Mobile': 'ios android mobile mobil flutter react native swift kotlin',
    'QA & Testing': 'qa test quality automation tester',
    'Frontend': 'frontend front-end ui ux react angular vue javascript',
    'Backend': 'backend back-end java c# .net python node php golang c++',
    'Full Stack': 'full stack full-stack fullstack'
}

def build_filters(forced_exp=None):
    conditions = []
    if job_type_filter != "All Types": conditions.append({"work_model": job_type_filter})
    if city_filter != "All Locations": conditions.append({"location": city_filter})
    final_exp = forced_exp if forced_exp else (exp_level if exp_level != "All Levels" else None)
    if final_exp: conditions.append({"experience": final_exp})
    
    if not conditions: return None
    elif len(conditions) == 1: return conditions[0]
    else: return {"$and": conditions}

st.write("") 
# YENİ: Arama çubuğu tasarımına "Kaydedilenler" butonu eklendi
btn_col, cv_col, saved_col = st.columns([1.5, 2, 1.5])
search_btn = btn_col.button("🔍 Search Jobs", use_container_width=True)
cv_file = cv_col.file_uploader("📄 Magic Search with CV (PDF)", type=["pdf"], label_visibility="collapsed", key=f"uploader_{st.session_state.file_uploader_key}")
saved_btn = saved_col.button(f"🔖 Saved Jobs ({len(st.session_state.saved_jobs)})", use_container_width=True)

# Görünüm Modu Değiştiricileri
if saved_btn:
    st.session_state.view_mode = "saved"
    st.session_state.current_page = 1
    
if cv_file is None and st.session_state.cv_text != "":
    st.session_state.cv_text = ""
    st.session_state.last_cv_name = ""
    ui_filters = build_filters(forced_exp=None)
    search_query = domain_keywords.get(domain_filter, "") if domain_filter != "All Domains" else "yazılım bilişim teknoloji veri uzman geliştirici mühendis"
    st.session_state.jobs = chatbot.search_jobs_for_ui(search_query=search_query, ui_filters=ui_filters, limit=None)
    st.session_state.view_mode = "search"
    st.rerun()

if search_btn or (cv_file and cv_file.name != st.session_state.last_cv_name):
    st.session_state.search_performed = True
    st.session_state.view_mode = "search" # Aramaya basınca sonuçlara geri dön
    forced_exp = None
    search_query = "yazılım bilişim teknoloji veri uzman geliştirici mühendis" 
    
    if cv_file is not None:
        st.session_state.last_cv_name = cv_file.name
        pdf_reader = PyPDF2.PdfReader(cv_file)
        cv_text = " ".join([page.extract_text() for page in pdf_reader.pages])
        st.session_state.cv_text = cv_text 
        
        cv_text_lower = cv_text.lower()
        if any(kw in cv_text_lower for kw in ["öğrenci", "student", "stajyer", "intern", "bachelor"]):
            forced_exp = "Junior"
            st.toast("Student profile detected! Forcing Junior/Intern roles.", icon="🎓")
            
        tech_keywords = ["python", "java", "c#", "c++", "sql", "react", "node", "aws", "azure", "docker", "kubernetes", "machine learning", "data science", "excel", "powerbi", "javascript"]
        found_skills = [skill for skill in tech_keywords if skill in cv_text_lower]
        
        if found_skills: search_query = " ".join(found_skills) + " " + cv_text[:500]
        else: search_query = cv_text[:1000] 
        st.toast("CV Analyzed! Displaying tailored jobs...", icon="✨")
        
        if len(st.session_state.messages) <= 1:
            st.session_state.messages = [{"role": "assistant", "content": f"I've analyzed your CV! 🚀 I noticed your skills in **{', '.join(found_skills[:3])}**. I've listed the most suitable jobs on the left."}]

    if domain_filter != "All Domains":
        if not st.session_state.cv_text: search_query = domain_keywords.get(domain_filter, "")
        else: search_query += " " + domain_keywords.get(domain_filter, "")

    ui_filters = build_filters(forced_exp=forced_exp)
    st.session_state.jobs = chatbot.search_jobs_for_ui(search_query=search_query, ui_filters=ui_filters, limit=None)
    st.session_state.current_page = 1

# --- SPLIT SCREEN ---
st.write("---")
main_col, chat_col = st.columns([2, 1], gap="large")

with main_col:
    # Hangi listenin gösterileceğini belirleme (Arama Sonuçları mı yoksa Kaydedilenler mi?)
    if st.session_state.view_mode == "saved":
        display_jobs = list(st.session_state.saved_jobs.values())
        title_prefix = "🔖 Your Saved Jobs"
    else:
        display_jobs = st.session_state.jobs
        title_prefix = "Found Jobs" if st.session_state.search_performed else "Trending Jobs"
    
    if len(display_jobs) == 0:
        if st.session_state.view_mode == "saved":
            st.info("You haven't saved any jobs yet. Browse jobs and click '❤️ Save' to add them here.")
        elif st.session_state.search_performed:
            st.warning("⚠️ No jobs found matching your selected criteria. Please try broadening your filters.")
    else:
        st.subheader(f"{title_prefix} ({len(display_jobs)})")
        
        items_per_page = 5
        total_pages = math.ceil(len(display_jobs) / items_per_page) if display_jobs else 1
        
        if st.session_state.current_page > total_pages: st.session_state.current_page = max(1, total_pages)
            
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        for job in display_jobs[start_idx:end_idx]:
            logo_url = str(job.get('logo', '')).strip()
            if logo_url and len(logo_url) > 5 and logo_url.lower() != "none":
                logo_html = f'<img src="{logo_url}" class="job-logo" onerror="this.onerror=null; this.outerHTML=\'<div class=\\\'job-logo-fallback\\\'>🏢</div>\';">'
            else: logo_html = '<div class="job-logo-fallback">🏢</div>'
                
            match_score = job.get("match_score", 0)
            match_badge = f'<span style="background-color: #ef4444; color: white; font-weight: bold;">🔥 %{match_score} Match</span>' if st.session_state.cv_text and match_score else ""
            
            domain_tag = job.get('domain', 'Unknown')
            if domain_filter != "All Domains" and domain_tag == "Unknown": domain_tag = domain_filter 

            tags_html = ""
            if match_badge: tags_html += match_badge
            
            loc = job.get("location", "")
            if loc and loc not in ["Unknown", "Not specified"]: tags_html += f"<span>📍 {loc}</span>"
            wm = job.get("work_model", "")
            if wm and wm not in ["Unknown", "Not specified"]: tags_html += f"<span>💼 {wm}</span>"
            exp = job.get("experience", "")
            if exp and exp not in ["Unknown", "Not specified"]: tags_html += f"<span>⭐ {exp}</span>"
            if domain_tag and domain_tag not in ["Unknown", "Not specified", "All Domains"]: tags_html += f"<span>🏷️ {domain_tag}</span>"

            html_card = f'<div class="job-card"><div class="job-header-container">{logo_html}<div><div class="job-title">{job["title"]}</div><div class="job-company">{job["company"]}</div></div></div><div class="job-tags">{tags_html}</div></div>'
            st.markdown(html_card, unsafe_allow_html=True)
            
            # YENİ: İlan Detayı ve Save/Remove Butonları Yan Yana
            exp_col, save_col = st.columns([5, 1.2])
            with exp_col:
                with st.expander("View Job Details"):
                    st.write(job['description'])
                    st.markdown(f"[Apply Here]({job['link']})")
            
            with save_col:
                job_id = job.get('id', '')
                if job_id in st.session_state.saved_jobs:
                    # Kayıtlıysa Çıkar Butonu
                    if st.button("❌ Remove", key=f"remove_{job_id}_{st.session_state.view_mode}", use_container_width=True):
                        del st.session_state.saved_jobs[job_id]
                        st.rerun()
                else:
                    # Kayıtlı Değilse Ekle Butonu
                    if st.button("❤️ Save", key=f"save_{job_id}_{st.session_state.view_mode}", use_container_width=True):
                        st.session_state.saved_jobs[job_id] = job
                        st.rerun()
                
        # --- SAYFALAMA ---
        st.write("")
        if total_pages > 1:
            window_size = 5
            start_page = max(1, st.session_state.current_page - window_size // 2)
            end_page = min(total_pages, start_page + window_size - 1)
            
            if end_page - start_page + 1 < window_size: start_page = max(1, end_page - window_size + 1)
            num_buttons = (end_page - start_page + 1) + 2
            spacer_left, pagination_content, spacer_right = st.columns([1, num_buttons, 1])
            
            with pagination_content:
                cols = st.columns(num_buttons)
                if cols[0].button("⬅️", disabled=(st.session_state.current_page == 1), key="prev_btn", use_container_width=True):
                    st.session_state.current_page -= 1
                    st.rerun()
                for i, p_num in enumerate(range(start_page, end_page + 1)):
                    is_active = (p_num == st.session_state.current_page)
                    btn_type = "primary" if is_active else "secondary"
                    if cols[i+1].button(str(p_num), type=btn_type, key=f"page_{p_num}", use_container_width=True):
                        st.session_state.current_page = p_num
                        st.rerun()
                if cols[-1].button("➡️", disabled=(st.session_state.current_page == total_pages), key="next_btn", use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()
            
        # MODEL 3: KARIYER GALAKSISI (Sadece Arama Modunda Çıkar)
        if st.session_state.view_mode == "search":
            st.write("---")
            with st.expander("🌌 View Career Galaxy (Job Clustering Map)", expanded=False):
                if len(display_jobs) > 3:
                    if st.button("🚀 Generate AI Galaxy Map", use_container_width=True):
                        with st.spinner("Mapping your CV in the AI Galaxy..."):
                            try:
                                texts_for_map = [j['description'] for j in display_jobs]
                                labels = [j['experience'] for j in display_jobs]
                                titles = [j['title'] for j in display_jobs]
                                companies = [j['company'] for j in display_jobs]
                                links = [j['link'] for j in display_jobs]
                                
                                if st.session_state.cv_text:
                                    texts_for_map.append(st.session_state.cv_text)
                                    labels.append("🎯 MY CV")
                                    titles.append("Your Profile")
                                    companies.append("You")
                                    links.append("N/A")

                                embeddings = chatbot.sentence_transformer_ef(texts_for_map)
                                pca = PCA(n_components=2)
                                coords = pca.fit_transform(embeddings)
                                
                                df_plot = pd.DataFrame({
                                    'X': coords[:, 0], 'Y': coords[:, 1], 'Title': titles, 
                                    'Company': companies, 'Category': labels, 'Link': links 
                                })
                                
                                fig = px.scatter(df_plot, x='X', y='Y', color='Category', 
                                                 hover_data={'Title': True, 'Company': True, 'Link': True, 'X': False, 'Y': False}, 
                                                 title="Semantic Similarity Map (You vs. Market)", 
                                                 template="plotly_dark", color_discrete_map={"🎯 MY CV": "#ef4444"}) 
                                fig.update_traces(marker=dict(size=12, opacity=0.85, line=dict(width=1, color='DarkSlateGrey')))
                                for i, trace in enumerate(fig.data):
                                    if trace.name == "🎯 MY CV":
                                        trace.marker.symbol = 'star'
                                        trace.marker.size = 20
                                fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)') 
                                st.plotly_chart(fig, use_container_width=True)
                                
                                if st.session_state.cv_text:
                                    st.markdown("### 🎯 Top 3 Jobs Closest to Your CV")
                                    for top_job in display_jobs[:3]:
                                        st.markdown(f"- **[{top_job['title']} at {top_job['company']}]({top_job['link']})** (🔥 %{top_job.get('match_score', 0)} Match)")
                            except Exception as e:
                                st.error(f"Galaxy map could not be generated: {e}")
                else:
                    st.info("Not enough jobs found to generate the Galaxy Map. Try a broader search.")

# --- RIGHT PANEL: CHATBOT WIDGET ---
with chat_col:
    with st.expander("💬 Chat with AI Career Assistant", expanded=False):
        c1, c2 = st.columns([3, 1])
        if c2.button("🗑️ Clear", help="Reset Memory"):
            st.session_state.messages = [{"role": "assistant", "content": "Memory cleared! How can I help your career today? 😊"}]
            chatbot.reset_chat_session()
            st.session_state.cv_text = ""
            st.session_state.last_cv_name = ""
            st.session_state.file_uploader_key += 1 
            st.session_state.search_performed = False
            st.session_state.view_mode = "search"
            ui_filters = build_filters(forced_exp=None)
            st.session_state.jobs = chatbot.search_jobs_for_ui(ui_filters=ui_filters, limit=50)
            st.rerun()

        chat_container = st.container(height=450)
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    user_html = f"<div style='display: flex; justify-content: flex-end; align-items: center; margin-bottom: 15px;'><div style='background-color: #10B981; color: white; padding: 12px 18px; border-radius: 18px 18px 0px 18px; margin-right: 10px; max-width: 80%; word-wrap: break-word;'>{message['content']}</div><div style='font-size: 24px;'>👤</div></div>"
                    st.markdown(user_html, unsafe_allow_html=True)
                else:
                    with st.chat_message("assistant", avatar="💬"):
                        st.markdown(message["content"])

        user_input = st.chat_input("Ask for career advice...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with chat_container:
                user_html = f"<div style='display: flex; justify-content: flex-end; align-items: center; margin-bottom: 15px;'><div style='background-color: #10B981; color: white; padding: 12px 18px; border-radius: 18px 18px 0px 18px; margin-right: 10px; max-width: 80%; word-wrap: break-word;'>{user_input}</div><div style='font-size: 24px;'>👤</div></div>"
                st.markdown(user_html, unsafe_allow_html=True)
                
                with st.chat_message("assistant", avatar="💬"):
                    response_placeholder = st.empty()
                    full_response = ""
                    # Hangi ekrandaysak chatbot'a o veriyi yolla (Arananlar veya Kaydedilenler)
                    chat_jobs = list(st.session_state.saved_jobs.values()) if st.session_state.view_mode == "saved" else st.session_state.jobs
                    for chunk in chatbot.generate_response_stream(user_input, chat_jobs, st.session_state.cv_text):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()