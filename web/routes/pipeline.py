from fastapi import APIRouter
from src.utils import export_staging_ads, process_silver

router = APIRouter()

@router.post("/")
def run_full_pipeline():
    staging_file = export_staging_ads()
    if not staging_file:
        return {"error": "Aucune donnée pour le staging"}

    clean_file, report = process_silver(staging_file)

    return {
        "message": "Pipeline complet exécuté ✔",
        "staging_file": staging_file,
        "clean_file": clean_file,
        "quality_report": report
    }