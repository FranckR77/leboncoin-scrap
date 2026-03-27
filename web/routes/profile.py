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

from fastapi import Form
import bcrypt

@router.post("/profile/change-password")
def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):

    if "user" not in request.session:
        return RedirectResponse("/login", status_code=302)

    username = request.session["user"]

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Récupérer les infos utilisateur
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            if not user:
                return RedirectResponse("/logout", status_code=302)

            # Vérifier ancien mot de passe
            if not bcrypt.checkpw(old_password.encode(), user["password_hash"].encode()):
                return RedirectResponse("/profile?error=old", status_code=302)

            # Vérifier confirmation
            if new_password != confirm_password:
                return RedirectResponse("/profile?error=confirm", status_code=302)

            # Hasher le nouveau mot de passe
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

            # Sauvegarder en base
            cur.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s",
                (new_hash, user["id"])
            )
            conn.commit()

    return RedirectResponse("/profile?success=1", status_code=302)