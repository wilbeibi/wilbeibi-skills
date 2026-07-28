# wilbeibi-skills

Personal agent skills packaged for `npx skills`.

## Skills

| Skill | Description |
|-------|-------------|
| [obsidian-search](skills/obsidian-search/SKILL.md) | Search an Obsidian vault three-tier: Meilisearch for topic/fuzzy queries, ripgrep for exact matches, date-aware helper for natural-language dates and tasks. |
| [obsidian-capture](skills/obsidian-capture/SKILL.md) | Append quick todos (with due dates), log lines, learnings, and reflections to the right section of Obsidian daily and weekly notes. |
| [test-writing](skills/test-writing/SKILL.md) | Guide effective, maintainable test writing. |
| [newcomer-lens-review](skills/newcomer-lens-review/SKILL.md) | Review code for missing context, onboarding gaps, and undocumented assumptions. |
| [code-review](skills/code-review/SKILL.md) | Review a diff, package, or API through one of three lenses — necessity and layering (Russ Cox), invariant and cost honesty (BurntSushi), or product-versus-library fit (Mitsuhiko). |
| [complexity-budget](skills/complexity-budget/SKILL.md) | Gate a change to an existing codebase: added complexity must justify declared marginal value, before and after the edit. |
| [grill-me](skills/grill-me/SKILL.md) | Relentlessly interview the user one question at a time to stress-test a plan or design, capturing resolved terminology and durable decisions in CONTEXT.md or ADRs when the repo warrants it. |
| [write-skill](skills/write-skill/SKILL.md) | Scaffold compact trigger-rich and command-first skills in this repo. |
| [skill-curator](skills/skill-curator/SKILL.md) | Audit and de-duplicate an existing skill library — forked scripts, contradictory instructions, bloat, internal defects. |
| [write-docs](skills/write-docs/SKILL.md) | Write or critique the prose that ships with a codebase — READMEs, CLI shape, code comments, AGENTS.md guides, and commit/PR descriptions. |
| [grok-repo](skills/grok-repo/SKILL.md) | Understand an unfamiliar codebase: a full briefing (purpose, architecture, seams, taste, history, standout code) or a scoped dataflow trace of one subsystem. |
| [repo-eval](skills/repo-eval/SKILL.md) | Score a public GitHub repo on momentum (popularity trajectory) and maintenance (how well it is run) via the OSS Insight API and `gh`. |
| [paper-search](skills/paper-search/SKILL.md) | Find papers across Semantic Scholar, OpenAlex, and arXiv, ranked by impact relative to field and age — so recent work and credible work are told apart from noise. |
| [ast-grep](skills/ast-grep/SKILL.md) | Write ast-grep rules for structural (AST-based) code search that goes beyond text grep. Adapted from [ast-grep/agent-skill](https://github.com/ast-grep/agent-skill). |
| [web-recap](skills/web-recap/SKILL.md) | Extract browser history (Chrome, Firefox, Safari, Edge, Brave) to find URLs by topic or get visit stats. Adapted from [robzolkos/web-recap](https://github.com/robzolkos/web-recap). |
| [karpathy-planning](skills/karpathy-planning/SKILL.md) | Pre-coding planning gate: surface assumptions, pick the simplest approach, and define declarative success criteria with a verification loop. Adapted from [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills). |
| [hammerspoon](skills/hammerspoon/SKILL.md) | Operate macOS via Hammerspoon: one-off `hs -c` Lua for apps, browser tabs, and system toggles, plus authoring persistent automations in ~/.hammerspoon. |

## Install

Install all skills (auto-detects Claude Code or Codex):

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*'
```

Install a single skill:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill test-writing
```

<details>
<summary>More install options</summary>

Target a specific agent:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a claude-code
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a codex
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a claude-code codex
```

Install globally (all projects) instead of the current project only:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*' --global
```

List available skills before installing:

```bash
npx skills add wilbeibi/wilbeibi-skills --list
```

By default, `skills add` symlinks skill files so local edits propagate automatically. Use `--copy` for a detached snapshot.

</details>

## Update

```bash
npx skills update
```

<details>
<summary>More update options</summary>

```bash
npx skills update --global          # global installs only
npx skills update --project         # project installs only
npx skills update test-writing      # one skill
```

</details>

## Layout

Each skill lives in `skills/<name>/SKILL.md`. Supporting scripts and reference docs are colocated in the same directory.

## Validation

Check skill frontmatter before pushing:

```bash
uv run scripts/check_skill_frontmatter.py
```
