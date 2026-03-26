from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import routes
from web.routes import ads, scrap
from web.routes import export
from web.routes import clean
from web.routes import pipeline

app = FastAPI()

# Mount static files
#app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates (HTML)
templates = Jinja2Templates(directory="web/templates")


# Home Page (index.html)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Add routes
app.include_router(ads.router, prefix="/ads", tags=["Ads"])
app.include_router(scrap.router, prefix="/scrap", tags=["Scraper"])
app.include_router(export.router, prefix="/export", tags=["Export"])
app.include_router(clean.router, prefix="/clean", tags=["Clean"])
app.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"])
@app.get("/legal/cgu", response_class=HTMLResponse)
async def legal_cgu(request: Request):
    return templates.TemplateResponse("cgu.html", {"request": request})

@app.get("/legal/privacy", response_class=HTMLResponse)
async def legal_privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})
