---
name: write-skill
description: Author a new agent skill in this repo following compact trigger-rich and command-first skill patterns. Use when the user asks to "write a skill", "add a skill", "create a new skill", update skill guidance, or scaffold a SKILL.md. Targets the `npx skills` layout (top-level `skills/<name>/SKILL.md`).
---

# write-skill

Create compact skills under `skills/<name>/` that load only the behavior needed at invocation time.

## Workflow

1. Clarify only missing essentials: capability, triggers, non-triggers, tool/script needs, and portability.
2. Pick a unique kebab-case name.
3. Draft `SKILL.md` as an operator card: what to run, when to run it, what output means, what traps matter.
4. Add helper files only when they remove repeated deterministic work.
5. Compress once; add one README row; do not commit unless asked.

## Template

````md
---
name: <kebab-case>
description: <Concrete capability.> Use when <real phrases, file types, tools, or contexts>. Do NOT use <negative triggers if broad>.
---

# <name>

<One-line operational contract.>

## Usage / Commands / Routing

```bash
scripts/tool_or_helper.py <arg>
```

## Notes

- <What output shape means, or how to consume it.>
- <Hard rule, setup failure, safety boundary, or common mistake.>
````

## Description

The description is the routing surface; optimize it first.

- Use 1-3 sentences, third person, present tense.
- Sentence 1 names the concrete capability.
- Sentence 2 starts with `Use when ...` and lists actual trigger phrases, file types, tools, or contexts.
- Add `Do NOT use ...` for broad domains such as review, search, docs, macOS, git, or browser work.
- Avoid marketing words, time-sensitive claims, and duplicate "this skill should be used when" phrasing.

## Body

Keep:
- runnable commands or exact workflow steps;
- setup checks that commonly block first use;
- compact output contracts;
- routing boundaries and safety pitfalls;
- one strong example per command or concept.

Delete:
- overview prose that restates the description;
- installation/contributing/privacy/troubleshooting sections unless they change agent behavior;
- copied CLI help, schemas, flag catalogs, or generated docs;
- repeated prompt examples and canned analyses;
- detail already present in README, references, or helper scripts.

## Tool Skills

- Put deterministic work in `scripts/` or the existing executable.
- Make `SKILL.md` a menu of invocations plus output shape and gotchas.
- Use `Run <tool> --help for all flags`; keep only non-obvious flags.
- Prefer 30-60 lines. If setup is long, keep the readiness check inline and move walkthroughs one hop away.

## Workflow Skills

- Keep the lens, decision order, and output contract.
- Avoid rigid full templates unless structure is the skill's core value.
- Findings should lead for review skills; summaries and praise are optional.
- Split philosophy, examples, and source notes into `REFERENCE.md`.

## Portability

This repo is consumed by multiple agents via `npx skills`. Avoid agent-specific frontmatter such as `allowed-tools:`, hooks, or `context: fork` unless the skill requires that platform and says so in the description.

## Final Check

- Name is unique kebab-case.
- Description has concrete `Use when ...` triggers and needed `Do NOT use ...` boundaries.
- `SKILL.md` is under ~100 lines, preferably 30-60 for tool wrappers.
- Helpers are invoked, not duplicated in prose.
- README has one row.
