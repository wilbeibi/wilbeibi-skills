---
name: code-review-russ-cox
description: Review code for simplicity, necessity, and anti-bloat — whether code, features, or dependencies should exist at all. Use when reviewing system design, dependency additions, new features, or when the user asks "do we need this?", "is this too complex?", or wants a deletion-focused review. Do NOT use for API design or product-vs-library tradeoffs (use code-review-mitsuhiko).
---

# code-review-russ-cox

Review for whether the code should exist, whether it belongs at this layer, and whether it adds more long-term cost than value.

## Steps

1. State the problem in one sentence. If you cannot, ask before reviewing.
2. Walk the four passes below.
3. Produce findings first, ordered by severity.

## Four Passes

1. **Feature creep** — Does this solve a real problem that existing pieces cannot compose? Is the 5-year maintenance cost worth the user value?
2. **Wrong layer** — Is this treating a symptom instead of fixing the layer that owns the behavior?
3. **Dependency explosion** — What does the dependency actually do, what transitive cost arrives with it, and could 20-50 lines replace it?
4. **Quality debt** — Will a new maintainer understand it in six months, and is any debt paired with a concrete paydown trigger?

## Universal Tests

- **Simplicity:** explainable to a smart junior in two minutes.
- **Deletion:** if deleting it changes nothing important, delete it.
- **Composition:** use existing primitives when they compose cleanly.
- **Future-self:** understandable during an outage.
- **Abstraction:** wait for 3 real use cases before generalizing.

## Output Contract

- Findings first: `Must fix`, `Consider`, `Open questions`; omit empty sections.
- Prefix findings with `[Pass N | file:line]`.
- Each finding states what should not exist, should move layers, or should be simplified, plus one concrete alternative.
- Add a brief `Summary` after findings. Do not add praise unless asked.

See [PRINCIPLES.md](PRINCIPLES.md) for the full anti-bloat catalog and phrasing patterns.
