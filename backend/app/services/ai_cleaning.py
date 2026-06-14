import json
import os
import re
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import load_env_file
from app.services.cleaner import suggest_cleaning_steps
from app.services.csv_reader import read_csv_file


ALLOWED_TYPES = {
    "remove_duplicate_rows",
    "remove_empty_rows",
    "trim_whitespace",
    "handle_empty_strings",
    "fill_missing",
    "drop_column",
    "drop_columns",
    "cap_outliers_iqr",
    "no_op",
}


def suggest_ai_cleaning_steps(file_path: str) -> dict:
    df = read_csv_file(file_path)
    candidates = _candidate_catalog(file_path)
    payload = _request_llm_cleaning_plan(df, candidates)
    suggestions = _validated_suggestions(payload, candidates, set(df.columns))

    return {
        "generated_by": "llm_cleaning_advisor",
        "model": payload.get("model"),
        "llm_required": True,
        "summary": payload.get("summary", "LLM reviewed the dataset profile and cleaning candidates."),
        "suggestions": suggestions,
    }


def _candidate_catalog(file_path: str) -> list[dict]:
    candidates = suggest_cleaning_steps(file_path)

    if not candidates:
        candidates = [{
            "type": "no_op",
            "column": None,
            "risk": "safe",
            "message": "No deterministic cleaning candidate was found.",
            "affected_rows": 0,
            "params": {},
        }]

    catalog = []
    for index, candidate in enumerate(candidates[:40], start=1):
        catalog.append({
            "candidate_id": f"c{index}",
            **candidate,
        })

    return catalog


def _dataset_context(df) -> dict:
    columns = []
    for column in df.columns[:80]:
        series = df[column]
        top_values = []
        if not str(series.dtype).startswith(("float", "int")):
            top_values = [
                {"value": str(index), "count": int(value)}
                for index, value in series.astype(str).value_counts(dropna=True).head(3).items()
            ]

        columns.append({
            "name": column,
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_rate": float(series.isna().mean()),
            "unique_count": int(series.nunique(dropna=True)),
            "top_values": top_values,
        })

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "schema": columns,
    }


def _request_llm_cleaning_plan(df, candidates: list[dict]) -> dict:
    load_env_file()

    api_key = os.getenv("AI_AGENT_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="LLM cleaning suggestions require AI_AGENT_API_KEY or OPENAI_API_KEY in your .env file.",
        )

    base_url = os.getenv("AI_AGENT_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    model = os.getenv("AI_CLEANING_MODEL") or os.getenv("AI_AGENT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
    fallback_model = os.getenv("AI_CLEANING_FALLBACK_MODEL") or os.getenv("AI_AGENT_FALLBACK_MODEL", "meta/llama-3.1-8b-instruct")
    max_tokens = min(int(os.getenv("AI_CLEANING_MAX_TOKENS", "900")), 1200)
    timeout_seconds = min(float(os.getenv("AI_CLEANING_TIMEOUT_SECONDS", os.getenv("AI_AGENT_TIMEOUT_SECONDS", "20"))), 30)
    reasoning_effort = os.getenv("AI_AGENT_REASONING_EFFORT")
    endpoint = base_url.rstrip("/") + "/chat/completions"

    prompt = (
        "Return JSON only. You are a senior data quality cleaning advisor. "
        "You must choose cleaning recommendations only from the provided candidate_id list. "
        "Do not invent columns or cleaning actions. Prefer conservative, reversible actions. "
        "For medium/high risk actions, mark review_required true and explain the business risk. "
        "Return this schema: "
        '{"summary":"...","suggestions":[{"candidate_id":"c1","confidence":0.0,"why":"...","review_required":true,"priority":1}]}.\n\n'
        f"Dataset context:\n{json.dumps(_dataset_context(df), ensure_ascii=False)}\n\n"
        f"Allowed candidates:\n{json.dumps(candidates, ensure_ascii=False)}"
    )

    errors = []
    for candidate_model in _configured_models(model, fallback_model):
        try:
            content = _chat_completion(
                endpoint=endpoint,
                api_key=api_key,
                model=candidate_model,
                prompt=prompt,
                max_tokens=max_tokens,
                timeout_seconds=timeout_seconds,
                reasoning_effort=reasoning_effort,
            )
            parsed = _parse_json_content(content)
            parsed["model"] = candidate_model
            return parsed
        except Exception as exc:
            errors.append(str(exc))

    raise HTTPException(status_code=502, detail=f"LLM cleaning suggestion failed: {' | '.join(errors)}")


def _configured_models(model: str, fallback_model: str) -> list[str]:
    return list(dict.fromkeys(item for item in [model, fallback_model] if item))


def _chat_completion(
    *,
    endpoint: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout_seconds: float,
    reasoning_effort: str | None,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You produce strict JSON for a guarded data-cleaning recommendation system.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "stream": False,
    }

    if reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort

    try:
        response = httpx.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=httpx.Timeout(timeout_seconds, connect=10),
        )
    except httpx.ReadTimeout as exc:
        raise RuntimeError(f"{model} read timeout after {timeout_seconds:.0f}s") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"{model} request timeout after {timeout_seconds:.0f}s") from exc

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"{model} HTTP {exc.response.status_code}: {exc.response.text[:500]}") from exc

    return response.json()["choices"][0]["message"]["content"]


def _parse_json_content(content: str) -> dict:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _validated_suggestions(payload: dict, candidates: list[dict], columns: set[str]) -> list[dict]:
    candidate_by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    raw_suggestions = payload.get("suggestions")

    if not isinstance(raw_suggestions, list):
        raise HTTPException(status_code=502, detail="LLM cleaning response did not include a suggestions list.")

    validated = []
    used_ids = set()

    for raw in raw_suggestions:
        if not isinstance(raw, dict):
            continue

        candidate_id = raw.get("candidate_id")
        candidate = candidate_by_id.get(candidate_id)
        if not candidate or candidate_id in used_ids:
            continue

        step_type = candidate.get("type")
        column = candidate.get("column")
        if step_type not in ALLOWED_TYPES:
            continue
        if column and column not in columns:
            continue

        confidence = _bounded_float(raw.get("confidence"), default=0.75)
        why = str(raw.get("why") or candidate.get("message") or "LLM recommended this guarded candidate.")
        review_required = bool(raw.get("review_required", candidate.get("risk") != "safe"))
        priority = int(raw.get("priority") or len(validated) + 1)

        validated.append({
            **{key: value for key, value in candidate.items() if key != "candidate_id"},
            "candidate_id": candidate_id,
            "confidence": confidence,
            "why": why[:800],
            "review_required": review_required,
            "priority": priority,
            "suggested_by": "llm",
        })
        used_ids.add(candidate_id)

    if not validated:
        raise HTTPException(status_code=502, detail="LLM did not select any valid guarded cleaning candidate.")

    return sorted(validated, key=lambda item: item.get("priority", 999))


def _bounded_float(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default

    return round(max(0.0, min(number, 1.0)), 2)
