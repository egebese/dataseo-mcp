"""AI-assisted SEO research helpers."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from seo_mcp.config import Settings, get_settings
from seo_mcp.errors import ConfigurationError
from seo_mcp.schemas import SUPPORTED_INTENTS

SEARCH_QUERY_PROMPT = """Generate exactly {count} Google search queries for SEO research.

Keyword: {keyword}
Language: {language}

Return only JSON with this shape:
{{"queries":[{{"query":"...", "intent":"commercial"}}]}}

Cover informational, commercial, transactional, and navigational angles when they fit.
Avoid duplicate or near-duplicate queries."""


def _extract_json(content: str) -> dict[str, Any] | None:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _normalize_queries(raw_queries: Any, limit: int) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    if not isinstance(raw_queries, list):
        return normalized

    for item in raw_queries:
        if not isinstance(item, dict):
            continue
        query = " ".join(str(item.get("query") or "").split())
        intent = str(item.get("intent") or "informational").strip().lower()
        if not query:
            continue
        if intent not in SUPPORTED_INTENTS:
            intent = "informational"
        key = query.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"query": query, "intent": intent})
        if len(normalized) >= limit:
            break

    return normalized


class AISearchService:
    """OpenRouter-backed AI query generator."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def generate_queries(
        self,
        keyword: str,
        *,
        count: int = 10,
        model: str | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        """Generate validated search queries, returning controlled errors."""

        model_id = model or self.settings.openrouter_model
        response_data: dict[str, Any] = {
            "keyword": keyword,
            "queries": [],
            "model_used": model_id,
            "total_queries": 0,
        }

        if not self.settings.openrouter_api_key:
            response_data["error"] = (
                "OpenRouter API key not configured. Set OPENROUTER_API_KEY."
            )
            return response_data

        client = OpenAI(
            api_key=self.settings.openrouter_api_key,
            base_url=self.settings.openrouter_base_url,
        )
        prompt = SEARCH_QUERY_PROMPT.format(
            keyword=keyword,
            count=count,
            language=language,
        )

        messages = [
            {
                "role": "system",
                "content": "You are an SEO analyst. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                response_format={"type": "json_object"},
                timeout=self.settings.request_timeout,
            )
        except Exception:
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    timeout=self.settings.request_timeout,
                )
            except Exception as exc:
                response_data["error"] = f"AI provider error: {exc.__class__.__name__}"
                return response_data

        content = response.choices[0].message.content if response.choices else None
        if not content:
            response_data["error"] = "Empty response from model."
            return response_data

        parsed = _extract_json(content)
        if parsed is None:
            response_data["error"] = "Model returned malformed JSON."
            return response_data

        queries = _normalize_queries(parsed.get("queries"), count)
        response_data["queries"] = queries
        response_data["total_queries"] = len(queries)
        if not queries:
            response_data["error"] = "Model returned no usable queries."
        return response_data


def require_ai_config() -> None:
    """Raise when AI config is unavailable for callers that require it."""

    if not get_settings().openrouter_api_key:
        raise ConfigurationError("OPENROUTER_API_KEY is not configured.")
