from pathlib import Path
from uuid import uuid4

import pandas as pd

from app.services.csv_reader import read_csv_file


CLEANED_DIR = Path("storage/cleaned")
DEFAULT_SAMPLE_SIZE = 10


def _as_list(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _safe_records(
    df: pd.DataFrame,
    limit: int = DEFAULT_SAMPLE_SIZE,
    indexes: list | None = None,
) -> list[dict]:
    if indexes is not None:
        available_indexes = [index for index in indexes if index in df.index]
        sample = df.loc[available_indexes] if available_indexes else df.head(limit)
    else:
        sample = df.head(limit)
    sample = sample.head(limit).astype(object)
    sample = sample.where(pd.notna(sample), None)
    return sample.to_dict(orient="records")


def _dataset_stats(df: pd.DataFrame) -> dict:
    return {
        "num_rows": int(len(df)),
        "num_columns": int(len(df.columns)),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def _cleaned_columns(step_details: list[dict]) -> list[str]:
    columns = []

    for detail in step_details or []:
        if detail.get("column"):
            columns.append(detail["column"])
        columns.extend(_as_list(detail.get("columns_changed")))
        columns.extend(_as_list(detail.get("columns_removed")))

    return list(dict.fromkeys(col for col in columns if col))


def _affected_indexes(before: pd.DataFrame, after: pd.DataFrame, columns: list[str]) -> list:
    if before.empty:
        return []

    shared_indexes = before.index.intersection(after.index)
    shared_columns = [col for col in columns if col in before.columns and col in after.columns]

    if not len(shared_indexes) or not shared_columns:
        return list(before.head(DEFAULT_SAMPLE_SIZE).index)

    changed_mask = pd.Series(False, index=shared_indexes)
    before_subset = before.loc[shared_indexes, shared_columns].astype(object)
    after_subset = after.loc[shared_indexes, shared_columns].astype(object)

    for column in shared_columns:
        changed_mask = changed_mask | (before_subset[column] != after_subset[column]).fillna(False)

    changed_indexes = list(changed_mask[changed_mask].index)
    return changed_indexes[:DEFAULT_SAMPLE_SIZE] if changed_indexes else list(before.head(DEFAULT_SAMPLE_SIZE).index)


def build_cleaning_comparison(
    before_path: str,
    after_path: str,
    step_details: list[dict] | None = None,
) -> dict:
    before = read_csv_file(before_path)
    after = read_csv_file(after_path)
    step_details = step_details or []
    cleaned_columns = _cleaned_columns(step_details)
    sample_indexes = _affected_indexes(before, after, cleaned_columns)

    return {
        "before": {
            **_dataset_stats(before),
            "sample": _safe_records(before, indexes=sample_indexes),
        },
        "after": {
            **_dataset_stats(after),
            "sample": _safe_records(after, indexes=sample_indexes),
        },
        "diff": {
            "rows_removed": int(len(before) - len(after)),
            "columns_removed": [col for col in before.columns if col not in after.columns],
            "columns_changed": [
                col for col in before.columns.intersection(after.columns)
                if not before[col].equals(after[col])
            ],
            "cleaned_columns": cleaned_columns,
            "missing_cells_delta": int(after.isna().sum().sum() - before.isna().sum().sum()),
        },
        "step_details": step_details,
    }


def _normalize_step(step: dict) -> dict:
    normalized = {
        "type": step.get("type"),
        "column": step.get("column"),
        "columns": step.get("columns") or [],
        "params": step.get("params") or {},
        "risk": step.get("risk", "safe"),
        "message": step.get("message"),
    }

    if not normalized["type"]:
        raise ValueError("Cleaning step must include a type.")

    return normalized


def _numeric_outlier_summary(series: pd.Series, factor: float = 1.5) -> dict:
    numeric = pd.to_numeric(series, errors="coerce").dropna()

    if numeric.empty:
        return {
            "lower_bound": None,
            "upper_bound": None,
            "outlier_count": 0,
            "outlier_rate": 0.0,
        }

    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - factor * iqr
    upper_bound = q3 + factor * iqr
    mask = (numeric < lower_bound) | (numeric > upper_bound)
    outlier_count = int(mask.sum())

    return {
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
        "outlier_count": outlier_count,
        "outlier_rate": float(outlier_count / len(numeric)) if len(numeric) else 0.0,
    }


def suggest_cleaning_steps(file_path: str) -> list[dict]:
    df = read_csv_file(file_path)
    suggestions = []

    duplicated_rows = int(df.duplicated().sum())
    if duplicated_rows > 0:
        suggestions.append({
            "type": "remove_duplicate_rows",
            "column": None,
            "risk": "safe",
            "message": f"Remove {duplicated_rows} fully duplicate rows.",
            "affected_rows": duplicated_rows,
            "params": {},
        })

    empty_rows = int(df.isna().all(axis=1).sum())
    if empty_rows > 0:
        suggestions.append({
            "type": "remove_empty_rows",
            "column": None,
            "risk": "safe",
            "message": f"Remove {empty_rows} rows where every column is empty.",
            "affected_rows": empty_rows,
            "params": {},
        })

    object_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in object_cols:
        series = df[col].dropna().astype(str)

        whitespace_count = int((series != series.str.strip()).sum())
        if whitespace_count > 0:
            suggestions.append({
                "type": "trim_whitespace",
                "column": col,
                "risk": "safe",
                "message": f'Trim leading/trailing whitespace in "{col}".',
                "affected_rows": whitespace_count,
                "params": {},
            })

        empty_string_count = int((series.str.strip() == "").sum())
        if empty_string_count > 0:
            suggestions.append({
                "type": "handle_empty_strings",
                "column": col,
                "risk": "safe",
                "message": f'Replace {empty_string_count} empty strings in "{col}" with null values.',
                "affected_rows": empty_string_count,
                "params": {},
            })

    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if missing_count == 0:
            continue

        missing_rate = float(missing_count / len(df)) if len(df) else 0.0

        if missing_rate >= 0.6:
            suggestions.append({
                "type": "drop_column",
                "column": col,
                "risk": "medium",
                "message": f'Drop "{col}" because {missing_rate:.1%} of values are missing.',
                "affected_rows": missing_count,
                "params": {},
            })
        elif pd.api.types.is_numeric_dtype(df[col]):
            suggestions.append({
                "type": "fill_missing",
                "column": col,
                "risk": "safe",
                "message": f'Fill {missing_count} missing values in numeric column "{col}" with the median.',
                "affected_rows": missing_count,
                "params": {"method": "median"},
            })
        else:
            suggestions.append({
                "type": "fill_missing",
                "column": col,
                "risk": "safe",
                "message": f'Fill {missing_count} missing values in categorical column "{col}" with the mode.',
                "affected_rows": missing_count,
                "params": {"method": "mode"},
            })

    for col in df.select_dtypes(include="number").columns:
        outliers = _numeric_outlier_summary(df[col])
        if outliers["outlier_rate"] > 0.05:
            suggestions.append({
                "type": "cap_outliers_iqr",
                "column": col,
                "risk": "medium",
                "message": f'Cap {outliers["outlier_count"]} IQR outliers in "{col}".',
                "affected_rows": outliers["outlier_count"],
                "params": {
                    "factor": 1.5,
                    "lower_bound": outliers["lower_bound"],
                    "upper_bound": outliers["upper_bound"],
                },
            })

    return suggestions


def apply_step(df: pd.DataFrame, step: dict) -> tuple[pd.DataFrame, dict]:
    normalized = _normalize_step(step)
    step_type = normalized["type"]
    column = normalized["column"]
    params = normalized["params"]
    before = df.copy()
    after = df.copy()

    if step_type == "remove_duplicate_rows":
        after = after.drop_duplicates()

    elif step_type == "remove_empty_rows":
        after = after.dropna(how="all")

    elif step_type == "trim_whitespace":
        if column not in after.columns:
            raise ValueError(f'Column "{column}" does not exist.')
        mask = after[column].notna()
        after.loc[mask, column] = after.loc[mask, column].astype(str).str.strip()

    elif step_type == "handle_empty_strings":
        if column not in after.columns:
            raise ValueError(f'Column "{column}" does not exist.')
        after[column] = after[column].replace(r"^\s*$", pd.NA, regex=True)

    elif step_type == "fill_missing":
        if column not in after.columns:
            raise ValueError(f'Column "{column}" does not exist.')

        method = params.get("method", "median")
        missing_mask = after[column].isna()

        if method == "mean":
            value = pd.to_numeric(after[column], errors="coerce").mean()
        elif method == "median":
            value = pd.to_numeric(after[column], errors="coerce").median()
        elif method == "mode":
            modes = after[column].dropna().mode()
            value = modes.iloc[0] if not modes.empty else params.get("value")
        elif method == "constant":
            value = params.get("value")
        else:
            raise ValueError(f"Unsupported fill_missing method: {method}")

        after.loc[missing_mask, column] = value

    elif step_type == "drop_column":
        if column not in after.columns:
            raise ValueError(f'Column "{column}" does not exist.')
        after = after.drop(columns=[column])

    elif step_type == "drop_columns":
        columns = [col for col in normalized["columns"] if col in after.columns]
        after = after.drop(columns=columns)

    elif step_type == "cap_outliers_iqr":
        if column not in after.columns:
            raise ValueError(f'Column "{column}" does not exist.')
        factor = float(params.get("factor", 1.5))
        outliers = _numeric_outlier_summary(after[column], factor=factor)
        lower_bound = params.get("lower_bound", outliers["lower_bound"])
        upper_bound = params.get("upper_bound", outliers["upper_bound"])

        if lower_bound is not None and upper_bound is not None:
            numeric = pd.to_numeric(after[column], errors="coerce")
            after[column] = numeric.clip(lower=lower_bound, upper=upper_bound)

    else:
        raise ValueError(f"Unknown cleaning step type: {step_type}")

    changed_columns = [
        col for col in before.columns.intersection(after.columns)
        if not before[col].equals(after[col])
    ]
    affected_rows = max(0, int(len(before) - len(after)))

    if column and column in before.columns and column in after.columns:
        affected_rows = max(
            affected_rows,
            int((before[column].astype(object) != after[column].astype(object)).fillna(False).sum()),
        )

    if step_type in {"drop_column", "drop_columns"}:
        affected_rows = int(len(before))

    detail = {
        "type": step_type,
        "column": column,
        "params": params,
        "risk": normalized["risk"],
        "before_rows": int(len(before)),
        "after_rows": int(len(after)),
        "affected_rows": affected_rows,
        "columns_removed": [col for col in before.columns if col not in after.columns],
        "columns_changed": changed_columns,
    }

    return after, detail


def preview_cleaning(file_path: str, steps: list[dict]) -> dict:
    before = read_csv_file(file_path)
    after = before.copy()
    step_details = []

    for step in steps:
        after, detail = apply_step(after, step)
        step_details.append(detail)

    return {
        "before": {
            **_dataset_stats(before),
            "sample": _safe_records(before),
        },
        "after": {
            **_dataset_stats(after),
            "sample": _safe_records(after),
        },
        "diff": {
            "rows_removed": int(len(before) - len(after)),
            "columns_removed": [col for col in before.columns if col not in after.columns],
            "columns_changed": [
                col for col in before.columns.intersection(after.columns)
                if not before[col].equals(after[col])
            ],
            "missing_cells_delta": int(after.isna().sum().sum() - before.isna().sum().sum()),
        },
        "steps": steps,
        "step_details": step_details,
    }


def apply_cleaning(file_path: str, steps: list[dict]) -> dict:
    before = read_csv_file(file_path)
    after = before.copy()
    step_details = []

    for step in steps:
        after, detail = apply_step(after, step)
        step_details.append(detail)

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLEANED_DIR / f"{Path(file_path).stem}_cleaned_{uuid4().hex[:8]}.csv"
    after.to_csv(output_path, index=False)
    cleaned_columns = _cleaned_columns(step_details)
    sample_indexes = _affected_indexes(before, after, cleaned_columns)

    return {
        "output_path": str(output_path),
        "before": _dataset_stats(before),
        "after": _dataset_stats(after),
        "rows_removed": int(len(before) - len(after)),
        "columns_removed": [col for col in before.columns if col not in after.columns],
        "columns_changed": [
            col for col in before.columns.intersection(after.columns)
            if not before[col].equals(after[col])
        ],
        "cleaned_columns": cleaned_columns,
        "steps_applied": len(steps),
        "step_details": step_details,
        "before_sample": _safe_records(before, indexes=sample_indexes),
        "after_sample": _safe_records(after, indexes=sample_indexes),
        "sample": _safe_records(after),
    }
