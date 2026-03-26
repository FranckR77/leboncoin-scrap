from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import bcrypt
from src.utils import get_connection

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...)):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, hashed)
                )
            conn.commit()
    except Exception:
        return RedirectResponse("/register?error=1", status_code=302)

    return RedirectResponse("/login", status_code=302)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cur.fetchone()

    # Si utilisateur introuvable
    if not user:
        return RedirectResponse("/login?error=1", status_code=302)

    # Vérifier le hash
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return RedirectResponse("/login?error=1", status_code=302)

    request.session["user"] = username
    return RedirectResponse("/", status_code=302)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()  # supprime toutes les données de session
    return RedirectResponse("/login", status_code=302)