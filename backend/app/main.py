from pathlib import Path

from fastapi import Request
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.agent import router as agent_router
from app.api.datasets import router as dataset_router
from app.api.cleaning import router as cleaning_router
from app.api.eda import router as eda_router
from app.api.jobs import router as jobs_router
from app.api.observability import router as observability_router
from app.api.reports import router as reports_router
from app.api.rules import router as rules_router
from app.api.workspace import router as workspace_router
from app.db.database import Base, SessionLocal, engine, ensure_database_schema
from app.db import models
from app.services.observability import log_event

Base.metadata.create_all(bind=engine)
ensure_database_schema()

app = FastAPI(title="DataGuardian")


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        db = SessionLocal()
        try:
            log_event(
                db,
                level="error",
                source="backend",
                message=str(exc),
                context={"path": request.url.path, "method": request.method},
            )
        finally:
            db.close()
        raise

    if response.status_code >= 500:
        db = SessionLocal()
        try:
            log_event(
                db,
                level="error",
                source="backend",
                message=f"HTTP {response.status_code}",
                context={"path": request.url.path, "method": request.method},
            )
        finally:
            db.close()

    return response

app.include_router(dataset_router, prefix="/datasets", tags=["datasets"])
app.include_router(rules_router, prefix="/rules", tags=["rules"])
app.include_router(agent_router, prefix="/agent", tags=["agent"])
app.include_router(eda_router, tags=["eda"])
app.include_router(cleaning_router, prefix="/cleaning", tags=["cleaning"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(observability_router, prefix="/observability", tags=["observability"])
app.include_router(workspace_router, prefix="/workspace", tags=["workspace"])

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
