from typing import Any

import pytest
import requests

from seo_mcp.captcha import CaptchaClient
from seo_mcp.config import Settings
from seo_mcp.errors import CaptchaConfigurationError, CaptchaSolvingError


class FakeResponse:
    def __init__(self, data: Any, status_code: int = 200) -> None:
        self.data = data
        self.status_code = status_code

    def json(self) -> Any:
        return self.data


class FakeSession:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(url)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def settings(**overrides: Any) -> Settings:
    defaults = {
        "capsolver_api_key": None,
        "anticaptcha_api_key": None,
        "openrouter_api_key": None,
        "openrouter_base_url": "https://openrouter.ai/api/v1",
        "openrouter_model": "openai/gpt-4o-mini",
        "request_timeout": 1.0,
        "max_polling_attempts": 2,
        "cache_dir": None,
        "debug": False,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_captcha_requires_a_provider() -> None:
    client = CaptchaClient(settings(), sleep=lambda _: None)

    with pytest.raises(CaptchaConfigurationError):
        client.solve("https://ahrefs.com")


def test_captcha_falls_back_to_anticaptcha_after_capsolver_network_error() -> None:
    fake_session = FakeSession(
        [
            requests.RequestException("down"),
            FakeResponse({"taskId": 7}),
            FakeResponse({"status": "ready", "solution": {"token": "anti-token"}}),
        ]
    )
    client = CaptchaClient(
        settings(capsolver_api_key="cap", anticaptcha_api_key="anti"),
        session=fake_session,
        sleep=lambda _: None,
    )

    assert client.solve("https://ahrefs.com") == "anti-token"


def test_captcha_polling_is_bounded() -> None:
    fake_session = FakeSession(
        [
            FakeResponse({"taskId": 1}),
            FakeResponse({"status": "processing"}),
            FakeResponse({"status": "processing"}),
        ]
    )
    client = CaptchaClient(
        settings(capsolver_api_key="cap", max_polling_attempts=2),
        session=fake_session,
        sleep=lambda _: None,
    )

    with pytest.raises(CaptchaSolvingError):
        client.solve("https://ahrefs.com")
    assert len(fake_session.calls) == 3
