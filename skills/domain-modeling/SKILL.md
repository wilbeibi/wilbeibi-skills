---
name: domain-modeling
description: Keeps a project's vocabulary and decision records honest by challenging overloaded terms against the code and recording canonical terms and hard-to-reverse decisions where the repo already keeps them. Use when a term, status, or field means two things, when naming a new concept or state, or when editing a glossary, GLOSSARY.md, or ADR. Do NOT use to interview the user about a plan (use grill-me) or to write a design doc.
---

# domain-modeling

Give each term one meaning, check that meaning against the code, and record it in the repo's existing home.

## 1. Find the home (REQUIRED)

1. Read the repo's agent guide (`AGENTS.md`, `CLAUDE.md`) for where docs live.
2. Search for an existing glossary and decision record:
   ```bash
   rg -n -i '^#+ .*(glossary|vocabulary|terminology)' -g '*.md'
   fd -H 'GLOSSARY(-MAP)?\.md|^adr$'
   ```
   Numbered decisions in design docs (`D1.`, `**D3.**`) are a decision record too.
3. Use the home you found, in its format. Create `GLOSSARY.md` or `docs/adr/` only when none exists: lazily, in the docs location the guide names.

Done when you can name the one place each new term and decision goes.

## 2. Sharpen the language

- **Probe each suspect term:** ask what it means to each reader (the code that writes it, each code path that reads it, the user). Two answers mean two concepts: propose a name for each.
- **Check the code:** when someone states how a term behaves, find the `path:line` that agrees or contradicts, and surface a contradiction at once.
- **Test the boundary** with one concrete scenario: "a `failed` row that later becomes `deleted`: is `failed` terminal?"
- **Ask naming choices as decisions.** When the canonical name is the user's call, ask it in a grill-me round.
- **Record each term when it resolves.** Do not batch them.

Done when every term the current decision uses has one recorded meaning, with its aliases under `_Avoid_`.

## 3. Record

- **Terms:** [GLOSSARY-FORMAT.md](GLOSSARY-FORMAT.md) for a new glossary. An existing glossary keeps its format.
- **Decisions:** only when hard to reverse, surprising without context, and a real tradeoff. Use [ADR-FORMAT.md](ADR-FORMAT.md), or the repo's own decision format.
- A status value is a term: define the one fact it records. If two writers set it for different reasons, it names two concepts.

## Notes

- A glossary holds terms, not specs, status, or plans.
- Ported from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), adapted to this repo's conventions and voice.
