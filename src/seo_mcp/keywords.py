"""Ahrefs free keyword endpoint adapters."""

from typing import Any

import requests

from seo_mcp.config import get_settings
from seo_mcp.http import post_json

AHREFS_KEYWORD_IDEAS_URL = "https://ahrefs.com/v4/stGetFreeKeywordIdeas"
AHREFS_KEYWORD_DIFFICULTY_URL = (
    "https://ahrefs.com/v4/stGetFreeSerpOverviewForKeywordDifficultyChecker"
)


def _coerce_int(value: Any) -> int:
    """Coerce common Ahrefs metric labels into integers."""

    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            cleaned = value.replace(",", "").lower().strip()
            if cleaned.endswith("k"):
                return int(float(cleaned[:-1]) * 1000)
            if cleaned.endswith("m"):
                return int(float(cleaned[:-1]) * 1_000_000)
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0
    return 0


def _map_difficulty_label_to_int(label: str | int | float | None) -> int:
    """Map Ahrefs difficulty labels onto a 0-100 scale."""

    if label is None:
        return 0
    if isinstance(label, (int, float)):
        return _coerce_int(label)

    difficulty_map = {
        "very easy": 5,
        "easy": 15,
        "medium": 40,
        "hard": 70,
        "very hard": 85,
        "super hard": 90,
        "unknown": 0,
    }
    return difficulty_map.get(str(label).lower().strip(), _coerce_int(label))


def _map_volume_label_to_int(label: str | int | float | None) -> int:
    """Map Ahrefs volume labels onto integer estimates."""

    if label is None:
        return 0
    if isinstance(label, (int, float)):
        return _coerce_int(label)

    label_str = str(label).strip()
    if "-" in label_str:
        parts = label_str.split("-", 1)
        return _coerce_int(parts[0])
    return _coerce_int(label_str)


def format_keyword_ideas(keyword_data: Any) -> list[dict[str, Any]]:
    """Format Ahrefs keyword ideas into the existing label/value public shape."""

    if not isinstance(keyword_data, list) or len(keyword_data) < 2:
        return []
    data = keyword_data[1]
    if not isinstance(data, dict):
        return []

    result: list[dict[str, Any]] = []
    for source_key, label in (
        ("allIdeas", "keyword ideas"),
        ("questionIdeas", "question ideas"),
    ):
        ideas = data.get(source_key, {}).get("results", [])
        if not isinstance(ideas, list):
            continue
        for idea in ideas:
            if not isinstance(idea, dict):
                continue
            result.append(
                {
                    "label": label,
                    "value": {
                        "keyword": idea.get("keyword", "No keyword"),
                        "country": idea.get("country", "-"),
                        "difficulty": _map_difficulty_label_to_int(
                            idea.get("difficultyLabel")
                        ),
                        "volume": _map_volume_label_to_int(idea.get("volumeLabel")),
                        "updatedAt": idea.get("updatedAt", "-"),
                    },
                }
            )

    return result


def get_keyword_ideas(
    token: str,
    keyword: str,
    country: str = "us",
    search_engine: str = "Google",
    *,
    session: requests.Session | None = None,
) -> list[dict[str, Any]] | None:
    """Fetch keyword ideas from Ahrefs."""

    if not token:
        return None

    response = post_json(
        AHREFS_KEYWORD_IDEAS_URL,
        json={
            "withQuestionIdeas": True,
            "captcha": token,
            "searchEngine": search_engine,
            "country": country,
            "keyword": ["Some", keyword],
        },
        headers={"Content-Type": "application/json"},
        timeout=get_settings().request_timeout,
        session=session,
    )
    if not response or response.status_code != 200:
        return None

    return format_keyword_ideas(response.data)


def get_keyword_difficulty(
    token: str,
    keyword: str,
    country: str = "us",
    *,
    session: requests.Session | None = None,
) -> dict[str, Any] | None:
    """Get keyword difficulty and SERP information from Ahrefs."""

    if not token:
        return None

    response = post_json(
        AHREFS_KEYWORD_DIFFICULTY_URL,
        json={"captcha": token, "country": country, "keyword": keyword},
        headers={
            "accept": "*/*",
            "content-type": "application/json; charset=utf-8",
            "referer": (
                f"https://ahrefs.com/keyword-difficulty/?country={country}"
                f"&input={keyword}"
            ),
        },
        timeout=get_settings().request_timeout,
        session=session,
    )
    if not response or response.status_code != 200:
        return None

    data = response.data
    if not isinstance(data, list) or len(data) < 2 or data[0] != "Ok":
        return None
    kd_data = data[1]
    if not isinstance(kd_data, dict):
        return None

    result: dict[str, Any] = {
        "difficulty": kd_data.get("difficulty", 0),
        "shortage": kd_data.get("shortage", 0),
        "lastUpdate": kd_data.get("lastUpdate", ""),
        "serp": {"results": []},
    }

    serp_results = kd_data.get("serp", {}).get("results", [])
    if not isinstance(serp_results, list):
        return result

    formatted_results = []
    for item in serp_results:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list) or len(content) < 2 or content[0] != "organic":
            continue
        organic_data = content[1]
        if not isinstance(organic_data, dict):
            continue
        link = organic_data.get("link")
        if not isinstance(link, list) or len(link) < 2 or link[0] != "Some":
            continue
        link_data = link[1]
        if not isinstance(link_data, dict):
            continue

        url_payload = link_data.get("url", [None, {}])
        url = ""
        if isinstance(url_payload, list) and len(url_payload) > 1:
            url_data = url_payload[1]
            if isinstance(url_data, dict):
                url = str(url_data.get("url", ""))

        result_item = {
            "title": link_data.get("title", ""),
            "url": url,
            "position": item.get("pos", 0),
        }

        metrics = link_data.get("metrics")
        if isinstance(metrics, dict):
            result_item.update(
                {
                    "domainRating": metrics.get("domainRating", 0),
                    "urlRating": metrics.get("urlRating", 0),
                    "traffic": metrics.get("traffic", 0),
                    "keywords": metrics.get("keywords", 0),
                    "topKeyword": metrics.get("topKeyword", ""),
                    "topVolume": metrics.get("topVolume", 0),
                }
            )

        formatted_results.append(result_item)

    result["serp"]["results"] = formatted_results
    return result
