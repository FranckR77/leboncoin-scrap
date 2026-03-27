from fastapi import APIRouter, HTTPException, Query, Request
from math import ceil
from src.utils import get_connection

router = APIRouter()

@router.get("/")
def list_ads(
    request: Request,
    city: str | None = Query(None, description="Filter by city"),
    min_price: str | None = Query(None, description="Minimum price"),
    max_price: str | None = Query(None, description="Maximum price"),
    suspicious_only: bool = Query(False, description="If true, only return suspicious ads"),
    order_by_score: bool = Query(False, description="If true, order results by score DESC"),
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of ads per page"),
):

    where_clause = " WHERE 1=1"
    params: list = []

    # Normalisation des filtres
    city = city.strip() if city else None
    try:
        min_price = int(min_price) if min_price not in (None, "", "null") else None
        max_price = int(max_price) if max_price not in (None, "", "null") else None
    except ValueError:
        raise HTTPException(status_code=400, detail="min_price and max_price must be numbers")

    if city:
        where_clause += " AND city LIKE %s"
        params.append(f"%{city}%")

    if min_price is not None:
        where_clause += " AND price >= %s"
        params.append(min_price)

    if max_price is not None:
        where_clause += " AND price <= %s"
        params.append(max_price)

    if suspicious_only:
        where_clause += " AND suspicious = 1"

    count_query = "SELECT COUNT(*) AS total FROM ads" + where_clause
    data_query = "SELECT * FROM ads" + where_clause

    if order_by_score:
        data_query += " ORDER BY score DESC"
    else:
        data_query += " ORDER BY id DESC"

    offset = (page - 1) * page_size
    data_query += " LIMIT %s OFFSET %s"
    data_params = params + [page_size, offset]

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(count_query, params)
                row = cur.fetchone()
                total = row["total"] if row and "total" in row else 0
                total_pages = ceil(total / page_size) if total else 1

                cur.execute(data_query, data_params)
                data = cur.fetchall()

            # 🔥 AJOUT : Récupération des favoris de l'utilisateur connecté
            username = request.session.get("user")
            fav_ids = set()

            if username:
                with get_connection() as conn:
                    with conn.cursor() as cur2:
                        cur2.execute("SELECT id FROM users WHERE username=%s", (username,))
                        user = cur2.fetchone()
                        if user:
                            cur2.execute("SELECT ad_id FROM favorites WHERE user_id=%s", (user["id"],))
                            fav_ids = {row["ad_id"] for row in cur2.fetchall()}

            # Ajouter la clé is_favorite à chaque annonce
            for ad in data:
                ad["is_favorite"] = ad["id"] in fav_ids

    except Exception as e:
        return {"count": 0, "ads": [], "error": str(e)}

    return {
        "count": len(data),
        "ads": data,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }