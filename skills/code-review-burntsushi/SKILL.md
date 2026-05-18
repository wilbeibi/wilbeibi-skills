---
name: code-review-burntsushi
description: Review code through BurntSushi's "honest machinery" lens — asking whether APIs, invariants, error contracts, performance boundaries, and defaults accurately represent reality. Use when reviewing library APIs, patches that change complexity or cost, dependency additions, or when the user asks "is this API honest?", "will this panic?", "is the cost visible?", "does this scale?", or "are the defaults right?". Works across languages; see REFERENCE.md for Rust-specific elaborations. Do NOT use for deletion/anti-bloat review (use code-review-russ-cox) or product-vs-library tradeoffs (use code-review-mitsuhiko).
---

# code-review-burntsushi

> "Is there a reasonable expectation that the code will behave as advertised?" — BurntSushi

A code review should ask: is this code *honest* about its invariants, failure modes, costs, and semantics? Not just: does it work?

## Quick start

Paste a diff or file and say "burntsushi review" or "honest review". Walk the ten general axes in [REFERENCE.md](REFERENCE.md), add the two Rust-specific axes if the code is Rust, then emit findings.

## Steps

1. **State the change** — what is this patch doing in one sentence? If unclear, ask first.
2. **Walk all ten general axes** from [REFERENCE.md](REFERENCE.md) in order. Flag every axis with a finding.
3. **If Rust:** also apply the two Rust-specific axes (encoding invariants, ownership/allocation).
4. **Emit findings** in the output format below.

## Output format

```
## Summary
<one paragraph: overall verdict and the single most important honesty gap>

## Must fix
- [Axis N | file:line] <finding — name the invariant, cost, or failure mode>.
  Suggestion: <one concrete alternative>.

## Consider
- [Axis N | file:line] <finding>.
  Tradeoff: <what's gained vs. lost>.

## Praise
- <what is genuinely honest — name it specifically>

## Open questions
- <anything needing author context before a final call>
```

## Tone rules

- Name the invariant, failure mode, or hidden cost precisely.
- Suggest one practical alternative per finding.
- Do not nitpick style, naming, or formatting unless it obscures correctness or cost.
- Do not complain about `unwrap`/assertions on static programmer invariants — only flag panics when the failure source is runtime/user/environment.

## Reference

- [REFERENCE.md](REFERENCE.md) — all axes with examples, model comments, and skill rules.
