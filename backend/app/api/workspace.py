from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import Dataset, Workspace
from app.db.session import get_db
from app.services.workspace import get_or_create_local_user, get_workspace_from_header

router = APIRouter()


def _workspace_to_dict(workspace: Workspace, db: Session) -> dict:
    user = get_or_create_local_user(db, workspace)
    dataset_count = db.query(Dataset).filter(Dataset.workspace_id == workspace.id).count()
    return {
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "created_at": workspace.created_at,
        },
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        },
        "auth_mode": "local_development",
        "dataset_count": dataset_count,
    }


@router.get("/current")
def current_workspace(db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    return _workspace_to_dict(workspace, db)


@router.get("")
def list_workspaces(db: Session = Depends(get_db)):
    workspaces = db.query(Workspace).order_by(Workspace.created_at.asc()).all()
    return [
        {
            "id": workspace.id,
            "name": workspace.name,
            "slug": workspace.slug,
            "created_at": workspace.created_at,
        }
        for workspace in workspaces
    ]
