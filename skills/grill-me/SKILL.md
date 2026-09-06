---
name: grill-me
disable-model-invocation: true
description: Interview the user one question at a time until a plan is resolved, capturing durable decisions in CONTEXT.md or ADRs when the repo warrants it. Use when asked to "grill me," stress-test a design, or challenge assumptions before implementation.
---

# grill-me

Relentlessly interview the user about a plan or design until you both reach shared understanding and every open decision is resolved.

## How to run it

- Read the plan, linked docs, code, or local files needed to understand the topic first.
- Ask **one** question at a time. Wait for the answer before the next question.
- For each question, state **your recommended answer** and a one-line why.
- Walk **each branch** of the decision tree. When an answer opens new questions, follow them; resolve dependencies between decisions in order rather than jumping around.
- If a question can be answered by **exploring the codebase**, explore instead of asking.
- Push on fuzzy words, hidden assumptions, edge cases, dependencies between decisions, and reversibility.
- Keep going until no unresolved branch remains. Then summarize the agreed plan.

## Question patterns

- "What outcome would make this change a success?"
- "Which existing concept owns this behavior?"
- "What is the smallest scenario that proves the design works?"
- "What breaks if this assumption is false?"
- "What would a future maintainer be tempted to change back?"
- "Which term should be canonical, and which aliases should be avoided?"

## Capturing decisions

Only when the repo already keeps `CONTEXT.md`, `CONTEXT-MAP.md`, or `docs/adr/`, or the interview resolves terminology or a decision worth outliving the conversation. Check for those files before proposing new ones.

- Update the appropriate `CONTEXT.md` as soon as terminology is resolved — it is a glossary and relationship map for project-specific language, not a spec or scratchpad.
- Use `CONTEXT-MAP.md` only when the repository has multiple bounded contexts.
- Offer an ADR only for decisions that are hard to reverse, surprising without context, and based on a real tradeoff.
- Create docs lazily: no `CONTEXT.md` or `docs/adr/` until there is real resolved content, and keep them short enough that future agents actually read them.

For glossary format, read [CONTEXT-FORMAT.md](CONTEXT-FORMAT.md). For ADR format and thresholds, read [ADR-FORMAT.md](ADR-FORMAT.md).

## Notes

- Do not soften or batch questions to "be efficient" — the value is the relentlessness. One question, one recommendation, repeat.
- Stop early only if the user explicitly says to stop or accepts all remaining recommendations at once.
- Ported from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), adapted to this repo's conventions and voice.
