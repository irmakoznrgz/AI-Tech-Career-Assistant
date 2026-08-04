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

async def start_techcareer_scraper():
    os.makedirs("data/raw", exist_ok=True)
    jsonl_path = "data/raw/techcareer.jsonl"
    
    seen_job_urls = load_seen_links(jsonl_path)
    print(f"[INFO] Loaded {len(seen_job_urls)} existing job links from database to prevent duplicates.")
    
    today_date = datetime.now().strftime("%Y-%m-%d") 

    valid_title_keywords = [
        "developer", "geliştirici", "software", "yazılım", "backend", "frontend", 
        "full stack", "fullstack", "data", "veri", "machine learning", "yapay zeka", 
        "ai", "ml", "devops", "qa", "test", "cyber", "siber", "security", "güvenlik", 
        "system", "sistem", "it ", "bilişim", "cloud", "bulut", "database", "veritabanı",
        "mimar", "architect", "mühendis", "engineer", "uzman", "analyst", "analist"
    ]

    invalid_title_keywords = [
        "iç mimar", "peyzaj", "inşaat", "makine", "elektrik", "elektronik", 
        "endüstri", "gıda", "ziraat", "biyomedikal", "çevre", "kimya", "harita",
        "satış", "pazarlama", "ik ", "insan kaynakları", "muhasebe", "finans", 
        "halkla ilişkiler", "sekreter", "asistan", "şoför", "kurye", "depo", 
        "çağrı merkezi", "garson", "kasiyer", "temizlik", "güvenlik görevlisi",
        "öğretmen", "hemşire", "doktor", "avukat", "tesisat", "mekanik"
    ]
    
    closed_keywords = [
        "başvuru kabul etmiyor", "yayından kaldırılmıştır", "başvuru süresi dolmuştur", 
        "başvuruya kapanmıştır", "ilan yayında değildir", "no longer accepting applications", 
        "job is no longer available", "posting has expired"
    ]

    async with async_playwright() as p:
        print("Techcareer Automation Bot is being launched (Patchright / Cloud Mode)...")
        
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
        
        main_page = await context.new_page() 
        current_page = 1 
        
        print("\n--- TECHCAREER AUTOMATED SCRAPING STARTED ---")
        
        max_retries = 3
        page_loaded = False
        
        for attempt in range(max_retries):
            try:
                await main_page.goto("https://www.techcareer.net/jobs", timeout=45000, wait_until="domcontentloaded")
                await human_like_delay(2.0, 3.5)
                page_loaded = True
                break
            except Exception as e:
                print(f"    -> [WARNING] Bağlantı hatası (Deneme {attempt + 1}/{max_retries}). Tekrar deneniyor... Hata: {e}")
                await human_like_delay(2.5, 4.0)
                
        if not page_loaded:
            print("Error: Could not connect to the site after 3 attempts. Terminating.")
            await context.close()
            await browser.close()
            return

        while True:
            try:
                await main_page.wait_for_selector('[data-test="single-job-item"]', timeout=15000)
                await simulate_human_behavior(main_page)
            except:
                print(f"\n-> No job cards found on page {current_page}. Scraping completed.")
                break 
            
            job_cards = await main_page.query_selector_all('[data-test="single-job-item"]')
            
            if not job_cards:
                print(f"\n-> [SYSTEM] No ads found on page {current_page}. Ending scan.")
                break
            current_first_card_href = await job_cards[0].get_attribute('href')
            
            page_new_jobs = 0
            page_valid_it_jobs = 0
            
            print(f"\n-> Page {current_page} scanned. Fetching details for jobs...")
            
            for card in job_cards:
                href = await card.get_attribute('href')
                job_url = f"https://www.techcareer.net{href}" if href and href.startswith("/") else href
                
                if not job_url or job_url in seen_job_urls:
                    continue 

                page_new_jobs += 1

                title_element = await card.query_selector('[data-test="single-job-title"]')
                title = await title_element.inner_text() if title_element else "Not found"
                title = title.strip()
                title_lower = title.lower()
                if any(invalid_word in title_lower for invalid_word in invalid_title_keywords):
                    continue
                if not any(valid_word in title_lower for valid_word in valid_title_keywords):
                    continue
                
                company_element = await card.query_selector('[data-test="single-job-company-name"]')
                company = await company_element.inner_text() if company_element else "Not found"
                company = company.strip()
                
                detail_element = await card.query_selector('[data-test="single-job-location-and-work-place"]')
                raw_detail = await detail_element.inner_text() if detail_element else ""
                raw_detail = raw_detail.strip()
                
                location = raw_detail
                emp_type = "Not specified"
                
                if "(" in raw_detail and ")" in raw_detail:
                    parts = raw_detail.split("(")
                    location = parts[0].strip()
                    emp_type = parts[1].replace(")", "").strip()
                
                logo_element = await card.query_selector('img')
                logo_url = await logo_element.get_attribute('src') if logo_element else "No Logo"
                if logo_url.startswith("/"):
                    logo_url = f"https://www.techcareer.net{logo_url}"

                detail_page = await context.new_page()
                full_page_text = ""
                try:
                    await detail_page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
                    await human_like_delay(0.5, 1.5)
                    
                    body_element = detail_page.locator('body')
                    full_page_text = (await body_element.inner_text()).lower()
                    
                    await detail_page.wait_for_selector('[data-test="job-detail-desc-content"]', timeout=5000) 
                    desc_locator = detail_page.locator('[data-test="job-detail-desc-content"]')
                    job_description = await desc_locator.inner_text()
                    job_description = job_description.strip()
                    
                    skills = ""
                    skills_locator = detail_page.locator('[data-test="job-detail-skills-container"]')
                    if await skills_locator.count() > 0:
                        skills_text = await skills_locator.inner_text()
                        skills = skills_text.replace('\n', ', ')
                        
                    await detail_page.evaluate("window.scrollTo(0, document.body.scrollHeight/2);")
                except:
                    job_description = "Description could not be retrieved"
                    skills = ""
                
                await detail_page.close() 
                
                if any(ck in full_page_text for ck in closed_keywords):
                    print(f"    -> [CLOSED] Ad '{title}' is no longer accepting applications. Skipping...")
                    continue
                
                seen_job_urls.add(job_url)
                
                job_data = {
                    "Platform": "Techcareer",
                    "Job_Title": title,
                    "Company": company,
                    "Location_Details": location,
                    "Job_Type": emp_type,
                    "Required_Skills": skills,  
                    "Job_Description": job_description,
                    "Job_Link": job_url,
                    "Logo_Link": logo_url,
                    "Withdrawal_Date": today_date 
                }
                
                append_to_jsonl(jsonl_path, job_data)
                page_valid_it_jobs += 1
            
            if page_new_jobs == 0:
                print(f"\n-> [BRAKE] All jobs on page {current_page} already exist in database. Terminating successfully!")
                break
                
            print(f"-> Page {current_page} completed: {page_new_jobs} new jobs seen, {page_valid_it_jobs} valid IT jobs retrieved.")
            next_page_num = current_page + 1

            print(f"Triggering DOM Hacker for page {next_page_num}...")
            
            await main_page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await human_like_delay(1.0, 2.0)
            
            js_hacker_code = f"""
            () => {{
                const num = '{next_page_num}';
                const allElements = document.querySelectorAll('*');
                let target = null;
                let maxY = -1;

                for(let el of allElements) {{
                    if(el.children.length === 0 && el.textContent.trim() === num) {{
                        const rect = el.getBoundingClientRect();
                        if(rect.top > maxY) {{
                            maxY = rect.top;
                            target = el;
                        }}
                    }}
                }}

                if(target) {{
                    target.dispatchEvent(new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true
                    }}));
                    return true;
                }}
                return false;
            }}
            """
            
            successful_transition = await main_page.evaluate(js_hacker_code)

            if successful_transition:
                print("Success! Actively waiting for SPA to render new ads...")
                page_changed = False
                for _ in range(20):
                    await human_like_delay(0.8, 1.2)
                    check_cards = await main_page.query_selector_all('[data-test="single-job-item"]')
                    if check_cards:
                        check_href = await check_cards[0].get_attribute('href')
                        if check_href != current_first_card_href:
                            page_changed = True
                            break 
                if page_changed:
                    current_page += 1
                else:
                    print("\n[SYSTEM BRAKE] API did not return new jobs after 20 seconds. Reached the end!")
                    break
            else:
                print("\n[INFO] Forward command could not find the target number. Reached the final page.")
                break

        print("\nClosing the browser...")
        await context.close()
        await browser.close()
        print(f"AUTOMATION SUCCESSFUL! Data is securely streamed to '{jsonl_path}'.")

if __name__ == "__main__":
    asyncio.run(start_techcareer_scraper())