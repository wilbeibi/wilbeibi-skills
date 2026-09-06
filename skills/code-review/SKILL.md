---
name: code-review
description: Review a diff, package, or API through one of five lenses (necessity and layering, honest invariants and costs, product-versus-library fit, a complexity gate before a design change, or newcomer clarity). Use when asked to review, audit, or polish code, vet a dependency, judge whether a change is too complex, or find what a new hire would not understand.
---

# code-review

State the problem the code solves in one sentence before reviewing anything. If you cannot, ask — a review of code whose purpose you have guessed at is worse than no review.

Then pick **one** lens and read only that file (`/code-review <lens>` names it directly). They are different methods, not different vocabularies for the same method; running two produces findings that contradict each other on priority.

| The question in front of you | Lens | Read |
|---|---|---|
| Should this exist at all? Is it at the right layer? Does the diff/package/dependency earn its maintenance cost? Asked to "audit", "polish", or "refactor" something | **Russ Cox** | [RUSS-COX.md](RUSS-COX.md) |
| Will it behave as advertised? Can it panic, silently truncate, or cost more than it looks? Are the defaults and error contracts honest? Reviewing a library API or a patch that changes complexity | **BurntSushi** | [BURNTSUSHI.md](BURNTSUSHI.md) |
| Is this being held to the right standard? Should the dumb version ship, or does this need to stay stable for years? Reviewing a public interface, a breaking change, or product code that looks over-engineered | **Mitsuhiko** | [MITSUHIKO.md](MITSUHIKO.md) |
| Is a *proposed* change worth its complexity, and which layer owns it? Asked before a substantial design change, or when necessity is contested mid-review | **Complexity** | [COMPLEXITY.md](COMPLEXITY.md) |
| What would a competent engineer who just joined fail to understand? Asked for an onboarding review, a handover check, or what to document first | **Newcomer** | [NEWCOMER.md](NEWCOMER.md) |

Default to **Russ Cox** for an unqualified "review this diff." Reach for the others when the code is a library boundary (BurntSushi), when the product/library call is itself in question (Mitsuhiko), when the change does not exist yet (Complexity), or when the question is comprehension rather than correctness (Newcomer). The Complexity and Newcomer lenses are for explicit requests, not a ceremony before routine edits.

In an established codebase, search for existing primitives before judging anything new — under any lens, the most common real finding is that a helper, interface, or package already does this.

Not this skill: writing the commit or PR message (use `write-docs`) or building your own understanding of an unfamiliar codebase (use `grok-repo`).

## Output contract — all lenses

The Complexity lens reports decisions and unresolved tradeoffs rather than findings, and the Newcomer lens uses its own contract (see its file); everything else below applies to them too.

Analyze freely first. This contract governs the final output only — do not begin emitting findings before you have read enough to know which ones matter.

Each finding is one block, most-consequential first:

```
[file:line] <one-line claim — traced | inferred>
  Failure: <concrete inputs or state> → <wrong output, crash, or cost>
  Instead: <one alternative, sketched>
```

- **The failure line is the filter.** A finding that cannot name concrete inputs producing concrete wrong behavior is not a finding — drop it rather than softening it into a suggestion.
- Say `traced` when you followed the path, `inferred` when you reasoned from shape. Never blur the two.
- Sketch the alternative; do not merely point at the problem.
- Close with one line naming what you checked and found sound — coverage, not praise, so the reader knows what the silence covers — then a brief `Summary`.
- Do not nitpick style, naming, or formatting unless it obscures correctness or cost.
- Report only what you found. Never pad toward a count, per axis, per dimension, or per section — a short review of a clean change is the correct output.

## Accepting a compromise — all lenses

When the author answers a finding with "I know, but we ship Friday," the reviewer still has to rule.

- **Legitimate**: hard deadlines paired with a documented debt plan; regulatory or compliance requirements; vendor lock-in chosen with eyes open; team-skill constraints paired with training.
- **How to accept one**: document the decision in the code, write a dated paydown plan, minimize the scope of the shortcut, and set a review date. An accepted compromise with no paydown trigger is just a defect with better manners.
- **Never**: security vulnerabilities, data-integrity risks, silent failures, or untested critical paths. These do not have a legitimate deadline exception — say so plainly and leave them ranked at the top.

## Phrasing

Findings land when they carry the analysis, not the verdict. Applies under every lens.

- Instead of "This is too complex": "This has N layers of indirection. Could we solve directly: [sketch]. Benefits: [list]. Tradeoffs: [list]."
- Instead of "Don't add this dependency": "This adds N transitive deps. Alternative: [stdlib / 20 lines]. The simpler approach wins here because [reason]."
- Instead of "This abstraction is wrong": "We have 1 use case; suggest solving directly now and abstracting when the pattern emerges (3+ uses)."
- Instead of "Rewrite this": "Current approach: [analysis]. Maintenance implications: [list]. Alternative: [sketch]. Which fits our long-term goals?"
