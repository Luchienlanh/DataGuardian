from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.storage import save_upload_file
from app.services.quality_pipeline import analyze_dataset_file, persist_quality_check
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models import Dataset, QualityCheck, QualityIssue
from app.db.session import get_db
from app.services.workspace import get_workspace_from_header

router = APIRouter()


def _dataset_to_dict(dataset: Dataset) -> dict:
    return {
        'id': dataset.id,
        'filename': dataset.filename,
        'storage_path': dataset.storage_path,
        'size': dataset.size,
        'source': dataset.source or 'uploaded',
        'version': dataset.version or 1,
        'parent_dataset_id': dataset.parent_dataset_id,
        'root_dataset_id': dataset.root_dataset_id or dataset.id,
        'cleaning_run_id': dataset.cleaning_run_id,
        'workspace_id': dataset.workspace_id,
        'created_at': dataset.created_at,
    }

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    file_path = await save_upload_file(file)
    if not file_path:
        raise HTTPException(status_code=400, detail="Failed to save the uploaded file.")
    
    profile, issues = analyze_dataset_file(db, file_path['storage_path'])

    dataset = Dataset(
        filename = file.filename,
        storage_path = file_path['storage_path'],
        size = file_path['size'],
        source="uploaded",
        version=1,
        workspace_id=workspace.id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    dataset.root_dataset_id = dataset.id
    db.commit()
    db.refresh(dataset)
    
    check = persist_quality_check(db, dataset.id, profile, issues)
    
    
    return {
        'dataset_id': dataset.id,
        'quality_check_id': check.id,
        'file_info': file_path,
        'profile': profile,
        'quality_issues': issues,
    }


@router.get("")
def list_datasets(db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    datasets = (
        db.query(Dataset)
        .filter(Dataset.workspace_id == workspace.id)
        .order_by(Dataset.created_at.desc())
        .all()
    )

    return [_dataset_to_dict(dataset) for dataset in datasets]
    
@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    
    return _dataset_to_dict(dataset)


@router.get("/{dataset_id}/versions")
def get_dataset_versions(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    root_dataset_id = dataset.root_dataset_id or dataset.id
    versions = (
        db.query(Dataset)
        .filter(or_(Dataset.root_dataset_id == root_dataset_id, Dataset.id == root_dataset_id))
        .order_by(Dataset.version.asc(), Dataset.created_at.asc())
        .all()
    )

    return [_dataset_to_dict(version) for version in versions]
    
@router.get("/{dataset_id}/checks")
def get_quality_check(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    
    checks = (
        db.query(QualityCheck)
        .filter(QualityCheck.dataset_id == dataset_id)
        .order_by(QualityCheck.created_at.desc())
        .all()
    )

    return [
        {
            'id': check.id,
            'dataset_id': check.dataset_id,
            'profile': check.profile,
            'status': check.status,
            'created_at': check.created_at,
        }
        for check in checks
    ]
    

@router.get("/checks/{check_id}/issues")
def get_quality_issues(check_id: int, db: Session = Depends(get_db)):
    check = db.query(QualityCheck).filter(QualityCheck.id == check_id).first()

    if not check:
        raise HTTPException(status_code=404, detail="Quality check not found.")

    issues = db.query(QualityIssue).filter(QualityIssue.quality_check_id == check_id).all()

    return [
        {
            'id': issue.id,
            'quality_check_id': issue.quality_check_id,
            'type': issue.type,
            'column': issue.column,
            'severity': issue.severity,
            'message': issue.message,
            'evidence': issue.evidence,
        }
        for issue in issues
    ]
