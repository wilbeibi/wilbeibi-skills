---
name: write-skill
description: Author a new agent skill in this repo following progressive-disclosure, trigger-rich-description, and script-over-prose principles. Use when the user asks to "write a skill", "add a skill", "create a new skill", or scaffold a SKILL.md. Targets the `npx skills` layout (top-level `skills/<name>/SKILL.md`).
---

# write-skill

Create compact agent skills under `skills/<name>/` that load only the behavior an agent needs.

## Steps

1. **Clarify once** — ask only for missing essentials: capability, triggers, negative triggers, scripts, and portability.
2. **Pick a name** — kebab-case, verb-or-noun, unique within `skills/`.
3. **Draft `skills/<name>/SKILL.md`** with only sections that change agent behavior.
4. **Add scripts only when deterministic** — repeated queries, formatters, API calls, validators, or error-prone command sequences belong in `scripts/`.
5. **Compress once** — reread the draft as per-invocation context. Cut until only triggers, commands, contracts, and pitfalls remain.
6. **Update `README.md`** with one line under "## Skills"; do not commit unless asked.

## Minimal Template

````md
---
name: <kebab-case-name>
description: <Concrete capability.> Use when <real trigger phrases, file types, or contexts>. Do NOT use <negative triggers if broad>.
---

# <name>

<One-line operational contract.>

## Steps / Commands / Usage Patterns

1. <Imperative step, or one real command/pattern.>
2. <Next behavior the agent must perform.>

## Notes

- <Hard rule, common pitfall, or argument convention.>
````

Omit empty sections. Rename sections to match the behavior: `Commands`, `Output Format`, `Usage Patterns`, `Review Lens`, or `Routing`.

## Description Rules

The description is the only thing the agent sees when picking skills.

- Aim for 1-3 sentences and stay under ~1024 chars.
- Use third person, present tense.
- Sentence 1 names the concrete capability, not a vague benefit.
- Sentence 2 starts with `Use when ...` and lists actual phrases, file types, or contexts.
- Add `Do NOT use ...` for broad domains such as macOS, git, review, search, or docs.
- Delete duplicate trigger sentences such as "This skill should be used when..."
- No marketing words, emojis, or time-sensitive claims.

## Content Rules

`SKILL.md` is a behavioral nudge loaded into context, not a README. The test: does the shorter file work just as well with fewer tokens?

Keep:
- Trigger description and routing boundaries.
- Critical flags or arguments that are easy to misuse.
- Compact input/output contracts.
- Reusable primitives: filter, count, group, inspect metadata, validate output.

Delete:
- Overview, Installation, Contributing, Privacy, See Also, and Troubleshooting sections unless they directly change agent behavior.
- Body sections that restate the description.
- Full CLI help, JSON schemas, API schemas, or flag catalogs; say `Run <tool> --help for all flags` and keep only non-obvious flags.
- Repeated examples and canned analysis prompts that only vary user wording.
- Content duplicated from `references/`, `README.md`, or generated docs.

For CLI-wrapper skills, prefer 40-60 lines. For broader workflows, stay under ~100 lines or split details into one-hop `REFERENCE.md`, `EXAMPLES.md`, or `scripts/` files linked from `SKILL.md`.

## Scripts

Add scripts when prose would make the agent regenerate deterministic code:
- local-data queries;
- formatters, converters, or API request shapes;
- validators, token reducers, or brittle shell pipelines.

Then `SKILL.md` becomes a menu of script invocations with one runnable example per command.

## Portability

This repo is consumed via `npx skills` by multiple agents. `allowed-tools:`, hooks, and `context: fork` are Claude-only; say so if required. If platform-specific, say so in sentence 1.

## Review Checklist

- [ ] Name is kebab-case and unique in `skills/`.
- [ ] Description has concrete `Use when ...` triggers.
- [ ] Broad topics include `Do NOT use ...` boundaries.
- [ ] `SKILL.md` is under ~100 lines, or details are split one hop away.
- [ ] Examples are reusable primitives, not canned prompts.
- [ ] Scripts are invoked from `SKILL.md`, not duplicated as prose.
- [ ] No copied help text, schemas, README sections, or description restatement.
- [ ] `README.md` has a one-line entry.
