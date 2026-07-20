import pandas as pd
import re

def assign_domain(title):
    title = str(title).lower().strip()

    domains = {
        'Product & Business Analysis': r'\b(product|ürün|business analyst|iş analisti|scrum|agile|project|proje|owner)\b',

        'Cybersecurity': r'\b(security|cyber|güvenlik|siber|penetration|pentest|soc)\b',

        'System, Network & IT Ops': r'\b(system|sistem|network|ağ|it ops|support|helpdesk|help desk|altyapı|infrastructure)\b',

        'Data & AI': r'\b(data|veri|machine learning|ai|yapay zeka|bi|sql|analytics|scientist)\b',

        'DevOps & Cloud': r'\b(devops|cloud|aws|azure|gcp|kubernetes|docker|ci/cd)\b',

        'Mobile': r'\b(ios|android|mobile|mobil|flutter|react native|swift|kotlin)\b',

        'QA & Testing': r'\b(qa|test|quality|automation|tester)\b',

        'Frontend': r'\b(frontend|front-end|ui|ux|react|angular|vue|javascript)\b',

        'Backend': r'\b(backend|back-end|java|c#|\.net|python|node|php|golang|c\+\+)\b',

        'Full Stack': r'\b(full stack|full-stack|fullstack)\b'
    }
    
    for domain, pattern in domains.items():
        if re.search(pattern, title):
            return domain
            
    return 'Other'

def process_and_label_data():
    df = pd.read_csv("data/processed/cleaned_data.csv")
    
    df['Job_Domain'] = df['Job_Title'].apply(assign_domain)
    
    print("="*50)
    print("CATEGORY DISTRIBUTION CREATED:")
    print("="*50)
    print(df['Job_Domain'].value_counts())
    
    df_filtered = df[df['Job_Domain'] != 'Other'].copy()

    print(f"\n-> Total Data: {len(df_filtered)}")
    
    output_path = "data/processed/labeled_domain_data.csv"

    df_filtered.to_csv(output_path, index=False)
    print(f"-> [SUCCESS] Labeled data saved to: {output_path}")

if __name__ == "__main__":
    process_and_label_data()