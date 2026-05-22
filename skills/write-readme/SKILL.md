---
name: write-readme
description: Write or critique a README for an open-source project (library or CLI tool) using the inverted-pyramid structure — concrete value first, install second, explanation third, reference last. Use when the user asks to "write a README", "draft a README", "review my README", "improve my README", or starts a new lib/tool and needs documentation. Do NOT use for internal service docs, monorepo root READMEs, or non-public projects.
---

# write-readme

Produce a README that answers the reader's questions in the order they actually ask them: *why care → how to install → what it does → how it works → what if it breaks.*

## Quick start

Ask one question, then draft:

> "Is this a **library** (imported as a dependency) or a **tool/CLI** (run directly)?"

The answer changes the lead section and the template. See [REFERENCE.md](REFERENCE.md) for full templates.

## Steps

1. **Classify** — lib or tool? When unclear, ask. This determines the reader's first question and the README's opening frame.

2. **Find the lead metric** — one line of concrete numbers before any prose description. If the project has no benchmark yet, use the sharpest qualitative differentiator ("zero dependencies", "100% local", "single binary"). Never lead with "A library that…"

3. **Draft in inverted-pyramid order** — most newsworthy first, reference material last. A reader who stops after two sections should still have a complete, useful picture.

4. **Apply the matching template** from [REFERENCE.md](REFERENCE.md). Fill every section; delete a section only if it truly has nothing to say (not to save space).

5. **Run the checklist** at the bottom of [REFERENCE.md](REFERENCE.md) before handing off.

## Non-negotiables

- Install/quickstart comes **before** the explanation of why it works.
- Benchmarks and capability claims need a methodology note — even one sentence. Claims without method are marketing.
- Admit where the tool **doesn't** help. Readers trust bounded claims.
- Troubleshooting lives in the README, not "open an issue".
- `<details>` for depth: advanced config, raw data, alternative setup. The happy path must be scannable without expanding anything.

See [REFERENCE.md](REFERENCE.md) for templates, badge patterns, and the full checklist.
