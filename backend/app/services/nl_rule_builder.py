import re
from difflib import get_close_matches

from app.services.csv_reader import read_csv_file
from app.services.rule_engine import validate_condition


def build_rule_from_text(file_path: str, instruction: str) -> dict:
    df = read_csv_file(file_path)
    columns = list(df.columns)
    column = _find_column(instruction, columns) or columns[0]
    lowered = instruction.lower()
    quoted_column = f'"{column}"'
    severity = "medium"
    condition = f"{quoted_column} IS NOT NULL"
    description = instruction.strip()

    if any(token in lowered for token in ["not null", "không null", "khong null", "không được null", "missing", "rỗng", "rong"]):
        condition = f"{quoted_column} IS NOT NULL"
    elif any(token in lowered for token in ["unique", "duy nhất", "không trùng", "khong trung"]):
        condition = f"{quoted_column} IS NOT NULL"
        description += " Unique checks are tracked as a column-level data quality intent; duplicate detection runs in the quality engine."
    elif any(token in lowered for token in ["positive", "dương", "duong", "> 0", "greater than 0"]):
        condition = f"{quoted_column} > 0"
    elif any(token in lowered for token in ["non-negative", "non negative", "không âm", "khong am", ">= 0"]):
        condition = f"{quoted_column} >= 0"
    elif "between" in lowered or "trong khoảng" in lowered or "trong khoang" in lowered:
        numbers = _numbers(instruction)
        if len(numbers) >= 2:
            low, high = sorted(numbers[:2])
            condition = f"{quoted_column} BETWEEN {low} AND {high}"
    elif any(token in lowered for token in ["less than", "nhỏ hơn", "nho hon", "<"]):
        numbers = _numbers(instruction)
        if numbers:
            condition = f"{quoted_column} < {numbers[0]}"
    elif any(token in lowered for token in ["greater than", "lớn hơn", "lon hon", ">"]):
        numbers = _numbers(instruction)
        if numbers:
            condition = f"{quoted_column} > {numbers[0]}"
    elif any(token in lowered for token in ["contains", "chứa", "chua"]):
        value = _quoted_text(instruction)
        if value:
            escaped_value = value.replace("'", "''")
            condition = f"{quoted_column} LIKE '%{escaped_value}%'"
    elif any(token in lowered for token in ["equals", "equal", "bằng", "bang", "="]):
        value = _quoted_text(instruction)
        numbers = _numbers(instruction)
        if value:
            escaped_value = value.replace("'", "''")
            condition = f"{quoted_column} = '{escaped_value}'"
        elif numbers:
            condition = f"{quoted_column} = {numbers[0]}"

    if any(token in lowered for token in ["critical", "high", "nghiêm trọng", "nghiem trong"]):
        severity = "high"
    elif any(token in lowered for token in ["low", "thấp", "thap"]):
        severity = "low"

    validate_condition(condition)

    return {
        "name": _rule_name(column, instruction),
        "description": description,
        "column": column,
        "condition": condition,
        "severity": severity,
        "is_active": True,
        "generated_by": "natural_language_rule_builder",
    }


def _find_column(text: str, columns: list[str]) -> str | None:
    lowered = text.lower()
    for column in columns:
        if column.lower() in lowered:
            return column

    tokens = re.findall(r"[a-zA-Z0-9_ -]+", lowered)
    candidates = [token.strip() for token in tokens if token.strip()]
    matches = get_close_matches(" ".join(candidates), [column.lower() for column in columns], n=1, cutoff=0.65)
    if matches:
        lookup = {column.lower(): column for column in columns}
        return lookup[matches[0]]

    return None


def _numbers(text: str) -> list[float]:
    values = [float(match) for match in re.findall(r"-?\d+(?:\.\d+)?", text)]
    return [int(value) if value.is_integer() else value for value in values]


def _quoted_text(text: str) -> str | None:
    match = re.search(r"['\"]([^'\"]+)['\"]", text)
    if match:
        return match.group(1)
    return None


def _rule_name(column: str, instruction: str) -> str:
    words = re.findall(r"\w+", instruction)
    suffix = " ".join(words[:5]) if words else "natural language rule"
    return f"{column}: {suffix}"[:120]
