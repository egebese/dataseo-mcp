import pytest
from pydantic import ValidationError as PydanticValidationError

from seo_mcp.errors import ValidationError
from seo_mcp.schemas import (
    AISearchQueriesInput,
    BacklinksInput,
    CompareDomainsInput,
    TrafficInput,
    normalize_domain,
    normalize_domain_or_url,
)


def test_normalize_domain_accepts_url() -> None:
    assert normalize_domain("https://Example.COM/path?q=1") == "example.com"


def test_normalize_domain_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        normalize_domain("not-a-domain")


def test_normalize_domain_or_url_preserves_path_without_scheme() -> None:
    assert normalize_domain_or_url("Example.com/blog/post/") == "example.com/blog/post"


def test_ai_search_count_is_bounded() -> None:
    with pytest.raises(PydanticValidationError):
        AISearchQueriesInput(keyword="seo tools", count=51)


def test_compare_domains_dedupes_and_requires_two_unique_domains() -> None:
    with pytest.raises(ValidationError):
        CompareDomainsInput(domains=["example.com", "https://example.com"])


def test_schemas_normalize_supported_inputs() -> None:
    assert BacklinksInput(domain="https://SUPARANK.io/pricing").domain == "suparank.io"
    traffic = TrafficInput(domain_or_url="egebese.com/about", country="all", mode="exact")
    assert traffic.domain_or_url == "egebese.com/about"
    assert traffic.country == "None"
