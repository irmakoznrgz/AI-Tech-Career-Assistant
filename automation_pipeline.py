import subprocess
import sys
import time
import os
from datetime import datetime

SCRAPERS = [
    "src/scraper/youthall.py",
    "src/scraper/techcareer.py",
    "src/scraper/linkedin.py",
    "src/scraper/indeed.py",
    "src/scraper/kariyer.py"
]

CORE_PIPELINE = [
    "src/data_cleaner.py",
    "src/predict.py",
    "src/build_vector_db.py"
]

def run_script(script_path, strict=False):
    print(f"\n{'='*50}")
    print(f"STARTING: {script_path}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_path], 
            check=True, 
            text=True,
            timeout=900
        )
        end_time = time.time()
        print(f"✅ SUCCESSFUL: {script_path} (Time: {end_time - start_time:.2f} seconds)")
        return True
        
    except subprocess.TimeoutExpired:
        end_time = time.time()
        print(f"⚠️ TIMEOUT: {script_path} hung for too long (>15 mins) and was killed! Moving to next...")
        if strict:
            sys.exit(1)
        return False
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        print(f"❌ ERROR: {script_path} crashed! (Duration: {end_time - start_time:.2f} seconds)")
        
        if strict:
            print("[CRITICAL] Kritik bir aşamada hata alındı. Pipeline durduruluyor!")
            sys.exit(1) 
        else:
            print("[WARNING] Scraper error. Ignore and move on to the next one...")
            return False

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if os.path.exists(os.path.join(project_root, "src")):
        os.chdir(project_root)

    print(f"\nMASTER PIPELINE STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pipeline_start = time.time()
  
    print("\n" + "#"*40)
    print("PHASE 1: DATA COLLECTION (SCRAPERS)")
    print("#"*40)
    
    successful_scrapers = 0
    for scraper in SCRAPERS:
        if os.path.exists(scraper):
            if run_script(scraper, strict=False):
                successful_scrapers += 1
        else:
            print(f"FILE NOT FOUND: {scraper}")

    print(f"\nScraper Summary: {successful_scrapers} out of {len(SCRAPERS)} bots have run successfully.")

    if successful_scrapers == 0:
        sys.exit(1)

    print("\n" + "#"*40)
    print("PHASE 2: DATA PROCESSING & CHROMA DB")
    print("#"*40)
    
    for core_script in CORE_PIPELINE:
        if os.path.exists(core_script):
            run_script(core_script, strict=True)
        else:
            print(f"FILE NOT FOUND: {core_script}")
            sys.exit(1)

    print("\n" + "#"*40)
    print("PHASE 3: DATABASE CLEANUP (STATUS CHECKER)")
    print("#"*40)
    
    status_checker_path = "src/status_checker.py"
    if os.path.exists(status_checker_path):
        run_script(status_checker_path, strict=False)
    else:
        print(f"FILE NOT FOUND: {status_checker_path}. Skipping cleanup phase.")
            
    pipeline_end = time.time()
    print("\n" + "="*40)
    print(f"MASTER PIPELINE COMPLETED!")

    print(f"Total Runtime: {(pipeline_end - pipeline_start) / 60:.2f} minutes")
    print("\n" + "="*40)

if __name__ == "__main__":
    main()