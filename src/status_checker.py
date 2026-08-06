import asyncio
import chromadb
import os
import random
from patchright.async_api import async_playwright

DB_PATH = "data/chroma_db"
COLLECTION_NAME = "job_postings"

CLOSED_KEYWORDS = [
    "başvuru kabul etmiyor", 
    "bu ilan başvuruları artık kabul etmiyor", 
    "bu ilan artık başvuruları kabul etmiyor", 
    "yayından kaldırılmıştır", 
    "başvuru süresi dolmuştur",
    "başvuruya kapanmıştır", 
    "ilan yayında değildir", 
    "no longer accepting applications", 
    "job is no longer available", 
    "posting has expired", 
    "artık başvuru kabul etmiyor",
    "bu iş ilanının süresi doldu" 
]

async def human_like_delay(min_sec=2.0, max_sec=5.0):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def check_job_status(page, url):
    try:
        await page.goto(url, timeout=35000, wait_until="domcontentloaded")
        await human_like_delay(2.5, 4.5)
        
        content = await page.content()
        content_lower = content.lower()
      
        for keyword in CLOSED_KEYWORDS:
            if keyword in content_lower:
                return False
        return True 
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return True

async def main():
    print("\n" + "="*50)
    print("STATUS CHECKER STARTED: Cleaning up closed jobs from DB")
    print("="*50)
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_full_path = os.path.join(project_root, DB_PATH)
    
    if not os.path.exists(db_full_path):
        print(f"[ERROR] Database path {db_full_path} not found.")
        return

    client = chromadb.PersistentClient(path=db_full_path)
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"[ERROR] Collection '{COLLECTION_NAME}' not found: {e}")
        return

    results = collection.get(include=['metadatas'])
    ids = results['ids']
    metadatas = results['metadatas']
    
    if not ids:
        print("Database is empty. Nothing to check.")
        return
        
    print(f"Found {len(ids)} jobs in the database. Starting verification...")
 
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        for i, (job_id, meta) in enumerate(zip(ids, metadatas)):
            url = meta.get('link', '')
            title = meta.get('title', 'Unknown Title')
            
            if not url or url == 'No link available':
                continue
                
            print(f"[{i+1}/{len(ids)}] Checking: {title[:40]}...")
            is_active = await check_job_status(page, url)
     
            if not is_active:
                print(f"  -> [CLOSED] Deleting immediately: {url}")
                try:
                    collection.delete(ids=[job_id])
                    print(f"  -> [SUCCESS] Removed from ChromaDB.")
                except Exception as e:
                    print(f"  -> [ERROR] Failed to delete: {e}")
            
            await human_like_delay(1.5, 3.5)
                
        await context.close()
        await browser.close()
        
    print("="*50)
    print("STATUS CHECKER COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())