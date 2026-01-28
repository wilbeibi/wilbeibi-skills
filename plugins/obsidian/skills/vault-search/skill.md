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
"找3-2-1技巧" → Chinese patterns
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

## Language-Aware Patterns

**English query → English patterns:**
- 3-2-1 → ["3-2-1", "three-two-one", "321"]

**Chinese query → Chinese patterns:**
- 3-2-1 → ["3-2-1技巧", "321技巧", "三二一"]

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
vault_search.py "recent week psychology"
vault_search.py "找3-2-1技巧"

# Tasks
vault_search.py "tasks due today"
vault_search.py "overdue tasks"

# Raw output for piping
vault_search.py "3-2-1" --raw | xargs -I {} echo "{}"
```