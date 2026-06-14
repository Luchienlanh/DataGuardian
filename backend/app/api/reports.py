from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.models import AppJob, Dataset, ReportExport
from app.db.session import get_db
from app.services.report_exporter import export_dataset_report
from app.services.workspace import get_workspace_from_header

router = APIRouter()


def _report_to_dict(report: ReportExport) -> dict:
    return {
        "id": report.id,
        "dataset_id": report.dataset_id,
        "workspace_id": report.workspace_id,
        "job_id": report.job_id,
        "format": report.format,
        "output_path": report.output_path,
        "summary": report.summary,
        "created_at": report.created_at,
        "download_url": f"/reports/{report.id}/download",
    }


@router.post("/datasets/{dataset_id}/export")
def export_report(dataset_id: int, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    job = AppJob(
        workspace_id=workspace.id,
        type="report_export",
        status="running",
        progress=20,
        payload={"dataset_id": dataset_id, "format": "html"},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        result = export_dataset_report(db, dataset)
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        job.progress = 100
        db.commit()
        raise

    report = ReportExport(
        dataset_id=dataset.id,
        workspace_id=workspace.id,
        job_id=job.id,
        format=result["format"],
        output_path=result["output_path"],
        summary=result["summary"],
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    job.status = "completed"
    job.progress = 100
    job.result = {"report_id": report.id, "download_url": f"/reports/{report.id}/download"}
    db.commit()

    return {
        "job": {
            "id": job.id,
            "type": job.type,
            "status": job.status,
            "progress": job.progress,
            "result": job.result,
        },
        "report": _report_to_dict(report),
    }


@router.get("")
def list_reports(dataset_id: int | None = None, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    query = db.query(ReportExport).filter(ReportExport.workspace_id == workspace.id)
    if dataset_id:
        query = query.filter(ReportExport.dataset_id == dataset_id)

    reports = query.order_by(ReportExport.created_at.desc()).limit(50).all()
    return [_report_to_dict(report) for report in reports]


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(ReportExport).filter(ReportExport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    file_path = Path(report.output_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found.")

    return FileResponse(
        path=file_path,
        filename=f"dataguard_report_{report.dataset_id}_{report.id}.html",
        media_type="text/html",
    )
