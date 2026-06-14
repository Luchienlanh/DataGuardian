import sqlite3
from typing import Any

from fastapi import HTTPException

from app.services.csv_reader import read_csv_file
from app.services.sql_agent import validate_select_sql


def execute_select_query(file_path: str, sql: str, limit: int = 200) -> dict[str, Any]:
    capped_limit = max(1, min(limit, 500))
    safe_sql = validate_select_sql(sql, capped_limit)
    df = read_csv_file(file_path)

    with sqlite3.connect(":memory:") as connection:
        df.to_sql("data", connection, if_exists="replace", index=False)
        connection.row_factory = sqlite3.Row

        try:
            cursor = connection.execute(safe_sql)
            rows = [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            raise HTTPException(status_code=400, detail=f"SQL execution failed: {exc}") from exc

    return {
        "sql": safe_sql,
        "columns": list(rows[0].keys()) if rows else [],
        "rows": rows,
        "row_count": len(rows),
    }
