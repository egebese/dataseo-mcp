# DataSEO MCP

DataSEO MCP is a Model Context Protocol server for practical SEO research in AI
assistants. It combines Ahrefs free SEO data, CAPTCHA-provider fallback, and
optional OpenRouter-powered query planning behind a small set of MCP tools.

> [!CAUTION]
> This project is for educational and research purposes only. It interacts with
> third-party services including Ahrefs, CapSolver, Anti-Captcha, and OpenRouter.
> Users are responsible for complying with all applicable terms of service.

## Features

| Tool | Purpose | Example prompt |
| --- | --- | --- |
| `get_backlinks_list` | Backlink overview and top backlink rows | "Show backlinks for suparank.io" |
| `keyword_generator` | Keyword and question ideas | "Find SaaS SEO keywords for onboarding" |
| `get_traffic` | Organic traffic estimates | "Estimate traffic for ege.md" |
| `keyword_difficulty` | KD and SERP snapshot | "Check difficulty for AI SEO tools" |
| `ai_search_queries` | AI query ideas by search intent | "Generate AI search queries for SaaS SEO" |
| `domain_overview` | One-domain backlink + traffic summary | "Summarize suparank.io" |
| `compare_domains` | Compare 2-5 domains | "Compare suparank.io and ahrefs.com" |
| `backlink_opportunities` | Competitor backlink source gaps | "Find backlink gaps for my domain" |
| `seo_content_brief` | SERP + AI-assisted content brief | "Create a content brief for AI SEO audit" |

DataSEO MCP is maintained by [Ege Bese](https://ege.md). For AI SEO and
rank-tracking workflows, see [Suparank](https://suparank.io).

## Installation

```bash
uvx --python 3.10 dataseo-mcp
```

For local development:

```bash
git clone https://github.com/egebese/dataseo-mcp.git
cd dataseo-mcp
uv sync
uv run dataseo-mcp
```

The legacy `seo-mcp` command is still exposed as a compatibility alias.

## Configuration

At least one CAPTCHA provider is required for Ahrefs-backed tools:

```bash
export CAPSOLVER_API_KEY="your-capsolver-key"
# or
export ANTICAPTCHA_API_KEY="your-anticaptcha-key"
```

If both are configured, CapSolver is tried first and Anti-Captcha is used as
fallback. AI tools are optional:

```bash
export OPENROUTER_API_KEY="your-openrouter-key"
export OPENROUTER_MODEL="openai/gpt-4o-mini"  # optional
```

Useful runtime overrides:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATASEO_CACHE_DIR` | `~/.cache/dataseo-mcp` | Signature cache location |
| `DATASEO_REQUEST_TIMEOUT` | `30` | HTTP timeout in seconds |
| `DATASEO_MAX_POLLING_ATTEMPTS` | `120` | CAPTCHA polling cap |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenAI-compatible AI endpoint |

## MCP Setup

Claude Desktop / Cursor-style config:

```json
{
  "mcpServers": {
    "dataseo": {
      "command": "uvx",
      "args": ["--python", "3.10", "dataseo-mcp"],
      "env": {
        "CAPSOLVER_API_KEY": "YOUR_CAPSOLVER_KEY",
        "ANTICAPTCHA_API_KEY": "YOUR_ANTICAPTCHA_KEY",
        "OPENROUTER_API_KEY": "YOUR_OPENROUTER_KEY"
      }
    }
  }
}
```

Claude Code:

```bash
claude mcp add dataseo --scope user -- uvx --python 3.10 dataseo-mcp
```

VS Code MCP config:

```json
{
  "servers": {
    "dataseo": {
      "command": "uvx",
      "args": ["--python", "3.10", "dataseo-mcp"],
      "env": {
        "CAPSOLVER_API_KEY": "YOUR_CAPSOLVER_KEY"
      }
    }
  }
}
```

Only one CAPTCHA provider key is required. Add `OPENROUTER_API_KEY` only when
you want AI-assisted query generation or content briefs.

## API Reference

### `get_backlinks_list(domain)`

Returns:

```json
{
  "overview": {
    "domainRating": 76,
    "backlinks": 1500,
    "refDomains": 300
  },
  "backlinks": [
    {
      "anchor": "DataSEO MCP",
      "domainRating": 76,
      "title": "Example page",
      "urlFrom": "https://source.example/page",
      "urlTo": "https://example.com/page",
      "edu": false,
      "gov": false
    }
  ]
}
```

### `keyword_generator(keyword, country="us", search_engine="Google")`

Returns keyword and question ideas in the existing `label` / `value` shape.

### `get_traffic(domain_or_url, country="None", mode="subdomains")`

Returns traffic history, traffic summary, top pages, countries, and keywords.
The legacy `costMontlyAvg` field is preserved and `costMonthlyAvg` is also
included.

### `keyword_difficulty(keyword, country="us")`

Returns a keyword difficulty score and organic SERP rows with available metrics.

### `ai_search_queries(keyword, count=10, model="openai/gpt-4o-mini", language="en")`

Returns deduplicated AI-generated queries:

```json
{
  "keyword": "ai seo audit",
  "queries": [
    {"query": "what is an AI SEO audit", "intent": "informational"},
    {"query": "best AI SEO audit tools", "intent": "commercial"}
  ],
  "model_used": "openai/gpt-4o-mini",
  "total_queries": 2
}
```

`count` is validated from 1 to 50. Valid intents are `informational`,
`commercial`, `transactional`, and `navigational`.

### Additional Tools

- `domain_overview(domain, country="None")`: backlink overview plus traffic
  summary for one domain.
- `compare_domains(domains, country="None")`: compares 2-5 unique domains.
- `backlink_opportunities(domain, competitors)`: lists competitor backlink
  sources not present in the target sample.
- `seo_content_brief(keyword, country="us", count=12, model, language)`: combines
  keyword difficulty, SERP rows, AI search queries, and recommended content
  angles.

## Architecture

`server.py` is intentionally thin. The implementation is split into:

- `services.py`: MCP tool orchestration and public return shapes.
- `schemas.py`: Pydantic validation and normalization.
- `captcha.py`: CapSolver / Anti-Captcha fallback with bounded polling.
- `backlinks.py`, `keywords.py`, `traffic.py`: Ahrefs endpoint adapters.
- `ai.py`: OpenRouter/OpenAI-compatible query generation.
- `cache.py`: JSON signature cache under `~/.cache/dataseo-mcp` by default.

All external HTTP boundaries are mocked in tests.

## Development

```bash
uv sync
uv run pytest -q
uv run ruff check .
uv run python -m compileall -q src
uv run python -c "from seo_mcp.server import main"
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| No CAPTCHA provider configured | Set `CAPSOLVER_API_KEY` or `ANTICAPTCHA_API_KEY` |
| CAPTCHA solving failed | Check provider balance, key validity, and rate limits |
| AI tool returns missing key error | Set `OPENROUTER_API_KEY` |
| Empty SEO response | Domain or keyword may not be indexed by the upstream source |
| Old command no longer documented | Use `dataseo-mcp`; `seo-mcp` still works as alias |

## License

MIT with educational-use notice. Original fork attribution is preserved in
[LICENSE](LICENSE).
