import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

urls = [
    "https://www.leboncoin.fr/c/ventes_immobilieres/?page=1",
    "https://www.leboncoin.fr/recherche?category=9&locations=Paris&page=1",
    "https://www.leboncoin.fr/recherche?category=9&page=1",
    "https://www.leboncoin.fr/c/ventes_immobilieres/offres/ile_de_france/?page=1",
    "https://www.leboncoin.fr/recherche?text=vente+immobiliere&page=1",
]

for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        has_next = "__NEXT_DATA__" in r.text
        print(f"[{r.status_code}] {len(r.text):>6} chars | NEXT_DATA={has_next} | {url}")
    except Exception as e:
        print(f"[ERR] {e} | {url}")
