from typing import Any

from seo_mcp.ai import AISearchService
from seo_mcp.config import Settings


class FakeMessage:
    def __init__(self, content: str | None) -> None:
        self.content = content


class FakeChoice:
    def __init__(self, content: str | None) -> None:
        self.message = FakeMessage(content)


class FakeCompletionResponse:
    def __init__(self, content: str | None) -> None:
        self.choices = [FakeChoice(content)] if content is not None else []


class FakeCompletions:
    def __init__(self, content: str | None) -> None:
        self.content = content

    def create(self, **kwargs: Any) -> FakeCompletionResponse:
        return FakeCompletionResponse(self.content)


class FakeChat:
    def __init__(self, content: str | None) -> None:
        self.completions = FakeCompletions(content)


class FakeOpenAI:
    content: str | None = None

    def __init__(self, **kwargs: Any) -> None:
        self.chat = FakeChat(self.content)


def settings(api_key: str | None = "key") -> Settings:
    return Settings(
        capsolver_api_key=None,
        anticaptcha_api_key=None,
        openrouter_api_key=api_key,
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_model="openai/gpt-4o-mini",
        request_timeout=1.0,
        max_polling_attempts=1,
        cache_dir=None,
        debug=False,
    )


def test_ai_search_queries_returns_controlled_missing_key_error() -> None:
    result = AISearchService(settings(api_key=None)).generate_queries("seo tools")

    assert result["queries"] == []
    assert "OPENROUTER_API_KEY" in result["error"]


def test_ai_search_queries_handles_malformed_json(monkeypatch) -> None:
    FakeOpenAI.content = "not json"
    monkeypatch.setattr("seo_mcp.ai.OpenAI", FakeOpenAI)

    result = AISearchService(settings()).generate_queries("seo tools")

    assert result["queries"] == []
    assert result["error"] == "Model returned malformed JSON."


def test_ai_search_queries_dedupes_and_normalizes_intents(monkeypatch) -> None:
    FakeOpenAI.content = (
        '{"queries": ['
        '{"query": "best seo tools", "intent": "commercial"},'
        '{"query": "best seo tools", "intent": "commercial"},'
        '{"query": "how seo tools work", "intent": "invalid"}'
        "]}"
    )
    monkeypatch.setattr("seo_mcp.ai.OpenAI", FakeOpenAI)

    result = AISearchService(settings()).generate_queries("seo tools", count=10)

    assert result["total_queries"] == 2
    assert result["queries"][1]["intent"] == "informational"
