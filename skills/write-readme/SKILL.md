---
name: write-readme
description: Write or critique a README for an open-source project (library, CLI tool, or agent tool) with an impatient-reader lens: concrete value first, shortest path to use, no duplicated claims, and reference material only when it earns space. Use when the user asks to "write a README", "draft a README", "review my README", "improve my README", or starts a new lib/tool and needs documentation. Do NOT use for internal service docs, monorepo root READMEs, or non-public projects.
---

# write-readme

Write READMEs for readers with short attention: what is it, when do I use it, how do I start, what should I not expect.

## Workflow

1. Gather context: problem solved, target audience, current alternatives, sharpest value/proof, and non-goals.
2. Classify once: library, CLI/tool, or agent tool. Ask if unclear.
3. Cut before adding: remove duplicated inventories, badge noise, marketing claims, and copied `--help` tables.
4. Draft in inverted-pyramid order: plain value, install, common use, boundaries, then optional reference.
5. Put the most common invocation or import path in the first 30 lines.
6. Use [REFERENCE.md](REFERENCE.md) only for section choices, not as a required template.
7. Final pass: every line must answer a likely reader question or change their next action.

## Opening Rules

- Lead with concrete value: metric, named capability, or sharp differentiator.
- Never start with "A library/tool that..."; show the reader's outcome first.
- Name the target audience and the non-goal early.
- Claims need evidence or a methodology note.
- Be genuine. Avoid ad-copy words like "seamless", "instant", "powerful", and "no re-explaining" unless the README proves them.

## Ruthless Cut Pass

Delete or compress:

- Repeated supported-platform or integration lists. Name them once, where they affect command syntax or installation.
- Full flag/reference tables when `--help`, generated docs, or package docs already cover them.
- Badges that do not affect trust or installation decisions.
- Separate "What it does", "Features", and "Why" sections that restate the same sentence.
- Long caveats. Keep boundaries, but write them as short operational facts.

## Agent Tools

For CLIs meant to be invoked by coding agents:

- Treat the README as the tool's function signature.
- Show exact command shape, required args, important flags, and expected success/error shape when that output helps the agent verify work.
- Add `Not for X` guardrails so agents avoid misuse.
- Keep the core interface scannable without expanding `<details>`.

## Non-Negotiables

- Install/quickstart before architecture.
- Limitations get their own heading, not a buried caveat.
- Broad support claims must name platforms, formats, languages, or integrations.
- Troubleshooting belongs in the README only when the failure is common and actionable.
- Use `<details>` only for advanced config, raw data, methodology, or alternative setup.
- No marketing adjectives; use numbers, examples, and named evidence.

See [REFERENCE.md](REFERENCE.md) for templates, badge patterns, screenshot guidance, tone notes, and final-pass prompts.
