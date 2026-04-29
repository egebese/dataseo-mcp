"""DataSEO MCP server entrypoint."""

from typing import Any, Literal

from fastmcp import FastMCP

from seo_mcp import services

mcp = FastMCP("DataSEO MCP")


@mcp.tool()
def get_backlinks_list(domain: str) -> dict[str, Any]:
    """Get backlink overview and top backlinks for a domain."""

    return services.get_backlinks_list(domain)


@mcp.tool()
def keyword_generator(
    keyword: str,
    country: str = "us",
    search_engine: str = "Google",
) -> list[dict[str, Any]]:
    """Get keyword ideas for a seed keyword."""

    return services.keyword_generator(keyword, country, search_engine)


@mcp.tool()
def get_traffic(
    domain_or_url: str,
    country: str = "None",
    mode: Literal["subdomains", "exact"] = "subdomains",
) -> dict[str, Any] | None:
    """Check estimated search traffic for a domain or URL."""

    return services.get_traffic(domain_or_url, country, mode)


@mcp.tool()
def keyword_difficulty(keyword: str, country: str = "us") -> dict[str, Any] | None:
    """Get keyword difficulty and SERP data."""

    return services.keyword_difficulty(keyword, country)


@mcp.tool()
def ai_search_queries(
    keyword: str,
    count: int = 10,
    model: str = "openai/gpt-4o-mini",
    language: str = "en",
) -> dict[str, Any]:
    """Generate AI-powered search queries categorized by intent."""

    return services.ai_search_queries(keyword, count, model, language)


@mcp.tool()
def domain_overview(domain: str, country: str = "None") -> dict[str, Any]:
    """Get backlink and traffic summary for one domain."""

    return services.domain_overview(domain, country)


@mcp.tool()
def compare_domains(domains: list[str], country: str = "None") -> dict[str, Any]:
    """Compare 2-5 domains using backlink and traffic summaries."""

    return services.compare_domains(domains, country)


@mcp.tool()
def backlink_opportunities(domain: str, competitors: list[str]) -> dict[str, Any]:
    """Find competitor backlink sources not present in the target sample."""

    return services.backlink_opportunities(domain, competitors)


@mcp.tool()
def seo_content_brief(
    keyword: str,
    country: str = "us",
    count: int = 12,
    model: str = "openai/gpt-4o-mini",
    language: str = "en",
) -> dict[str, Any]:
    """Build an SEO content brief from SERP data and AI search queries."""

    return services.seo_content_brief(keyword, country, count, model, language)


def main() -> None:
    """Run the MCP server."""

    mcp.run()


if __name__ == "__main__":
    main()
