"""Ahrefs free backlink endpoint adapter."""

from typing import Any

import requests

from seo_mcp.cache import SignatureCache, get_signature_cache
from seo_mcp.config import get_settings
from seo_mcp.http import post_json

AHREFS_BACKLINKS_OVERVIEW_URL = "https://ahrefs.com/v4/stGetFreeBacklinksOverview"
AHREFS_BACKLINKS_LIST_URL = "https://ahrefs.com/v4/stGetFreeBacklinksList"


def save_signature_to_cache(
    signature: str,
    valid_until: str,
    overview_data: dict[str, Any],
    domain: str,
) -> bool:
    """Compatibility wrapper for saving signed backlink input."""

    return get_signature_cache().save(domain, signature, valid_until, overview_data)


def load_signature_from_cache(
    domain: str,
) -> tuple[str | None, str | None, dict[str, Any] | None]:
    """Compatibility wrapper for loading signed backlink input."""

    record = get_signature_cache().load(domain)
    if not record:
        return None, None, None
    return record.signature, record.valid_until, record.overview_data


def get_signature_and_overview(
    token: str,
    domain: str,
    *,
    cache: SignatureCache | None = None,
    session: requests.Session | None = None,
) -> tuple[str | None, str | None, dict[str, Any] | None]:
    """Get signed backlink-list input and overview data from Ahrefs."""

    response = post_json(
        AHREFS_BACKLINKS_OVERVIEW_URL,
        json={"captcha": token, "mode": "subdomains", "url": domain},
        headers={"Content-Type": "application/json"},
        timeout=get_settings().request_timeout,
        session=session,
    )
    if not response or response.status_code != 200:
        return None, None, None

    data = response.data
    if not isinstance(data, list) or len(data) < 2 or data[0] != "Ok":
        return None, None, None

    signed_payload = data[1]
    if not isinstance(signed_payload, dict):
        return None, None, None

    try:
        signed_input = signed_payload["signedInput"]
        signature = signed_input["signature"]
        valid_until = signed_input["input"]["validUntil"]
    except (KeyError, TypeError):
        return None, None, None

    overview_data = signed_payload.get("data")
    if not isinstance(signature, str) or not isinstance(valid_until, str):
        return None, None, None
    if overview_data is not None and not isinstance(overview_data, dict):
        overview_data = None

    (cache or get_signature_cache()).save(domain, signature, valid_until, overview_data)
    return signature, valid_until, overview_data


def format_backlinks(
    backlinks_data: Any,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """Format Ahrefs backlink response into a stable public shape."""

    if not isinstance(backlinks_data, list) or len(backlinks_data) < 2:
        return []
    payload = backlinks_data[1]
    if not isinstance(payload, dict):
        return []

    # New v4 shape: rows live directly under payload["backlinks"]. Fall back to
    # the older topBacklinks.backlinks nesting so cached/old responses still parse.
    backlinks = payload.get("backlinks")
    if not isinstance(backlinks, list):
        backlinks = payload.get("topBacklinks", {}).get("backlinks", [])
    if not isinstance(backlinks, list):
        return []

    formatted = []
    for backlink in backlinks:
        if not isinstance(backlink, dict):
            continue
        formatted.append(
            {
                "anchor": backlink.get("anchor", ""),
                "domainRating": backlink.get("domainRating", 0),
                "title": backlink.get("title", ""),
                "urlFrom": backlink.get("urlFrom", ""),
                "urlTo": backlink.get("urlTo", ""),
                "edu": backlink.get("edu", False),
                "gov": backlink.get("gov", False),
            }
        )
    return formatted


def get_backlinks(
    signature: str,
    valid_until: str,
    domain: str,
    *,
    session: requests.Session | None = None,
) -> list[dict[str, Any]] | None:
    """Retrieve top backlinks using a signed Ahrefs input."""

    if not signature or not valid_until:
        return None

    response = post_json(
        AHREFS_BACKLINKS_LIST_URL,
        json={
            "reportType": ["TopBacklinks"],
            "signedInput": {
                "signature": signature,
                "input": {
                    "validUntil": valid_until,
                    "mode": "subdomains",
                    "url": f"{domain}/",
                },
            },
        },
        headers={"Content-Type": "application/json"},
        timeout=get_settings().request_timeout,
        session=session,
    )
    if not response or response.status_code != 200:
        return None

    return format_backlinks(response.data, domain)


def get_backlinks_overview(
    token: str,
    domain: str,
    *,
    session: requests.Session | None = None,
) -> dict[str, Any] | None:
    """Retrieve backlink overview data without writing debug output."""

    _, _, overview = get_signature_and_overview(token, domain, session=session)
    return overview
