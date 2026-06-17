---
name: write-skill
description: Author a new agent skill in this repo following progressive-disclosure, trigger-rich-description, and script-over-prose principles. Use when the user asks to "write a skill", "add a skill", "create a new skill", or scaffold a SKILL.md. Targets the `npx skills` layout (top-level `skills/<name>/SKILL.md`).
---

# write-skill

Scaffold a new skill under `skills/<name>/` that is short, trigger-rich, and self-contained.

## Steps

1. **Clarify the skill** — ask the user, in one round:
   - What capability does it provide? (one sentence)
   - What concrete user phrases or contexts should trigger it?
   - Are there contexts where it should *not* trigger? (negative triggers)
   - Does it need executable scripts, or are instructions enough?
   - Is it cross-agent (Claude Code + Codex + Cursor) or Claude-Code-only?
2. **Pick a name** — kebab-case, verb-or-noun, unique within `skills/`. Check with `ls skills/`.
3. **Draft `skills/<name>/SKILL.md`** using the template below. Cap at ~100 lines.
4. **Add scripts only if deterministic** — see "When to add scripts".
5. **Update `README.md`** — add a one-line entry under "## Skills" pointing to the new SKILL.md.
6. **Verify** with the checklist at the bottom. Do not commit unless asked.

## SKILL.md template

```md
---
name: <kebab-case-name>
description: <Sentence 1: what it does, third person.> Use when <explicit triggers: phrases, file types, contexts>. Do NOT use <negative triggers, if topic is broad>.
---

# <name>

<One-line purpose.>

## Quick start

<Smallest working example — command or invocation.>

## Steps

1. <Numbered, imperative.>
2. <…>

## Notes

- <Hard rules: "never do X", "always Y".>
- <Argument handling, if any.>
```

## Description rules (the highest-leverage part)

The description is the *only* thing the agent sees when picking skills. Get it right.

- Max ~1024 chars; aim for 1–3 sentences.
- Third person, present tense.
- Sentence 1: concrete capability ("Search an Obsidian vault…", not "Helps with notes").
- Sentence 2: `Use when …` — list real trigger phrases, file types, or contexts.
- If the topic is broad (macOS, git, "review"), add `Do NOT use …` to suppress false positives. See `m-cli/SKILL.md` for a strong example.
- Two trigger sentences max. If you've written a *third* sentence that restates "Use when…" in new words ("This skill should be used when the user asks to…"), delete it — that restatement is the classic tell of a bloated description.
- No marketing words ("powerful", "comprehensive"). No emojis.

## When to add scripts

Add a `scripts/` subdirectory when:
- The operation is deterministic (a query, a formatter, an API call shape).
- The agent would otherwise regenerate the same code each invocation.
- Errors need explicit handling that prose can't enforce.

Then SKILL.md becomes a *menu of script invocations* with one example per command (see `youtube-transcript/` and `obsidian-vault-search/` in this repo, or agent-stuff's `web-browser`).

## Cut, don't document

A SKILL.md is a behavioral nudge loaded into context, not a human-facing README. Every line costs tokens on every invocation, so authoring is mostly *deletion*. When trimming a bloated skill, expect to cut 80–90% with no loss of capability — that ratio means the original was carrying human docs the agent never needed.

Delete on sight:
- **README sections** — Installation, Contributing, Privacy, See Also, Troubleshooting. None change what the agent does. (A human-facing `README.md` living *inside* a skill dir is this same smell — it duplicates SKILL.md for an audience the skill doesn't serve.)
- **Body sections that restate the description.** An "## Overview" or "## When to Use This Skill" that paraphrases the frontmatter is pure waste — the description is already in context when the body loads, and a paraphrase only invites drift. Delete them.
- **Transcribed CLI flags and schemas.** Defer to the source of truth: `Run <tool> --help for all flags`. Keep only the non-obvious or easily-misused flags as a short list. Replace a 20-line JSON schema with one line: `Each entry has: a, b, c`.
- **Repeated examples.** One example per concept. If the same `async/await` example fits five sections, it gets *one* home and the others cross-reference it. Ten `tool | claude --prompt "..."` variations that differ only in the prompt collapse into 2–3 *real, runnable commands* (script-over-prose applied to examples).
- **Parallel command catalogs.** Documenting `run` / `scan` / `--inline-rules` once per section triplicates them. Collapse into a single compact table or list.
- **Anything a `references/` file already holds.** If you split detail out, SKILL.md must *link* to it, not re-inline it. A long SKILL.md sitting next to a long reference means the split never happened.

Front-load the one load-bearing rule as a blunt imperative (`**Never dump raw output.** Use jq to reduce tokens.`) instead of burying it under "Tips for Better Results."

Caveat: deferring to `--help` is only safe if `--help` is complete and stable. A genuinely non-obvious or commonly-misused flag still earns its line in the body.

## When to split files

If SKILL.md would exceed ~100 lines, split:

```
skills/<name>/
  SKILL.md         # entry: triggers, quick start, steps
  REFERENCE.md     # detailed rules, long lists, edge cases
  EXAMPLES.md      # worked examples
  scripts/         # deterministic helpers
```

Link one level deep from SKILL.md (`See [REFERENCE.md](REFERENCE.md)`). Don't nest further — the agent loads files lazily and deep chains defeat that.

## Cross-agent portability

This repo is consumed via `npx skills`, which targets multiple agents.

- `allowed-tools:` in frontmatter is Claude-Code-only. Other agents ignore it. Use it when you want to constrain Claude, but don't rely on it for correctness.
- Hooks and `context: fork` are Claude-only — note in the description if a skill requires them.
- If the skill is platform-specific (macOS, local sqlite, a specific CLI), say so in sentence 1 of the description.

## Review checklist

- [ ] Name is kebab-case and unique in `skills/`.
- [ ] Description has explicit `Use when …` triggers.
- [ ] Description has `Do NOT use …` if the topic is broad.
- [ ] SKILL.md is ≤100 lines (else split into REFERENCE.md).
- [ ] No time-sensitive claims ("as of 2025…").
- [ ] Concrete examples, not abstractions.
- [ ] Scripts colocated under `scripts/` and invoked by SKILL.md, not duplicated as prose.
- [ ] No transcribed flag lists or schemas that `<tool> --help` already provides.
- [ ] No "Overview"/"When to use" body section that just restates the description.
- [ ] No content duplicated between SKILL.md and its own `references/` files.
- [ ] `README.md` updated with a one-line entry.
