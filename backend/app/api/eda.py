from fastapi import APIRouter, Depends, HTTPException
from app.services.eda import eda_report
from sqlalchemy.orm import Session
from app.db.models import Dataset
from app.db.session import get_db


router = APIRouter()

@router.get("/datasets/{dataset_id}/eda")
def get_eda(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    
    eda = eda_report(dataset.storage_path)
    
    return {
        'dataset_id': dataset_id,
        'eda': eda,
    }
