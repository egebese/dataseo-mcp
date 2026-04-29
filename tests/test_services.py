from typing import Any

from seo_mcp import services


def test_get_backlinks_list_uses_cache_without_captcha(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "load_signature_from_cache",
        lambda domain: ("sig", "2099-01-01T00:00:00Z", {"domainRating": 10}),
    )
    monkeypatch.setattr(
        services,
        "get_backlinks",
        lambda signature, valid_until, domain: [{"urlFrom": "https://source.com"}],
    )

    result = services.get_backlinks_list("https://example.com/path")

    assert result["overview"] == {"domainRating": 10}
    assert result["backlinks"][0]["urlFrom"] == "https://source.com"


def test_domain_overview_combines_backlink_and_traffic(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "get_backlinks_list",
        lambda domain: {"overview": {"refDomains": 5}, "backlinks": []},
    )
    monkeypatch.setattr(
        services,
        "get_traffic",
        lambda domain, country="None", mode="subdomains": {
            "traffic": {"trafficMonthlyAvg": 100},
            "top_countries": [{"country": "us"}],
            "top_keywords": [{"keyword": "seo"}],
        },
    )

    result = services.domain_overview("example.com")

    assert result["domain"] == "example.com"
    assert result["backlinks_overview"] == {"refDomains": 5}
    assert result["traffic"] == {"trafficMonthlyAvg": 100}


def test_backlink_opportunities_excludes_existing_target_sources(monkeypatch) -> None:
    def fake_backlinks(domain: str) -> dict[str, Any]:
        if domain == "target.com":
            return {
                "overview": {},
                "backlinks": [{"urlFrom": "https://shared.com/a", "domainRating": 80}],
            }
        return {
            "overview": {},
            "backlinks": [
                {"urlFrom": "https://shared.com/b", "domainRating": 70},
                {
                    "urlFrom": "https://new-source.com/post",
                    "urlTo": "https://competitor.com",
                    "anchor": "competitor",
                    "domainRating": 60,
                },
            ],
        }

    monkeypatch.setattr(services, "get_backlinks_list", fake_backlinks)

    result = services.backlink_opportunities("target.com", ["competitor.com"])

    assert result["total_opportunities"] == 1
    assert result["opportunities"][0]["sourceDomain"] == "new-source.com"


def test_seo_content_brief_includes_ai_angles(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "keyword_difficulty",
        lambda keyword, country="us": {
            "difficulty": 20,
            "serp": {"results": [{"title": "Result"}]},
        },
    )
    monkeypatch.setattr(
        services,
        "ai_search_queries",
        lambda keyword, count=12, model="openai/gpt-4o-mini", language="en": {
            "queries": [{"query": "best seo tools", "intent": "commercial"}],
            "total_queries": 1,
        },
    )

    result = services.seo_content_brief("seo tools")

    assert result["difficulty"] == 20
    assert result["recommended_angles"] == ["best seo tools"]
