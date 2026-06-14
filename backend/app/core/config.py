import os
from pathlib import Path


def load_env_file() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    project_dir = backend_dir.parent
    env_paths = [project_dir / ".env", backend_dir / ".env"]

    for env_path in env_paths:
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key:
                os.environ.setdefault(key, value)


def get_agent_config() -> dict:
    load_env_file()

    api_key = os.getenv("AI_AGENT_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("AI_AGENT_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    model = os.getenv("AI_AGENT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
    fallback_model = os.getenv("AI_AGENT_FALLBACK_MODEL", "meta/llama-3.1-8b-instruct")

    return {
        "configured": bool(api_key),
        "base_url": base_url,
        "model": model,
        "fallback_model": fallback_model,
        "max_tokens": min(int(os.getenv("AI_AGENT_MAX_TOKENS", "160")), 220),
        "timeout_seconds": min(float(os.getenv("AI_AGENT_TIMEOUT_SECONDS", "15")), 20),
    }
