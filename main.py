from src.scraper import scrape_all_pages, insert_ads_to_db
from src.utils import save_to_json

if __name__ == "__main__":
    ads = scrape_all_pages(max_pages=4)
    save_to_json(ads, "./dist/ads.json")
    insert_ads_to_db(ads)
