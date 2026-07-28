---
name: obsidian-search
description: Search an Obsidian vault for topics, exact text, tags, recent notes, and tasks. Use when fuzzy, date-aware, due, or overdue note retrieval is needed.
---

# obsidian-search

Find Markdown notes and tasks in an Obsidian vault without loading the whole vault into context.

## Routing

1. **Topic / fuzzy / "notes about X"** → `scripts/meili_search.py`. Typo-tolerant full-text over a Meilisearch index; best when the user won't remember exact words. Expand synonyms yourself across queries.
2. **Exact content, frontmatter, tags, task glyphs** → direct `rg`.
3. **Natural-language dates, overdue comparisons, CJK term extraction** → `scripts/vault_search.py`.

If Meilisearch is unreachable or unconfigured (script exits non-zero), fall back to tiers 2–3 — they only need the local vault.

Env: `OBSIDIAN_VAULT` (vault root), `MEILI_URL` (default `http://127.0.0.1:7700`), `MEILI_SEARCH_KEY` (file fallback `~/meilisearch/search-key.txt`), `MEILI_INDEX` (default `notes`).

## Meilisearch

Run with `--help` for all flags. **Never dump raw hits into context** — use `--fields` and small `--limit`.

```bash
uv run scripts/meili_search.py "spaced repetition" --limit 5 --fields "title,path"
uv run scripts/meili_search.py "prompt caching" --filter "tags=ai" --sort "updated:desc" --json
```

Hit `path` values are vault-relative (e.g. `Library/Book Notes/Influence.md`); join with `$OBSIDIAN_VAULT` to open.

## Direct Patterns

```bash
rg "keyword" --glob "*.md" "$OBSIDIAN_VAULT"
rg -lU 'tags:\n(\s*- .*\n)*?\s*- tagname\b' --glob "*.md" "$OBSIDIAN_VAULT"  # YAML list tags; prefer meili --filter "tags=tagname" when index is up
rg "created: $(date +%Y-%m)" --glob "*.md" "$OBSIDIAN_VAULT"
rg "^- \[ \].*📅 $(date +%F)" --glob "*.md" "$OBSIDIAN_VAULT"
rg "^- \[ \].*⏫" --glob "*.md" "$OBSIDIAN_VAULT"
```

## Date-Aware Script

```bash
uv run scripts/vault_search.py "recent week psychology"
uv run scripts/vault_search.py "overdue tasks"
uv run scripts/vault_search.py "找3-2-1技巧" --raw   # --raw: plain paths for piping
```

## Notes

- `created: YYYY-MM-DD` frontmatter drives dates; `vault_search.py` falls back to file mtime.
- Task markers (Tasks plugin): `📅` due, `🛫` start, `⏳` scheduled, `⏫`/`🔼`/`🔽` priority.
- Synonym expansion is the agent's job, not the scripts'.
