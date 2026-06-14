from html import escape
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import CleaningRun, Dataset, QualityCheck, QualityIssue
from app.services.eda import eda_report


REPORT_DIR = Path("storage/reports")


def export_dataset_report(db: Session, dataset: Dataset) -> dict:
    latest_check = (
        db.query(QualityCheck)
        .filter(QualityCheck.dataset_id == dataset.id)
        .order_by(QualityCheck.created_at.desc())
        .first()
    )
    issues = []
    if latest_check:
        issues = db.query(QualityIssue).filter(QualityIssue.quality_check_id == latest_check.id).all()

    cleaning_runs = (
        db.query(CleaningRun)
        .filter(CleaningRun.dataset_id == dataset.id)
        .order_by(CleaningRun.created_at.desc())
        .limit(10)
        .all()
    )
    eda = eda_report(dataset.storage_path)
    profile = latest_check.profile if latest_check else {}

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORT_DIR / f"dataset_{dataset.id}_report_{uuid4().hex[:8]}.html"
    output_path.write_text(
        _render_html(dataset, profile, issues, cleaning_runs, eda),
        encoding="utf-8",
    )

    return {
        "output_path": str(output_path),
        "format": "html",
        "summary": {
            "dataset_id": dataset.id,
            "filename": dataset.filename,
            "rows": profile.get("num_rows"),
            "columns": profile.get("num_columns"),
            "issue_count": len(issues),
            "cleaning_run_count": len(cleaning_runs),
            "eda_insight_count": len(eda.get("insights", [])),
        },
    }


def _render_html(dataset, profile, issues, cleaning_runs, eda) -> str:
    issue_rows = "\n".join(
        f"<tr><td>{escape(issue.severity)}</td><td>{escape(issue.type)}</td><td>{escape(issue.column or '-')}</td><td>{escape(issue.message)}</td></tr>"
        for issue in issues
    ) or "<tr><td colspan='4'>No issues found.</td></tr>"
    run_rows = "\n".join(
        f"<tr><td>#{run.id}</td><td>{escape(run.status)}</td><td>{escape(str(run.created_at))}</td><td>{escape(str((run.summary or {}).get('steps_applied', 0)))}</td></tr>"
        for run in cleaning_runs
    ) or "<tr><td colspan='4'>No cleaning runs yet.</td></tr>"
    insights = "\n".join(
        f"<li><strong>{escape(item.get('severity', 'info'))}</strong>: {escape(item.get('message', ''))}</li>"
        for item in eda.get("insights", [])
    ) or "<li>No EDA insights generated.</li>"

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>DataGuardian Report - {escape(dataset.filename)}</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; color: #15201c; margin: 32px; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .meta {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }}
    .card {{ border: 1px solid #dbe7e2; border-radius: 8px; padding: 12px; background: #f8fbfa; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border-bottom: 1px solid #dbe7e2; padding: 8px; text-align: left; font-size: 13px; }}
    th {{ background: #eef6f3; }}
  </style>
</head>
<body>
  <h1>{escape(dataset.filename)}</h1>
  <p>DataGuardian quality, EDA, and cleaning report.</p>
  <section class="meta">
    <div class="card"><span>Dataset ID</span><h2>{dataset.id}</h2></div>
    <div class="card"><span>Rows</span><h2>{escape(str(profile.get("num_rows", "-")))}</h2></div>
    <div class="card"><span>Columns</span><h2>{escape(str(profile.get("num_columns", "-")))}</h2></div>
    <div class="card"><span>Issues</span><h2>{len(issues)}</h2></div>
  </section>
  <h2>Quality Issues</h2>
  <table><thead><tr><th>Severity</th><th>Type</th><th>Column</th><th>Message</th></tr></thead><tbody>{issue_rows}</tbody></table>
  <h2>EDA Insights</h2>
  <ul>{insights}</ul>
  <h2>Cleaning Runs</h2>
  <table><thead><tr><th>Run</th><th>Status</th><th>Created</th><th>Steps</th></tr></thead><tbody>{run_rows}</tbody></table>
</body>
</html>"""
