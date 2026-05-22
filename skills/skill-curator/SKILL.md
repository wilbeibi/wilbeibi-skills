---
name: skill-curator
description: Audit and de-duplicate an existing agent-skill library — find forked scripts, contradictory or restated instructions across SKILL.md files, bloated frequently-loaded files, and internal defects (duplicate headers/numbering, dead refs, dead code). Use when the user says "audit my skills", "some skills look duplicated", "polish/clean up the skill library", "consolidate these skills", or points at a skills/ tree and asks what overlaps. Do NOT use to author one new skill (use write-skill) or to review application source code (use a code-review skill).
---

# skill-curator

Keep a skill library lean: one source of truth per capability, terse where it loads often, defect-free.

## Audit workflow

1. **Inventory** — extract every skill's `name` + `description` (tier-1 signal):
   `for d in <root>/*/*/; do grep -E '^(name|description):' "$d/SKILL.md"; done`
2. **Cluster** — group by topic; flag any pair whose descriptions overlap or whose triggers could both fire.
3. **Confirm by reading** — for each suspect, read the actual SKILL.md and scripts. Never classify from the description or a regex alone.
4. **Classify** each finding against the taxonomy below.
5. **Surface, then act** — report findings + a recommended fix per finding. Get direction before any multi-file refactor. Small isolated fixes can proceed.
6. **Fix and verify** each one. Report what changed. Don't commit unless asked.

## Defect taxonomy

- **Forked script** — same script copied across skills. Diff them; check for drift and shared side effects (e.g. both write the same cache dir). Keep one canonical owner; the other points to it.
- **Contradiction** — two skills give conflicting instructions for the same artifact (save path, commit behavior, env var). Pick the owner; make the other defer.
- **Restatement** — one skill weakly re-derives another's content. Replace with a one-line pointer (keep it self-sufficient if the other may not be loaded).
- **Bloat** — a frequently/every-load file carrying rare deep-dive detail. Externalize to `references/`; keep short high-frequency quick-fixes inline.
- **Internal defect** — duplicate headers, duplicate list numbering, dead path refs, dead/duplicated code branches.

## Hard rules

- **Verify before asserting.** Text-stripped/regex defect detection misfires — comments inside code blocks, intentional parallel headers (CLI vs slash command). Read the real content of every claimed defect before calling it one. Over-claiming wastes the user's trust.
- **Single source of truth.** When two skills do the same thing, one owns it and the other references it by explicit path. Avoid symlinks if skills are copied per-profile or per-agent — a relative symlink breaks under copy.
- **Progressive disclosure.** Tier-1 = description; tier-2 = SKILL.md (terse); tier-3 = `references/` (deep, lazy-loaded). Externalize heavy rarely-hit detail. But moving a 3-line common quick-fix behind an indirection is worse, not better — keep high-frequency fixes inline.
- **Terseness scales with load frequency.** The more often a file enters context, the stricter its line budget.
- **Scope discipline.** Fix the defect; don't refactor adjacent prose, don't "improve" what isn't broken, don't add cross-links beyond what the fix needs.
- **Don't commit unless asked.** Leave changes local for review.

## Review checklist

- [ ] Inventoried all skills (name + description).
- [ ] Every claimed defect verified by reading actual content, not heuristic alone.
- [ ] Forked scripts diffed; drift and shared side effects noted.
- [ ] Findings surfaced with a recommended fix before any multi-file change.
- [ ] Each fix verified — refs resolve, target exists and runs, no new dup headers.
- [ ] No scope creep; nothing committed unless asked.

## Related

- `write-skill` — authoring one new skill. skill-curator is the maintenance counterpart for an existing library.
