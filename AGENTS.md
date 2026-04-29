# AGENTS.md

Guidance for Codex and other coding agents working in this repository.

## Product

DataSEO MCP is an educational SEO research MCP server. It exposes Ahrefs-backed
research tools plus optional OpenRouter-powered AI query planning. Users must
comply with third-party terms of service.

## Public Tool Contracts

Preserve these MCP tool names unless a migration is explicitly requested:

| Tool | Purpose |
| --- | --- |
| `get_backlinks_list(domain)` | Backlink overview and top backlinks |
| `keyword_generator(keyword, country?, search_engine?)` | Keyword and question ideas |
| `get_traffic(domain_or_url, country?, mode?)` | Organic traffic estimates |
| `keyword_difficulty(keyword, country?)` | KD and SERP rows |
| `ai_search_queries(keyword, count?, model?, language?)` | AI query ideas by intent |
| `domain_overview(domain, country?)` | One-domain backlink and traffic summary |
| `compare_domains(domains, country?)` | 2-5 domain comparison |
| `backlink_opportunities(domain, competitors)` | Competitor backlink gap sample |
| `seo_content_brief(keyword, country?, count?, model?, language?)` | SERP + AI brief |

Keep existing return-shape compatibility where practical. In particular,
`get_traffic` still returns `costMontlyAvg` and also includes `costMonthlyAvg`.

## Architecture Rules

- Keep `src/seo_mcp/server.py` as a thin FastMCP entrypoint.
- Put tool orchestration in `services.py`.
- Put validation and normalization in `schemas.py` with Pydantic.
- Put provider-specific HTTP logic in `backlinks.py`, `keywords.py`, `traffic.py`,
  `captcha.py`, and `ai.py`.
- Keep cache writes out of the repo root. Use `DATASEO_CACHE_DIR` or
  `~/.cache/dataseo-mcp`.
- Do not log secrets, API keys, CAPTCHA tokens, raw provider responses, or user
  credentials.

## Development Commands

```bash
uv sync
uv run pytest -q
uv run ruff check .
uv run python -m compileall -q src
uv run python -c "from seo_mcp.server import main"
```

Run all checks before calling implementation complete.

## Configuration

At least one CAPTCHA provider is required for Ahrefs-backed tools:

- `CAPSOLVER_API_KEY`
- `ANTICAPTCHA_API_KEY`

Optional AI config:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL`

Runtime tuning:

- `DATASEO_CACHE_DIR`
- `DATASEO_REQUEST_TIMEOUT`
- `DATASEO_MAX_POLLING_ATTEMPTS`
