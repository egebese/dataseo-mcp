"""Tool-level DataSEO services built on provider adapters."""

from __future__ import annotations

from typing import Any, Literal
from urllib.parse import quote, urlsplit

from pydantic import ValidationError as PydanticValidationError

from seo_mcp.ai import AISearchService
from seo_mcp.backlinks import (
    get_backlinks,
    get_signature_and_overview,
    load_signature_from_cache,
)
from seo_mcp.captcha import get_captcha_token
from seo_mcp.errors import UpstreamError, ValidationError
from seo_mcp.keywords import get_keyword_difficulty, get_keyword_ideas
from seo_mcp.schemas import (
    AISearchQueriesInput,
    BacklinkOpportunitiesInput,
    BacklinksInput,
    CompareDomainsInput,
    KeywordDifficultyInput,
    KeywordIdeasInput,
    SEOContentBriefInput,
    TrafficInput,
)
from seo_mcp.traffic import check_traffic


def _validate(schema: type, **values: Any) -> Any:
    try:
        return schema(**values)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc


def _backlink_site_url(domain: str) -> str:
    return f"https://ahrefs.com/backlink-checker/?input={domain}&mode=subdomains"


def _source_domain(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    return parsed.netloc.lower().split("@")[-1].split(":", 1)[0]


def get_backlinks_list(domain: str) -> dict[str, Any]:
    """Return backlink overview and top backlink rows."""

    payload = _validate(BacklinksInput, domain=domain)
    signature, valid_until, overview_data = load_signature_from_cache(payload.domain)
    if not signature or not valid_until:
        token = get_captcha_token(_backlink_site_url(payload.domain))
        signature, valid_until, overview_data = get_signature_and_overview(
            token, payload.domain
        )
        if not signature or not valid_until:
            raise UpstreamError(f"Failed to get backlink signature for {payload.domain}.")

    backlinks = get_backlinks(signature, valid_until, payload.domain)
    return {"overview": overview_data, "backlinks": backlinks or []}


def keyword_generator(
    keyword: str,
    country: str = "us",
    search_engine: str = "Google",
) -> list[dict[str, Any]]:
    """Return keyword ideas for a seed keyword."""

    payload = _validate(
        KeywordIdeasInput,
        keyword=keyword,
        country=country,
        search_engine=search_engine,
    )
    site_url = (
        "https://ahrefs.com/keyword-generator/"
        f"?country={payload.country}&input={quote(payload.keyword)}"
    )
    token = get_captcha_token(site_url)
    return (
        get_keyword_ideas(
            token,
            payload.keyword,
            payload.country,
            payload.search_engine,
        )
        or []
    )


def get_traffic(
    domain_or_url: str,
    country: str = "None",
    mode: Literal["subdomains", "exact"] = "subdomains",
) -> dict[str, Any] | None:
    """Return traffic data for a domain or URL."""

    payload = _validate(
        TrafficInput,
        domain_or_url=domain_or_url,
        country=country,
        mode=mode,
    )
    site_url = (
        "https://ahrefs.com/traffic-checker/"
        f"?input={payload.domain_or_url}&mode={payload.mode}"
    )
    token = get_captcha_token(site_url)
    return check_traffic(token, payload.domain_or_url, payload.mode, payload.country)


def keyword_difficulty(keyword: str, country: str = "us") -> dict[str, Any] | None:
    """Return keyword difficulty and SERP data."""

    payload = _validate(KeywordDifficultyInput, keyword=keyword, country=country)
    site_url = (
        "https://ahrefs.com/keyword-difficulty/"
        f"?country={payload.country}&input={quote(payload.keyword)}"
    )
    token = get_captcha_token(site_url)
    return get_keyword_difficulty(token, payload.keyword, payload.country)


def ai_search_queries(
    keyword: str,
    count: int = 10,
    model: str = "openai/gpt-4o-mini",
    language: str = "en",
) -> dict[str, Any]:
    """Return AI-generated SEO search queries."""

    payload = _validate(
        AISearchQueriesInput,
        keyword=keyword,
        count=count,
        model=model,
        language=language,
    )
    return AISearchService().generate_queries(
        payload.keyword,
        count=payload.count,
        model=payload.model,
        language=payload.language,
    )


def domain_overview(domain: str, country: str = "None") -> dict[str, Any]:
    """Return backlink and traffic summary for one domain."""

    domain_payload = _validate(BacklinksInput, domain=domain)
    traffic_payload = _validate(
        TrafficInput,
        domain_or_url=domain_payload.domain,
        country=country,
        mode="subdomains",
    )
    backlinks = get_backlinks_list(domain_payload.domain)
    traffic = get_traffic(
        traffic_payload.domain_or_url,
        country=traffic_payload.country,
        mode=traffic_payload.mode,
    )
    return {
        "domain": domain_payload.domain,
        "backlinks_overview": backlinks.get("overview"),
        "traffic": traffic.get("traffic") if isinstance(traffic, dict) else None,
        "top_countries": traffic.get("top_countries", []) if traffic else [],
        "top_keywords": traffic.get("top_keywords", []) if traffic else [],
    }


def compare_domains(domains: list[str], country: str = "None") -> dict[str, Any]:
    """Compare 2-5 domains using backlink and traffic summaries."""

    payload = _validate(CompareDomainsInput, domains=domains, country=country)
    results = []
    for domain in payload.domains:
        results.append(domain_overview(domain, payload.country))
    return {"country": payload.country, "domains": results}


def backlink_opportunities(domain: str, competitors: list[str]) -> dict[str, Any]:
    """Find top competitor backlink sources not present in the target sample."""

    payload = _validate(
        BacklinkOpportunitiesInput,
        domain=domain,
        competitors=competitors,
    )
    target_backlinks = get_backlinks_list(payload.domain).get("backlinks", [])
    target_sources = {
        _source_domain(item.get("urlFrom", ""))
        for item in target_backlinks
        if isinstance(item, dict)
    }

    opportunities: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for competitor in payload.competitors:
        if competitor == payload.domain:
            continue
        competitor_backlinks = get_backlinks_list(competitor).get("backlinks", [])
        for backlink in competitor_backlinks:
            if not isinstance(backlink, dict):
                continue
            source = _source_domain(backlink.get("urlFrom", ""))
            if not source or source in target_sources or source in seen_sources:
                continue
            seen_sources.add(source)
            opportunities.append(
                {
                    "sourceDomain": source,
                    "competitor": competitor,
                    "sourceUrl": backlink.get("urlFrom", ""),
                    "targetUrl": backlink.get("urlTo", ""),
                    "anchor": backlink.get("anchor", ""),
                    "domainRating": backlink.get("domainRating", 0),
                }
            )

    opportunities.sort(key=lambda item: item.get("domainRating", 0), reverse=True)
    return {
        "domain": payload.domain,
        "competitors": [item for item in payload.competitors if item != payload.domain],
        "opportunities": opportunities,
        "total_opportunities": len(opportunities),
    }


def seo_content_brief(
    keyword: str,
    country: str = "us",
    count: int = 12,
    model: str = "openai/gpt-4o-mini",
    language: str = "en",
) -> dict[str, Any]:
    """Build a compact SEO content brief from SERP data and optional AI queries."""

    payload = _validate(
        SEOContentBriefInput,
        keyword=keyword,
        country=country,
        count=count,
        model=model,
        language=language,
    )
    kd = keyword_difficulty(payload.keyword, payload.country)
    ai_queries = ai_search_queries(
        payload.keyword,
        count=payload.count,
        model=payload.model,
        language=payload.language,
    )
    serp_results = []
    if isinstance(kd, dict):
        serp_results = kd.get("serp", {}).get("results", [])

    return {
        "keyword": payload.keyword,
        "country": payload.country,
        "difficulty": kd.get("difficulty") if isinstance(kd, dict) else None,
        "serp_results": serp_results,
        "search_queries": ai_queries,
        "recommended_angles": [
            item["query"]
            for item in ai_queries.get("queries", [])
            if isinstance(item, dict)
            and item.get("intent") in {"informational", "commercial"}
        ][:8],
    }
