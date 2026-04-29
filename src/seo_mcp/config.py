"""Runtime configuration for DataSEO MCP."""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"


@dataclass(frozen=True)
class Settings:
    """Environment-backed settings used by providers and tools."""

    capsolver_api_key: str | None
    anticaptcha_api_key: str | None
    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_model: str
    request_timeout: float
    max_polling_attempts: int
    cache_dir: Path
    debug: bool


def _bool_from_env(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _float_from_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _int_from_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def get_settings() -> Settings:
    """Read settings from environment variables on demand."""

    cache_dir = Path(
        os.environ.get("DATASEO_CACHE_DIR", Path.home() / ".cache" / "dataseo-mcp")
    ).expanduser()

    return Settings(
        capsolver_api_key=os.environ.get("CAPSOLVER_API_KEY") or None,
        anticaptcha_api_key=os.environ.get("ANTICAPTCHA_API_KEY") or None,
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY") or None,
        openrouter_base_url=os.environ.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        openrouter_model=os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
        request_timeout=max(_float_from_env("DATASEO_REQUEST_TIMEOUT", 30.0), 1.0),
        max_polling_attempts=max(_int_from_env("DATASEO_MAX_POLLING_ATTEMPTS", 120), 1),
        cache_dir=cache_dir,
        debug=_bool_from_env(os.environ.get("DEBUG")),
    )
