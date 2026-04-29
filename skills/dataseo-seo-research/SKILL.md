---
name: dataseo-seo-research
description: Use DataSEO MCP for SEO research workflows including backlink analysis, keyword research, traffic checks, domain comparison, backlink opportunity discovery, AI search query planning, and SEO content briefs. Use this whenever the user asks to investigate a domain, compare competitors, plan SEO content, find backlink gaps, or generate search-intent queries with DataSEO MCP.
---

# DataSEO SEO Research

Use this skill when a user wants SEO research through DataSEO MCP tools. The
workflow should produce concise, decision-ready findings, not raw dumps.

## Required Setup

Before calling Ahrefs-backed tools, ensure at least one CAPTCHA provider is
configured:

- `CAPSOLVER_API_KEY`
- `ANTICAPTCHA_API_KEY`

AI query planning and content briefs improve when `OPENROUTER_API_KEY` is set.
If it is missing, continue with non-AI SEO data and clearly mark AI output as
unavailable.

## Tool Selection

Choose the narrowest tool that answers the request:

| User intent | Tool |
| --- | --- |
| Backlink profile for one domain | `get_backlinks_list` |
| Keyword ideas from seed terms | `keyword_generator` |
| Traffic estimate for a domain or URL | `get_traffic` |
| Ranking difficulty / SERP snapshot | `keyword_difficulty` |
| AI search query ideas by intent | `ai_search_queries` |
| Quick domain health summary | `domain_overview` |
| Competitor comparison | `compare_domains` |
| Link-building source gaps | `backlink_opportunities` |
| Article or landing-page brief | `seo_content_brief` |

## Research Workflow

1. Normalize all domains to bare domains unless the user asks for an exact URL.
2. For one-domain audits, start with `domain_overview`, then deepen with
   `get_backlinks_list` or `keyword_generator` only if needed.
3. For competitor work, use `compare_domains` first, then
   `backlink_opportunities` for link-building next steps.
4. For content planning, use `keyword_difficulty` and `keyword_generator`; add
   `ai_search_queries` or `seo_content_brief` when AI is configured.
5. Summarize findings by priority: opportunity, evidence, recommended action.

## Output Format

Use this structure unless the user asks for something else:

```markdown
## Summary
- One-sentence SEO readout.

## Findings
- Domain/keyword evidence with metrics.

## Opportunities
- Prioritized actions and why they matter.

## Next Steps
- 3-5 concrete tasks.
```

## Safety and Quality

- Do not claim live accuracy beyond the returned tool data.
- Do not scrape or bypass sites outside the MCP provider behavior.
- Do not expose API keys, CAPTCHA tokens, signed inputs, or raw provider
  responses.
- Prefer comparisons and patterns over long raw tables.
- Mention when a domain or keyword appears missing from upstream data.

## Examples

Input: "Analyze backlinks for suparank.io"

Action: Call `get_backlinks_list(domain="suparank.io")`, then summarize domain
rating, referring domains, strongest sources, anchors, and link-building angles.

Input: "Compare these: suparank.io, ahrefs.com, semrush.com"

Action: Call `compare_domains(domains=[...])`, then report traffic/backlink
differences and practical positioning notes.

Input: "Create a brief for AI SEO audit"

Action: Call `seo_content_brief(keyword="AI SEO audit")`; if AI is unavailable,
fall back to `keyword_difficulty` and `keyword_generator`.
