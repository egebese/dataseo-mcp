"""Ahrefs free traffic endpoint adapter."""

import json
from typing import Any, Literal

import requests

from seo_mcp.config import get_settings
from seo_mcp.http import get_json

AHREFS_TRAFFIC_OVERVIEW_URL = "https://ahrefs.com/v4/stGetFreeTrafficOverview"


def check_traffic(
    token: str,
    domain_or_url: str,
    mode: Literal["subdomains", "exact"] = "subdomains",
    country: str = "None",
    *,
    session: requests.Session | None = None,
) -> dict[str, Any] | None:
    """Check estimated search traffic for a domain or URL."""

    if not token:
        return None

    response = get_json(
        AHREFS_TRAFFIC_OVERVIEW_URL,
        params={
            "input": json.dumps(
                {
                    "captcha": token,
                    # Ahrefs requires a valid country + protocol="https"
                    # (rejects "None"/"Both").
                    "country": country if country and country != "None" else "us",
                    "protocol": "https",
                    "mode": mode,
                    "url": domain_or_url,
                }
            )
        },
        headers={
            "accept": "*/*",
            "content-type": "application/json",
            "referer": (
                f"https://ahrefs.com/traffic-checker/?input={domain_or_url}"
                f"&mode={mode}"
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
    traffic_data = data[1]
    if not isinstance(traffic_data, dict):
        return None

    traffic_summary = traffic_data.get("traffic", {})
    if not isinstance(traffic_summary, dict):
        traffic_summary = {}

    cost_avg = traffic_summary.get("costMontlyAvg", 0)
    result = {
        "traffic_history": traffic_data.get("traffic_history", []),
        "traffic": {
            "trafficMonthlyAvg": traffic_summary.get("trafficMonthlyAvg", 0),
            "costMontlyAvg": cost_avg,
            "costMonthlyAvg": cost_avg,
        },
        "top_pages": traffic_data.get("top_pages", []),
        "top_countries": traffic_data.get("top_countries", []),
        "top_keywords": traffic_data.get("top_keywords", []),
    }

    return result
