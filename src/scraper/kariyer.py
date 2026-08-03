import asyncio
import json
import os
import random
import sys
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

async def human_like_delay(min_sec=1.5, max_sec=3.5):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def simulate_human_behavior(page):
    try:
        width = page.viewport_size['width']
        height = page.viewport_size['height']
        await page.mouse.move(random.randint(100, width - 100), random.randint(100, height - 100))
        await human_like_delay(0.5, 1.5)

        await page.evaluate("window.scrollBy(0, window.innerHeight / 2)")
        await human_like_delay(0.5, 1.0)
        await page.evaluate("window.scrollBy(0, -window.innerHeight / 4)")
        await human_like_delay(0.5, 1.0)
    except:
        pass

async def bypass_cloudflare_advanced(page):
    try:
        page_content = await page.content()
        
        if "We could not verify this request" in page_content or "Please refresh and try again" in page_content:
            print("    -> [STEALTH] 'Verify Failed' error detected. Executing hard refresh...")
            await human_like_delay(2.0, 3.5)
            await page.reload(wait_until="domcontentloaded")
            await human_like_delay(4.0, 6.0)
            return

        print(" -> [STEALTH] Scanning for security widgets...")
        await asyncio.sleep(2.5) 
        
        target_box = None
        
        print("    -> [STEALTH] Checking for custom 'Basılı Tut' buttons...")
        custom_button_selectors = [
            'text="Basılı Tut"',
            'button:has-text("Basılı Tut")',
            'a:has-text("Basılı Tut")',
            '[role="button"]'
        ]
        for btn_sel in custom_button_selectors:
            try:
                btn = await page.query_selector(btn_sel)
                if btn:
                    target_box = await btn.bounding_box()
                    if target_box and target_box["width"] > 0:
                        print(f"    -> [STEALTH] Custom button found via text match: {btn_sel}")
                        break
            except:
                pass

        if not target_box:
            for frame in page.frames:
                if "cloudflare" in frame.url.lower() or "turnstile" in frame.url.lower():
                    cf_iframe_element = await page.query_selector(f'iframe[src="{frame.url}"]')
                    if cf_iframe_element:
                        target_box = await cf_iframe_element.bounding_box()
                        break
        
        if not target_box:
            print("    -> [STEALTH] Standard iframe missed. Activating Advanced Selectors...")
            advanced_selectors = [
                '#challenge-stage', '#turnstile-wrapper', '.cf-turnstile', '.cf-turnstile-wrapper',
                '#cf-please-wait', 'div[class*="cloudflare"]', 'iframe[src*="cloudflare"]',
                'iframe[title*="Widget"]', 'iframe[title*="Cloudflare"]',
                '[role="checkbox"]'
            ]
            for sel in advanced_selectors:
                el = await page.query_selector(sel)
                if el:
                    target_box = await el.bounding_box()
                    if target_box and target_box["width"] > 0:
                        print(f"    -> [STEALTH] Target found via selector: {sel}")
                        break

        if not target_box:
            print("    -> [STEALTH] All radars failed. Looking for fallback interaction area...")
            body_box = await page.locator('body').bounding_box()
            if body_box:
                target_box = {
                    "x": (body_box["width"] / 2) - 50, 
                    "y": min(300, (body_box["height"] / 3)), 
                    "width": 100, 
                    "height": 100
                }

        if target_box:
            print("    -> [STEALTH] Target acquired. Executing LONG human-like press...")
            target_x = target_box["x"] + (target_box["width"] / 2)
            target_y = target_box["y"] + (target_box["height"] / 2)
            
            await page.mouse.move(target_x + random.uniform(-10, 10), target_y + random.uniform(-5, 5), steps=15) 
            await asyncio.sleep(0.5)
            await page.mouse.move(target_x, target_y, steps=5)
            await asyncio.sleep(1.0)
            
            await page.mouse.down()
            
            hold_time = random.uniform(11.5, 14.5)
            print(f"    -> [STEALTH] Holding and wiggling for {hold_time:.1f} seconds to clear verification...")
            
            iterations = int(hold_time / 0.3)
            for _ in range(iterations):
                await page.mouse.move(
                    target_x + random.uniform(-3.5, 3.5), 
                    target_y + random.uniform(-3.5, 3.5)
                )
                await asyncio.sleep(0.3)
                
            await page.mouse.up()
            
            print("    -> [STEALTH] Action completed. Waiting for validation...")
            await human_like_delay(5.0, 7.0)
        else:
            print("    -> [STEALTH] No visible widget found to click.")
    except Exception as e:
        print(f"    -> [STEALTH] Bypass logic encountered an issue: {e}")

async def start_kariyer_scraper():
    os.makedirs("data/raw", exist_ok=True)
    jsonl_path = "data/raw/kariyer.jsonl"

    if not os.path.exists(jsonl_path):
        open(jsonl_path, 'a', encoding='utf-8').close()
    
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
        print("Kariyer.net Automation Bot is being launched...")
        
        browser = await p.chromium.launch(
            channel="chrome",
            headless=False,
            slow_mo=100,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-popup-blocking",
                "--ignore-certificate-errors",
                "--window-size=1920,1080"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="tr-TR",
            timezone_id="Europe/Istanbul"
        )
       
        async def block_heavy_resources(route):
            if route.request.resource_type in ["image", "media"]:
                await route.abort()
            else:
                await route.continue_()
                
        await context.route("**/*", block_heavy_resources)
        
        await context.add_init_script("""
        (() => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        })();
        """)
        
        print("\nScraping process is starting with advanced stealth & memory protection!\n")
        
        for keyword in keywords:
            page = await context.new_page()
            detail_page = await context.new_page() 
            
            print(f"\n=======================================================")
            print(f"--- SEARCHING FOR '{keyword.upper()}' ---")
            print(f"=======================================================")
            
            formatted_keyword = keyword.replace(" ", "%20")
            current_page = 1
            
            while True:
                target_url = f"https://www.kariyer.net/is-ilanlari?kw={formatted_keyword}&cp={current_page}"
                
                max_retries = 3
                page_loaded = False
                for attempt in range(max_retries):
                    try:
                        await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                        page_loaded = True
                        break
                    except Exception as e:
                        print(f" -> [WARNING] Connection error (Attempt {attempt + 1}/{max_retries})...")
                        await human_like_delay(3.0, 5.0)
                        
                if not page_loaded:
                    print(f" -> [ERROR] Could not reach {target_url}. Word is being skipped.")
                    break
                
                await human_like_delay(2.5, 4.0)
                page_title = await page.title()
                
                if "Access to" in page_title or "Just a moment" in page_title or "Cloudflare" in page_title:
                    print(f"\n[SYSTEM WARNING] Security wall detected for '{keyword}'. Initiating stealth bypass...")
                    await bypass_cloudflare_advanced(page)
                    
                    page_title = await page.title()
                    if "Access to" in page_title or "Just a moment" in page_title:
                        print("[SYSTEM WARNING] Stuck in loop! Wiping session and cookies to drop tracking...")
                        await context.clear_cookies()
                        try:
                            await page.evaluate("""
                                window.localStorage.clear();
                                window.sessionStorage.clear();
                            """)
                        except:
                            pass
                        
                        await human_like_delay(2.0, 3.0)
                        await page.reload(wait_until="domcontentloaded")
                        await human_like_delay(3.0, 5.0)
                        await bypass_cloudflare_advanced(page)
                        
                        page_title = await page.title()
                        if "Access to" in page_title or "Just a moment" in page_title:
                            print("[SYSTEM WARNING] Bypass failed completely. Skipping keyword to prevent IP ban.")
                            break

                try:
                    await page.wait_for_selector('.k-ad-card', timeout=15000)
                    await simulate_human_behavior(page)
                except:
                    print(f"-> [INFO] No ads found on page {current_page}. Reached the last page. Moving to next keyword.")
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
                    detail_text = await detail_element.inner_text() if detail_element else "Not found"
                    
                    type_element = await card.query_selector('text="Zamanlı"')
                    emp_type = await type_element.inner_text() if type_element else "Not specified"
                    
                    logo_url = "No Logo"
                    
                    try:
                        await detail_page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
                        await human_like_delay(1.0, 2.0)
                        
                        detail_title = await detail_page.title()
                       
                        if "Just a moment" in detail_title or "Cloudflare" in detail_title or "Access to" in detail_title:
                            await bypass_cloudflare_advanced(detail_page)
                       
                        description_selectors = [
                            '[data-test="qualifications-and-job-description"]',
                            '.job-detail-content',
                            'job-detail-qualifications',
                            '.job-description',
                            '.detail-section'
                        ]
                        
                        job_description = "Description could not be retrieved"
                        
                        for selector in description_selectors:
                            try:
                                await detail_page.wait_for_selector(selector, timeout=4000)
                                desc_element = detail_page.locator(selector).first
                                desc_text = await desc_element.inner_text()
                                if desc_text:
                                    job_description = desc_text.strip()
                                    break 
                            except:
                                continue 
                                
                        if job_description == "Description could not be retrieved":
                             print(f"    -> [INFO] Description could not be loaded for {title}.")
                        
                    except Exception as e:
                        print(f"    -> [INFO] Connection timeout on detail page for {title}. Skipping description.")
                        job_description = "Description could not be retrieved"
                    
                    job_data = {
                        "Platform": "Kariyer.net",
                        "Search_Keyword": keyword,
                        "Job_Title": title,
                        "Company": company.strip(),
                        "Location_Details": detail_text.strip(),
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

                print(f"-> Page {current_page} completed: {page_valid_jobs} valid IT jobs retrieved and saved.")
                current_page += 1
                await human_like_delay(3.5, 6.0)

            await page.close()
            await detail_page.close()

        print("\nClosing the browser...")
        await context.close()
        await browser.close()
        print(f"AUTOMATION SUCCESSFUL! Data is securely streamed to '{jsonl_path}'.")

if __name__ == "__main__":
    if sys.platform.startswith("linux"):
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))
        display.start()
    else:
        display = None
        print("[INFO] Local OS detected. Running with real display...")

    try:
        asyncio.run(start_kariyer_scraper())
    finally:
        if display is not None:
            display.stop()