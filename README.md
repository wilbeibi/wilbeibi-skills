# wilbeibi-skills

> A trillion-parameter brain to wash my digital dishes.

22 skills for Claude Code and Codex, covering code review, research, documentation, visualization, and personal automation.
Keep the full collection here; choose what to use on each machine and in each project.
The [route-skill](skills/route-skill/SKILL.md) entrypoint recommends skills and loads them after you explicitly select one.

Clone once and enable the router (Python 3.10+):

```bash
git clone https://github.com/wilbeibi/wilbeibi-skills ~/src/wilbeibi-skills
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link route-skill
```

Then tell your agent: "Use dataviz to chart these benchmark results."
It uses local files or cache, fetching a missing skill without asking again.
For an uninstalled skill, invoke the router with ordinary language; the target need not appear in the native skill menu.
The router can recommend a skill for a generic task, but waits for your selection before fetching or loading its instructions.
Asking what a skill does does not activate it.

Already installed this repo with `npx skills add … --all` or `load-skill`? See [MIGRATION.md](MIGRATION.md).

## Skills

| Skill | Description |
|-------|-------------|
| [route-skill](skills/route-skill/SKILL.md) | Recommend from the catalog; load explicitly selected skills from local files or cache, fetching only missing content. |
| [obsidian-search](skills/obsidian-search/SKILL.md) | Search an Obsidian vault three-tier: Meilisearch for topic/fuzzy queries, ripgrep for exact matches, date-aware helper for natural-language dates and tasks. |
| [obsidian-capture](skills/obsidian-capture/SKILL.md) | Append quick todos (with due dates), log lines, learnings, and reflections to the right section of Obsidian daily and weekly notes; run the separate `#agent-todo` queue. |
| [test-writing](skills/test-writing/SKILL.md) | Guide effective, maintainable test writing. |
| [newcomer-lens-review](skills/newcomer-lens-review/SKILL.md) | Review code for missing context, onboarding gaps, and undocumented assumptions. |
| [code-review](skills/code-review/SKILL.md) | Review a diff, package, or API through one of three lenses — necessity and layering (Russ Cox), invariant and cost honesty (BurntSushi), or product-versus-library fit (Mitsuhiko). |
| [complexity-budget](skills/complexity-budget/SKILL.md) | Explicit-only review of ownership, coupling, and value before a substantial design change. |
| [grill-me](skills/grill-me/SKILL.md) | Explicit-only design interview, one question at a time; capture durable terminology and decisions when useful. |
| [questionnaire](skills/questionnaire/SKILL.md) | Batch a long discussion's open decisions into an offline HTML questionnaire (branching, autosaved drafts) whose answers come back as markdown keyed by stable question ids. |
| [write-skill](skills/write-skill/SKILL.md) | Write compact shared skills for Codex, Claude Code, and Pi; isolate harness-specific behavior. |
| [skill-curator](skills/skill-curator/SKILL.md) | Audit and de-duplicate an existing skill library — forked scripts, contradictory instructions, bloat, internal defects. |
| [write-docs](skills/write-docs/SKILL.md) | Write or critique codebase prose — READMEs, developer guides and runbooks, CLI text, comments, agent guides, and commit/PR descriptions — with an advisory clarity checker. |
| [show-me](skills/show-me/SKILL.md) | Answer with a compact visual — call tree, component tree, file tree, pseudocode, type signature, diff, or Mermaid — instead of a wall of prose. Adapted from [humanlayer/skills](https://github.com/humanlayer/skills). |
| [dataviz](skills/dataviz/SKILL.md) | Turn real measurements into evidence-first editorial charts for benchmarks, performance comparisons, technical articles, reports, and READMEs. |
| [sketch-concept](skills/sketch-concept/SKILL.md) | Generate a hand-drawn illustration that explains one technical mechanism as a small physical world — metaphor, palette, and prompt skeleton, plus a meaning/legibility/coherence check on the draft. |
| [grok-repo](skills/grok-repo/SKILL.md) | Understand an unfamiliar codebase through a full briefing, scoped dataflow trace, or reconstruction of why and how a feature changed. |
| [sherlock](skills/sherlock/SKILL.md) | Work an open question like a case: log graded clues, run competing theories through a consistency matrix, kill by evidence, backtrack, converge — for puzzling bugs, reverse-engineering a product from public signals, or "what happened here". |
| [repo-eval](skills/repo-eval/SKILL.md) | Score a public GitHub repo on momentum (popularity trajectory) and maintenance (how well it is run) via the OSS Insight API and `gh`. |
| [paper-search](skills/paper-search/SKILL.md) | Find papers across Semantic Scholar, OpenAlex, and arXiv, ranked by impact relative to field and age — so recent work and credible work are told apart from noise. |
| [web-recap](skills/web-recap/SKILL.md) | Extract browser history (Chrome, Firefox, Safari, Edge, Brave) to find URLs by topic or get visit stats. Adapted from [robzolkos/web-recap](https://github.com/robzolkos/web-recap). |
| [karpathy-planning](skills/karpathy-planning/SKILL.md) | Explicit-only implementation planning: scope, material assumptions, and verifiable completion. |
| [hammerspoon](skills/hammerspoon/SKILL.md) | Operate macOS via Hammerspoon: one-off `hs -c` Lua for apps, browser tabs, and system toggles, plus authoring persistent automations in ~/.hammerspoon. |

## Use and cache

Commands below assume you are in this checkout. From another directory, use the script's absolute path.

```bash
python3 skills/route-skill/scripts/route_skill.py list chart
python3 skills/route-skill/scripts/route_skill.py get dataviz
python3 skills/route-skill/scripts/route_skill.py get dataviz --remote
python3 skills/route-skill/scripts/route_skill.py get dataviz --refresh
```

- `list` reads catalog metadata, including requirements and local paths. It downloads no skill bodies.
- `get` prints the `SKILL.md` path on stdout and provenance on stderr. The agent reads it before continuing.
- Local selection checks project ancestors up to the repository root, then user skill directories. Distinct local sources require a choice.
- `--remote` selects the repository source instead of installed skills or the checkout. It still reuses cached content.
- `--refresh` explicitly fetches the current remote version. It does not update your checkout or installed copies.

Remote downloads include only the selected skill's files, verified against catalog checksums at a resolved Git commit.
Cache lives under `${XDG_CACHE_HOME:-~/.cache}/route-skill` and has no automatic expiry.
Failed refreshes return an error and preserve the old snapshot; omit `--refresh` to use it again.
Caching makes a skill available for future selection; it does not enable automatic invocation.

## Enable for a project or host

One-off use creates no agent-directory links. To keep a skill available, request that scope explicitly:

```bash
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link code-review
cd ~/some/project
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link dataviz --project
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py unlink dataviz --project
```

Global links use `~/.agents/skills` and existing Claude/Codex/Pi/Hermes installations.
Project links use `.agents/skills` and `.claude/skills` in the current directory.
Keep these machine-specific links out of commits, for example using the project's `.git/info/exclude`.
The repo contains no host manifests. Existing real directories or conflicting links are preserved and reported.

The router allows automatic discovery by default in both Claude Code and Codex.
Its instructions require explicit selection before loading a recommended skill.
Other skills retain their own invocation policies; local preferences stay in each agent's settings.

## Update

```bash
bin/skills-sync          # repair only this checkout's selected global links
bin/skills-sync --pull   # first update the checkout with git pull --ff-only
python3 skills/route-skill/scripts/route_skill.py list --refresh
```

Updating does not enable additional skills or change other installers' lockfiles.
After migration, owned links follow the checkout; use the original installer only for skills that remain as unmanaged copies.
Hosts still on the old full install should follow [MIGRATION.md](MIGRATION.md).

## Limits

Persistent links require a checkout. A standalone copy of the router can discover and fetch without one.
Remote sources must publish this repo's `catalog.json` format; this is not a general skill marketplace client.
Use `--repo owner/repo --ref branch-or-commit --remote` to select a compatible source explicitly.
Private GitHub repositories are not supported by the unauthenticated downloader.
Compatibility is reported for the agent to check; missing dependencies are not installed automatically.

## Layout

Each skill lives in `skills/<name>/SKILL.md`. Supporting scripts and reference docs are colocated in the same directory.

## Validation

Check skill frontmatter and script tests before pushing (CI runs the same):

```bash
uv run scripts/check_skill_frontmatter.py
uv run scripts/build_catalog.py
uv run scripts/build_catalog.py --check
python3 skills/route-skill/scripts/test_route_skill.py
```

Regenerate and commit `catalog.json` whenever skill files change. CI rejects stale metadata or checksums.
