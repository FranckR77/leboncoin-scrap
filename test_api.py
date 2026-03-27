import requests
import json

payload = {
    "limit": 3,
    "offset": 0,
    "filters": {
        "category": {"id": "9"},
        "enums": {"ad_type": ["offer"]}
    },
    "sort_by": "time",
    "sort_order": "desc",
}

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://www.leboncoin.fr",
    "Referer": "https://www.leboncoin.fr/",
    "api_key": "ba0c2dad52b3ec",
}

r = requests.post("https://api.leboncoin.fr/finder/search", json=payload, headers=headers, timeout=30)
print(f"HTTP {r.status_code}")
if r.status_code == 200:
    data = r.json()
    ads = data.get("ads", [])
    total = data.get("total", 0)
    print(f"Ads returned: {len(ads)}, Total available: {total}")
    for a in ads:
        loc = a.get("location", {})
        price = a.get("price", [])
        title = a.get("subject", "N/A")[:60]
        city = loc.get("city", "?")
        print(f"  - {title} | {price} | {city}")
else:
    print(f"Error response: {r.text[:500]}")
