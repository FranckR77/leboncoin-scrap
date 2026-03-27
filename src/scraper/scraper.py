import time
import json
import requests
from lxml import html
from config.settings import HEADERS, BASE_URL
from src.utils import anonymize

def fetch_page(page: int) -> dict | None:
    """Fetch one page using requests and return parsed JSON from __NEXT_DATA__."""
    url = BASE_URL.format(page)
    print(f"[SCRAPER] Fetching page {page}: {url}")

    try:
        # verify=False to avoid SSL issues in some environments, similar to the test script
        response = requests.get(url, headers=HEADERS, timeout=20, verify=False)
    except Exception as e:
        print(f"[SCRAPER] Network error: {e}")
        return None

    print(f"[SCRAPER] HTTP {response.status_code} — {len(response.text)} chars")

    if response.status_code != 200:
        print(f"[SCRAPER] Failed to fetch page {page}: HTTP {response.status_code}")
        return None

    tree = html.fromstring(response.text)
    json_data_raw = tree.xpath('//script[@id="__NEXT_DATA__"]/text()')

    if not json_data_raw:
        print("[SCRAPER] No __NEXT_DATA__ found.")
        # Debug: save response for inspection
        try:
            import os
            os.makedirs("/app/datalake", exist_ok=True)
            with open("/app/datalake/debug_page.html", "w", encoding="utf-8") as f:
                f.write(response.text[:50000])
            print("[SCRAPER] Debug HTML saved to /app/datalake/debug_page.html")
        except Exception:
            pass
        return None

    try:
        data = json.loads(json_data_raw[0])
        return data
    except json.JSONDecodeError:
        print(f"[SCRAPER] Invalid JSON on page {page}")
        return None


def parse_ads(data: dict) -> list[dict]:
    """Extract ads from the JSON structure."""
    search_data = data.get("props", {}).get("pageProps", {}).get("searchData", {})
    ads = search_data.get("ads", [])
    parsed = []

    for ad in ads:
        location = ad.get("location", {})
        attributes = ad.get("attributes", [])
        images = ad.get("images", {})

        real_estate_type = next(
            (
                a.get("value_label")
                for a in attributes
                if a.get("key") == "real_estate_type"
            ),
            "N/A",
        )
        surface = get_attribute_value(
            attributes, "square", "living_area", "land_plot_surface")

        # Author info
        owner = ad.get("owner", {})
        author_name = owner.get("name", "N/A")
        has_phone = ad.get("has_phone", False)
        contact_info = "Disponible" if has_phone else "Non communiqué"

        parsed.append(
            {
                "title": ad.get("subject", "N/A"),
                "category": ad.get("category_name", "N/A"),
                "type": real_estate_type,
                "surface": surface,
                "price": ad.get("price", [None])[0],
                "city": location.get("city", ""),
                "zipcode": location.get("zipcode", ""),
                "region": location.get("region_name", ""),
                "url": ad.get("url", ""),
                "image_url": images.get("urls", [None])[0],
                "author": author_name,
                "contact": contact_info,
            }
        )
    return parsed


def get_attribute_value(attributes: list[dict], *keys: str, default="N/A"):
    """Extract the first matching attribute value."""
    for key in keys:
        for attribute in attributes:
            if attribute.get("key") == key:
                return (
                    attribute.get("value_label")
                    or attribute.get("value")
                    or default
                )
    return default


def scrape_all_pages(max_pages: int = 10, delay: float = 2.0) -> list[dict]:
    """Scrape multiple pages using pagination until no more ads."""
    all_ads = []
    for page in range(1, max_pages + 1):
        data = fetch_page(page)
        if not data:
            break
        ads = parse_ads(data)
        if not ads:
            print(f"[SCRAPER] No more ads on page {page}, stopping.")
            break

        # Anonymize each ad before saving
        anonymized = [anonymize(a) for a in ads]
        all_ads.extend(anonymized)

        print(f"[SCRAPER] Page {page}: {len(ads)} ads collected (total: {len(all_ads)})")
        time.sleep(delay)
    return all_ads
