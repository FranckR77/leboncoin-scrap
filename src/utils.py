import pymysql
import json
from hashlib import sha256
from config.settings import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
from pymysql.err import OperationalError, IntegrityError
from fastapi import HTTPException


# Save all ads into a JSON file
def save_to_json(data: list[dict], filename: str = "./data/ads.json"):
    import os

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nData exported to {filename}")


# Anonymize sensitive fields
def anonymize(ad: dict) -> dict:
    ad["author"] = sha256(ad.get("author", "anon").encode()).hexdigest()[:12]
    ad["contact"] = "hidden"
    return ad


def is_suspicious(ad: dict) -> bool:
    """Règles simples pour marquer une annonce comme suspecte."""
    price = ad.get("price")

    try:
        price = int(price) if price is not None else None
    except (TypeError, ValueError):
        price = None

    title = (ad.get("title") or "").lower()

    # règle 1 : prix très bas
    if price is not None and price < 50000:
        return True

    # règle 2 : terrain très peu cher
    if "terrain" in title and price is not None and price < 10000:
        return True

    return False


def compute_score(ad: dict) -> int:
    """
    Score simple de qualité (0–5).
    Plus il y a d'infos utiles, plus le score monte.
    """
    score = 0

    price = ad.get("price")
    image_url = ad.get("image_url")
    city = ad.get("city")
    ad_type = ad.get("type")

    # prix renseigné
    if price not in (None, "", 0):
        score += 1

    # image présente
    if image_url:
        score += 1

    # ville renseignée
    if city:
        score += 1

    # type de bien renseigné
    if ad_type and ad_type != "N/A":
        score += 1

    # bonus si l'annonce n'est pas jugée suspecte
    if not is_suspicious(ad):
        score += 1

    return score


# Insert ads into MySQL
def insert_ads_to_db(ads: list[dict]):
    if not ads:
        print("No ads to insert.")
        return

    sql = """
        INSERT INTO ads (
            title, category, type, price, city,
            zipcode, region, url, image_url, author, contact, suspicious, score
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = []
    for ad in ads:
        suspicious = 1 if is_suspicious(ad) else 0
        score = compute_score(ad)
        values.append(
            (
                ad.get("title"),
                ad.get("category"),
                ad.get("type"),
                ad.get("price"),
                ad.get("city"),
                ad.get("zipcode"),
                ad.get("region"),
                ad.get("url"),
                ad.get("image_url"),
                ad.get("author"),
                ad.get("contact"),
                suspicious,
                score,
            )
        )

    inserted = 0
    skipped = 0
    BATCH_SIZE = 20
    MAX_RETRIES = 3

    i = 0
    while i < len(values):
        batch = values[i : i + BATCH_SIZE]

        for attempt in range(MAX_RETRIES):
            try:
                conn = get_connection()
                with conn:
                    conn.ping(reconnect=True)  # contre les erreurs 2013
                    with conn.cursor() as cursor:
                        try:
                            cursor.executemany(sql, batch)
                            inserted += cursor.rowcount
                        except IntegrityError:
                            # doublons dans le batch → fallback unitaire
                            for row in batch:
                                try:
                                    cursor.execute(sql, row)
                                    inserted += 1
                                except IntegrityError:
                                    skipped += 1
                    conn.commit()

                break  # batch OK, on sort du retry
            except OperationalError as e:
                if attempt == MAX_RETRIES - 1:
                    raise HTTPException(
                        status_code=500, detail=f"Insert failed: {str(e)}"
                    )
                print(
                    f"[DB] Lost connection during batch, retry {attempt+1}/{MAX_RETRIES} ... {e}"
                )

        i += BATCH_SIZE

    print(f"{inserted} new ads inserted, {skipped} duplicates skipped.")


# Simple DB connection
def get_connection():
    try:
        return pymysql.connect(
            host=DB_HOST,  # idéalement "127.0.0.1" pour Docker sous Windows
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            read_timeout=60,
            write_timeout=60,
            charset="utf8mb4",
            autocommit=False,
        )
    except OperationalError as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )
