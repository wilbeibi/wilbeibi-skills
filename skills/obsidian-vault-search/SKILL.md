---
name: obsidian-vault-search
description: Search an Obsidian vault using natural language, date filters, tags, task states, and multilingual terms. Use when finding notes, recent writing, tagged content, due tasks, overdue tasks, or high-priority tasks in a local Markdown vault.
---

# obsidian-vault-search

Find Markdown notes and tasks in a local Obsidian vault without loading the whole vault into context.

## Routing

Use direct `rg` for exact content, frontmatter, tags, and simple task glyph matches. Use `scripts/vault_search.py` when the query needs natural-language dates, overdue comparisons, language-aware term extraction, result ranking, or mtime fallback.

## Direct Patterns

```bash
rg "keyword" --glob "*.md" <vault>
rg "tags:.*tagname" --glob "*.md" <vault>
rg "created: $(date +%Y-%m)" --glob "*.md" <vault>
rg "^- \[ \]" --glob "*.md" <vault>
rg "^- \[ \].*📅 $(date +%F)" --glob "*.md" <vault>
rg "^- \[ \].*⏫" --glob "*.md" <vault>
```

## Script Usage

```bash
scripts/vault_search.py "recent week psychology" --vault <vault>
scripts/vault_search.py "找3-2-1技巧" --vault <vault>
scripts/vault_search.py "tasks due today" --vault <vault>
scripts/vault_search.py "overdue tasks" --vault <vault>
scripts/vault_search.py "3-2-1" --vault <vault> --raw
```

## Notes

- Most date frontmatter uses `created: YYYY-MM-DD`; the script falls back to file mtime when frontmatter is missing.
- Task markers: `📅` due, `🛫` start, `⏳` scheduled, `⏫` high, `🔼` medium, `🔽` low.
- Chinese queries use contiguous CJK terms; English queries use alnum tokens of 3+ chars.
- Synonym expansion is the agent's job, not the script's.
- Prefer `--raw` when piping into another command or combining with `xargs`.
