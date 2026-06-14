from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import AppJob
from app.db.session import get_db
from app.services.workspace import get_workspace_from_header

router = APIRouter()


def _job_to_dict(job: AppJob) -> dict:
    return {
        "id": job.id,
        "workspace_id": job.workspace_id,
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "payload": job.payload,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.get("")
def list_jobs(db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    jobs = (
        db.query(AppJob)
        .filter(AppJob.workspace_id == workspace.id)
        .order_by(AppJob.created_at.desc())
        .limit(50)
        .all()
    )
    return [_job_to_dict(job) for job in jobs]


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(AppJob).filter(AppJob.id == job_id).first()
    return _job_to_dict(job) if job else {"error": "Job not found"}
