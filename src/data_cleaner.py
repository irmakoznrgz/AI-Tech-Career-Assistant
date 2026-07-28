import pandas as pd
import os
import json
import re
from datetime import datetime

def load_jsonl_files(raw_dir):
    all_data = []
    files = ["kariyer.jsonl", "techcareer.jsonl", "youthall.jsonl", "indeed.jsonl", "linkedin.jsonl"]
    
    for file in files:
        filepath = os.path.join(raw_dir, file)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            all_data.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        else:
            print(f"[WARNING] {file} not found, skipping...")
            
    return pd.DataFrame(all_data)

def extract_work_model(text):
    text = str(text).lower()
    if 'uzaktan' in text or 'remote' in text: return 'Remote'
    if 'hibrit' in text or 'hybrid' in text: return 'Hybrid'
    return 'On-site'

def clean_city_name(text):
    text = str(text).lower()
    
    if 'istanbul' in text or 'i̇stanbul' in text: return 'İstanbul'
    if 'izmir' in text or 'i̇zmir' in text: return 'İzmir'
    if 'ankara' in text: return 'Ankara'
    if 'bursa' in text: return 'Bursa'
    if 'kocaeli' in text: return 'Kocaeli'
    if 'antalya' in text: return 'Antalya'
    if 'eskişehir' in text or 'eskisehir' in text: return 'Eskişehir'
    
    text = re.sub(r'uzaktan|remote|hibrit|hybrid|türkiye|turkiye|turkey|iş yerinde|Serbest Zamanlı|i̇ş yerinde|asya|avrupa|\(|\)|-|/|,|\d+', ' ', text)
    text = ' '.join(text.split())
    
    if not text or text == 'nan': 
        return 'Not specified'
        
    return text.title()

def extract_skills_from_desc(desc):
    desc = str(desc).lower()
    tech_pool = [
        'python', 'java', 'c#', '.net', 'c++', 'javascript', 'typescript', 'react', 
        'angular', 'vue', 'node', 'sql', 'mysql', 'postgresql', 'mongodb', 'nosql',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux', 'git', 'ci/cd',
        'machine learning', 'deep learning', 'yapay zeka', 'nlp', 'data science', 
        'hadoop', 'spark', 'pytorch', 'tensorflow', 'excel', 'power bi', 'tableau'
    ]
    found_skills = [tech for tech in tech_pool if tech in desc]
    return ", ".join(found_skills) if found_skills else "Not specified"

def extract_experience_level(title, desc):
    title = str(title).lower()
    desc = str(desc).lower()

    if any(w in title for w in ['lead', 'manager', 'director', 'head', 'vp', 'müdür', 'baş']):
        return 'Lead/Manager'
    if any(w in title for w in ['senior', 'kıdemli', 'sr.', 'snr']):
        return 'Senior'
    if any(w in title for w in ['junior', 'jr.', 'yeni mezun', 'stajyer', 'intern', 'new grad']):
        return 'Junior'
    if any(w in title for w in ['mid-level', 'mid level', 'orta seviye']):
        return 'Mid-Level'
    
    if any(w in desc for w in ['lead', 'manager', 'director', 'yöneticisi']):
        return 'Lead/Manager'
    if any(w in desc for w in ['senior', 'kıdemli', 'en az 5 yıl', 'minimum 5 years']):
        return 'Senior'
    if any(w in desc for w in ['junior', 'yeni mezun', 'new grad', 'tecrübesiz', 'deneyimsiz']):
        return 'Junior'
    if any(w in desc for w in ['mid-level', 'orta seviye', 'en az 2 yıl', 'en az 3 yıl']):
        return 'Mid-Level'
        
    return 'Not specified'

def clean_data(df):
    print(f"-> Starting: Total {len(df)} raw job postings found.")

    df = df.drop_duplicates(subset=['Job_Link'], keep='first')
    
    df['temp_title'] = df['Job_Title'].astype(str).str.lower().str.strip()
    df['temp_company'] = df['Company'].astype(str).str.lower().str.strip()
    df['desc_length'] = df['Job_Description'].astype(str).str.len()
    df = df.sort_values(by='desc_length', ascending=False)
    df = df.drop_duplicates(subset=['temp_title', 'temp_company'], keep='first')
    df = df.drop(columns=['temp_title', 'temp_company', 'desc_length'])

    if 'Posting_Type' in df.columns:
        df['Job_Type'] = df['Job_Type'].fillna(df['Posting_Type'])
        df = df.drop(columns=['Posting_Type'])

    df['Location_Details'] = df['Location_Details'].fillna("N/A")
    df['Work_Model'] = df['Location_Details'].apply(extract_work_model)
    df['Location_Details'] = df['Location_Details'].apply(clean_city_name)
    
    def standardize_job_type(row):
        title = str(row['Job_Title']).lower()
        j_type = str(row['Job_Type']).lower()
        
        if "staj" in title or "intern" in title: return "Intern"
        if "yarı" in title or "part" in title: return "Part-time"
        if "freelance" in title: return "Freelance"
        
        if "yarı" in j_type or "part" in j_type: return "Part-time"
        if "staj" in j_type or "intern" in j_type: return "Intern"
        if "freelance" in j_type or "serbest" in j_type: return "Freelance"
        
        return "Full-time" 
        
    df['Job_Type'] = df.apply(standardize_job_type, axis=1)

    if 'Required_Skills' not in df.columns:
        df['Required_Skills'] = "Not specified"
        
    df['Required_Skills'] = df['Required_Skills'].fillna("Not specified")
    mask = (df['Required_Skills'] == "Not specified") | (df['Required_Skills'] == "")
    df.loc[mask, 'Required_Skills'] = df.loc[mask, 'Job_Description'].apply(extract_skills_from_desc)

    print("-> Extracting Experience Level...")
    df['Experience_Level'] = df.apply(lambda row: extract_experience_level(row['Job_Title'], row['Job_Description']), axis=1)

    blacklist = [
        "iç mimar", "peyzaj", "inşaat", "makine", "elektrik", "elektronik", 
        "endüstri", "gıda", "ziraat", "biyomedikal", "çevre", "kimya", "harita",
        "satış", "pazarlama", "ik ", "insan kaynakları", "muhasebe", "finans", 
        "halkla ilişkiler", "sekreter", "asistan", "şoför", "kurye", "depo", 
        "çağrı merkezi", "garson", "kasiyer", "temizlik", "güvenlik görevlisi",
        "öğretmen", "hemşire", "doktor", "avukat", "tesisat", "mekanik","müşteri ilişkileri", 
        "satış temsilcisi", "satış danışmanı", "satış uzmanı", "köpek eğitmeni", "müşteri hizmetleri" 
    ]
    
    df = df[~df['Job_Title'].astype(str).str.lower().apply(lambda x: any(b in x for b in blacklist))]

    print(f"-> Number of Remaining IT Job Postings: {len(df)}")
    return df

def main():
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)
    
    df_raw = load_jsonl_files(raw_dir)
    
    if df_raw.empty:
        print("[ERROR] No data found to clear!")
        return
        
    df_clean = clean_data(df_raw)
    
    output_path = os.path.join(processed_dir, "cleaned_data.csv")
    df_clean.to_csv(output_path, index=False, encoding='utf-8-sig') 
    print(f"SUCCESS: Cleaned data saved to '{output_path}'!")

if __name__ == "__main__":
    main()