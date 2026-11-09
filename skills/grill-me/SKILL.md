---
name: grill-me
description: Resolves the open decisions of a plan or design with the user in short rounds of numbered questions, each with its context, options, and a recommended answer. Use when asked to "grill me" or stress-test a design, or when a plan has two or more open decisions only the user can make, including from karpathy-planning, state-prototype, or domain-modeling. Do NOT use for one quick clarifying question, or to collect comments on a long document (use readback).
---

# grill-me

Resolve a plan's open decisions with the user. Each question carries the context needed to answer it without opening anything else.

## Before the first round

1. Read the plan, its linked docs, and the code. Find every fact yourself, delegating to a fresh-context helper when the harness has one. Never ask the user for a fact you can look up.
2. Map the decisions as a tree: each decision and the decisions that depend on it. The frontier is every decision whose prerequisites are settled.

Done when every frontier item is a decision, not a fact.

## Each round

Ask at most three frontier questions, the most consequential first. The rest wait for the next round. Use this shape (every slot REQUIRED):

```md
**Q1. <the decision, in a few words>**
Context: what this decides, where it shows up (`path:line`, doc, or issue with a few words on what it is), and what is true today. Two or three sentences.
Options: A: <choice and its main cost>. B: <choice and its main cost>.
Recommend: B, because <one line>. "yes" accepts it.
```

- Explain every label on first use: issue numbers, decision ids, phases, acronyms.
- Reply in the user's language and keep code identifiers as they are.
- Wait for the answers, then recompute the frontier. A question that depends on a still-open answer waits for a later round.

Done when each answer maps to exactly one decision.

## Finish

1. Stop when the frontier is empty or the user accepts the remaining recommendations.
2. Summarize the decisions as one list, plus the branches deferred for later.
3. Record resolved terms and hard-to-reverse decisions with the domain-modeling skill.
4. If the work was not already authorized, wait for the user to confirm the summary before acting.

## Notes

- Ported from [mattpocock/skills](https://github.com/mattpocock/skills) `grilling` (MIT). Adapted: a required context slot, rounds of at most three, and the user's language.
