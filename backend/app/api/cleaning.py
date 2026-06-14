from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Dataset, CleaningStep, CleaningRun
from pathlib import Path
from fastapi.responses import FileResponse
from app.services.cleaner import (
    suggest_cleaning_steps,
    preview_cleaning, 
    apply_cleaning,
    build_cleaning_comparison,
)
from app.services.ai_cleaning import suggest_ai_cleaning_steps
from app.services.quality_pipeline import analyze_dataset_file, persist_quality_check

router = APIRouter()


class CleaningRequest(BaseModel):
    steps: list[dict]


def _get_dataset_or_404(dataset_id: int, db: Session) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    return dataset


def _run_to_dict(cleaning_run: CleaningRun) -> dict:
    return {
        "id": cleaning_run.id,
        "dataset_id": cleaning_run.dataset_id,
        "status": cleaning_run.status,
        "output_path": cleaning_run.output_path,
        "summary": cleaning_run.summary,
        "created_at": cleaning_run.created_at,
    }


def _dataset_to_summary(dataset: Dataset | None) -> dict | None:
    if not dataset:
        return None

    return {
        "id": dataset.id,
        "filename": dataset.filename,
        "size": dataset.size,
        "source": dataset.source or "uploaded",
        "version": dataset.version or 1,
        "parent_dataset_id": dataset.parent_dataset_id,
        "root_dataset_id": dataset.root_dataset_id or dataset.id,
        "cleaning_run_id": dataset.cleaning_run_id,
        "workspace_id": dataset.workspace_id,
        "created_at": dataset.created_at,
    }


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _step_to_dict(step: CleaningStep) -> dict:
    return {
        "id": step.id,
        "type": step.type,
        "column": step.column,
        "risk": step.risk,
        "status": step.status,
        "params": step.params,
        "affected_rows": step.affected_rows,
        "preview": step.preview,
    }


def _history_summary(
    cleaning_run: CleaningRun,
    steps: list[CleaningStep],
    previous_dataset: Dataset | None = None,
    current_dataset: Dataset | None = None,
) -> dict:
    summary = cleaning_run.summary or {}
    before = summary.get("before") or {}
    after = summary.get("after") or {}
    columns_touched = []
    risk_counts = {"safe": 0, "medium": 0, "high": 0}
    action_counts = {}
    total_affected_rows = 0

    for step in steps:
        preview = step.preview or {}
        if step.column:
            columns_touched.append(step.column)
        columns_touched.extend(_as_list(preview.get("columns_changed")))
        columns_touched.extend(_as_list(preview.get("columns_removed")))

        risk = step.risk or "safe"
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        action_counts[step.type] = action_counts.get(step.type, 0) + 1

        affected_rows = step.affected_rows
        if affected_rows is None:
            affected_rows = preview.get("affected_rows", 0)
        total_affected_rows += int(affected_rows or 0)

    columns_touched.extend(_as_list(summary.get("cleaned_columns")))
    columns_touched.extend(_as_list(summary.get("columns_changed")))
    columns_touched.extend(_as_list(summary.get("columns_removed")))
    columns_touched = list(dict.fromkeys(col for col in columns_touched if col))

    return {
        "run_id": cleaning_run.id,
        "status": cleaning_run.status,
        "created_at": cleaning_run.created_at,
        "previous_dataset": _dataset_to_summary(previous_dataset),
        "current_dataset": _dataset_to_summary(current_dataset),
        "steps_applied": len(steps) or int(summary.get("steps_applied") or 0),
        "total_affected_rows": total_affected_rows,
        "columns_touched": columns_touched,
        "columns_removed": _as_list(summary.get("columns_removed")),
        "rows_before": before.get("num_rows"),
        "rows_after": after.get("num_rows"),
        "columns_before": before.get("num_columns"),
        "columns_after": after.get("num_columns"),
        "missing_cells_before": before.get("missing_cells"),
        "missing_cells_after": after.get("missing_cells"),
        "rows_removed": summary.get("rows_removed", 0),
        "risk_counts": risk_counts,
        "action_counts": action_counts,
        "quality_check_id": summary.get("quality_check_id"),
        "download_url": f"/cleaning/runs/{cleaning_run.id}/download",
    }


def _cleaned_filename(filename: str, version: int) -> str:
    source_path = Path(filename)
    suffix = source_path.suffix or ".csv"
    return f"{source_path.stem}_cleaned_v{version}{suffix}"


def _next_dataset_version(db: Session, root_dataset_id: int) -> int:
    max_version = (
        db.query(func.max(Dataset.version))
        .filter(Dataset.root_dataset_id == root_dataset_id)
        .scalar()
    )

    return int(max_version or 1) + 1


@router.get("/datasets/{dataset_id}/suggestions")
def get_cleaning_suggestions(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(dataset_id, db)
    suggestions = suggest_cleaning_steps(dataset.storage_path)

    return {
        'dataset_id': dataset_id,
        'suggestions': suggestions,
    }


@router.get("/datasets/{dataset_id}/ai-suggestions")
def get_ai_cleaning_suggestions(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(dataset_id, db)
    result = suggest_ai_cleaning_steps(dataset.storage_path)

    return {
        "dataset_id": dataset_id,
        **result,
    }


@router.post("/datasets/{dataset_id}/preview")
def preview_cleaning_step(dataset_id: int, payload: CleaningRequest, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(dataset_id, db)

    try:
        preview = preview_cleaning(dataset.storage_path, payload.steps)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        'dataset_id': dataset_id,
        'steps': payload.steps,
        'preview': preview,
    }


@router.post("/datasets/{dataset_id}/apply")
def apply_cleaning_steps(dataset_id: int, payload: CleaningRequest, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(dataset_id, db)

    try:
        res = apply_cleaning(dataset.storage_path, payload.steps)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    output_path = Path(res["output_path"])
    profile, issues = analyze_dataset_file(db, str(output_path))

    cleaning_run = CleaningRun(
        dataset_id=dataset_id,
        status='applied',
        output_path=res['output_path'],
        summary=res,
    )
    db.add(cleaning_run)
    db.commit()
    db.refresh(cleaning_run)

    root_dataset_id = dataset.root_dataset_id or dataset.id
    next_version = _next_dataset_version(db, root_dataset_id)
    cleaned_dataset = Dataset(
        filename=_cleaned_filename(dataset.filename, next_version),
        storage_path=str(output_path),
        size=output_path.stat().st_size if output_path.exists() else 0,
        source="cleaned",
        version=next_version,
        parent_dataset_id=dataset.id,
        root_dataset_id=root_dataset_id,
        cleaning_run_id=cleaning_run.id,
        workspace_id=dataset.workspace_id,
    )
    db.add(cleaned_dataset)
    db.commit()
    db.refresh(cleaned_dataset)

    quality_check = persist_quality_check(db, cleaned_dataset.id, profile, issues)

    cleaned_dataset_summary = {
        "id": cleaned_dataset.id,
        "filename": cleaned_dataset.filename,
        "size": cleaned_dataset.size,
        "source": cleaned_dataset.source,
        "version": cleaned_dataset.version,
        "parent_dataset_id": cleaned_dataset.parent_dataset_id,
        "root_dataset_id": cleaned_dataset.root_dataset_id,
        "cleaning_run_id": cleaned_dataset.cleaning_run_id,
    }
    res["cleaned_dataset_id"] = cleaned_dataset.id
    res["cleaned_dataset"] = cleaned_dataset_summary
    res["quality_check_id"] = quality_check.id
    cleaning_run.summary = res

    details_by_index = res.get("step_details", [])
    for index, step in enumerate(payload.steps):
        detail = details_by_index[index] if index < len(details_by_index) else {}
        db.add(CleaningStep(
            cleaning_run_id=cleaning_run.id,
            type=step["type"],
            column=step.get("column"),
            params=step.get("params", {}),
            risk=step.get("risk", "safe"),
            status="applied",
            affected_rows=detail.get("affected_rows", step.get("affected_rows", 0)),
            preview=detail,
        ))

    db.commit()

    return {
        'dataset_id': dataset_id,
        'cleaning_run_id': cleaning_run.id,
        'cleaned_dataset_id': cleaned_dataset.id,
        'cleaned_dataset': cleaned_dataset_summary,
        'quality_check_id': quality_check.id,
        'result': res,
        'download_url': f'/cleaning/runs/{cleaning_run.id}/download',
    }


@router.get("/datasets/{dataset_id}/runs")
def list_cleaning_runs(dataset_id: int, db: Session = Depends(get_db)):
    dataset = _get_dataset_or_404(dataset_id, db)
    root_dataset_id = dataset.root_dataset_id or dataset.id
    version_datasets = (
        db.query(Dataset)
        .filter(or_(Dataset.root_dataset_id == root_dataset_id, Dataset.id == root_dataset_id))
        .all()
    )
    version_dataset_ids = [version.id for version in version_datasets]
    version_run_ids = [
        version.cleaning_run_id for version in version_datasets
        if version.cleaning_run_id is not None
    ]
    runs = (
        db.query(CleaningRun)
        .filter(or_(
            CleaningRun.dataset_id.in_(version_dataset_ids),
            CleaningRun.id.in_(version_run_ids),
        ))
        .order_by(CleaningRun.created_at.desc())
        .all()
    )

    response = []
    for run in runs:
        steps = (
            db.query(CleaningStep)
            .filter(CleaningStep.cleaning_run_id == run.id)
            .order_by(CleaningStep.id.asc())
            .all()
        )
        previous_dataset = db.query(Dataset).filter(Dataset.id == run.dataset_id).first()
        current_dataset = db.query(Dataset).filter(Dataset.cleaning_run_id == run.id).first()
        response.append({
            **_run_to_dict(run),
            "previous_dataset": _dataset_to_summary(previous_dataset),
            "current_dataset": _dataset_to_summary(current_dataset),
            "history": _history_summary(run, steps, previous_dataset, current_dataset),
            "steps": [_step_to_dict(step) for step in steps],
        })

    return response


@router.get("/runs/{cleaning_run_id}")
def get_cleaning_run(cleaning_run_id: int, db: Session = Depends(get_db)):
    cleaning_run = db.query(CleaningRun).filter(CleaningRun.id == cleaning_run_id).first()

    if not cleaning_run:
        raise HTTPException(status_code=404, detail="Cleaning run not found.")

    steps = (
        db.query(CleaningStep)
        .filter(CleaningStep.cleaning_run_id == cleaning_run_id)
        .order_by(CleaningStep.id.asc())
        .all()
    )
    previous_dataset = db.query(Dataset).filter(Dataset.id == cleaning_run.dataset_id).first()
    current_dataset = db.query(Dataset).filter(Dataset.cleaning_run_id == cleaning_run.id).first()
    step_previews = [step.preview for step in steps if step.preview]

    comparison = None
    if previous_dataset and Path(cleaning_run.output_path).exists():
        comparison = build_cleaning_comparison(
            previous_dataset.storage_path,
            cleaning_run.output_path,
            step_previews,
        )

    return {
        **_run_to_dict(cleaning_run),
        "previous_dataset": _dataset_to_summary(previous_dataset),
        "current_dataset": _dataset_to_summary(current_dataset),
        "history": _history_summary(cleaning_run, steps, previous_dataset, current_dataset),
        "comparison": comparison,
        "steps": [_step_to_dict(step) for step in steps],
        "download_url": f"/cleaning/runs/{cleaning_run.id}/download",
    }


@router.get("/runs/{cleaning_run_id}/download")
def download_cleaned_file(cleaning_run_id: int, db: Session = Depends(get_db)):
    cleaning_run = db.query(CleaningRun).filter(CleaningRun.id == cleaning_run_id).first()

    if not cleaning_run:
        raise HTTPException(status_code=404, detail="Cleaning run not found.")

    file_path = Path(cleaning_run.output_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Cleaned file not found.")

    return FileResponse(path=file_path, filename=f"cleaned_dataset_{cleaning_run.id}.csv", media_type='text/csv')


# Backward-compatible aliases for earlier local URLs.
router.add_api_route(
    "/datasets/{dataset_id}/cleaning/suggestions",
    get_cleaning_suggestions,
    methods=["GET"],
    include_in_schema=False,
)
router.add_api_route(
    "/datasets/{dataset_id}/cleaning/preview",
    preview_cleaning_step,
    methods=["POST"],
    include_in_schema=False,
)
router.add_api_route(
    "/datasets/{dataset_id}/cleaning/apply",
    apply_cleaning_steps,
    methods=["POST"],
    include_in_schema=False,
)
router.add_api_route(
    "/cleaning_runs/{cleaning_run_id}/download",
    download_cleaned_file,
    methods=["GET"],
    include_in_schema=False,
)

