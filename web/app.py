from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import routes
from web.routes import ads, scrap

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
