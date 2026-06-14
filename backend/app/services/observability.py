from sqlalchemy.orm import Session

from app.db.models import AppEvent


def log_event(
    db: Session,
    *,
    level: str,
    source: str,
    message: str,
    context: dict | None = None,
    workspace_id: int | None = None,
) -> AppEvent:
    event = AppEvent(
        level=level,
        source=source,
        message=message,
        context=context or {},
        workspace_id=workspace_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
