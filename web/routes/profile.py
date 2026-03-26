from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.utils import get_connection

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    # Vérifier que l'utilisateur est connecté
    if "user" not in request.session:
        return RedirectResponse("/login")

    username = request.session["user"]

    # Récupérer les infos utilisateur
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cur.fetchone()

            # Récupérer les favoris
            cur.execute("""
                SELECT ads.* FROM ads
                JOIN favorites ON favorites.ad_id = ads.id
                WHERE favorites.user_id = %s
                ORDER BY favorites.created_at DESC
            """, (user["id"],))

            favorites = cur.fetchall()

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "favorites": favorites}
    )