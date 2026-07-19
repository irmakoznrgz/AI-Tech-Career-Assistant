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

    await page.evaluate("window.scrollBy(0, window.innerHeight / 2)")
    await human_like_delay(0.5, 1.0)
    await page.evaluate("window.scrollBy(0, -window.innerHeight / 4)")
    await human_like_delay(0.5, 1.0)

async def bypass_cloudflare_turnstile(page):
    try:
        print("    -> [STEALTH] Scanning for specific Cloudflare Turnstile widget...")
        cf_iframe_element = None
        
        for frame in page.frames:
            if "cloudflare" in frame.url.lower() or "turnstile" in frame.url.lower():
                cf_iframe_element = await page.query_selector(f'iframe[src="{frame.url}"]')
                break
                
        if cf_iframe_element:
            box = await cf_iframe_element.bounding_box()
            if box:
                print("    -> [STEALTH] Target acquired. Executing human-like press...")
                target_x = box["x"] + (box["width"] / 4) + random.uniform(5, 15)
                target_y = box["y"] + (box["height"] / 2) + random.uniform(-5, 5)
                
                await page.mouse.move(target_x, target_y, steps=15) 
                await human_like_delay(0.5, 1.0)
                
                await page.mouse.down()
                await human_like_delay(2.5, 4.2) 
                await page.mouse.up()
                
                print("    -> [STEALTH] Action completed. Waiting for Cloudflare validation...")
                await human_like_delay(4.0, 6.0)
        else:
            print("    -> [STEALTH] No visible Cloudflare widget found to click.")
    except Exception as e:
        pass

async def start_kariyer_scraper():
    user_data_dir = "./chrome_profile_kariyer_patchright"
    os.makedirs("data/raw", exist_ok=True)
    jsonl_path = "data/raw/kariyer.jsonl"
    
    seen_job_urls = load_seen_links(jsonl_path)
    print(f"[INFO] Loaded {len(seen_job_urls)} existing job links from database to prevent duplicates.")
    
    MAX_PAGES_PER_KEYWORD = 10 
    today_date = datetime.now().strftime("%Y-%m-%d")

    keywords = [
        "veri bilimi", "data scientist", "data engineer", "veri analisti", "data analyst",
        "machine learning", "yapay zeka", "artificial intelligence",
        "yazılım geliştirici", "software developer", "backend", "frontend", "full stack",
        "python", "java", ".net", "javascript", "devops", 
        "siber güvenlik", "cyber security", "qa engineer", "software test"
    ]
    
    valid_title_keywords = [
        "developer", "geliştirici", "software", "yazılım", "backend", "frontend", 
        "full stack", "fullstack", "data", "veri", "machine learning", "yapay zeka", 
        "ai", "ml", "devops", "qa", "test", "cyber", "siber", "security", "güvenlik", 
        "system", "sistem", "it ", "bilişim", "cloud", "bulut", "database", "veritabanı",
        "mimar", "architect", "mühendis", "engineer", "uzman", "analyst", "analist"
    ]

    async with async_playwright() as p:
        print("Kariyer.net Automation Bot is being launched (Patchright / Async Mode)...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome", 
            headless=True,   
            slow_mo=100,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-popup-blocking",
                "--ignore-certificate-errors",
                "--window-size=1920,1080" 
            ] 
        )
        
        page = context.pages[0]
        
        for keyword in keywords:
            print(f"\n=======================================================")
            print(f"--- SEARCHING FOR '{keyword.upper()}' ---")
            print(f"=======================================================")
            
            formatted_keyword = keyword.replace(" ", "%20")
            current_page = 1 
            
            while current_page <= MAX_PAGES_PER_KEYWORD:
                target_url = f"https://www.kariyer.net/is-ilanlari?kw={formatted_keyword}&cp={current_page}"
                try:
                    await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                except Exception as e:
                    print(f"Error occurred while loading the page: {e}")
                    break
                
                await human_like_delay(2.5, 4.0) 
                page_title = await page.title()
                
                if "Access to" in page_title or "Just a moment" in page_title or "Cloudflare" in page_title:
                    print(f"\n[SYSTEM WARNING] Security wall detected for '{keyword}'. Initiating stealth bypass...")
                    await bypass_cloudflare_turnstile(page)
                    
                    page_title = await page.title()
                    if "Access to" in page_title or "Just a moment" in page_title:
                        print("[SYSTEM WARNING] Still stuck in Cloudflare loop. Reloading page for a second attempt...")
                        await page.reload(wait_until="domcontentloaded")
                        await human_like_delay(3.0, 5.0)
                        await bypass_cloudflare_turnstile(page)
                        
                        page_title = await page.title()
                        if "Access to" in page_title or "Just a moment" in page_title:
                            print("[SYSTEM WARNING] Bypass completely failed. IP might be flagged. Skipping keyword.")
                            break

                try:
                    await page.wait_for_selector('.k-ad-card', timeout=20000)
                    await simulate_human_behavior(page)
                except:
                    print(f"-> [INFO] No ads found on page {current_page}. (Note: 1 page = 50 jobs. If there are fewer jobs for this keyword, stopping here is mathematically correct). Moving to next keyword.")
                    break 
                
                job_cards = await page.query_selector_all('.k-ad-card')
                page_valid_jobs = 0  
                page_new_urls = 0
                
                for card in job_cards:
                    href = await card.get_attribute('href')
                    job_url = f"https://www.kariyer.net{href}" if href else ""
                    
                    if not job_url or job_url in seen_job_urls:
                        continue
                    
                    seen_job_urls.add(job_url)
                    page_new_urls += 1

                    title_element = await card.query_selector('.title-left')
                    title = await title_element.inner_text() if title_element else ""
                    title = title.strip()
                    
                    title_lower = title.lower()
                    if not any(valid_word in title_lower for valid_word in valid_title_keywords):
                        continue
                    
                    company_element = await card.query_selector('[data-test="subtitle-section"]')
                    company = await company_element.inner_text() if company_element else "Not found"
                    
                    detail_element = await card.query_selector('[data-test="job-detail"]')
                    detail = await detail_element.inner_text() if detail_element else "Not found"
                    
                    type_element = await card.query_selector('text="Zamanlı"')
                    emp_type = await type_element.inner_text() if type_element else "Not specified"
                    
                    logo_element = await card.query_selector('img')
                    logo_url = await logo_element.get_attribute('src') if logo_element else "No Logo"
                    
                    detail_page = await context.new_page()
                    try:
                        await detail_page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
                        await human_like_delay(0.5, 1.5)
                        
                        detail_title = await detail_page.title()
                        if "Just a moment" in detail_title or "Cloudflare" in detail_title:
                            await bypass_cloudflare_turnstile(detail_page)
                            
                        await detail_page.wait_for_selector('[data-test="qualifications-and-job-description"]', timeout=5000)
                        desc_element = detail_page.locator('[data-test="qualifications-and-job-description"]')
                        job_description = await desc_element.inner_text()
                        job_description = job_description.strip()
                        
                        await detail_page.evaluate("window.scrollTo(0, document.body.scrollHeight/2);")
                    except:
                        job_description = "Description could not be retrieved"
                    await detail_page.close() 
                    
                    job_data = {
                        "Platform": "Kariyer.net",
                        "Search_Keyword": keyword,
                        "Job_Title": title,
                        "Company": company.strip(),
                        "Location_Details": detail.strip(),
                        "Job_Type": emp_type.strip(),
                        "Job_Description": job_description,
                        "Job_Link": job_url,
                        "Logo_Link": logo_url,
                        "Withdrawal_Date": today_date
                    }
                    
                    append_to_jsonl(jsonl_path, job_data)
                    page_valid_jobs += 1
                
                if page_new_urls == 0:
                    print(f"\n-> [BRAKE] All jobs on page {current_page} already exist. Moving to the next keyword!")
                    break

                print(f"-> Page {current_page} completed: {page_valid_jobs} NEW jobs retrieved and saved immediately.")
                
                current_page += 1 
                await human_like_delay(3.5, 6.5)

        print("\nClosing the browser...")
        await context.close()
        print(f"AUTOMATION SUCCESSFUL! Data is securely streamed to '{jsonl_path}'.")

if __name__ == "__main__":
    asyncio.run(start_kariyer_scraper())