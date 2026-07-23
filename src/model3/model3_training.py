import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
import umap
import hdbscan
import warnings

warnings.filterwarnings('ignore')

def clean_seniority_words(text):
    text = str(text).lower()
    pattern = r'\b(senior|junior|mid-level|mid|lead|Middle|Leader|manager|Part time|Working|student|intern|Kıdemli|stajyer|uzman|specialist)\b'

    text = re.sub(pattern, '', text)

    return " ".join(text.split())

def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)
    
    df['Cleaned_Title'] = df['Job_Title'].apply(clean_seniority_words)
    df['Combined_Text'] = df['Cleaned_Title'].fillna('').astype(str) + " " + \
                          df['Required_Skills'].fillna('').astype(str) + " " + \
                          df['Job_Description'].fillna('').astype(str)                   
    return df

def perform_advanced_clustering(df):
    tr_stop_words = ['ve', 'veya', 'ile', 'için', 'bir', 'bu', 'da', 'de', 'gibi', 'olarak', 'olan', 'göre', 'en', 'daha', 'çok', 'var', 'yok', 'nan', 'yıl', 'tecrübe', 'çalışma', 'ekip', 'aranan', 'nitelikler']
    custom_stop_words = list(ENGLISH_STOP_WORDS) + tr_stop_words
    
    tfidf = TfidfVectorizer(max_features=7000, stop_words=custom_stop_words)
    X_tfidf = tfidf.fit_transform(df['Combined_Text'])
    
    reducer = umap.UMAP(n_neighbors=15, n_components=2, metric='cosine', random_state=42)
    X_umap = reducer.fit_transform(X_tfidf)
    
    min_cluster_sizes = [5, 10, 15, 20, 25, 30, 50]
    min_samples_list = [3, 5, 10, 15]
    
    best_score = -1.0
    best_params = {}
    best_clusterer = None
    
    for mcs in min_cluster_sizes:
        for ms in min_samples_list:
            clusterer = hdbscan.HDBSCAN(min_cluster_size=mcs, min_samples=ms, metric='euclidean', gen_min_span_tree=True)
            cluster_labels = clusterer.fit_predict(X_umap)
            
            total_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            noise_ratio = list(cluster_labels).count(-1) / len(cluster_labels)
            
            if total_clusters > 1 and noise_ratio < 0.5:
                dbcv_score = clusterer.relative_validity_
                print(f" Trying -> mcs: {mcs:2d} | ms: {ms:2d} | Clusters: {total_clusters:2d} | DBCV: {dbcv_score:.4f}")
                
                if dbcv_score > best_score:
                    best_score = dbcv_score
                    best_params = {'min_cluster_size': mcs, 'min_samples': ms}
                    best_clusterer = clusterer
    
    if best_clusterer is None:
        return

    print("="*55)
    print(f"Best Parameters: {best_params}")
    print(f"Highest DBCV Score: {best_score:.4f}")
    print("="*55)
    
    cluster_labels = best_clusterer.labels_

    total_ads = len(cluster_labels)
    noise_count = list(cluster_labels).count(-1)
    noise_rate = (noise_count / total_ads) * 100
    cluster_number = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)

    print("\n--- SCORE TRAP CONTROL REPORT ---")
    print(f"Total Number of Ads: {total_ads}")
    print(f"Net Number of Clusters: {cluster_number}")
    print(f"Excluded Ads (Noise): {noise_count}")
    print(f"Noise Rate: %{noise_rate:.2f}")
    
    if noise_rate > 40.0:
        print("WARNING: The model may be trapped! The noise level is very high.")
    elif noise_rate < 5.0:
        print("WARNING: The model is very challenging! It may be forcibly grouping dissimilar ads together.")
    else:
        print("GREAT: Noise level meets industry standards.")


    df['Cluster_ID'] = cluster_labels
    df[['Job_Title', 'Required_Skills', 'Cluster_ID']].to_csv('data/processed/clustered_preview.csv', index=False)
    
    df_plot = pd.DataFrame(X_umap, columns=['X', 'Y'])
    df_plot['Cluster'] = cluster_labels
    
    plt.figure(figsize=(12, 8))
    
    noise_data = df_plot[df_plot['Cluster'] == -1]
    plt.scatter(noise_data['X'], noise_data['Y'], color='lightgrey', s=20, alpha=0.5, label='Gürültü (-1)')
    
    cluster_data = df_plot[df_plot['Cluster'] != -1]
    sns.scatterplot(data=cluster_data, x='X', y='Y', hue='Cluster', palette='tab20', s=40, legend='full', alpha=0.9)
    
    plt.title(f"UMAP + HDBSCAN (Best Settings: mcs={best_params['min_cluster_size']}, ms={best_params['min_samples']})", fontsize=14, fontweight='bold') 
    plt.xlabel('UMAP Size 1') 
    plt.ylabel('UMAP Size 2') 
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='Clusters')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    filepath = "data/processed/cleaned_data.csv"
    df = load_and_prepare_data(filepath)
    perform_advanced_clustering(df)