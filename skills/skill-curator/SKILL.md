---
name: skill-curator
description: Audit a skill library for duplicated guidance, contradictions, bloat, dead references, and defects. Use when cleaning, consolidating, or de-duplicating a skills tree.
disable-model-invocation: true
---

# skill-curator

## Workflow

1. **Inventory** — `for d in <root>/*/*/; do grep -E '^(name|description):' "$d/SKILL.md"; done`
2. **Cluster** — group by topic; flag pairs whose descriptions overlap or triggers could both fire.
3. **Read suspects** — never classify from description or regex alone.
4. **Classify** against taxonomy below.
5. **Surface findings + recommended fix** — get direction before multi-file refactor; small isolated fixes can proceed.
6. **Fix and verify**. Don't commit unless asked.

## Taxonomy

- **Forked script** — same script copied across skills. Diff for drift. One owner; the other points to it.
- **Contradiction** — conflicting instructions for the same artifact. Pick owner; other defers.
- **Restatement** — one skill re-derives another's content. Replace with a one-line pointer.
- **Bloat** — frequently-loaded file carrying rare detail. Externalize to `references/`; keep quick-fixes inline.
- **Unused or over budget** — a skill no session log has read, or descriptions that together exceed the harness's list budget (Codex: 2% of context, then equal truncation). [steipete/agent-scripts skill-cleaner](https://github.com/steipete/agent-scripts/blob/main/skills/skill-cleaner/SKILL.md) measures both for Codex; elsewhere, sum description bytes by hand.
- **Internal defect** — duplicate headers/numbering, dead path refs, dead code.
- **Smell** — a single skill that fails on its own. From a 238-skill survey (arXiv 2607.01456), the ones worth flagging: stepless workflow; option buffet (choices with no decision rule); rationalization loophole ("usually", "if needed"); buried gotchas (traps mid-paragraph instead of in Notes); confusing description (what, when, and keywords blurred into one sentence); time-sensitive claims; non-third-person description; XML or backslash paths in frontmatter.

## Rules

- Read every claimed defect before asserting it — heuristics misfire on code blocks and intentional parallel structures.
- One owner per capability; the other references it by explicit path.
- Progressive disclosure: description → SKILL.md (terse) → `references/REFERENCE.md` (deep). Terseness scales with load frequency.
- Fix the defect only — no adjacent refactoring, no extra cross-links.

## See also

- `write-skill` — author one new skill.
