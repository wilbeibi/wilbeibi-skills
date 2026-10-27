# wilbeibi-skills

> A trillion-parameter brain to wash my digital dishes.

These are the skills I keep around for Claude Code and Codex. Most began as a prompt I got tired of retyping: how I want a diff reviewed, when a test deserves to be committed, how to get my bearings in a repo I've never seen. Some are useful anywhere. Others only make sense on my machines, like the ones that assume a Mac running Hammerspoon or my Obsidian vault's layout.

Browse [`skills/`](skills/) and take what fits. Each skill is one folder with a `SKILL.md` at its root, so you can copy a single folder into your agent's skills directory and ignore the rest of the repo.

## What's here

<!-- skills-table:start -->
| Skill | Use it for |
|---|---|
| [agent-guardrails](skills/agent-guardrails/SKILL.md) | Turn recurring agent mistakes in a project into enforceable constraints. |
| [benchmark-checklist](skills/benchmark-checklist/SKILL.md) | Check whether a measured performance claim supports a comparison or decision. |
| [blast-radius](skills/blast-radius/SKILL.md) | Trace what a change could break beyond its diff and verify the assumptions its safety depends on. |
| [blog-review](skills/blog-review/SKILL.md) | Review a technical blog draft and report what loses its reader, ordered by cost. |
| [code-review](skills/code-review/SKILL.md) | Review a diff, package, or API through one of five lenses — necessity and layering (Russ Cox), honest invariants and costs (BurntSushi), product-versus-library fit (Mitsuhiko), a complexity gate before a design change, or newcomer clarity. |
| [create-verification-skill](skills/create-verification-skill/SKILL.md) | Create a project-local skill for launching, driving, and collecting evidence from a real app, CLI, API, or library. |
| [dataviz](skills/dataviz/SKILL.md) | Design and implement evidence-first charts from real data for technical blogs, reports, READMEs, and product explainers. |
| [grill-me](skills/grill-me/SKILL.md) | Interview the user one question at a time until a plan is resolved, capturing durable decisions in CONTEXT.md or ADRs when the repo warrants it. |
| [grok-repo](skills/grok-repo/SKILL.md) | Explain an unfamiliar codebase through a repository briefing, dataflow trace, or reconstruction of why and how a change was made. |
| [hammerspoon](skills/hammerspoon/SKILL.md) | Operate macOS via Hammerspoon, either one-off `hs -c` Lua (launch, quit, or focus apps and browser tabs; volume, wifi, caffeinate, alerts, clipboard) or persistent hotkeys, watchers, and menubar items in ~/.hammerspoon. |
| [html-lesson](skills/html-lesson/SKILL.md) | Turn a paper, notebook, chapter, or design doc into a narrated, self-paced HTML lesson — one self-contained file with chapters, subtitles, worked numbers, pause-and-predict questions, and optional TTS narration; the finished lesson can also be filmed into one MP4. |
| [karpathy-planning](skills/karpathy-planning/SKILL.md) | Develop a scoped implementation plan when explicitly asked to plan a coding task. |
| [mechanism-viz](skills/mechanism-viz/SKILL.md) | Plan and build a trace-grounded explanation of how a mechanism in your own system works, as a post with animated figures, an interactive explorer that replays one real instance, and benchmark charts. |
| [obsidian-capture](skills/obsidian-capture/SKILL.md) | Append todos, logs, learnings, and reflections to Obsidian daily or weekly notes and run the agent-todo queue via scripts/capture.py. |
| [obsidian-search](skills/obsidian-search/SKILL.md) | Search an Obsidian vault for topics, exact text, tags, recent notes, and tasks. |
| [paper-search](skills/paper-search/SKILL.md) | Find and rank research papers by relevance, recency, field-adjusted impact, venue, and author affiliation. |
| [readback](skills/readback/SKILL.md) | Put a long reply of your own - or a plan, document, or session transcript - on an HTML page the user reads, highlights, and comments on, returning their notes as a follow-up prompt through a waiting local command. |
| [repo-eval](skills/repo-eval/SKILL.md) | Evaluate a public GitHub repository's momentum and maintenance health. |
| [route-skill](skills/route-skill/SKILL.md) | Discovers skills in the wilbeibi-skills catalog and loads explicitly selected skills from local files or cache, fetching missing skills. |
| [sherlock](skills/sherlock/SKILL.md) | Work an open question like a case — graded clues, competing theories in a consistency matrix, eliminate by evidence, backtrack, converge, with a casebook on disk for long cases. |
| [show-me](skills/show-me/SKILL.md) | Explain code structure, dataflow, or proposed changes with a compact tree, pseudocode, type signature, diff, or diagram. |
| [sketch-concept](skills/sketch-concept/SKILL.md) | Draw a hand-drawn SVG illustration that explains one technical mechanism or data insight — architecture, concurrency, storage, caching, queues, retries — for a blog post, doc, or slide. |
| [skill-curator](skills/skill-curator/SKILL.md) | Audit a skill library for duplicated guidance, contradictions, bloat, dead references, and defects. |
| [test-writing](skills/test-writing/SKILL.md) | Writes, reviews, and prunes tests so the committed suite protects contracts and invariants rather than implementation. |
| [tla-model](skills/tla-model/SKILL.md) | Models concurrent and distributed designs in TLA+ or PlusCal and checks them with the TLC model checker. |
| [web-recap](skills/web-recap/SKILL.md) | Search browser history for URLs by topic or visit statistics. |
| [write-docs](skills/write-docs/SKILL.md) | Write or critique prose that ships with a codebase — READMEs, guides and runbooks, CLI help and error text, code comments, AGENTS.md/CLAUDE.md, commit messages, PR titles and descriptions, and changelog entries. |
| [write-skill](skills/write-skill/SKILL.md) | Author or update compact agent skills under skills/<name>/SKILL.md. |
<!-- skills-table:end -->

`blast-radius`, `benchmark-checklist`, `agent-guardrails`, and `create-verification-skill` adapt selected [pstack](https://github.com/cursor/plugins/tree/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack) skills for use across agents; each folder retains its upstream MIT notice. The table is generated from `catalog.json`; edit a skill's `description`, not the table.

## Let the router pick

If you don't want to decide up front, link the router once (Python 3.10+):

```bash
git clone https://github.com/wilbeibi/wilbeibi-skills ~/src/wilbeibi-skills
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link route-skill
```

Then describe the job to your agent in plain words, such as "review this diff" or "why did this function change last spring?" The router suggests a skill and waits for you to choose before it loads anything. Asking what a skill does won't load it either.

To see what's available, run `route_skill.py list`, optionally with a word to filter on. `get <name>` loads a skill from your checkout or cache, and fetches it from GitHub only when it's missing. Downloads are checked against `catalog.json` and cached under `${XDG_CACHE_HOME:-~/.cache}/route-skill` until you pass `--refresh`.

## Keep a skill around

Loading a skill once leaves nothing behind. To keep one available, link it globally or for a single project:

```bash
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link code-review
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link test-writing --project
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py unlink test-writing --project
```

Global links go into `~/.agents/skills` and any Claude, Codex, Pi, or Hermes skill directories that already exist. Project links go into `.agents/skills` and `.claude/skills` in the current directory; keep them out of commits, for example with `.git/info/exclude`. The router never overwrites a real directory or a link it doesn't own.

To update, run `bin/skills-sync --pull`. It pulls with `--ff-only` and repairs the links this checkout owns. It never enables anything new. If you installed with `npx skills add … --all` or the old `load-skill`, follow [MIGRATION.md](MIGRATION.md) first.

## Limits

Persistent links need a checkout; a standalone copy of the router can only discover and fetch. The downloader is unauthenticated, so private GitHub repos won't work, and other sources must publish this repo's `catalog.json` format (select one with `--repo owner/repo --ref <branch-or-commit> --remote`). Skills report their requirements, but nothing gets installed for you.

## Changing a skill

Regenerate `catalog.json` whenever skill files change; CI rejects stale metadata and checksums. Run the same checks locally before pushing:

```bash
uv run scripts/check_skill_frontmatter.py
uv run scripts/build_catalog.py
python3 skills/route-skill/scripts/test_route_skill.py
```
