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

async def bypass_cloudflare_advanced(page):
    """Hem Turnstile kutucuğunu hem de 'Refresh' hatasını çözen gelişmiş Cloudflare Bypass"""
    try:
        page_content = await page.content()
        
        if "We could not verify this request" in page_content or "Please refresh and try again" in page_content:
            print("    -> [STEALTH] 'Verify Failed' error detected. Executing hard refresh...")
            await human_like_delay(2.0, 3.5)
            await page.reload(wait_until="domcontentloaded")
            await human_like_delay(4.0, 6.0)
            return

        print("    -> [STEALTH] Scanning for Cloudflare Turnstile widget...")
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
                
                print("    -> [STEALTH] Action completed. Waiting for validation...")
                await human_like_delay(4.0, 6.0)
    except Exception as e:
        print(f"    -> [STEALTH] Bypass logic encountered an issue: {e}")

async def destroy_login_popups(page):
    """Ekrana aniden fırlayan Indeed 'Giriş Yap' veya 'Google' popup'larını HTML'den zorla siler."""
    try:
        await page.evaluate("""
            document.querySelectorAll('[role="dialog"], .mosaic-provider-signin-prompt, [id*="modal"], [class*="modal"]').forEach(e => e.remove());
            document.body.style.overflow = 'auto';
        """)
    except:
        pass

async def start_indeed_scraper():
    os.makedirs("data/raw", exist_ok=True)
    jsonl_path = "data/raw/indeed.jsonl"
    
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

    async with async_playwright() as p:
        print("Indeed Automation Bot is being launched (GHOST MODE)...")
        browser = await p.chromium.launch(
            channel="chrome", 
            headless=False,   
            slow_mo=150,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-popup-blocking",
                "--ignore-certificate-errors",
                "--window-size=1920,1080"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page() 
        print("\nScraping process is starting with a clean slate!\n")
        
        for keyword in keywords:
            print(f"\n=======================================================")
            print(f"--- SEARCHING FOR '{keyword.upper()}' ON INDEED ---")
            print(f"=======================================================")
            
            formatted_keyword = keyword.replace(" ", "+")
            start_param = 0 
            current_page = 1
            
            while True:
                target_url = f"https://tr.indeed.com/jobs?q={formatted_keyword}&l=&start={start_param}"
                
                try:
                    await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                except Exception as e:
                    print(f"Error occurred while loading the page: {e}")
                    break
                
                await human_like_delay(2.5, 4.0)
                page_title = await page.title()
                if "Cloudflare" in page_title or "Doğrulama" in page_title or "Just a moment" in page_title or "Robot" in page_title or "Security Check" in page_title:
                    print(f"\n[SYSTEM WARNING] Security wall detected for '{keyword}'. Initiating stealth bypass...")
                    await bypass_cloudflare_advanced(page)
                    
                    page_title = await page.title()
                    if "Cloudflare" in page_title or "Just a moment" in page_title or "Robot" in page_title or "Security Check" in page_title:
                        print("[SYSTEM WARNING] Bypass failed. IP might be flagged. Skipping keyword.")
                        break 
                
                try:
                    await page.wait_for_selector('.cardOutline', timeout=15000)
                    await simulate_human_behavior(page)
                except:
                    page_title = await page.title()
                    current_url = page.url
                    if "Sign In" in page_title or "Giriş Yap" in page_title or "auth" in current_url or "Hesapları" in page_title:
                        print("\n[STEALTH] Login Wall detected! Attempting 'Return to Home' human-bypass...")
                        
                        try:
                            home_btn = page.locator("text=Ana sayfaya git")
                            if await home_btn.count() > 0:
                                await home_btn.first.click()
                                await human_like_delay(2.5, 4.0)
                            else:
                                home_btn_en = page.locator("text=Return to home")
                                if await home_btn_en.count() > 0:
                                    await home_btn_en.first.click()
                                    await human_like_delay(2.5, 4.0)
                        except:
                            print("    -> [STEALTH] 'Return home' button not found. Proceeding to force wipe.")
                        await context.clear_cookies()
                        try:
                            await page.evaluate("""
                                window.localStorage.clear();
                                window.sessionStorage.clear();
                            """)
                        except:
                            pass
                            
                        await human_like_delay(1.5, 2.5)
                    
                        print(f"    -> [STEALTH] Memory wiped. Re-attempting access to page {current_page}...")
                        try:
                            await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                        except:
                            pass
                            
                        await human_like_delay(3.0, 4.0)
                        
                        try:
                            await page.wait_for_selector('.cardOutline', timeout=15000)
                            print("    -> [STEALTH] Login Wall successfully bypassed!")
                        except:
                            print("    -> [SYSTEM WARNING] Could not bypass Login Wall. IP might be temporarily limited. Skipping keyword.")
                            break
                    else:
                        print(f"\n-> [INFO] No ads found on page {current_page} (Reached the last page). Moving to the next keyword.")
                        break 
                
                job_cards = await page.query_selector_all('.cardOutline')
                page_new_jobs = 0  
                page_valid_it_jobs = 0
                
                for card in job_cards:
                    a_tag = await card.query_selector('a[data-jk]')
                    if not a_tag:
                        continue
                        
                    jk_code = await a_tag.get_attribute('data-jk')
                    job_url = f"https://tr.indeed.com/viewjob?jk={jk_code}"
                    
                    if job_url in seen_job_urls:
                        continue
                        
                    seen_job_urls.add(job_url)
                    page_new_jobs += 1

                    title_element = await card.query_selector('h2.jobTitle span[title]') or a_tag
                    title = await title_element.inner_text() if title_element else "Not found"
                    title = title.strip()
                    title_lower = title.lower()
                    
                    if not any(valid_word in title_lower for valid_word in valid_title_keywords):
                        continue
                    
                    company_element = await card.query_selector('[data-testid="company-name"]')
                    company = await company_element.inner_text() if company_element else "Not found"
                    
                    location_element = await card.query_selector('[data-testid="text-location"]')
                    location = await location_element.inner_text() if location_element else "Not found"
                    
                    type_element = await card.query_selector('.jobMetaDataGroup')
                    if type_element:
                        emp_type = await type_element.inner_text()
                        emp_type = emp_type.replace('\n', ' - ').strip()
                    else:
                        emp_type = "Not specified"

                    try:
                        await card.scroll_into_view_if_needed()
                        await human_like_delay(0.5, 1.5)
                        
                        await a_tag.click()
                        await human_like_delay(1.0, 2.0)
                        
                        await destroy_login_popups(page)
                        
                        await page.wait_for_selector('#jobDescriptionText', timeout=8000)
                        
                        desc_element = page.locator('#jobDescriptionText')
                        job_description = await desc_element.inner_text()
                        job_description = job_description.strip()
                        
                        await simulate_human_behavior(page)
                    except Exception as e:
                        print(f"    -> [INFO] Description could not be loaded in side panel for {title}.")
                        job_description = "Description could not be retrieved"
                    
                    job_data = {
                        "Platform": "Indeed",
                        "Search_Keyword": keyword,
                        "Job_Title": title,
                        "Company": company.strip(),
                        "Location_Details": location.strip(),
                        "Job_Type": emp_type,
                        "Job_Description": job_description,
                        "Job_Link": job_url,
                        "Logo_Link": "No Logo",
                        "Withdrawal_Date": today_date
                    }
                    
                    append_to_jsonl(jsonl_path, job_data)
                    page_valid_it_jobs += 1
                
                if page_new_jobs == 0:
                    print(f"\n-> [BRAKE] All jobs on page {current_page} have already been retrieved. Skipping keyword!")
                    break
                
                print(f"-> Page {current_page} scanned: {page_new_jobs} new jobs seen, {page_valid_it_jobs} valid IT jobs retrieved.")
                
                start_param += 10 
                current_page += 1
                await human_like_delay(4.5, 7.5)

        print("\nClosing the browser...")
        await browser.close()
        print(f"AUTOMATION SUCCESSFUL! Data is securely streamed to '{jsonl_path}'.")

if __name__ == "__main__":
    asyncio.run(start_indeed_scraper())