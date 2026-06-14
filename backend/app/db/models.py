from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from app.db.database import Base

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    source = Column(String, default="uploaded")
    version = Column(Integer, default=1)
    parent_dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    root_dataset_id = Column(Integer, nullable=True)
    cleaning_run_id = Column(Integer, nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    email = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    role = Column(String, default="owner")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    
class QualityCheck(Base):
    __tablename__ = "quality_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    profile = Column(JSON, nullable=False)
    status = Column(String, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    

class QualityIssue(Base):
    __tablename__ = "quality_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    quality_check_id = Column(Integer, ForeignKey("quality_checks.id"), nullable=False)
    type = Column(String, nullable=False)
    column = Column(String, nullable=True)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    evidence = Column(JSON, nullable=True)


class QualityRule(Base):
    __tablename__ = "quality_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    column = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    severity = Column(String, default="medium")
    is_active = Column(Boolean, default=True)
    created_by = Column(String, default="manual")
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CleaningRun(Base):
    __tablename__ = 'cleaning_runs'
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'), nullable=False)
    status = Column(String, default='applied')
    output_path = Column(String, nullable=False)
    summary = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    
class CleaningStep(Base):
    __tablename__ = 'cleaning_steps'
    
    id = Column(Integer, primary_key=True, index=True)
    cleaning_run_id = Column(Integer, ForeignKey('cleaning_runs.id'), nullable=False)
    type = Column(String, nullable=False)
    column = Column(String, nullable=True)
    risk = Column(String, default='safe')
    status = Column(String, default='applied')
    params = Column(JSON, nullable=True)
    affected_rows = Column(Integer, nullable=True)
    preview = Column(JSON, nullable=True)


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    question = Column(Text, nullable=True)
    sql = Column(Text, nullable=False)
    mode = Column(String, default="agent")
    status = Column(String, default="completed")
    row_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportExport(Base):
    __tablename__ = "report_exports"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("app_jobs.id"), nullable=True)
    format = Column(String, default="html")
    output_path = Column(String, nullable=False)
    summary = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppJob(Base):
    __tablename__ = "app_jobs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    type = Column(String, nullable=False)
    status = Column(String, default="queued")
    progress = Column(Integer, default=0)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AppEvent(Base):
    __tablename__ = "app_events"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    level = Column(String, default="info")
    source = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
