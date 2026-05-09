---
name: obsidian-vault-search
description: Search an Obsidian vault using natural language, date filters, tags, task states, and multilingual terms. Use when finding notes, recent writing, tagged content, due tasks, overdue tasks, or high-priority tasks in a local Markdown vault.
---

# Vault Search Skill

## Architecture: 3 Layers

### Layer 1: Direct ripgrep (80% of queries)
```bash
# Fast, direct patterns
rg "3-2-1 technique" --glob '*.md'              # content search
rg "tags:.*psychology" --glob '*.md'            # tag search
rg "created: 2026-01" --glob '*.md'             # date search
rg "^- \[ \].*📅 2026-01-27" --glob '*.md'      # tasks due today
```

### Layer 2: Python script (date math & language detection)
```python
# Only for what regex can't do:
"recent week" → datetime.now() - timedelta(7)
"overdue" → filter(date < today)
"找3-2-1技巧" → Chinese term extraction
```

### Layer 3: AI agent (orchestration)
- Understands intent
- Chooses tool (ripgrep vs Python)
- Combines results
- Formats output

## Direct Patterns (Use ripgrep)

| Query Type | Pattern |
|------------|---------|
| Content | `keyword` or `(word1\|word2)` |
| Tags | `tags:.*tagname` |
| Date (YYYY-MM-DD) | `created: 2026-01-27` |
| Date range | `created: 2026-01` |
| Tasks | `^- \[ \]` |
| Tasks due today | `^- \[ \].*📅 2026-01-27` |
| High priority | `^- \[ \].*⏫` |

## When to Use Python Script

| Need | Why Python |
|------|-----------|
| "recent week" | Date calculation |
| "overdue tasks" | Date comparison |
| Language-specific | Pattern variants |
| Fallback dates | File system mtime |

## Language-Aware Term Extraction

- Chinese queries → extract contiguous CJK terms for rg
- English queries → extract alnum tokens (3+ chars)
- Synonym expansion is handled by the agent, not this script

## Date Field Patterns

Most common in Clippings:
- `created: 2026-01-27` (YYYY-MM-DD)

Fallback:
- File system modified time if no frontmatter

## Task Emojis

- 📅 Due date
- 🛫 Start date
- ⏳ Scheduled
- ⏫ High priority
- 🔼 Medium
- 🔽 Low

## CLI Usage

```bash
# Notes
scripts/vault_search.py "recent week psychology"
scripts/vault_search.py "找3-2-1技巧"

# Tasks
scripts/vault_search.py "tasks due today"
scripts/vault_search.py "overdue tasks"

# Raw output for piping
scripts/vault_search.py "3-2-1" --raw | xargs -I {} echo "{}"
```
