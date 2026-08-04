import asyncio
import json
import os
import random
from datetime import datetime
from patchright.async_api import async_playwright

def load_seen_links(filepath):
    seen_links = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        seen_links.add(data.get("Job_Link"))
                    except json.JSONDecodeError:
                        continue
    return seen_links

def append_to_jsonl(filepath, data):
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

async def human_like_delay(min_sec=1.0, max_sec=3.0):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def simulate_human_behavior(page):
    width = page.viewport_size['width']
    height = page.viewport_size['height']
    await page.mouse.move(random.randint(100, width - 100), random.randint(100, height - 100))
    await human_like_delay(0.5, 1.5)

    await page.evaluate("window.scrollBy(0, window.innerHeight / 3)")
    await human_like_delay(0.5, 1.0)
    await page.evaluate("window.scrollBy(0, -window.innerHeight / 5)")
    await human_like_delay(0.5, 1.0)

async def start_youthall_scraper():
    os.makedirs("data/raw", exist_ok=True)
    jsonl_path = "data/raw/youthall.jsonl"
    
    seen_job_urls = load_seen_links(jsonl_path)
    print(f"[INFO] Loaded {len(seen_job_urls)} existing job links from database to prevent duplicates.")
    
    today_date = datetime.now().strftime("%Y-%m-%d") 

    valid_title_keywords = [
        "developer", "geliştirici", "engineer", "mühendis", "uzman", 
        "analist", "analyst", "scientist", "architect", "data", "veri", 
        "yazılım", "backend", "frontend", "full stack", "fullstack", 
        "devops", "qa", "test", "security", "güvenlik", "machine learning", 
        "yapay zeka", "ai", "ml", "sistem", "system", "mimarı", "mimar", 
        "it ", "bilgi teknolojileri", "cyber"
    ]

    closed_keywords = [
        "başvuru kabul etmiyor", "yayından kaldırılmıştır", "başvuru süresi dolmuştur", 
        "başvuruya kapanmıştır", "ilan yayında değildir", "no longer accepting applications", 
        "job is no longer available", "posting has expired"
    ]

    categories = [
        {"url": "https://www.youthall.com/tr/jobs", "type": "Job Posting"},
        {"url": "https://www.youthall.com/tr/talent-programs", "type": "Talent Program / Internship"}
    ]

    async with async_playwright() as p:
        print("Youthall Automation Bot is being launched...")
        
        browser = await p.chromium.launch(
            headless=True, 
            slow_mo=100,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--window-size=1920,1080"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        
        page = await context.new_page() 
        
        for category in categories:
            print(f"\n=======================================================")
            print(f"--- SEARCHING YOUTHALL CATEGORY: {category['type'].upper()} ---")
            print(f"=======================================================")
            
            current_page = 1
            
            while True:
                target_url = f"{category['url']}/?page={current_page}"
                
                max_retries = 3
                page_loaded = False
                
                for attempt in range(max_retries):
                    try:
                        
                        await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                        page_loaded = True
                        break 
                    except Exception as e:
                       print(f" -> [WARNING] Page failed to load (Attempt {attempt + 1}/{max_retries}). Retrying...")
                       await human_like_delay(2.5, 4.0)
                
                if not page_loaded:
                    print(f" -> [ERROR] Could not reach {target_url} after 3 attempts. Category skipped.")
                    break
                
                try:
                    await page.wait_for_selector('.jobs', timeout=15000)
                    await simulate_human_behavior(page)
                except:
                    print(f"\n-> [INFO] No ads found on page {current_page} (End of pagination). Category completed.")
                    break 
                
                job_cards = await page.query_selector_all('.jobs')
                
                page_new_total_jobs = 0  
                page_valid_it_jobs = 0   
                
                for card in job_cards:
                    a_tag = await card.query_selector('a')
                    href = await a_tag.get_attribute('href') if a_tag else None
                    
                    if not href:
                        continue
                        
                    job_url = f"https://www.youthall.com{href}" if href.startswith("/") else href
                    
                    if job_url in seen_job_urls:
                        continue
                    
                    page_new_total_jobs += 1

                    header_elem = await card.query_selector('.jobs-content-header')
                    desc_elem = await card.query_selector('.jobs-content-desc')
                    
                    title = await header_elem.inner_text() if header_elem else "Not found"
                    title = title.strip()
                    
                    company = await desc_elem.inner_text() if desc_elem else "Not found"
                    company = company.strip()
                    
                    title_lower = title.lower()
                    if not any(valid_word in title_lower for valid_word in valid_title_keywords):
                        continue 
                    
                    logo_element = await card.query_selector('img')
                    logo_url = await logo_element.get_attribute('src') if logo_element else "No Logo"
                    if logo_url.startswith("/"):
                        logo_url = f"https://www.youthall.com{logo_url}"

                    bottom_elem = await card.query_selector('.jobs-content-bottom')
                    if bottom_elem:
                        bottom_text = await bottom_elem.inner_text()
                        bottom_text = bottom_text.replace('\n', ' - ').strip()
                    else:
                        bottom_text = "Not specified"

                    detail_page = await context.new_page()
                    full_page_text = ""
                    try:
                        await detail_page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
                        await human_like_delay(0.5, 1.5)
                        
                        body_element = detail_page.locator('body')
                        full_page_text = (await body_element.inner_text()).lower()
                        
                        detail_selector = '.c-job_post__content, .c-profile-home-section'
                        await detail_page.wait_for_selector(detail_selector, timeout=5000) 
                        
                        desc_elements = await detail_page.query_selector_all(detail_selector)
                        if desc_elements:
                            job_description = await desc_elements[0].inner_text()
                            job_description = job_description.strip()
                        else:
                            job_description = "Description could not be retrieved"
                            
                        await detail_page.evaluate("window.scrollTo(0, document.body.scrollHeight/3);")
                    except:
                        job_description = "Description could not be retrieved"
                    
                    await detail_page.close() 
                    
                    if any(ck in full_page_text for ck in closed_keywords):
                        print(f"    -> [CLOSED] Ad '{title}' is no longer accepting applications. Skipping...")
                        continue

                    seen_job_urls.add(job_url)
                    
                    job_data = {
                        "Platform": "Youthall",
                        "Posting_Type": category['type'], 
                        "Job_Title": title,
                        "Company": company,
                        "Location_Details": bottom_text,
                        "Job_Description": job_description,
                        "Job_Link": job_url,
                        "Logo_Link": logo_url,
                        "Withdrawal_Date": today_date 
                    }
                    append_to_jsonl(jsonl_path, job_data)
                    page_valid_it_jobs += 1 
                
                if page_new_total_jobs == 0:
                    print(f"\n-> [SYSTEM BRAKE] All jobs on page {current_page} have already been retrieved. Category completed.")
                    break
                
                print(f"-> Page {current_page} scanned: {page_new_total_jobs} new jobs seen, {page_valid_it_jobs} IT jobs retrieved and streamed.")
                
                current_page += 1 
                await human_like_delay(2.5, 4.5)

        print("\nClosing the browser...")
        await context.close()
        await browser.close()
        print(f"AUTOMATION SUCCESSFUL! Data is securely streamed to '{jsonl_path}'.")

if __name__ == "__main__":
    asyncio.run(start_youthall_scraper())