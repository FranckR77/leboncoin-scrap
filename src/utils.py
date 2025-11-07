import pymysql
import json
from hashlib import sha256
from config.settings import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
from pymysql.err import OperationalError
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


# Insert ads into MySQL
def insert_ads_to_db(ads: list[dict]):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            for ad in ads:
                sql = """
                    INSERT INTO ads (
                        title, category, type, price, city,
                        zipcode, region, url, author, contact
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cursor.execute(
                    sql,
                    (
                        ad.get("title"),
                        ad.get("category"),
                        ad.get("type"),
                        ad.get("price"),
                        ad.get("city"),
                        ad.get("zipcode"),
                        ad.get("region"),
                        ad.get("url"),
                        ad.get("author"),
                        ad.get("contact"),
                    ),
                )
        connection.commit()
    print(f"{len(ads)} ads inserted into database.")


# Simple DB connection
def get_connection():
    try:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor,
        )
    except OperationalError as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )
