---
name: skill-curator
description: Audit and de-duplicate an existing agent-skill library — find forked scripts, contradictory or restated instructions across SKILL.md files, bloated frequently-loaded files, and internal defects (duplicate headers/numbering, dead refs, dead code). Use when the user says "audit my skills", "some skills look duplicated", "polish/clean up the skill library", "consolidate these skills", or points at a skills/ tree and asks what overlaps. Do NOT use to author one new skill (use write-skill) or to review application source code (use a code-review skill).
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
- Progressive disclosure: description → SKILL.md (terse) → `references/` (deep). Terseness scales with load frequency.
- Fix the defect only — no adjacent refactoring, no extra cross-links.

## See also

- `write-skill` — author one new skill.
