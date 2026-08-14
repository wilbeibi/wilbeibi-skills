---
name: skill-curator
description: Audit a skill library for duplicated guidance, contradictions, bloat, dead references, and defects. Use when cleaning, consolidating, or de-duplicating a skills tree.
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
- **Internal defect** — duplicate headers/numbering, dead path refs, dead code.

## Rules

- Read every claimed defect before asserting it — heuristics misfire on code blocks and intentional parallel structures.
- One owner per capability; the other references it by explicit path.
- Progressive disclosure: description → SKILL.md (terse) → `references/REFERENCE.md` (deep). Terseness scales with load frequency.
- Fix the defect only — no adjacent refactoring, no extra cross-links.

## See also

- `write-skill` — author one new skill.
