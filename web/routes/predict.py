from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import glob
import os

router = APIRouter()

class PredictionRequest(BaseModel):
    surface: float
    city: str
    type: str
    category: str
    suspicious: int = 0
    score: int = 3
    has_image: int = 1
    day_of_week: int = 3
    month: int = 6
    is_weekend: int = 0

@router.post("/")
def predict_price(request: PredictionRequest):
    # Find the latest model
    model_dir = "./datalake/models"
    model_files = glob.glob(f"{model_dir}/rf_price_pipeline_*.joblib")
    
    if not model_files:
        raise HTTPException(status_code=404, detail="Aucun modèle entraîné n'a été trouvé. Lancez d'abord le pipeline.")
    
    # Sort files to get the latest
    latest_model_file = max(model_files, key=os.path.getmtime)
    
    try:
        model = joblib.load(latest_model_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de chargement du modèle : {e}")
    
    # Create DataFrame from request
    df_input = pd.DataFrame([{
        'surface': request.surface,
        'city': request.city,
        'type': request.type,
        'category': request.category,
        'suspicious': request.suspicious,
        'score': request.score,
        'has_image': request.has_image,
        'day_of_week': request.day_of_week,
        'month': request.month,
        'is_weekend': request.is_weekend
    }])
    
    try:
        prediction = model.predict(df_input)
        price = round(prediction[0], 2)
        return {"estimated_price": price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction : {str(e)}")
