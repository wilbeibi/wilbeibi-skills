---
name: write-readme
description: Write or critique a README for an open-source project (library, CLI tool, or agent tool) using the inverted-pyramid structure — concrete value first, install second, explanation third, reference last. Use when the user asks to "write a README", "draft a README", "review my README", "improve my README", or starts a new lib/tool and needs documentation. Do NOT use for internal service docs, monorepo root READMEs, or non-public projects.
---

# write-readme

Produce a README that answers the reader's questions in the order they actually ask them: *is this for me? → why care? → how to install → what it does → what if it breaks.*

## Quick start

Ask one question, then draft:

> "Is this a **library** (imported as a dependency), a **tool/CLI** (run directly), or an **agent tool** (a CLI that coding agents invoke via bash)?"

The answer changes the lead section and the template. See [REFERENCE.md](REFERENCE.md) for full templates.

## Steps

1. **Classify** — lib, tool, or agent tool? When unclear, ask. This determines the reader's first question and the README's opening frame.

   - **Agent tools** have a dual audience: the human who installs it, *and* the coding agent who reads the README on demand to learn the interface. The README is the agent's tool description — it must be scannable by both.

2. **Nail the opening** — the title plus first 3 sentences must answer two questions the reader asks immediately: (a) "Did the author write this for someone like me?" and (b) "How will I benefit from reading it?" If you're in paragraph two and haven't answered both, you're in trouble.

3. **Find the lead metric** — one line of concrete numbers before any prose description. If the project has no benchmark yet, use the sharpest qualitative differentiator ("zero dependencies", "100% local", "single binary", "one command"). Never lead with "A library that…"

   Then find the **domain trust signal**: the one anxiety your tool's category triggers in readers. Data tools: "does this phone home?" → answer with "100% local". Build tools: "will this break my pipeline?" → answer with "reproducible, hermetic". Agent tools: "will this silently corrupt my repo?" → show a diff or dry-run flag. Surface the trust signal in the opening, not in a footnote.

4. **Draft in inverted-pyramid order** — most newsworthy first, reference material last. A reader who stops after two sections should still have a complete, useful picture. For agent tools, the most common invocation must be visible within the first 30 lines — the agent scans top-down for the command signature.

5. **Apply the matching template** from [REFERENCE.md](REFERENCE.md). Fill every section; delete a section only if it truly has nothing to say (not to save space).

   - For agent tools: follow the CLI template with additions from the agent tool guidance — explicit flags table, expected output format, and "Not for X" warnings the agent can use to avoid misuse.

6. **Final pass** — re-read the opening. Does it answer "Is this for me?" and "How will I benefit?" in the first 3 sentences? For agent tools, can an agent find the invocation and expected output in a 3-second scan? See [REFERENCE.md](REFERENCE.md) for the final pass prompts.

## Non-negotiables

- Install/quickstart comes **before** the explanation of why it works.
- Benchmarks and capability claims need a methodology note — even one sentence. Claims without method are marketing.
- Admit where the tool **doesn't** help — and give it a **heading**, not a parenthetical. A named limitation ("Estimate Accuracy", "Not for X") reads as honest engineering; a buried caveat reads as defensive marketing. For agent tools, limitations prevent the agent from using the tool for the wrong job — they're functional guardrails, not just honesty.
- When claiming broad support (platforms, formats, languages, integrations), **name the things**: list them explicitly. "Supports 15+ tools" is a count; "Claude Code, Codex, Cursor…" is evidence.
- Troubleshooting lives in the README, not "open an issue".
- `<details>` for depth: advanced config, raw data, alternative setup. The happy path must be scannable without expanding anything.
- **Agent tools**: invocation must be unambiguous — every flag, every argument, every expected output format must be explicit. Agents cannot infer defaults. The README *is* the tool's function signature.
- No marketing adjectives ("powerful", "blazing", "comprehensive", "robust"). Let numbers and named evidence do the convincing. Treat dev tools like consumer products — first impression coherence beats feature count.

## Tone rules

From the vault's writing notes (Lynch, Dia, Dax Raad):

- **Features → benefits**: not "we added X" but "you can now do Y." Speak directly to the reader.
- **Own your mistakes fast**: one crisp paragraph of limitations builds more trust than pages of triumphs.
- **One degree bigger**: can a sentence or two broaden the audience from "Go developers using PostgreSQL" to "backend developers"? Small tweaks, order-of-magnitude reach.
- **Don't bury answers in `<details>`**: the happy path must work without expanding anything. Use `<details>` only for raw data, alternative setups, or contributor notes.
- **Hook → roadmap → confession → evidence → ask**: the Dia letter's structure maps directly to a README. Lead with the tension, show the path, admit the limits, prove the claims, tell them what to do next.

See [REFERENCE.md](REFERENCE.md) for templates, badge patterns, screenshot guidance, and the final pass prompts.
