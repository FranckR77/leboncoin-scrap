from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from src.utils import get_connection

router = APIRouter()

@router.post("/favorites/{ad_id}")
def add_favorite(ad_id: int, request: Request):
    if "user" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    username = request.session["user"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username=%s", (username,))
            user = cur.fetchone()

            if not user:
                raise HTTPException(404, "User not found")

            try:
                cur.execute(
                    "INSERT INTO favorites (user_id, ad_id) VALUES (%s, %s)",
                    (user["id"], ad_id)
                )
                conn.commit()
            except:
                return JSONResponse({"message": "Déjà dans les favoris"})

    return {"message": "Ajouté aux favoris"}

@router.delete("/favorites/{ad_id}")
def remove_favorite(ad_id: int, request: Request):
    if "user" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    username = request.session["user"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            # récupérer user_id
            cur.execute("SELECT id FROM users WHERE username=%s", (username,))
            user = cur.fetchone()

            cur.execute(
                "DELETE FROM favorites WHERE user_id=%s AND ad_id=%s",
                (user["id"], ad_id),
            )
            conn.commit()

    return {"message": "Retiré des favoris"}