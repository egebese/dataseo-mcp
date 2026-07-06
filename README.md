# DataSEO MCP

Give your AI assistant real SEO data. DataSEO MCP is a [Model Context
Protocol](https://modelcontextprotocol.io) server that lets Claude, Cursor, and
other MCP clients pull **backlinks, keyword difficulty, traffic estimates, and
keyword ideas** from Ahrefs' free tools — plus optional AI query planning — just
by asking in plain English.

No dashboards, no CSV exports. Ask *"who links to suparank.io?"* and get an
answer inside your chat.

> [!CAUTION]
> For educational and research use. It automates third-party services (Ahrefs,
> CapSolver, Anti-Captcha, OpenRouter). You are responsible for complying with
> their terms of service.

## What you can ask

Talk to it in natural language — the assistant picks the right tool.

| Ask something like… | Tool it uses | You get |
| --- | --- | --- |
| "Who links to suparank.io?" | `get_backlinks_list` | Domain rating, referring domains, top backlink rows |
| "Give me keyword ideas for AI SEO tools" | `keyword_generator` | Keyword and question ideas |
| "How much organic traffic does suparank.io get?" | `get_traffic` | Monthly traffic, top pages, countries, keywords |
| "How hard is it to rank for 'AI SEO tools'?" | `keyword_difficulty` | KD score + the live SERP |
| "Generate AI search queries for 'AI SEO audit'" | `ai_search_queries` | Queries grouped by search intent |
| "Give me an SEO overview of suparank.io" | `domain_overview` | Backlink + traffic summary in one call |
| "Compare suparank.io with its competitors" | `compare_domains` | 2–5 domains side by side |
| "Find backlink gaps for suparank.io" | `backlink_opportunities` | Sources linking to competitors but not you |
| "Write a content brief for 'AI SEO audit'" | `seo_content_brief` | SERP data + AI-assisted content angles |

Maintained by [Ege Bese](https://egebese.com). Built for the AI SEO and
rank-tracking workflows behind [Suparank](https://suparank.io).

## Quick start

Run it with no install using [`uv`](https://docs.astral.sh/uv/):

```bash
export CAPSOLVER_API_KEY="your-capsolver-key"
uvx --python 3.10 dataseo-mcp
```

That's enough to use every SEO tool. See [MCP Setup](#mcp-setup) to wire it into
your assistant.

For local development:

```bash
git clone https://github.com/egebese/dataseo-mcp.git
cd dataseo-mcp
uv sync
uv run dataseo-mcp
```

The legacy `seo-mcp` command still works as an alias.

## Configuration

**One CAPTCHA provider is required** — it's how the Ahrefs-backed tools clear
the Turnstile challenge:

```bash
export CAPSOLVER_API_KEY="your-capsolver-key"
# or
export ANTICAPTCHA_API_KEY="your-anticaptcha-key"
```

If both are set, CapSolver is tried first and Anti-Captcha is the fallback.

**AI tools are optional.** `ai_search_queries` and `seo_content_brief` need
OpenRouter; without it, the other tools still work and AI output is marked
unavailable:

```bash
export OPENROUTER_API_KEY="your-openrouter-key"
export OPENROUTER_MODEL="openai/gpt-4o-mini"  # optional
```

Runtime overrides:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATASEO_CACHE_DIR` | `~/.cache/dataseo-mcp` | Signature cache location |
| `DATASEO_REQUEST_TIMEOUT` | `30` | HTTP timeout in seconds |
| `DATASEO_MAX_POLLING_ATTEMPTS` | `120` | CAPTCHA polling cap |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenAI-compatible AI endpoint |

## MCP Setup

**Claude Code:**

```bash
claude mcp add dataseo --scope user -- uvx --python 3.10 dataseo-mcp
```

**Claude Desktop / Cursor** (`claude_desktop_config.json` or equivalent):

```json
{
  "mcpServers": {
    "dataseo": {
      "command": "uvx",
      "args": ["--python", "3.10", "dataseo-mcp"],
      "env": {
        "CAPSOLVER_API_KEY": "YOUR_CAPSOLVER_KEY",
        "OPENROUTER_API_KEY": "YOUR_OPENROUTER_KEY"
      }
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`):

```json
{
  "servers": {
    "dataseo": {
      "command": "uvx",
      "args": ["--python", "3.10", "dataseo-mcp"],
      "env": { "CAPSOLVER_API_KEY": "YOUR_CAPSOLVER_KEY" }
    }
  }
}
```

Add `OPENROUTER_API_KEY` only if you want the AI tools.

## API Reference

### `get_backlinks_list(domain)`

```json
{
  "overview": { "domainRating": 76, "backlinks": 1500, "refdomains": 300 },
  "backlinks": [
    {
      "anchor": "Suparank",
      "domainRating": 71,
      "title": "The best AI SEO tools",
      "urlFrom": "https://source.example/best-seo-tools",
      "urlTo": "https://suparank.io/",
      "edu": false,
      "gov": false
    }
  ]
}
```

### `keyword_generator(keyword, country="us", search_engine="Google")`

Keyword and question ideas in the `label` / `value` shape. Volume and difficulty
come back as Ahrefs' bucketed estimates.

### `get_traffic(domain_or_url, country="None", mode="subdomains")`

Traffic history, traffic summary, and top pages / countries / keywords. Both
`costMonthlyAvg` and the legacy `costMontlyAvg` spelling are included.

### `keyword_difficulty(keyword, country="us")`

A keyword difficulty score plus the organic SERP rows with available metrics.

### `ai_search_queries(keyword, count=10, model="openai/gpt-4o-mini", language="en")`

```json
{
  "keyword": "ai seo audit",
  "queries": [
    { "query": "what is an AI SEO audit", "intent": "informational" },
    { "query": "best AI SEO audit tools", "intent": "commercial" }
  ],
  "model_used": "openai/gpt-4o-mini",
  "total_queries": 2
}
```

`count` is 1–50. Intents are `informational`, `commercial`, `transactional`,
`navigational`.

### Composite tools

- `domain_overview(domain, country="None")` — backlink overview + traffic
  summary for one domain.
- `compare_domains(domains, country="None")` — 2–5 unique domains side by side.
- `backlink_opportunities(domain, competitors)` — competitor backlink sources
  missing from the target's sample.
- `seo_content_brief(keyword, country="us", count=12, model, language)` — keyword
  difficulty, SERP rows, AI queries, and recommended content angles in one call.

## How it works

`server.py` stays thin; the work is split into focused modules:

- `services.py` — tool orchestration and public return shapes.
- `schemas.py` — Pydantic validation and normalization.
- `captcha.py` — CapSolver / Anti-Captcha fallback with bounded polling.
- `backlinks.py`, `keywords.py`, `traffic.py` — Ahrefs endpoint adapters.
- `ai.py` — OpenRouter query generation.
- `cache.py` — JSON signature cache (default `~/.cache/dataseo-mcp`).

Every external HTTP boundary is mocked in tests.

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
| AI tool returns a missing-key error | Set `OPENROUTER_API_KEY` |
| Empty SEO response | The domain or keyword may not be indexed upstream |
| `seo-mcp` command not documented | Use `dataseo-mcp`; `seo-mcp` still works as an alias |

## License

MIT with an educational-use notice. Original fork attribution is preserved in
[LICENSE](LICENSE).
