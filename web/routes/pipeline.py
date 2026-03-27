from fastapi import APIRouter, HTTPException
from src.utils import full_data_pipeline
import os
import json

router = APIRouter()


@router.post("/")
def run_full_pipeline():
    """Runs the full E2E pipeline: Bronze -> Gold -> Train Model."""
    result = full_data_pipeline()
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Données insuffisantes ou erreur lors de l'export. Lancez d'abord le scraping."
        )

    # Try to read generated metrics
    metrics = {}
    metrics_path = "./datalake/models/metrics_latest.json"
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

    return {
        "message": "Pipeline complet exécuté ✔ (Modèle ré-entraîné)",
        "gold_file": result.get("gold_file"),
        "model_path": result.get("model_path"),
        "metrics": metrics
    }


@router.get("/metrics")
def get_model_metrics():
    """Returns the performance metrics of the latest trained model."""
    metrics_path = "./datalake/models/metrics_latest.json"
    if not os.path.exists(metrics_path):
        raise HTTPException(
            status_code=404,
            detail="Aucun modèle n'a encore été entraîné avec succès."
        )

    with open(metrics_path, "r") as f:
        return json.load(f)