# AGENTS.md / CLAUDE.md

AGENTS.md is loaded into every agent session in the repo — its cost compounds across every future conversation. Optimize for token budget and signal density, not completeness.

Use **strict** mode for prohibitions and procedures. Use **natural** mode for short rationale that explains why a surprising rule exists.

## Workflow

1. Measure the current file: `wc -l` and a char/4 token estimate (see Bloat Scan below). Flag anything past ~150 lines / ~2500 tokens.
2. Classify every section: **operating rule** (keep inline), **reference material** (extract to a linked doc or the tool's own `--help`/docstring), or **filler** (cut outright).
3. Check ordering: the highest-blast-radius prohibitions must be readable in the first ~30 lines, not past the midpoint.
4. Run every remaining section against the Rules below.
5. For each extraction candidate, verify the reference target *actually contains* the detail before cutting — `grep`/`cat` it, don't assume from memory.
6. Re-measure. Confirm nothing load-bearing was lost, not just that the file got shorter.

## Rules

1. **Length**: target 100–150 lines / ~2000–2500 tokens; hard ceiling ~300 lines. Token count (chars/4), not line count, is the real budget — long unwrapped paragraphs hide bloat under a low line count.
2. **Front-load hard rules**: must-never-do / highest-blast-radius prohibitions go immediately after any index, before everything else. Earlier lines carry more weight in practice.
3. **Pair every prohibition with a concrete alternative.** "Don't do X" alone underperforms "don't do X; do Y instead" — bare warnings without an alternative cause over-exploration.
4. **Cut generic advice.** "Write clean code," "follow best practices" changes nothing — the agent already tries that. Every rule must be specific enough to test against a diff.
5. **No code-style prose.** Delegate to the linter/formatter config; a paragraph describing indentation is dead weight next to a working config file.
6. **No directory listings or architecture dumps.** Agents discover structure themselves. Only include what's non-obvious — where *new* content should land, not an inventory of what exists.
7. **Name exact tools and commands.** Tools named in AGENTS.md get invoked far more often than unmentioned ones — name the actual script, not "there are helper scripts available."
8. **Progressive disclosure for single-topic depth.** Incident post-mortems, design rationale, multi-paragraph "why" explanations move to a linked reference note or the tool's own docstring/`--help`. Leave a 1–3 sentence pointer, never silence.
9. **Procedural workflows as numbered steps** for anything multi-step and error-prone. Decision tables for either/or choices the agent would otherwise guess at.
10. **Grow it organically, not speculatively.** Add a rule only after an agent actually got something wrong once; delete a rule the moment the convention changes. Don't pre-write guidance for hypothetical mistakes.
11. **Write it by hand.** Auto-generated boilerplate measurably reduces task success while raising token cost — every line should earn its place.
12. **Monorepo layering**: agents load the nearest AGENTS.md in the directory tree. Keep subproject-specific detail in a nested AGENTS.md, not bolted onto the root file.

## Bloat Scan (mechanical, run this first)

```bash
wc -l AGENTS.md
python3 -c "t=open('AGENTS.md').read(); print(len(t), 'chars,', len(t)//4, 'approx tokens')"
grep -n '^## ' AGENTS.md                                            # section map
awk '{ if (length($0) > 600) print NR": "length($0)" chars" }' AGENTS.md   # extraction candidates
```

Any single bullet over ~500 chars (~80–100 words) is a strong extraction candidate. Before cutting it, check: does the linked reference note or the script's own docstring/`--help` already carry this detail? If not, extraction loses information — fix the target first, or don't cut.

## Final Check

- Token estimate is within ~2000–2500, or the overage is deliberate because every long section is genuinely irreplaceable operating instruction (not extractable rationale).
- The highest-stakes prohibition in the file is readable within the first ~30 lines.
- Every "don't" has a paired "instead, do X" in the same bullet or the next sentence.
- Every extraction target was actually checked to contain the removed detail — not assumed.
- Structure still validates (run the project's own frontmatter/linter checker if one exists).

See [AGENTSMD-REFERENCE.md](AGENTSMD-REFERENCE.md) for the sourced research behind these rules.
