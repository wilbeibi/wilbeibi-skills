# code-review-russ-cox — Principles

The full philosophy behind the four-pass checklist in `SKILL.md`. Load this when you need to justify a finding, explain a principle to the author, or decide an edge case.

## Core philosophy

**Maintenance cost vastly exceeds implementation cost.** Every decision optimizes for long-term sustainability, not short-term convenience.

**Orthogonality**: features should be basis vectors in a high-dimensional space — covering the problem space efficiently, interacting predictably when combined, avoiding redundant paths to the same solution.

**Simplicity is complicated.** Simple solutions require *more* thought than complex ones. The goal is to make the problem simpler, not just move complexity around.

## The four root causes of bloat

### 1. Feature creep — the "useful" fallacy

A feature can be useful but still not worth its permanent maintenance burden.

**Red flags**: nice-to-haves without clear ROI; duplicate functionality with different syntax; features added for resume building or promotion; solutions looking for problems.

**Good patterns**: small composable primitives that combine powerfully; features that enable new capabilities rather than replicate old ones; clear value proposition exceeding long-term cost; willingness to say "no" to reasonable requests.

### 2. Wrong-layer fixes — the wrapping trap

When facing a problem, we often patch at a higher layer instead of fixing the root cause at the correct layer.

**Red flags**: wrapper functions that only forward to other wrappers; "adapter"/"bridge" patterns without clear architectural boundaries; needing to modify 5+ files to change one behavior; error handling scattered across abstraction levels.

**Good patterns**: fix at the source, not the symptoms; minimal layers between problem and solution; clear ownership at each layer; each abstraction earns its keep.

**Worked example**: instead of wrapping validation errors three layers up, add proper constraints at the data layer and validation at the input boundary.

### 3. Dependency explosion — the hidden iceberg

Every dependency brings its own dependencies. You're responsible for maintaining all of them.

**Red flags**: "left-pad syndrome" (huge dep for a tiny utility); dependencies with their own complex trees; unmaintained libraries (no commits in 2+ years); deps that depend on multiple competing libraries; choosing by download count rather than code quality.

**Good patterns**: default to standard library / language primitives; implement simple functionality directly; audit the full transitive tree before adding; prefer deps with minimal transitive deps; document why each dependency is necessary.

**Dependency audit checklist**:
- [ ] Reviewed transitive dependency tree
- [ ] Verified active maintenance
- [ ] Confirmed no simpler alternative
- [ ] Understood security implications
- [ ] Documented cost-benefit decision

### 4. Low quality standards — the technical-debt lie

"We'll clean this up later" almost never happens. Debt compounds with interest.

**Red flags**: "works on my machine"; complex logic without explanation; missing or superficial tests; clever tricks requiring domain expertise to understand; comments explaining *what* code does instead of *why*.

**Good patterns**: code is merge-ready before review, not "almost there"; clarity over cleverness, always; self-documenting code with comments explaining "why"; comprehensive tests that document behavior; refusal to merge until the bar is met.

## Constructive feedback patterns

**Instead of**: "This is too complex."
**Say**: "This has N layers of indirection. Could we solve directly: [sketch]. Benefits: [list]. Tradeoffs: [list]."

**Instead of**: "Don't add this dependency."
**Say**: "This adds N transitive deps. Alternative: [stdlib / 20 lines]. For our use case, the simpler approach wins because [reason]."

**Instead of**: "This abstraction is wrong."
**Say**: "We have 1 use case; this adds abstraction for future needs. Suggest: solve directly now, abstract when the pattern emerges (3+ uses)."

**Instead of**: "Rewrite this."
**Say**: "Current approach: [analysis]. Maintenance implications: [list]. Alternative: [sketch]. Which approach better fits our long-term goals?"

## Anti-pattern catalog

- **Kitchen sink** — adding features "because we might need them someday". Solution: YAGNI.
- **Golden hammer** — using a familiar pattern even when inappropriate. Solution: choose tools by problem, not familiarity.
- **Framework fever** — adopting heavyweight frameworks for simple problems. Solution: prefer libraries to frameworks; compose, don't adopt.
- **Perfect system** — over-engineering for hypothetical scale. Solution: build for 10× current scale, not 1000×.
- **Busy work** — changes that grow the codebase without proportional value. Solution: measure value by code deleted, not added.

## When to compromise the principles

**Legitimate reasons**: hard business deadlines with a documented debt plan; regulatory/compliance requirements (GDPR, accessibility, security certs); vendor lock-in chosen with eyes open; team-skill constraints (paired with training investment).

**How to compromise well**: document the decision and reasoning explicitly; write a concrete plan to address the debt with dates; minimize the scope of the compromise; review quarterly.

**Never compromise on**: security vulnerabilities, data integrity, silent failures, critical paths without tests.

## Language-specific notes

The philosophy is universal; tactics vary per ecosystem.

- **Go** — strong stdlib, explicit error handling, small interfaces, composition over inheritance.
- **Python** — rich stdlib, avoid Django for simple needs, prefer composition, type hints for clarity.
- **JavaScript/TypeScript** — beware npm dependency explosion, prefer standard APIs, TypeScript for maintainability.
- **Rust** — strong stdlib, cargo minimizes dep pain but still audit trees, zero-cost abstractions are fine.
- **Java** — rich JDK, avoid framework soup (Spring for everything), prefer simple servlets for simple needs.
- **C/C++** — minimal dependencies by culture, STL/standard library first; avoid NIH but also avoid dependency hell.

## Source quotes

> "A little copying is better than a little dependency." — Go Proverbs

> "Make it correct, make it clear, make it concise, make it fast. In that order." — Wes Dyer

The essence: build software that humans can understand and machines can execute, not the reverse.
