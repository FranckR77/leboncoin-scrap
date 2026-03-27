from fastapi import APIRouter
from src.utils import get_connection
from statistics import mean, median
from datetime import datetime, date
from collections import defaultdict

router = APIRouter()

@router.get("/")
def get_stats():
    """Returns various stats about the scraped ads."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch prices and dates
                cur.execute("SELECT price, DATE(created_at) as created_date FROM ads WHERE price IS NOT NULL")
                rows = cur.fetchall()

        if not rows:
            return {
                "success": True,
                "count": 0,
                "mean": 0,
                "median": 0,
                "histogram": [],
                "evolution": []
            }

        prices = [float(row["price"]) for row in rows]
        
        # 2. Main indicators
        avg_price = mean(prices)
        med_price = median(prices)

        # 3. Histogram (Buckets of 50,000e)
        if prices:
            min_p = min(prices)
            max_p = max(prices)
            range_p = max_p - min_p
            step = 50000
            
            # Adjust step if range is too small
            if range_p < step and range_p > 0: 
                step = max(1000, int(range_p / 5))
            
            buckets = defaultdict(int)
            for p in prices:
                bucket_key = int(p // step) * step
                buckets[bucket_key] += 1
            
            # Sorted buckets for chart
            histogram = []
            for k in sorted(buckets.keys()):
                histogram.append({
                    "range": f"{k:,.0f}€ - {k+step:,.0f}€", 
                    "count": buckets[k], 
                    "min": k
                })
        else:
            histogram = []

        # 4. Evolution over time (Average price per day)
        evo_data = defaultdict(list)
        for row in rows:
            d = row["created_date"]
            # MySQL DATE() might return string, date object or datetime
            if isinstance(d, (datetime, date)):
                d_str = d.strftime("%Y-%m-%d")
            else:
                d_str = str(d)
                
            evo_data[d_str].append(float(row["price"]))

        evolution = []
        for d in sorted(evo_data.keys()):
            evolution.append({
                "date": d, 
                "avg_price": round(mean(evo_data[d]), 2)
            })

        return {
            "success": True,
            "count": len(prices),
            "mean": round(avg_price, 2),
            "median": round(med_price, 2),
            "histogram": histogram,
            "evolution": evolution
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
