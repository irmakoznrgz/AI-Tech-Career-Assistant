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

async def dismiss_linkedin_popups(page):
    try:
        dismiss_buttons = await page.query_selector_all('button.modal__dismiss, button[data-tracking-control-name="public_jobs_modal_dismiss"]')
        for btn in dismiss_buttons:
            if await btn.is_visible():
                await btn.click()
                await human_like_delay(0.5, 1.0)
        
        await page.evaluate("""
            document.querySelectorAll('.modal, [role="dialog"], .sign-in-modal').forEach(e => e.remove());
            document.body.style.overflow = 'auto';
        """)
    except:
        pass

async def load_infinite_scroll_jobs(page):    
    last_height = await page.evaluate("document.body.scrollHeight")
    scroll_count = 0
    
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await human_like_delay(2.0, 3.0)
        
        try:
            more_btn = await page.query_selector('button.infinite-scroller__show-more-button')
            if more_btn and await more_btn.is_visible():
                print(f"    -> [SCROLL] 'See more jobs' button clicked (Scroll {scroll_count+1})")
                await more_btn.click()
                await human_like_delay(2.0, 3.5)
        except:
            pass
            
        new_height = await page.evaluate("document.body.scrollHeight")
       
        if new_height == last_height:
            print("    -> [SCROLL] Reached the end of the job list organically.")
            break
            
        last_height = new_height
        scroll_count += 1
        if scroll_count > 100:
            break

    await dismiss_linkedin_popups(page)

async def start_linkedin_scraper():
    os.makedirs("data/raw", exist_ok=True)
    jsonl_path = "data/raw/linkedin.jsonl"
    
    seen_job_urls = load_seen_links(jsonl_path)
    print(f"[INFO] Loaded {len(seen_job_urls)} existing job links from database to prevent duplicates.")
    
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
    
    invalid_title_keywords = [
        "iç mimar", "peyzaj", "inşaat", "makine", "elektrik", "elektronik", 
        "endüstri", "gıda", "ziraat", "biyomedikal", "çevre", "kimya", "harita",
        "satış", "pazarlama", "ik ", "insan kaynakları", "muhasebe", "finans", 
        "halkla ilişkiler", "sekreter", "asistan", "şoför", "kurye", "depo", 
        "çağrı merkezi", "garson", "kasiyer", "temizlik", "güvenlik görevlisi",
        "öğretmen", "hemşire", "doktor", "avukat", "tesisat", "mekanik",
        "köpek eğitmeni", "müşteri hizmetleri"
    ]

    async with async_playwright() as p:
        print("LinkedIn Automation Bot is being launched (Patchright / Cloud Mode)...")
        
        browser = await p.chromium.launch(
            headless=True,
            slow_mo=100,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-popup-blocking",
                "--window-size=1920,1080"
            ] 
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        
        page = await context.new_page()
        
        print("\nScraping process is starting!\n")
        
        for keyword in keywords:
            print(f"\n=======================================================")
            print(f"--- SEARCHING FOR '{keyword.upper()}' ON LINKEDIN ---")
            print(f"=======================================================")
            
            formatted_keyword = keyword.replace(" ", "%20")
            target_url = f"https://www.linkedin.com/jobs/search?keywords={formatted_keyword}&location=T%C3%BCrkiye&geoId=102105699"
            
            try:
                await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"Error occurred while loading the page: {e}")
                continue
                
            await human_like_delay(2.5, 4.0)
            await dismiss_linkedin_popups(page)
            
            # Güncellenmiş, sınırsız kaydırma fonksiyonu
            await load_infinite_scroll_jobs(page)
            
            try:
                await page.wait_for_selector('.base-card, .job-search-card', timeout=10000)
            except:
                print(f"-> [INFO] No job cards found for '{keyword}'. Moving to next keyword.")
                continue
                
            job_cards = await page.query_selector_all('.base-card, .job-search-card')
            
            page_new_jobs = 0
            page_valid_it_jobs = 0
            consecutive_existing_jobs = 0 
            
            print(f"-> Found {len(job_cards)} total cards on screen. Applying filters & fetching details...")
            
            for card in job_cards:
                a_tag = await card.query_selector('a.base-card__full-link')
                if not a_tag:
                    continue
                    
                job_url = await a_tag.get_attribute('href')
                if job_url and "?" in job_url:
                    job_url = job_url.split("?")[0]
                    
                if not job_url:
                    continue

                if job_url in seen_job_urls:
                    consecutive_existing_jobs += 1
                    if consecutive_existing_jobs >= 3:
                        print(f"    -> [DYNAMIC BRAKE] Hit 3 existing jobs in a row. Skipping the rest of '{keyword}'.")
                        break
                    continue
                else:
                    consecutive_existing_jobs = 0 

                title_element = await card.query_selector('.base-search-card__title')
                title = await title_element.inner_text() if title_element else "Not found"
                title = title.strip()
                title_lower = title.lower()
                
                if any(invalid_word in title_lower for invalid_word in invalid_title_keywords):
                    continue
                if not any(valid_word in title_lower for valid_word in valid_title_keywords):
                    continue
                    
                company_element = await card.query_selector('.base-search-card__subtitle')
                company = await company_element.inner_text() if company_element else "Not found"
                company = company.strip()
                
                location_element = await card.query_selector('.job-search-card__location')
                location = await location_element.inner_text() if location_element else "Not found"
                location = location.strip()
                
                logo_element = await card.query_selector('img.artdeco-entity-image')
                logo_url = await logo_element.get_attribute('data-delayed-url') or await logo_element.get_attribute('src') if logo_element else "No Logo"
                
                seen_job_urls.add(job_url)
                page_new_jobs += 1
                
                try:
                    await card.scroll_into_view_if_needed()
                    await human_like_delay(0.5, 1.2) 
                    await card.click()
                    await human_like_delay(1.5, 2.5) 
                    await dismiss_linkedin_popups(page)
                    
                    await page.wait_for_selector('.show-more-less-html__markup, .description__text, .core-section-container__content', timeout=15000)
                    desc_element = await page.query_selector('.show-more-less-html__markup, .description__text, .core-section-container__content')
                    job_description = await desc_element.inner_text() if desc_element else "Description could not be retrieved"
                    job_description = job_description.strip()
                    
                except Exception as e:
                    job_description = "Description could not be retrieved"
                    
                job_data = {
                    "Platform": "LinkedIn",
                    "Search_Keyword": keyword,
                    "Job_Title": title,
                    "Company": company,
                    "Location_Details": location,
                    "Job_Type": "Not specified",
                    "Job_Description": job_description,
                    "Job_Link": job_url,
                    "Logo_Link": logo_url,
                    "Withdrawal_Date": today_date
                }
                
                append_to_jsonl(jsonl_path, job_data)
                page_valid_it_jobs += 1
                
            if page_new_jobs == 0:
                print(f"-> [INFO] All relevant jobs for '{keyword}' already exist in database. Moving to next keyword.")
            else:
                print(f"-> Keyword '{keyword}' completed: {page_valid_it_jobs} valid IT jobs retrieved and streamed.")

        print("\nClosing the browser...")
        await context.close()
        await browser.close()
        print(f"AUTOMATION SUCCESSFUL! Data is securely streamed to '{jsonl_path}'.")

if __name__ == "__main__":
    asyncio.run(start_linkedin_scraper())