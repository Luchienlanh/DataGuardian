from sqlalchemy.orm import Session

from app.db.models import QualityCheck, QualityIssue, QualityRule
from app.services.profiler import profile_csv
from app.services.quality_check import quality_check
from app.services.rule_engine import run_quality_rules


def analyze_dataset_file(db: Session, file_path: str) -> tuple[dict, list[dict]]:
    profile = profile_csv(file_path)
    issues = quality_check(file_path, profile=profile)
    active_rules = db.query(QualityRule).filter(QualityRule.is_active.is_(True)).all()
    issues.extend(run_quality_rules(file_path, active_rules))

    return profile, issues


def persist_quality_check(
    db: Session,
    dataset_id: int,
    profile: dict,
    issues: list[dict],
) -> QualityCheck:
    check = QualityCheck(
        dataset_id=dataset_id,
        profile=profile,
        status="completed",
    )
    db.add(check)
    db.commit()
    db.refresh(check)

    for issue in issues:
        db.add(QualityIssue(
            quality_check_id=check.id,
            type=issue["type"],
            column=issue.get("column"),
            severity=issue["severity"],
            message=issue["message"],
            evidence=issue.get("evidence"),
        ))

    db.commit()
    return check
