from seo_mcp.backlinks import format_backlinks
from seo_mcp.keywords import (
    _map_difficulty_label_to_int,
    _map_volume_label_to_int,
    format_keyword_ideas,
)


def test_volume_label_enum_tokens() -> None:
    assert _map_volume_label_to_int("MoreThanOneThousand") == 1000
    assert _map_volume_label_to_int("MoreThanTenThousand") == 10000
    assert _map_volume_label_to_int("Zero") == 0
    # Older numeric-range labels still map to the lower bound.
    assert _map_volume_label_to_int("1K-10K") == 1000


def test_difficulty_label_words() -> None:
    assert _map_difficulty_label_to_int("Hard") == 70
    assert _map_difficulty_label_to_int("Very Easy") == 5


def test_format_keyword_ideas_v4_shape() -> None:
    # Envelope + nested allIdeas/questionIdeas.results, enum labels (observed live).
    data = [
        "Ok",
        {
            "allIdeas": {
                "results": [
                    {
                        "keyword": "ai seo tools",
                        "country": "us",
                        "difficultyLabel": "Hard",
                        "volumeLabel": "MoreThanOneThousand",
                        "updatedAt": "2026-07-06T08:31:15Z",
                    }
                ]
            },
            "questionIdeas": {"results": []},
        },
    ]
    ideas = format_keyword_ideas(data)
    assert len(ideas) == 1
    value = ideas[0]["value"]
    assert value["keyword"] == "ai seo tools"
    assert value["difficulty"] == 70
    assert value["volume"] == 1000


def test_format_backlinks_v4_shape() -> None:
    # New v4: rows live directly under payload["backlinks"] (not topBacklinks.backlinks).
    data = [
        "TopBacklinks",
        {
            "backlinks": [
                {
                    "anchor": "Ahrefs",
                    "domainRating": 71,
                    "title": "The 20 best SEO tools",
                    "urlFrom": "https://morningscore.io/best-seo-tools/",
                    "urlTo": "https://ahrefs.com/",
                }
            ]
        },
    ]
    rows = format_backlinks(data)
    assert len(rows) == 1
    assert rows[0]["urlFrom"] == "https://morningscore.io/best-seo-tools/"
    assert rows[0]["domainRating"] == 71
