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
- No marketing words ("powerful", "comprehensive"). No emojis.

## When to add scripts

Add a `scripts/` subdirectory when:
- The operation is deterministic (a query, a formatter, an API call shape).
- The agent would otherwise regenerate the same code each invocation.
- Errors need explicit handling that prose can't enforce.

Then SKILL.md becomes a *menu of script invocations* with one example per command (see `youtube-transcript/` and `obsidian-vault-search/` in this repo, or agent-stuff's `web-browser`).

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
- [ ] `README.md` updated with a one-line entry.
