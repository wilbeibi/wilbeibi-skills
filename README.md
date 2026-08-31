# wilbeibi-skills

> A trillion-parameter brain to wash my digital dishes.

17 agent skills for **Claude Code** and **Codex**: code review, test writing, documentation, pre-coding planning, codebase onboarding, repo health evaluation, research paper search, skill authoring, browser history recall, macOS automation, and Obsidian note capture and search. Each is a single `SKILL.md` your agent loads on demand; install all of them or just one with `npx skills`.

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*'
```

## Skills

| Skill | Description |
|-------|-------------|
| [obsidian-search](skills/obsidian-search/SKILL.md) | Search an Obsidian vault three-tier: Meilisearch for topic/fuzzy queries, ripgrep for exact matches, date-aware helper for natural-language dates and tasks. |
| [obsidian-capture](skills/obsidian-capture/SKILL.md) | Append quick todos (with due dates), log lines, learnings, and reflections to the right section of Obsidian daily and weekly notes; run the separate `#agent-todo` queue. |
| [test-writing](skills/test-writing/SKILL.md) | Guide effective, maintainable test writing. |
| [newcomer-lens-review](skills/newcomer-lens-review/SKILL.md) | Review code for missing context, onboarding gaps, and undocumented assumptions. |
| [code-review](skills/code-review/SKILL.md) | Review a diff, package, or API through one of three lenses — necessity and layering (Russ Cox), invariant and cost honesty (BurntSushi), or product-versus-library fit (Mitsuhiko). |
| [complexity-budget](skills/complexity-budget/SKILL.md) | Gate a change to an existing codebase: added complexity must justify declared marginal value, before and after the edit. |
| [grill-me](skills/grill-me/SKILL.md) | Relentlessly interview the user one question at a time to stress-test a plan or design, capturing resolved terminology and durable decisions in CONTEXT.md or ADRs when the repo warrants it. |
| [questionnaire](skills/questionnaire/SKILL.md) | Batch a long discussion's open decisions into an offline HTML questionnaire (branching, autosaved drafts) whose answers come back as markdown keyed by stable question ids. |
| [write-skill](skills/write-skill/SKILL.md) | Scaffold compact trigger-rich and command-first skills in this repo. |
| [skill-curator](skills/skill-curator/SKILL.md) | Audit and de-duplicate an existing skill library — forked scripts, contradictory instructions, bloat, internal defects. |
| [write-docs](skills/write-docs/SKILL.md) | Write or critique codebase prose — READMEs, developer guides and runbooks, CLI text, comments, agent guides, and commit/PR descriptions — with an advisory clarity checker. |
| [show-me](skills/show-me/SKILL.md) | Answer with a compact visual — call tree, component tree, file tree, pseudocode, type signature, diff, or Mermaid — instead of a wall of prose. Adapted from [humanlayer/skills](https://github.com/humanlayer/skills). |
| [grok-repo](skills/grok-repo/SKILL.md) | Understand an unfamiliar codebase through a full briefing, scoped dataflow trace, or reconstruction of why and how a feature changed. |
| [repo-eval](skills/repo-eval/SKILL.md) | Score a public GitHub repo on momentum (popularity trajectory) and maintenance (how well it is run) via the OSS Insight API and `gh`. |
| [paper-search](skills/paper-search/SKILL.md) | Find papers across Semantic Scholar, OpenAlex, and arXiv, ranked by impact relative to field and age — so recent work and credible work are told apart from noise. |
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
