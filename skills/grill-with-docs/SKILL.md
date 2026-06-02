---
name: grill-with-docs
description: Run a rigorous planning interview that stress-tests a user's idea against the codebase, sharpens project terminology, and captures durable context in lightweight docs. Use when the user says "grill me", "grill me with docs", "stress-test this plan", "interview me on this design", or asks to turn a discussion into CONTEXT.md glossary entries or ADRs. Do NOT use for ordinary summaries, code review, or documentation-only cleanup when no interactive interrogation is requested.
---

# grill-with-docs

Interview the user one question at a time until the plan, terminology, and important decisions are clear enough to act on.

## Workflow

1. Read the user's plan, linked docs, code, or local files needed to understand the topic.
2. Look for existing `CONTEXT.md`, `CONTEXT-MAP.md`, and `docs/adr/` files before proposing new docs.
3. Ask one focused question at a time. Wait for the answer before continuing.
4. If the answer can be discovered from the codebase or existing docs, inspect those instead of asking.
5. For each question, include your recommended answer or likely tradeoff so the user can accept, reject, or refine it.
6. Push on fuzzy words, hidden assumptions, edge cases, dependencies between decisions, and reversibility.
7. When terminology is resolved, update the appropriate `CONTEXT.md` immediately.
8. Offer an ADR only for decisions that are hard to reverse, surprising without context, and based on a real tradeoff.

## Documentation Rules

- `CONTEXT.md` is a glossary and relationship map for project-specific language, not a spec or scratchpad.
- Use `CONTEXT-MAP.md` only when the repository has multiple bounded contexts.
- Create documentation lazily: do not add `CONTEXT.md` or `docs/adr/` until there is real resolved content.
- Keep docs concise enough that future agents will actually read them.

For glossary format, read [CONTEXT-FORMAT.md](CONTEXT-FORMAT.md).
For ADR format and thresholds, read [ADR-FORMAT.md](ADR-FORMAT.md).

## Question Patterns

- "What outcome would make this change a success?"
- "Which existing concept owns this behavior?"
- "What is the smallest scenario that proves the design works?"
- "What breaks if this assumption is false?"
- "What would a future maintainer be tempted to change back?"
- "Which term should be canonical, and which aliases should be avoided?"
