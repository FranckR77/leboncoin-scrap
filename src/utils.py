import pymysql
import json
from hashlib import sha256
from config.settings import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
from pymysql.err import OperationalError, IntegrityError
from fastapi import HTTPException
import csv
import os
from datetime import datetime
import pandas as pd
import numpy as np
from src.processing.features import engineer_features

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
            title, category, type, surface, price, city,
            zipcode, region, url, image_url, author, contact, suspicious, score
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
                ad.get("surface"),
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

def export_raw_ads(output_dir: str = "./datalake/raw"):
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{output_dir}/ads_raw_{timestamp}.csv"

    query = "SELECT * FROM ads ORDER BY id ASC"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    if not rows:
        print("Aucune donnée en base, export annulé.")
        return None

    fieldnames = rows[0].keys()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[RAW] CSV exporté : {filename}")
    return filename

def export_staging_ads(output_dir: str = "./datalake/staging"):
    raw_file = export_raw_ads()  # réutilisation de ton export RAW

    if not raw_file:
        return None

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(raw_file)

    # Nettoyage léger avant nettoyage complet (Silver)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["surface"] = (
        df["surface"].astype(str).str.extract(r"(\d+)").astype(float)
    )

    df["title"] = df["title"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["region"] = df["region"].astype(str).str.strip().str.title()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    staging_file = f"{output_dir}/ads_staging_{timestamp}.csv"
    df.to_csv(staging_file, index=False, encoding="utf-8")

    print(f"[STAGING] Fichier staging généré : {staging_file}")
    return staging_file

def process_silver(
    staging_file: str,
    output_dir="./datalake/processed",
    quality_dir="./datalake/quality"
):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(quality_dir, exist_ok=True)

    df = pd.read_csv(staging_file)
    report = {}

    # =============================
    # 1. Doublons
    # =============================
    before = len(df)
    df.drop_duplicates(subset=["url"], inplace=True)
    report["duplicates_removed"] = before - len(df)

    # =============================
    # 2. Normalisation types
    # =============================
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["surface"] = pd.to_numeric(df["surface"], errors="coerce")

    # =============================
    # 3. Clean des chaînes
    # =============================
    for col in ["title", "city", "region", "category", "type"]:
        df[col] = df[col].astype(str).str.strip().str.title()

    # =============================
    # 4. Anomalies (prix, surface)
    # =============================
    report["invalid_price"] = int(df["price"].lt(1000).sum())
    report["invalid_surface"] = int(df["surface"].lt(5).sum())

    # =============================
    # 5. URL valides
    # =============================
    df["url_valid"] = df["url"].str.startswith("http")
    report["invalid_urls"] = int((~df["url_valid"]).sum())
    df = df[df["url_valid"]]

    # =============================
    # 6. Valeurs manquantes
    # =============================
    report["missing_values"] = df.isna().sum().to_dict()

    # =============================
    # 7. Export SILVER (clean)
    # =============================
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = f"{output_dir}/ads_clean_{timestamp}.parquet"
    df.to_parquet(out_file, index=False)

    # =============================
    # 8. Rapport qualité
    # =============================
    quality_file = f"{quality_dir}/quality_report_{timestamp}.json"
    with open(quality_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[SILVER] Clean file: {out_file}")
    print(f"[QUALITY] Report: {quality_file}")

    return out_file, report

def process_gold(silver_file: str, output_dir="./datalake/gold"):
    """
    Step 6: Feature Engineering (Gold layer).
    Transforme les données cleanées en données exploitables par le ML.
    """
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_parquet(silver_file)
    df_features = engineer_features(df)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = f"{output_dir}/ads_gold_{timestamp}.parquet"
    df_features.to_parquet(out_file, index=False)

    print(f"[GOLD] Gold file (features): {out_file}")
    return out_file

def full_data_pipeline():
    # Bronze -> Staging
    staging_file = export_staging_ads()
    if not staging_file:
        return None

    # Staging -> Silver
    silver_file, _ = process_silver(staging_file)

    # Silver -> Gold
    gold_file = process_gold(silver_file)
    
    # Train Model
    from src.models.train import train_model
    model_path = train_model(gold_file)

    return {"gold_file": gold_file, "model_path": model_path}