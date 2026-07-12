---
name: code-review-russ-cox
description: Review a change or audit existing code through the Russ Cox lens — necessity, layering, minimal seams, error/logging/testing discipline, and anti-bloat. Use when reviewing diffs, new features, or dependency additions, or when asked to "audit this package", "refactor/polish this code", "find design, implementation, or style problems", "do we need this?", or "is this too complex?". Do NOT use for public API shape or product-vs-library tradeoffs (use code-review-mitsuhiko) or invariant/cost honesty (use code-review-burntsushi).
---

# code-review-russ-cox

Judge code by long-term maintenance cost: whether it should exist, whether it sits at the right layer, and whether its seams, errors, tests, and docs would pass the Go team's bar. Two modes — pick by input.

- **Change review** — input is a diff, PR, proposed feature, or new dependency: run the four passes.
- **Package audit** — input is existing code ("audit", "polish", "refactor", "what's wrong with this package"): read the target in full — doc comments, tests, and imports included — plus a sample of its callers, then walk the six dimensions. End with a refactor plan judged by what it deletes.

State the problem the code solves in one sentence before either mode. If you cannot, ask. In an established codebase, search for existing primitives before judging anything new — the most common finding is a helper, interface, or package that already does this.

## Change review — four passes

1. **Feature creep** — Does this solve a real problem that existing pieces cannot compose? Is the 5-year maintenance cost worth the user value?
2. **Wrong layer** — Is this treating a symptom instead of fixing the layer that owns the behavior?
3. **Dependency explosion** — What does the dependency actually do, what transitive cost arrives with it, and could 20-50 lines replace it? Heuristic: import what is hard, own what is core, copy what is small.
4. **Quality debt** — Will a new maintainer understand it in six months, and is any debt paired with a concrete paydown trigger?

## Package audit — six dimensions

These are principles, not a compliance checklist: translate each into the codebase's own language, ecosystem, and scale, and silently skip any dimension that doesn't apply (a CLI script has no seams to audit; a stateless lib has no long-running loops). Never write a finding that demands another project's idiom — name the principle and its local translation.

1. **Seams** — Does the code own minimal interfaces at each external boundary (storage, network, LLM, clock, exec), with heavy dependencies quarantined in leaf packages? Do external types cross internal seams? Is there a fake beside each interface, advertised in its doc?
2. **Composition payoff** — Given the abstractions below it, is each unit nearly trivial? If a package is fat, the abstractions under it are wrong. If explicit state, iterator stacks, queues, or state machines mainly record where execution should resume, ask whether direct control flow would make the unit trivial. Config should be methods/fields on the object; required dependencies positional constructor args — no functional-options or config-struct boilerplate for one caller.
3. **Error regimes** — Split by whose bug it is: fail fast (panic/assert) on programmer bugs and corrupted invariants, as documented policy; recoverable errors with context for expected environmental failure; log-and-continue in long-running loops so one bad item can't kill a pass. Are the error paths tested?
4. **Observability** — Logger injected as a dependency, never global. Structured key-value attrs; message strings are stable lowercase identifiers with variable data in attrs, not interpolated. Test logs route through the test harness so they appear only on failure.
5. **Testing** — A fake at every interface; deterministic tests (no timing/race dependence); record/replay for network calls; human-editable fixtures; conformance suites for interfaces with multiple impls; coverage gaps justified with a comment, not ignored.
6. **Docs & style** — Every package has a real package doc; the main package's doc is the living architecture tour. Doc comments state contract, edge cases, and cost shape, not mechanics: expensive APIs should look expensive, and cheap APIs should look cheap. Inline comments are *why*-only; TODOs are signed with the considered tradeoff; genuine design doubts are recorded, not smoothed over.

## Universal tests

- **Simplicity:** explainable to a smart junior in two minutes.
- **Deletion:** if deleting it changes nothing important, delete it.
- **Composition:** use existing primitives when they compose cleanly.
- **Future-self:** understandable during an outage.
- **Abstraction:** wait for 3 real use cases before generalizing.

## Output contract

- Findings first: `Must fix`, `Consider`, `Open questions`; omit empty sections. No praise unless asked.
- Prefix change-review findings `[Pass N | file:line]`; audit findings `[Dim N | file:line]`.
- Each finding names what should not exist, move layers, or be simplified — plus one concrete alternative (sketch the shape, don't just point).
- Audit mode ends with a **Refactor plan**: steps ordered by payoff, each stating what it lets you delete or simplify. Each step must be independently shippable — reviewable as one PR, tests green at every point; flag any step that changes behavior.
- Brief `Summary` last.

See [REFERENCE.md](REFERENCE.md) for the full philosophy, red-flag catalogs, phrasing patterns, and the oscar-repo exemplars behind each dimension.
