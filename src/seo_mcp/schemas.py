"""Validation and normalization schemas for MCP tool inputs."""

import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from seo_mcp.errors import ValidationError

SUPPORTED_SEARCH_ENGINES = {"Google", "Bing", "Yahoo", "Yandex", "Baidu"}
SUPPORTED_INTENTS = {"informational", "commercial", "transactional", "navigational"}
COUNTRY_RE = re.compile(r"^[a-z]{2}$")
LANGUAGE_RE = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$"
)


def normalize_domain(value: str) -> str:
    """Normalize a domain or URL-like value to a bare lowercase domain."""

    raw = str(value or "").strip()
    if not raw:
        raise ValidationError("Domain is required.")

    if "://" in raw:
        parsed = urlsplit(raw)
        raw = parsed.netloc
    else:
        raw = raw.split("/", 1)[0]

    raw = raw.split("@")[-1].split(":", 1)[0].strip(".").lower()
    if not DOMAIN_RE.match(raw):
        raise ValidationError(f"Invalid domain: {value}")
    return raw


def normalize_domain_or_url(value: str) -> str:
    """Normalize domain or URL input while preserving URL paths for exact checks."""

    raw = str(value or "").strip()
    if not raw:
        raise ValidationError("Domain or URL is required.")
    if any(char.isspace() for char in raw):
        raise ValidationError("Domain or URL cannot contain whitespace.")

    if "://" in raw:
        parsed = urlsplit(raw)
        domain = normalize_domain(parsed.netloc)
        path = parsed.path.rstrip("/")
        return f"{domain}{path}" if path else domain

    if "/" in raw:
        domain, path = raw.split("/", 1)
        normalized = normalize_domain(domain)
        path = path.strip().rstrip("/")
        return f"{normalized}/{path}" if path else normalized

    return normalize_domain(raw)


def normalize_country(value: str | None, *, allow_none: bool = False) -> str:
    """Normalize Ahrefs-style country input."""

    if value is None:
        return "None" if allow_none else "us"
    cleaned = str(value).strip()
    if allow_none and cleaned.lower() in {"none", "all", ""}:
        return "None"
    cleaned = cleaned.lower()
    if not COUNTRY_RE.match(cleaned):
        raise ValidationError("Country must be a two-letter country code.")
    return cleaned


def normalize_keyword(value: str) -> str:
    """Normalize a keyword-like input."""

    keyword = " ".join(str(value or "").split())
    if not keyword:
        raise ValidationError("Keyword is required.")
    if len(keyword) > 160:
        raise ValidationError("Keyword must be 160 characters or fewer.")
    return keyword


def normalize_language(value: str) -> str:
    """Normalize output language codes used by AI query generation."""

    language = str(value or "en").strip()
    if not LANGUAGE_RE.match(language):
        raise ValidationError("Language must look like 'en' or 'en-US'.")
    return language


class ToolInput(BaseModel):
    """Strict pydantic base for MCP inputs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BacklinksInput(ToolInput):
    domain: str

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        return normalize_domain(value)


class KeywordIdeasInput(ToolInput):
    keyword: str
    country: str = "us"
    search_engine: str = "Google"

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, value: str) -> str:
        return normalize_keyword(value)

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return normalize_country(value)

    @field_validator("search_engine")
    @classmethod
    def validate_search_engine(cls, value: str) -> str:
        cleaned = str(value or "").strip()
        if cleaned not in SUPPORTED_SEARCH_ENGINES:
            raise ValidationError(
                f"search_engine must be one of {sorted(SUPPORTED_SEARCH_ENGINES)}."
            )
        return cleaned


class TrafficInput(ToolInput):
    domain_or_url: str
    country: str = "None"
    mode: Literal["subdomains", "exact"] = "subdomains"

    @field_validator("domain_or_url")
    @classmethod
    def validate_domain_or_url(cls, value: str) -> str:
        return normalize_domain_or_url(value)

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return normalize_country(value, allow_none=True)


class KeywordDifficultyInput(ToolInput):
    keyword: str
    country: str = "us"

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, value: str) -> str:
        return normalize_keyword(value)

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return normalize_country(value)


class AISearchQueriesInput(ToolInput):
    keyword: str
    count: int = Field(default=10, ge=1, le=50)
    model: str = "openai/gpt-4o-mini"
    language: str = "en"

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, value: str) -> str:
        return normalize_keyword(value)

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        model = str(value or "").strip()
        if not model or len(model) > 120 or any(char.isspace() for char in model):
            raise ValidationError("Model must be a non-empty model id.")
        return model

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        return normalize_language(value)


class CompareDomainsInput(ToolInput):
    domains: list[str] = Field(min_length=2, max_length=5)
    country: str = "None"

    @field_validator("domains")
    @classmethod
    def validate_domains(cls, value: list[str]) -> list[str]:
        normalized = []
        for domain in value:
            clean = normalize_domain(domain)
            if clean not in normalized:
                normalized.append(clean)
        if len(normalized) < 2:
            raise ValidationError("At least two unique domains are required.")
        return normalized

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return normalize_country(value, allow_none=True)


class BacklinkOpportunitiesInput(ToolInput):
    domain: str
    competitors: list[str] = Field(min_length=1, max_length=5)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        return normalize_domain(value)

    @field_validator("competitors")
    @classmethod
    def validate_competitors(cls, value: list[str]) -> list[str]:
        normalized = []
        for domain in value:
            clean = normalize_domain(domain)
            if clean not in normalized:
                normalized.append(clean)
        return normalized


class SEOContentBriefInput(ToolInput):
    keyword: str
    country: str = "us"
    count: int = Field(default=12, ge=1, le=50)
    model: str = "openai/gpt-4o-mini"
    language: str = "en"

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, value: str) -> str:
        return normalize_keyword(value)

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        return normalize_country(value)

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        return AISearchQueriesInput(keyword="x", model=value).model

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        return normalize_language(value)
