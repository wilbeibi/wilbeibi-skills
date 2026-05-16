---
name: grill-me
description: Interview the user relentlessly about a plan or design, one question at a time, until every branch of the decision tree is resolved. Use when the user wants to stress-test a plan, pressure-test a design, asks to "grill me", or says they want their thinking challenged before implementing. Do NOT use for quick one-off questions or when the user just wants a direct answer.
---

# grill-me

Relentlessly interview the user about a plan or design until you both reach shared understanding and every open decision is resolved.

## How to run it

- Ask **one** question at a time. Wait for the answer before the next question.
- For each question, state **your recommended answer** and a one-line why.
- Walk **each branch** of the decision tree. When an answer opens new questions, follow them; resolve dependencies between decisions in order rather than jumping around.
- If a question can be answered by **exploring the codebase**, explore instead of asking.
- Keep going until no unresolved branch remains. Then summarize the agreed plan.

## Notes

- Do not soften or batch questions to "be efficient" — the value is the relentlessness. One question, one recommendation, repeat.
- Stop early only if the user explicitly says to stop or accepts all remaining recommendations at once.
- Ported from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), adapted to this repo's conventions and voice.
