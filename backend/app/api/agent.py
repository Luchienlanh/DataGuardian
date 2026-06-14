from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_agent_config
from app.db.models import Dataset, QueryHistory
from app.db.session import get_db
from app.services.sql_agent import query_dataset_with_agent
from app.services.sql_runner import execute_select_query
from app.services.workspace import get_workspace_from_header

router = APIRouter()


class AgentQueryRequest(BaseModel):
    dataset_id: int
    question: str = Field(min_length=1)
    limit: int = 200


class SqlQueryRequest(BaseModel):
    dataset_id: int
    sql: str = Field(min_length=1)
    limit: int = 200


def _history_to_dict(item: QueryHistory) -> dict:
    return {
        "id": item.id,
        "dataset_id": item.dataset_id,
        "workspace_id": item.workspace_id,
        "question": item.question,
        "sql": item.sql,
        "mode": item.mode,
        "status": item.status,
        "row_count": item.row_count,
        "error": item.error,
        "explanation": item.explanation,
        "created_at": item.created_at,
    }


@router.get("/config")
def get_config():
    return get_agent_config()


@router.post("/query")
def query_dataset(payload: AgentQueryRequest, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    history = QueryHistory(
        dataset_id=dataset.id,
        workspace_id=workspace.id,
        question=payload.question,
        sql="",
        mode="agent",
        status="running",
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    try:
        result = query_dataset_with_agent(
            file_path=dataset.storage_path,
            question=payload.question,
            limit=payload.limit,
        )
    except Exception as exc:
        history.status = "failed"
        history.error = str(getattr(exc, "detail", exc))
        db.commit()
        raise

    history.sql = result["sql"]
    history.status = "completed"
    history.row_count = result["row_count"]
    history.explanation = result.get("explanation")
    db.commit()

    return {
        "dataset": {
            "id": dataset.id,
            "filename": dataset.filename,
        },
        **result,
    }


@router.post("/sql")
def execute_manual_sql(payload: SqlQueryRequest, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    history = QueryHistory(
        dataset_id=dataset.id,
        workspace_id=workspace.id,
        question=None,
        sql=payload.sql,
        mode="manual_sql",
        status="running",
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    try:
        result = execute_select_query(dataset.storage_path, payload.sql, payload.limit)
    except Exception as exc:
        history.status = "failed"
        history.error = str(getattr(exc, "detail", exc))
        db.commit()
        raise

    history.sql = result["sql"]
    history.status = "completed"
    history.row_count = result["row_count"]
    history.explanation = "Manual read-only SQL executed successfully."
    db.commit()

    return {
        "dataset": {
            "id": dataset.id,
            "filename": dataset.filename,
        },
        "question": None,
        "explanation": history.explanation,
        "generated_by": "manual_sql",
        **result,
    }


@router.get("/history")
def list_query_history(dataset_id: int | None = None, limit: int = 25, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    query = db.query(QueryHistory).filter(QueryHistory.workspace_id == workspace.id)
    if dataset_id:
        query = query.filter(QueryHistory.dataset_id == dataset_id)

    items = query.order_by(QueryHistory.created_at.desc()).limit(max(1, min(limit, 100))).all()
    return [_history_to_dict(item) for item in items]
