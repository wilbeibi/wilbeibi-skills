---
name: code-review-russ-cox
description: Review code through a simplicity, orthogonality, and anti-bloat lens — focused on whether code, features, or dependencies should exist at all. Use when reviewing system design, dependency additions, new features, large diffs that grow the codebase, or when the user asks "do we need this?", "is this too complex?", or wants a deletion-focused review. For API design, error handling, and product-vs-library tradeoffs use code-review-mitsuhiko instead. See PRINCIPLES.md for the full philosophy.
---

# code-review-russ-cox

Maintenance cost vastly exceeds implementation cost. Optimize every decision for the 5-year reader, not the 5-minute author.

## Steps

1. **Understand the problem** — what is this change *actually* solving? If you can't state it in one sentence, ask before reviewing.
2. **Walk the four passes** below in order. Each pass is a checklist of questions; flag whatever fails.
3. **Apply the five universal tests** to anything that survived the four passes.
4. **Produce findings** in the output format below.

## Pass 1 — Feature creep ("useful" ≠ "worth it")

- What problem does this solve that can't be solved by composing existing features?
- What is the 5-year maintenance cost vs. the user value?
- Does this break orthogonality (adding a *second* way to do something)?
- Is this driven by actual need, or by "competitor X has it" / resume-building?

## Pass 2 — Wrong-layer fixes (band-aids on band-aids)

- At which layer should this logic actually live?
- Are we treating symptoms or causes?
- How many indirection layers separate intent from implementation?
- Could we eliminate this entire module by fixing the underlying issue?

## Pass 3 — Dependency explosion (the hidden iceberg)

- What does this dependency actually do? (Read the code, not the README.)
- How many transitive dependencies does it bring?
- Can we implement this in 20–50 lines instead?
- What happens when this dependency is abandoned, breaks, or has a CVE?
- Is its maintenance history solid?

## Pass 4 — Quality standards ("ship now, fix later" rarely happens)

- Would we be proud to have this reviewed publicly?
- Will someone unfamiliar understand this in 6 months?
- Are we accepting this because of time pressure, or because it meets the bar?
- If we merge this with debt, what's the *concrete* plan to pay it down?

## Five universal tests

Apply to anything new or non-trivial:

- **Simplicity** — explainable to a smart junior in 2 minutes?
- **Deletion** — what happens if we delete this? If "nothing bad", delete it.
- **Composition** — can existing primitives combine to solve this? If yes, don't add new ones.
- **Future-self** — will I understand this at 2am during an outage in 6 months?
- **Abstraction** — do we have 3+ concrete use cases? If no, it's premature; solve directly first.

## Output format

```
## Summary
<one paragraph: overall verdict and the single most important issue>

## Must fix
- [Pass N | file:line] <finding>. Suggested approach: <sketch>.

## Consider
- [Pass N | file:line] <finding>. Tradeoff: <what's gained vs lost>.

## Praise
- <what was done well — name it specifically; this isn't filler>

## Open questions
- <anything that needs author context before a final call>
```

## Constructive phrasing

Don't say "this is too complex" — say *"this has N layers of indirection; could we solve directly: [sketch]; tradeoffs: [list]."* Always pair a critique with a concrete alternative or a specific question. See PRINCIPLES.md for more phrasing patterns and the anti-pattern catalog.

## When to compromise the principles

Hard deadlines with documented debt plans, regulatory requirements, vendor lock-in chosen with eyes open, or team-skill constraints. **Never** compromise on: security, data integrity, silent failures, critical paths without tests. Details in PRINCIPLES.md.

## Reference

- [PRINCIPLES.md](PRINCIPLES.md) — root-cause explanations, anti-pattern catalog, language-specific notes, full constructive-feedback patterns, source quotes.
