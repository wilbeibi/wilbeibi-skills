---
name: code-review
description: Review a diff, package, or API through one of five lenses — necessity and layering (Russ Cox), honest invariants and costs (BurntSushi), product-versus-library fit (Mitsuhiko), a complexity gate before a design change, or newcomer clarity. Use when asked to review, audit, or polish code, vet a dependency, judge whether a change is too complex, or find what a new hire would not understand.
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

## Measure before judging

A model's opinion of how verbose or tangled code is is close to noise (the same judge flips on renamed inputs), so do not form one. Measure instead, then spend judgment only where the measurement points. Run this when the diff was written by an agent, exceeds ~100 lines, or you are in audit mode:

```
python3 scripts/slop.py [BASE] [--scope DIR] [--all]   # working tree vs BASE: HEAD for uncommitted work, main for a branch
```

It wraps [scb-check](https://github.com/gabeorlanski/scb-check) (SlopCodeBench's tool; Python, Rust, JS, TS, Zig, Haskell, C++) and prints: line delta; base-to-head counts for the changed files (functions over cyclomatic complexity 10, clone lines, flagged lines, erosion and verbosity ratios); and every clone, complexity, or slop-rule hit that lands on a touched line, as `file:line`. Cross-repo clones need the full scan; if scb-check aborts on a file it cannot parse, the script says so and falls back to the changed files. For Go, Java, C#, Swift, Kotlin, Ruby, PHP and C it uses [lizard](https://github.com/terryyin/lizard) instead: same complexity metric, a weaker token-level clone detector, no slop rules. Lizard's ratios are comparable to the same repo's history, not to scb-check's reference points below.

Reading the output:

- Every line is a lead, not a finding. Open the code. A 10-line function with complexity 15 is dense, not sloppy; a 40-line one with three branches that each re-derive the same state is the finding, and the number is only its evidence.
- Ratios are meaningful for a package, not a diff. On a small diff report the counts and locations; in audit mode use the package ratios as the refactor plan's baseline. SlopCodeBench's reference points: established repos average verbosity 0.15 and erosion 0.31, agent output roughly double both.
- Clone hits are the mechanical form of the "existing primitive" search above. The finding is the pair that will diverge, named on both sides.
- Slop accumulates across sessions because each agent run, reviewer included, starts without memory of the last. The base-to-head counts are the only view of that drift you get; when a package's numbers only ever rise, say so in the summary even if no single hit is a finding.

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
- Never emit a numeric quality score or grade, under any lens. Scores are where a model judge is least reliable, and once fed back to the author they become the target.
- A finding must survive renaming every identifier in the diff. If it would vanish, it was about vocabulary, not structure — drop it. (Newcomer is the exception; its subject is names and context.)
- A measurement (complexity, clone size, line count) may appear only in the `Failure` line as evidence. The claim names the tangle or divergence the number points at. "Complexity 18" is not a finding; "three branches each re-derive `refresh`, so changing one silently leaves two behind" is. This is what keeps a threshold from being gamed by splitting a function into fragments that share the same knot.

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
