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
@app.get("/legal/cgu", response_class=HTMLResponse)
async def legal_cgu(request: Request):
    return templates.TemplateResponse("cgu.html", {"request": request})

@app.get("/legal/privacy", response_class=HTMLResponse)
async def legal_privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

from ml.predict import predict_price
from fastapi import Body

@app.post("/predict")
async def predict(payload: dict = Body(...)):
    """
    Exemple de JSON attendu :
    {
        "city": "Nîmes",
        "zipcode": "30000",
        "region": "Occitanie",
        "category": "Ventes immobilières",
        "type": "Maison"
    }
    """
    try:
        predicted = predict_price(payload)
        return {"predicted_price": round(predicted)}
    except Exception as e:
        return {"error": str(e)}
