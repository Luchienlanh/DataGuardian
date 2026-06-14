import re
import sqlite3

from fastapi import HTTPException

from app.services.csv_reader import read_csv_file

BLOCKED_SQL = re.compile(
    r"\b(select|insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum)\b",
    re.IGNORECASE,
)


def validate_condition(condition: str) -> None:
    if not condition or not condition.strip():
        raise HTTPException(status_code=400, detail="Rule condition cannot be empty.")

    if ";" in condition or "--" in condition or "/*" in condition or "*/" in condition:
        raise HTTPException(status_code=400, detail="Rule condition contains unsafe SQL syntax.")

    if BLOCKED_SQL.search(condition):
        raise HTTPException(status_code=400, detail="Rule condition must be an expression, not a SQL statement.")


def run_quality_rules(file_path: str, rules: list) -> list[dict]:
    if not rules:
        return []

    df = read_csv_file(file_path)
    issues = []

    with sqlite3.connect(":memory:") as connection:
        df.to_sql("data", connection, if_exists="replace", index=False)

        for rule in rules:
            if rule.column not in df.columns:
                continue

            validate_condition(rule.condition)

            query = f"SELECT COUNT(*) FROM data WHERE NOT ({rule.condition})"

            try:
                failing_count = int(connection.execute(query).fetchone()[0])
            except sqlite3.Error as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid rule condition for '{rule.name}': {exc}",
                ) from exc

            if failing_count > 0:
                issues.append({
                    "type": "Rule violation",
                    "column": rule.column,
                    "severity": rule.severity,
                    "message": f"Rule '{rule.name}' failed for {failing_count} rows",
                    "evidence": {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "condition": rule.condition,
                        "failing_count": failing_count,
                        "total_count": int(len(df)),
                    },
                })

    return issues
