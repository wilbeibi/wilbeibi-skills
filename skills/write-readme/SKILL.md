---
name: write-readme
description: Write or critique a README for an open-source project (library, CLI tool, or agent tool) using the inverted-pyramid structure — concrete value first, install second, explanation third, reference last. Use when the user asks to "write a README", "draft a README", "review my README", "improve my README", or starts a new lib/tool and needs documentation. Do NOT use for internal service docs, monorepo root READMEs, or non-public projects.
---

# write-readme

Write READMEs in the order readers ask questions: is this for me, why care, how do I start, what does it do, what if it breaks.

## Workflow

1. Gather context: problem solved, target audience, current alternatives, sharpest value/proof, and non-goals.
2. Classify once: library, CLI/tool, or agent tool. Ask if unclear.
3. Draft in inverted-pyramid order: value, install, quickstart, boundaries, reference, internals, troubleshooting.
4. Put the most common invocation or import path in the first 30 lines.
5. Use the matching template in [REFERENCE.md](REFERENCE.md) for full section shape.
6. Final pass: the first 3 sentences answer "is this for me?" and "why should I care?"

## Opening Rules

- Lead with concrete value: metric, named capability, or sharp differentiator.
- Never start with "A library/tool that..."; show the reader's outcome first.
- Name the target audience and the non-goal early.
- Claims need evidence or a methodology note.

## Agent Tools

For CLIs meant to be invoked by coding agents:

- Treat the README as the tool's function signature.
- Show exact command, required args, important flags, expected success output, and expected error shape.
- Add `Not for X` guardrails so agents avoid misuse.
- Keep the core interface scannable without expanding `<details>`.

## Non-Negotiables

- Install/quickstart before architecture.
- Limitations get their own heading, not a buried caveat.
- Broad support claims must name platforms, formats, languages, or integrations.
- Troubleshooting belongs in the README.
- Use `<details>` only for advanced config, raw data, methodology, or alternative setup.
- No marketing adjectives; use numbers, examples, and named evidence.

See [REFERENCE.md](REFERENCE.md) for templates, badge patterns, screenshot guidance, tone notes, and final-pass prompts.
