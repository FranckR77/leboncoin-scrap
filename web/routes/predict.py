from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import glob
import os
import json
import glob

router = APIRouter()

class PredictionRequest(BaseModel):
    surface: float
    zipcode: str
    region: str
    city: str
    type: str
    category: str
    score: int = 3
    has_image: int = 1

@router.post("/")
def predict_price(request: PredictionRequest):
    # Find the latest model
    model_dir = "./datalake/models"
    model_files = glob.glob(f"{model_dir}/rf_price_pipeline_*.joblib")
    
    if not model_files:
        raise HTTPException(status_code=404, detail="Aucun modèle entraîné n'a été trouvé. Lancez d'abord le pipeline.")
    
    # Sort files to get the latest
    latest_model_file = max(model_files, key=os.path.getmtime)
    
    # Extraction du département (2 premiers chiffres)
    dept = str(request.zipcode).strip()[:2]
    
    try:
        model = joblib.load(latest_model_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de chargement du modèle : {e}")
    
    # CHARGEMENT DU CLUSTER DE MARCHÉ
    cluster_mapping_path = f"{model_dir}/market_clusters_v1.json"
    market_cluster = 5  # Valeur de repli (milieu de gamme)
    
    if os.path.exists(cluster_mapping_path):
        with open(cluster_mapping_path, "r") as f:
            cluster_data = json.load(f)
            mapping = cluster_data.get("map", {})
            key = f"{dept}_{request.city}"
            market_cluster = mapping.get(key, cluster_data.get("global_median_cluster", 5))

    # Create DataFrame from request
    df_input = pd.DataFrame([{
        'surface': request.surface,
        'market_cluster': market_cluster,
        'dept': dept,
        'region': request.region,
        'type': request.type,
        'category': request.category,
        'score': request.score,
        'has_image': request.has_image
    }])
    
    try:
        import numpy as np
        prediction = model.predict(df_input)
        pred_value = float(prediction[0])
        
        # Auto-detection du log-transform (si le prix est < 25, c'est probablement un log-prix)
        if pred_value < 25:
            price_real = np.expm1(pred_value)
        else:
            price_real = pred_value
            
        return {"estimated_price": round(price_real, 2), "dept_used": dept}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction : {str(e)}")
