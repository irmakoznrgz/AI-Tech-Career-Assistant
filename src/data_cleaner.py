import pandas as pd
import os
import json
import re
import time
from datetime import datetime

DISTRICT_MAP = {}
DISTRICT_PATTERN = None
csv_path = "data/city.csv"

if os.path.exists(csv_path):
    df_districts = pd.read_csv(csv_path)
    
    df_districts.columns = df_districts.columns.str.strip()
 
    raw_cities = df_districts['city'].str.strip().str.title()
    fixed_cities = raw_cities.str.replace('İS', 'İs', regex=False).str.replace('Istanbul', 'İstanbul', regex=False).str.replace('Izmir', 'İzmir', regex=False)
    
    DISTRICT_MAP = dict(zip(df_districts['district'].str.strip().str.lower(), fixed_cities))
    
    escaped_keys = [re.escape(k) for k in DISTRICT_MAP.keys()]
    DISTRICT_PATTERN = re.compile(r'\b(' + '|'.join(escaped_keys) + r')\b')
    print("[SYSTEM] Province-District reference file successfully loaded!")
else:
    print(f"[WARNING] '{csv_path}' not found! District scan will be skipped.")

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

def clean_city_name(text):
    text = str(text).lower()
    
    city_corrections = {
        'istanbul': 'İstanbul', 'i̇stanbul': 'İstanbul', 
        'izmir': 'İzmir', 'i̇zmir': 'İzmir', 
        'ankara': 'Ankara', 'bursa': 'Bursa', 
        'kocaeli': 'Kocaeli', 'antalya': 'Antalya', 
        'eskişehir': 'Eskişehir', 'eskisehir': 'Eskişehir',
        'izmit': 'Kocaeli' 
    }
    
    for key, correct_name in city_corrections.items():
        if key in text:
            return correct_name
 
    if DISTRICT_PATTERN:
        match = DISTRICT_PATTERN.search(text)
        if match:
            matched_district = match.group(1) 
            return DISTRICT_MAP[matched_district]
  
    text = re.sub(r'uzaktan|remote|hibrit|hybrid|türkiye|turkiye|turkey|iş yerinde|serbest zamanlı|i̇ş yerinde|asya|avrupa|\(|\)|-|/|,|\d+', ' ', text)
    text = ' '.join(text.split())
    
    if not text or text == 'nan' or text == 'not specified': 
        return 'Not specified'
    
    final_city = text.title()
    final_city = final_city.replace('İS', 'İs').replace('Istanbul', 'İstanbul').replace('Izmir', 'İzmir')
    return final_city

def extract_work_model(text):
    text = str(text).lower()
    if 'uzaktan' in text or 'remote' in text: return 'Remote'
    if 'hibrit' in text or 'hybrid' in text: return 'Hybrid'
    return 'On-site'

def extract_skills_from_desc(desc):
    desc = str(desc).lower()
    tech_pool = [
        'python', 'java', 'c#', '.net', 'c++', 'javascript', 'typescript', 'react', 
        'angular', 'vue', 'node', 'sql', 'mysql', 'postgresql', 'mongodb', 'nosql',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux', 'git', 'ci/cd',
        'machine learning', 'deep learning', 'yapay zeka', 'nlp', 'data science', 
        'hadoop', 'spark', 'pytorch', 'tensorflow', 'excel', 'power bi', 'tableau',
        'html', 'css', 'spring boot', 'django', 'flask', 'golang', 'rust', 'ruby', 'swift', 'kotlin'
    ]
    found_skills = [tech for tech in tech_pool if re.search(rf'\b{re.escape(tech)}\b', desc)]
    return ", ".join(found_skills) if found_skills else "Not specified"

def extract_experience_level(title, desc):
    title = str(title).lower()
    desc = str(desc).lower()

    if any(w in title for w in ['lead', 'manager', 'director', 'head', 'vp', 'müdür', 'baş']): return 'Lead/Manager'
    if any(w in title for w in ['senior', 'kıdemli', 'sr.', 'snr']): return 'Senior'
    if any(w in title for w in ['junior', 'jr.', 'yeni mezun', 'stajyer', 'intern', 'new grad']): return 'Junior'
    if any(w in title for w in ['mid-level', 'mid level', 'orta seviye']): return 'Mid-Level'
    
    if any(w in desc for w in ['lead', 'manager', 'director', 'yöneticisi']): return 'Lead/Manager'
    if any(w in desc for w in ['senior', 'kıdemli', 'en az 5 yıl', 'minimum 5 years', '5+ years']): return 'Senior'
    if any(w in desc for w in ['junior', 'yeni mezun', 'new grad', 'tecrübesiz', 'deneyimsiz']): return 'Junior'
    if any(w in desc for w in ['mid-level', 'orta seviye', 'en az 2 yıl', 'en az 3 yıl', '2+ years']): return 'Mid-Level'
        
    return 'Not specified'

def standardize_job_type(row):
    title = str(row.get('Job_Title', '')).lower()
    j_type = str(row.get('Job_Type', '')).lower()
    
    if "staj" in title or "intern" in title or "staj" in j_type or "intern" in j_type: return "Intern"
    if "yarı" in title or "part" in title or "yarı" in j_type or "part" in j_type: return "Part-time"
    if "freelance" in title or "freelance" in j_type or "serbest" in j_type: return "Freelance"
    
    return "Full-time" 

def clean_data(df):
    print(f"\n-> Starting: Total {len(df)} raw ads found.")
    
    if 'Withdrawal_Date' in df.columns:
        df['Withdrawal_Date'] = pd.to_datetime(df['Withdrawal_Date'], errors='coerce')
        df['first_seen'] = df.groupby('Job_Link')['Withdrawal_Date'].transform('min').dt.date
        df['last_seen'] = df.groupby('Job_Link')['Withdrawal_Date'].transform('max').dt.date
        df = df.drop(columns=['Withdrawal_Date'])
    else:
        today = datetime.now().date()
        df['first_seen'] = today
        df['last_seen'] = today

    df = df.drop_duplicates(subset=['Job_Link'], keep='first')
    df['temp_title'] = df['Job_Title'].astype(str).str.lower().str.strip()
    df['temp_company'] = df['Company'].astype(str).str.lower().str.strip()
    df = df.sort_values(by='last_seen', ascending=False)
    df = df.drop_duplicates(subset=['temp_title', 'temp_company'], keep='first')
    df = df.drop(columns=['temp_title', 'temp_company'])
    
    print(f"-> Copies deleted. Remaining unique ad: {len(df)}")

    if 'Posting_Type' in df.columns:
        df['Job_Type'] = df['Job_Type'].fillna(df['Posting_Type'])
        df = df.drop(columns=['Posting_Type'])
        
    df['Job_Type'] = df.apply(standardize_job_type, axis=1)

    df['Location_Details'] = df['Location_Details'].fillna("Not specified")
    df['Work_Model'] = df['Location_Details'].apply(extract_work_model)
    df['Location_Details'] = df['Location_Details'].apply(clean_city_name) 

    if 'Required_Skills' not in df.columns:
        df['Required_Skills'] = "Not specified"
        
    df['Required_Skills'] = df['Required_Skills'].fillna("Not specified")
    mask = (df['Required_Skills'] == "Not specified") | (df['Required_Skills'] == "") | (df['Required_Skills'] == "nan")
    df.loc[mask, 'Required_Skills'] = df.loc[mask, 'Job_Description'].apply(extract_skills_from_desc)

    df['Experience_Level'] = df.apply(lambda row: extract_experience_level(row['Job_Title'], row['Job_Description']), axis=1)

    blacklist = [
        "iç mimar", "peyzaj", "inşaat", "makine", "elektrik", "elektronik", 
        "endüstri", "gıda", "ziraat", "biyomedikal", "çevre", "kimya", "harita",
        "satış", "pazarlama", "ik ", "insan kaynakları", "muhasebe", "finans", 
        "halkla ilişkiler", "sekreter", "asistan", "şoför", "kurye", "depo", 
        "çağrı merkezi", "garson", "kasiyer", "temizlik", "güvenlik görevlisi",
        "öğretmen", "hemşire", "doktor", "avukat", "tesisat", "mekanik", "müşteri ilişkileri", "satış temsilcisi", "satış danışmanı", "satış uzmanı", "iş geliştirme", "sosyal medya", "kalite kontrol", "ürün uzmanı"
    ]
    
    df = df[~df['Job_Title'].astype(str).str.lower().apply(lambda x: any(b in x for b in blacklist))]

    print(f"-> Non-IT job postings have been eliminated. Number of remaining IT job postings: {len(df)}")
    return df

def main():
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)
    
    df_raw = load_jsonl_files(raw_dir)
    
    if df_raw.empty:
        print("[ERROR] No data found to clear!")
        return
        
    start_time = time.time()
    
    df_clean = clean_data(df_raw)
    
    output_path = os.path.join(processed_dir, "cleaned_data.csv")
    df_clean.to_csv(output_path, index=False, encoding='utf-8-sig') 
    
    end_time = time.time()
    print(f"\n[SUCCESSFUL] Operation completed! Total time: {end_time - start_time:.2f} seconds.")

    print(f"The cleaned data has been saved to '{output_path}'.")

if __name__ == "__main__":
    main()