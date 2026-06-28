---
name: code-review-mitsuhiko
description: Review code for API shape, error handling, backward compatibility, and product-vs-library fit. Use when reviewing public APIs, library interfaces, error types, dependency choices, or product code being over-engineered, or when deciding between "ship the dumb version" and "design for stability". Do NOT use for deletion-focused or anti-bloat review (use code-review-russ-cox).
---

# code-review-mitsuhiko

First decide whether this is product code, library code, or mixed. The right review standard changes with that call.

## Steps

1. State `Context call: Product / Library / Mixed`.
2. Apply the matching lens below, then the cross-cutting checks.
3. Produce findings first, ordered by severity.

## Product Lens

- Does this solve a real user problem now?
- Could a dumb working version ship faster and validate the need?
- Is this abstraction, dependency, or extension point justified by a second real use case?
- If debt is accepted, is there a concrete refactor trigger?

Flag: speculative flexibility, invisible elegance, non-bottleneck optimization, and generic frameworks for one feature.

## Library Lens

- Will this API still make sense years from now?
- Does it break existing users? If yes, call out versioning and migration cost.
- Can users extend behavior without forking?
- Are errors, defaults, and extension points treated as stable public API?

Flag: breaking changes for minor improvements, string-matched errors, undocumented extension contracts, and "just fork it" design.

## Cross-Cutting Checks

- Errors: typed/structured enough for callers and production diagnosis?
- Dependencies: worth the transitive tree, or implementable in 20-50 clear lines?
- Defaults: safe, unsurprising, and honest about cost?
- Product/library mismatch: library standards slowing a product, or product habits destabilizing a library?

## Output Contract

- Findings first: `Must fix`, `Consider`, `Open questions`; omit empty sections.
- Each finding includes `[file:line]`, the context-specific reason, and a concrete next step.
- Add a brief `Summary` after findings. Do not add praise unless asked.

See [PRINCIPLES.md](PRINCIPLES.md) for full philosophy and phrasing patterns.
