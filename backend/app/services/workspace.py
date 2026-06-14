from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db.models import AppUser, Workspace
from app.db.session import get_db


def get_default_workspace(db: Session) -> Workspace:
    workspace = db.query(Workspace).filter(Workspace.slug == "default").first()
    if workspace:
        return workspace

    workspace = Workspace(name="Default Workspace", slug="default")
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def get_workspace_from_header(
    db: Session = Depends(get_db),
    x_workspace_id: int | None = Header(default=None, alias="X-Workspace-Id"),
) -> Workspace:
    if x_workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == x_workspace_id).first()
        if workspace:
            return workspace

    return get_default_workspace(db)


def get_or_create_local_user(db: Session, workspace: Workspace) -> AppUser:
    user = db.query(AppUser).filter(AppUser.workspace_id == workspace.id).first()
    if user:
        return user

    user = AppUser(
        workspace_id=workspace.id,
        email="local@dataguard.dev",
        display_name="Local Analyst",
        role="owner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
