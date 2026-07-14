# write-agentsmd — sourced research

Background for the rules in [SKILL.md](SKILL.md). Pulled from a web research pass, July 2026.

## The standard

[AGENTS.md](https://agents.md/) is an open, minimal Markdown format for giving coding agents operational context a README doesn't carry — install/build/test commands, style rules, validation steps, security notes. Formalized in August 2025 (OpenAI, with Google/Cursor/Factory), donated to the Linux Foundation's Agentic AI Foundation in December 2025. As of December 2025, 60,000+ open-source projects had adopted it and 20+ agent tools support it. Agents load the *nearest* AGENTS.md up the directory tree, so monorepos can layer root + subproject files. ([openai/agents.md spec overview](https://deepwiki.com/openai/agents.md/5.1-format-overview-and-specification), [github.com/agentsmd/agents.md](https://github.com/agentsmd/agents.md))

## Length and structure

[Augment Code — "A good AGENTS.md is a model upgrade. A bad one is worse than no docs at all."](https://www.augmentcode.com/blog/how-to-write-good-agents-dot-md-files):
- Keep the main file 100–150 lines; use progressive disclosure — push deep guidance into separate reference docs, cap references per file at 10–15, make scope explicit so the agent knows when to load each one.
- **The overexploration trap**: excessive architecture overviews pull agents into reading dozens of files, degrading output with irrelevant context. 30+ warning-only rules without positive guidance cause agents to verify against every constraint even when irrelevant.
- Only AGENTS.md auto-loads reliably (100% discovery in the study). Orphaned docs in `_docs/` are found <10% of the time; nested READMEs in subdirectories ~40%.
- High-impact patterns, measured: procedural multi-step workflows moved correctness from failure to first-attempt success in one case (+25% correctness, +20% completeness); decision tables resolving ambiguous choices (e.g. "state library X vs Y") improved best-practices adherence +25%; 3–10 line real code examples improved code-reuse scores +20%.
- Paired guidance beats standalone prohibitions: "don't use float for money, use Decimal" outperforms "don't use float" alone.

[philschmid — "Writing a Good AGENTS.md"](https://www.philschmid.de/writing-good-agents):
- Target under 300 lines, ideally under 60.
- Exclude: directory listings (agents discover structure independently), code-style guidelines (linters/formatters are cheaper and deterministic), task-specific instructions that only sometimes apply (dilutes focus every session), auto-generated `/init` output.
- **Auto-generated AGENTS.md files reduced task success ~3% while increasing cost 20%** in the cited study — write it by hand.
- Link to `file:line` instead of pasting code snippets that go stale.
- "Tools mentioned in AGENTS.md get used 160x more often than unmentioned ones."

General search synthesis (multiple 2026 guides — betterclaw.io, atlan.com, buildbetter.ai):
- LLM-*generated* AGENTS.md files reduced task success in 5 of 8 tested settings — generic, verbose, state-the-obvious instructions are worse than nothing.
- Vague instructions ("write clean code," "follow best practices") do nothing; the agent already attempts that by default. What changes behavior is specific, testable rules a diff can be checked against.
- The agent reads top to bottom; earlier lines carry more practical weight. Put must-never-do items first.
- Warning-only documentation underperforms documentation that pairs a prohibition with a concrete alternative — the pair tells the agent what to do and lets it stop searching.
- Organic growth beats speculative completeness: "start with 30 lines; add a section when an agent consistently gets something wrong; remove a section when the convention changes."

## Applying this to an existing bloated file

The failure mode isn't "too much detail" — it's detail in the wrong place. A vault/repo AGENTS.md that has grown through real incidents (a Linter run that rewrote 1,191 files, a script that silently mis-parsed a table) is doing the *organic growth* pattern correctly — that content is earned, not filler. The fix is almost always:

1. Relocate the highest-stakes prohibitions to the top (reordering costs nothing and is the single highest-leverage change).
2. Extract single-topic design rationale (the "why" behind a script's architecture, a map-reduce pipeline, a model-choice tradeoff) to the tool's own docstring/`--help` or a linked reference note, leaving a 1–3 sentence pointer behind in the main file.
3. Leave the earned, incident-driven rules alone — they're exactly what the research says works.

Don't confuse "long" with "bad." A 200-line file that is all specific, tested, paired-with-alternatives operating rules is better than a 60-line file full of "follow best practices."
