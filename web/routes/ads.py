from fastapi import APIRouter, HTTPException, Query
from src.utils import get_connection

router = APIRouter()


# Fetch ads from database with optional filters
@router.get("/")
def list_ads(
    city: str | None = Query(None, description="Filter by city"),
    min_price: str | None = Query(None, description="Minimum price"),
    max_price: str | None = Query(None, description="Maximum price"),
    suspicious_only: bool = Query(
        False, description="If true, only return suspicious ads"
    ),
    order_by_score: bool = Query(
        False, description="If true, order results by score DESC"
    ),
):
    query = "SELECT * FROM ads WHERE 1=1"
    params: list = []

    # normalize inputs
    city = city.strip() if city else None
    try:
        min_price = int(min_price) if min_price not in (None, "", "null") else None
        max_price = int(max_price) if max_price not in (None, "", "null") else None
    except ValueError:
        raise HTTPException(
            status_code=400, detail="min_price and max_price must be numbers"
        )

    if city:
        query += " AND city LIKE %s"
        params.append(f"%{city}%")

    if min_price is not None:
        query += " AND price >= %s"
        params.append(min_price)

    if max_price is not None:
        query += " AND price <= %s"
        params.append(max_price)

    if suspicious_only:
        query += " AND suspicious = 1"

    if order_by_score:
        query += " ORDER BY score DESC"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                data = cur.fetchall()
    except Exception as e:
        # au lieu de crasher toute l'API
        return {"count": 0, "ads": [], "error": str(e)}

    return {"count": len(data), "ads": data}
