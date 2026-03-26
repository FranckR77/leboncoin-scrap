from fastapi import APIRouter
from src.utils import export_raw_ads

router = APIRouter()

@router.post("/")
def export_csv():
    path = export_raw_ads
    return {"message": "Export terminé", "file": path}