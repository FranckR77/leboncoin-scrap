from fastapi import APIRouter, HTTPException
from src.utils import full_data_pipeline

router = APIRouter()

@router.post("/")
def run_full_pipeline():
    result = full_data_pipeline()
    if not result:
        raise HTTPException(status_code=400, detail="Aucune donnée brute trouvée. Lancez d'abord le scraping.")
    
    return {
        "message": "Pipeline complet exécuté ✔",
        "gold_file": result.get("gold_file"),
        "model_path": result.get("model_path")
    }