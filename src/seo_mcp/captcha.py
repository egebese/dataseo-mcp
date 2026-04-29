"""CAPTCHA provider orchestration for DataSEO MCP."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

from seo_mcp.config import Settings, get_settings
from seo_mcp.errors import CaptchaConfigurationError, CaptchaSolvingError
from seo_mcp.http import post_json

TURNSTILE_SITE_KEY = "0x4AAAAAAAAzi9ITzSN9xKMi"


class CaptchaClient:
    """Solve Turnstile challenges with configured providers."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings or get_settings()
        self.session = session
        self.sleep = sleep

    def solve(self, site_url: str) -> str:
        """Return a CAPTCHA token using CapSolver first, then Anti-Captcha."""

        if not self.settings.capsolver_api_key and not self.settings.anticaptcha_api_key:
            raise CaptchaConfigurationError(
                "No CAPTCHA provider configured. Set CAPSOLVER_API_KEY or "
                "ANTICAPTCHA_API_KEY."
            )

        if self.settings.capsolver_api_key:
            token = self._solve_capsolver(site_url)
            if token:
                return token

        if self.settings.anticaptcha_api_key:
            token = self._solve_anticaptcha(site_url)
            if token:
                return token

        raise CaptchaSolvingError("Failed to solve CAPTCHA with available providers.")

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        response = post_json(
            url,
            json=payload,
            timeout=self.settings.request_timeout,
            session=self.session,
        )
        if (
            not response
            or response.status_code != 200
            or not isinstance(response.data, dict)
        ):
            return None
        return response.data

    def _solve_capsolver(self, site_url: str) -> str | None:
        api_key = self.settings.capsolver_api_key
        if not api_key:
            return None

        response = self._post(
            "https://api.capsolver.com/createTask",
            {
                "clientKey": api_key,
                "task": {
                    "type": "AntiTurnstileTaskProxyLess",
                    "websiteKey": TURNSTILE_SITE_KEY,
                    "websiteURL": site_url,
                    "metadata": {"action": ""},
                },
            },
        )
        task_id = response.get("taskId") if response else None
        if not task_id:
            return None

        for _ in range(self.settings.max_polling_attempts):
            self.sleep(1)
            response = self._post(
                "https://api.capsolver.com/getTaskResult",
                {"clientKey": api_key, "taskId": task_id},
            )
            if not response:
                return None
            if response.get("errorId"):
                return None
            if response.get("status") == "ready":
                token = response.get("solution", {}).get("token")
                return token if isinstance(token, str) and token else None
            if response.get("status") == "failed":
                return None

        return None

    def _solve_anticaptcha(self, site_url: str) -> str | None:
        api_key = self.settings.anticaptcha_api_key
        if not api_key:
            return None

        response = self._post(
            "https://api.anti-captcha.com/createTask",
            {
                "clientKey": api_key,
                "task": {
                    "type": "TurnstileTaskProxyless",
                    "websiteURL": site_url,
                    "websiteKey": TURNSTILE_SITE_KEY,
                },
            },
        )
        if not response or response.get("errorId", 0) != 0:
            return None
        task_id = response.get("taskId")
        if not task_id:
            return None

        for _ in range(self.settings.max_polling_attempts):
            self.sleep(1)
            response = self._post(
                "https://api.anti-captcha.com/getTaskResult",
                {"clientKey": api_key, "taskId": task_id},
            )
            if not response or response.get("errorId", 0) != 0:
                return None
            if response.get("status") == "ready":
                token = response.get("solution", {}).get("token")
                return token if isinstance(token, str) and token else None
            if response.get("status") == "failed":
                return None

        return None


def get_captcha_token(site_url: str) -> str:
    """Compatibility helper used by tool handlers."""

    return CaptchaClient().solve(site_url)
