from fastapi import APIRouter
from src.utils import process_silver
import glob

router = APIRouter()

@router.post("/")
def clean_data():
    files = sorted(glob.glob("./datalake/staging/*.csv"))
    if not files:
        return {"error": "Aucun fichier staging trouvé."}

    latest = files[-1]
    silver, report = process_silver(latest)
    return {
        "message": "Nettoyage terminé ✔",
        "clean_file": silver,
        "quality_report": report
    }