from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import AppEvent
from app.db.session import get_db
from app.services.observability import log_event
from app.services.workspace import get_workspace_from_header

router = APIRouter()


class ClientEvent(BaseModel):
    level: str = "error"
    source: str = "frontend"
    message: str
    context: dict | None = None


def _event_to_dict(event: AppEvent) -> dict:
    return {
        "id": event.id,
        "workspace_id": event.workspace_id,
        "level": event.level,
        "source": event.source,
        "message": event.message,
        "context": event.context,
        "created_at": event.created_at,
    }


@router.get("/events")
def list_events(level: str | None = None, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    query = db.query(AppEvent).filter(or_(AppEvent.workspace_id == workspace.id, AppEvent.workspace_id.is_(None)))
    if level:
        query = query.filter(AppEvent.level == level)
    events = query.order_by(AppEvent.created_at.desc()).limit(100).all()
    return [_event_to_dict(event) for event in events]


@router.post("/events")
def create_client_event(payload: ClientEvent, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    event = log_event(
        db,
        level=payload.level,
        source=payload.source,
        message=payload.message,
        context=payload.context,
        workspace_id=workspace.id,
    )
    return _event_to_dict(event)
