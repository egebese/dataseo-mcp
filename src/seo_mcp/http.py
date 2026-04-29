"""Small HTTP helpers with safe JSON handling."""

from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class JsonResponse:
    """Parsed JSON response metadata."""

    status_code: int
    data: Any


def request_json(
    method: str,
    url: str,
    *,
    timeout: float,
    session: requests.Session | None = None,
    **kwargs: Any,
) -> JsonResponse | None:
    """Perform an HTTP request and return parsed JSON or None on safe failure."""

    client = session or requests
    try:
        response = client.request(method, url, timeout=timeout, **kwargs)
        data = response.json()
    except (requests.RequestException, ValueError, TypeError):
        return None

    return JsonResponse(status_code=response.status_code, data=data)


def post_json(
    url: str,
    *,
    timeout: float,
    session: requests.Session | None = None,
    **kwargs: Any,
) -> JsonResponse | None:
    """POST and parse JSON."""

    return request_json("POST", url, timeout=timeout, session=session, **kwargs)


def get_json(
    url: str,
    *,
    timeout: float,
    session: requests.Session | None = None,
    **kwargs: Any,
) -> JsonResponse | None:
    """GET and parse JSON."""

    return request_json("GET", url, timeout=timeout, session=session, **kwargs)
