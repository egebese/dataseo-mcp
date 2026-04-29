# CLAUDE.md

This repository contains DataSEO MCP, an educational SEO research server for MCP
clients.

## Use

Run locally:

```bash
uv sync
uv run dataseo-mcp
```

The legacy command remains available:

```bash
uv run seo-mcp
```

## Tools

- `get_backlinks_list(domain)`: backlink overview and top backlink rows.
- `keyword_generator(keyword, country="us", search_engine="Google")`: keyword
  and question ideas.
- `get_traffic(domain_or_url, country="None", mode="subdomains")`: traffic
  estimates and top SEO data.
- `keyword_difficulty(keyword, country="us")`: KD and organic SERP rows.
- `ai_search_queries(keyword, count=10, model="openai/gpt-4o-mini", language="en")`:
  AI search queries by intent.
- `domain_overview(domain, country="None")`: backlink + traffic summary.
- `compare_domains(domains, country="None")`: compare 2-5 domains.
- `backlink_opportunities(domain, competitors)`: competitor source gap sample.
- `seo_content_brief(keyword, country="us", count=12, model, language)`: SERP
  data plus AI-assisted angles.

## Environment

At least one CAPTCHA key is required for Ahrefs-backed tools:

```bash
export CAPSOLVER_API_KEY="..."
export ANTICAPTCHA_API_KEY="..."
```

AI tools use OpenRouter when configured:

```bash
export OPENROUTER_API_KEY="..."
export OPENROUTER_MODEL="openai/gpt-4o-mini"
```

Cache and timeout controls:

```bash
export DATASEO_CACHE_DIR="$HOME/.cache/dataseo-mcp"
export DATASEO_REQUEST_TIMEOUT="30"
export DATASEO_MAX_POLLING_ATTEMPTS="120"
```

## Development Notes

- Keep `server.py` thin and preserve public tool names.
- Validate MCP inputs through Pydantic schemas.
- Mock all external HTTP boundaries in tests.
- Do not write signature cache files into the repo root.
- Do not log secrets, CAPTCHA tokens, or raw provider responses.

## Checks

```bash
uv run pytest -q
uv run ruff check .
uv run python -m compileall -q src
uv run python -c "from seo_mcp.server import main"
```
