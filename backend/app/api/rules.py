from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.models import Dataset, QualityRule
from app.db.session import get_db
from app.services.nl_rule_builder import build_rule_from_text
from app.services.rule_engine import validate_condition
from app.services.workspace import get_workspace_from_header

router = APIRouter()


class QualityRuleCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    column: str = Field(min_length=1)
    condition: str = Field(min_length=1)
    severity: str = "medium"
    is_active: bool = True


class NaturalLanguageRuleRequest(BaseModel):
    dataset_id: int
    instruction: str = Field(min_length=1)
    create: bool = False


@router.get("")
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(QualityRule).order_by(QualityRule.created_at.desc()).all()

    return [
        {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "column": rule.column,
            "condition": rule.condition,
            "severity": rule.severity,
            "is_active": rule.is_active,
            "created_by": rule.created_by,
            "workspace_id": rule.workspace_id,
            "created_at": rule.created_at,
        }
        for rule in rules
    ]


@router.post("")
def create_rule(payload: QualityRuleCreate, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    if payload.severity not in {"low", "medium", "high"}:
        raise HTTPException(status_code=400, detail="Severity must be low, medium, or high.")

    validate_condition(payload.condition)

    rule = QualityRule(
        name=payload.name,
        description=payload.description,
        column=payload.column,
        condition=payload.condition,
        severity=payload.severity,
        is_active=payload.is_active,
        workspace_id=workspace.id,
        created_by="manual",
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "column": rule.column,
        "condition": rule.condition,
        "severity": rule.severity,
        "is_active": rule.is_active,
        "created_by": rule.created_by,
        "created_at": rule.created_at,
    }


@router.post("/from-natural-language")
def create_rule_from_natural_language(payload: NaturalLanguageRuleRequest, db: Session = Depends(get_db), workspace=Depends(get_workspace_from_header)):
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    candidate = build_rule_from_text(dataset.storage_path, payload.instruction)

    if not payload.create:
        return {
            "dataset_id": dataset.id,
            "candidate": candidate,
            "created": False,
        }

    rule = QualityRule(
        name=candidate["name"],
        description=candidate["description"],
        column=candidate["column"],
        condition=candidate["condition"],
        severity=candidate["severity"],
        is_active=candidate["is_active"],
        created_by="natural_language",
        workspace_id=workspace.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return {
        "dataset_id": dataset.id,
        "candidate": candidate,
        "created": True,
        "rule": {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "column": rule.column,
            "condition": rule.condition,
            "severity": rule.severity,
            "is_active": rule.is_active,
            "created_by": rule.created_by,
            "created_at": rule.created_at,
        },
    }
