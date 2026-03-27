from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Import routes
from web.routes import (
    ads,
    scrap,
    export,
    clean,
    pipeline,
    predict,
    stats,
    auth,
    profile,
    favorites
)

app = FastAPI()

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGE_CE_SECRET",
)

# Templates
templates = Jinja2Templates(directory="web/templates")

# Home Page
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if "user" not in request.session:
        return RedirectResponse("/login")
    return templates.TemplateResponse("index.html", {"request": request})

# Include routes
app.include_router(ads.router, prefix="/ads", tags=["Ads"])
app.include_router(scrap.router, prefix="/scrap", tags=["Scraper"])
app.include_router(export.router, prefix="/export", tags=["Export"])
app.include_router(clean.router, prefix="/clean", tags=["Clean"])
app.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(predict.router, prefix="/predict", tags=["Prediction"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(auth.router)
app.include_router(favorites.router)
app.include_router(profile.router)

# Legal pages
@app.get("/legal/cgu", response_class=HTMLResponse)
async def legal_cgu(request: Request):
    return templates.TemplateResponse("cgu.html", {"request": request})

@app.get("/legal/privacy", response_class=HTMLResponse)
async def legal_privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})