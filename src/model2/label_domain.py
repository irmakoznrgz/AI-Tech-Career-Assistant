import pandas as pd
import numpy as np
import time

DOMAIN_PATTERNS = {
    'Full Stack': r'\b(full stack|full-stack|fullstack)\b',
    'Cybersecurity': r'\b(security|cyber|güvenlik|siber|penetration|pentest|soc|threat|audit|risk|compliance)\b',
    'DevOps & Cloud': r'\b(devops|cloud|aws|azure|gcp|kubernetes|docker|ci/cd)\b',
    'Data & AI': r'\b(data|veri|machine learning|ai|yapay zeka|bi|sql|analytics|scientist|big data)\b',
    'Mobile': r'\b(ios|android|mobile|mobil|flutter|react native|swift|kotlin)\b',
    'QA & Testing': r'\b(qa|test|quality|automation|tester)\b',
    'Product & Business Analysis': r'\b(product|ürün|business analyst|iş analisti|scrum|agile|project|proje|owner)\b',
    'System, Network & IT Ops': r'\b(system|sistem|network|ağ|it ops|support|helpdesk|help desk|altyapı|infrastructure|bilgi işlem)\b',
    'Frontend': r'\b(frontend|front-end|ui|ux|react|angular|vue|javascript)\b',
    'Backend': r'\b(backend|back-end|java|c#|\.net|python|node|php|golang|c\+\+)\b',
    'Database Administration': r'\b(dba|database|veritabanı|oracle|mssql|mysql)\b',
    'UI/UX & Design': r'\b(tasarım|designer|grafik|graphic|figma)\b',
    'Game Development': r'\b(game|oyun|unity|unreal)\b',
    'General Software': r'\b(yazılım|software|developer|geliştirici|engineer|mühendis|programmer)\b'
}

def process_and_label_data():
    start_time = time.time()

    df = pd.read_csv("data/processed/cleaned_data.csv")

    titles = df['Job_Title'].fillna('').astype(str).str.lower().str.strip()
    if 'Required_Skills' in df.columns:
        skills = df['Required_Skills'].fillna('').astype(str).str.lower().str.strip()
    else:
        skills = pd.Series([""] * len(df))

    conditions = []
    choices = []
 
    for domain, pattern in DOMAIN_PATTERNS.items():
        if domain != 'General Software':
            conditions.append(titles.str.contains(pattern, regex=True, na=False))
            choices.append(domain)

    for domain, pattern in DOMAIN_PATTERNS.items():
        if domain != 'General Software':
            conditions.append(skills.str.contains(pattern, regex=True, na=False))
            choices.append(domain)
            
    conditions.append(titles.str.contains(DOMAIN_PATTERNS['General Software'], regex=True, na=False))
    choices.append('General Software')

    df['Job_Domain'] = np.select(conditions, choices, default='Other')

    print("="*50)
    print("CATEGORY DISTRIBUTION:")
    print("="*50)
    print(df['Job_Domain'].value_counts())

    df_filtered = df[df['Job_Domain'] != 'Other'].copy()

    print(f"\n-> Total Tagged IT Ads: {len(df_filtered)}")
   
    output_path = "data/processed/labeled_domain_data.csv"
    df_filtered.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    print(f"-> Data labeled [SUCCESSFUL] was saved to the following location: {output_path}")

    print(f"-> Process completed in {end_time - start_time:.4f} seconds (milliseconds).")

if __name__ == "__main__":
    process_and_label_data()