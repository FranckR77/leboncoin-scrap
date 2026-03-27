from fastapi import APIRouter, HTTPException, Query
import threading
from src.scraper.scraper import scrape_all_pages
from src.utils import insert_ads_to_db

router = APIRouter()

# global flags
scraping_lock = threading.Lock()
scraping_in_progress = False


# Background task: scrape and insert ads
def run_scraping_task(max_pages: int):
    global scraping_in_progress
    try:
        print(f"[SCRAPER] Starting background scrape for {max_pages} pages...")
        # Scraper already has a delay between pages (2s)
        ads = scrape_all_pages(max_pages=max_pages)
        
        if ads:
            print(f"[SCRAPER] Successfully collected {len(ads)} ads. Inserting into database...")
            insert_ads_to_db(ads)
            print(f"[SCRAPER:OK] {len(ads)} ads processed.")
        else:
            print("[SCRAPER:WARN] No ads found during the scraping session.")
            
    except Exception as e:
        print(f"[SCRAPER:KO] Critical error during scraping: {e}")
    finally:
        scraping_in_progress = False
        if scraping_lock.locked():
            scraping_lock.release()
        print("[SCRAPER] Background task finished.")


@router.post("/")
def run_scrap(pages: int = Query(60, ge=1, le=100, description="Number of pages to scrape (35 ads/page). Use 60 to get ~2000 ads.")):
    global scraping_in_progress

    # Prevent concurrent runs
    if scraping_in_progress:
        raise HTTPException(status_code=409, detail="Scraping already in progress")

    # Try acquiring the lock
    if scraping_lock.acquire(blocking=False):
        scraping_in_progress = True
        
        # Start background thread
        thread = threading.Thread(target=run_scraping_task, args=(pages,), daemon=True)
        thread.start()
        
        return {
            "message": f"Scraping of {pages} pages ({pages * 35} ads estimated) started in background.",
            "status": "started"
        }
    else:
        raise HTTPException(status_code=409, detail="Scraping already in progress")


@router.get("/status")
def scrap_status():
    return {"scraping": scraping_in_progress}