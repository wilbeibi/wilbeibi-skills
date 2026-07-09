---
name: obsidian-capture
description: Append quick captures — todos with due dates, log lines, learnings, reflections — to the right section of Obsidian daily (DailyPlan/) and weekly (Weekly/) notes. Use when asked to "add a todo", "note this down", "log this", "capture an idea", "due Friday", or to record something fun or a weekly reflection. Do NOT use for searching notes (use obsidian-vault-search) or for creating standalone long-form notes.
---

# obsidian-capture

Turn a quick capture into one small edit in today's daily note or this week's weekly note, following the vault's existing template conventions.

## Targets

Vault root: `$OBSIDIAN_VAULT` (e.g. `~/vaults/Vault`).

```bash
daily=$OBSIDIAN_VAULT/DailyPlan/$(LC_TIME=C date '+%Y-%m-%d %a').md   # 2026-07-08 Wed.md
weekly=$OBSIDIAN_VAULT/Weekly/$(date +%G-W%V).md                       # 2026-W28.md (ISO week)
```

If the target note is missing, create it from `Meta-Obsidian/Templates/DailyTemplate.md` or `Weekly Template.md`, resolving `{{date:...}}` placeholders to real dates (nav links use adjacent day/week names).

## Section Routing

| Capture | Destination |
|---------|-------------|
| Must-do / important todo | daily `## 🎯 今天必须完成` |
| Any other todo, incl. future due dates | daily `## ✅ 其他` |
| Timestamped happening | daily `## 🪵 Log` as `- HH:mm <text>` |
| Learned something new / diary entry | daily `## 📝 今日记` (`新知:` / `新事:`) |
| Fun thing this week | weekly `## Something Fun This Week` |
| Reflection answer | weekly `## Reflections`, under the matching `Q:` |

A todo due next month still goes in **today's** daily note — the Tasks plugin finds it by its `📅` date, not by file location.

## Task Format (Tasks plugin)

```markdown
- [ ] Review Daytona doc 📅 2026-07-10 ⏫
```

- `📅` due, `🛫` start, `⏳` scheduled, `⏫` high, `🔼` medium, `🔽` low.
- Resolve natural-language dates ("Friday", "next week") to absolute `YYYY-MM-DD` — check `date +%F` first, never guess today's date.
- Keep the capture text in the language the user used.

## Rules

- Fill the first empty `- [ ]` slot in the target section before appending a new line; likewise replace a still-empty `- HH:mm ` placeholder in Log.
- Append at the end of the section otherwise; one capture = one line.
- Never touch: frontmatter, `> [!summary]` callouts (RescueTime), ` ```base ` and ` ```dataviewjs ` blocks, the `**<< [[prev]] | [[next]] >>` nav line.
- Marking a todo done: `- [x] ... ✅ YYYY-MM-DD` (append the completion date, keep the rest of the line).
