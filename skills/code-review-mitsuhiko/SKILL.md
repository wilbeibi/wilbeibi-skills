---
name: code-review-mitsuhiko
description: Review code for API shape, error handling, backward compatibility, and product-vs-library fit. Use when reviewing public APIs, library interfaces, error types, dependency choices, or product code being over-engineered, or when deciding between "ship the dumb version" and "design for stability". Do NOT use for deletion-focused or anti-bloat review (use code-review-russ-cox).
---

# code-review-mitsuhiko

Different projects need different rules. Products optimize for speed and user value; libraries optimize for stability and reusability. Decide which one this is *first* — then apply the right checklist.

## Steps

1. **Classify the context** — is this a product (application code, end-user feature) or a library (reusable interface, framework, SDK)? When in doubt, ask. The answer changes most subsequent calls.
2. **Walk the matching checklist** below. Don't apply library standards to product code or vice versa.
3. **Always walk the cross-cutting checks** (errors, dependencies, extension points).
4. **Produce findings** in the output format below.

## Product checklist (ship fast, validate, iterate)

- Does this solve a real, validated user problem?
- Could a "dumb but working" version ship faster?
- Are we building generic abstractions before the second use case appears?
- Are we optimizing non-bottlenecks?
- If we accept debt, is there a written "refactor when X happens" trigger?

**Red flags**: hypothetical-future generality; elegance users won't perceive; "we might need this someday"; premature optimization.

## Library checklist (stability, clear APIs, extensibility)

- Will this API still make sense in 5 years?
- Does this break existing code? (If yes — major version bump + migration guide, no exceptions.)
- Can users extend this without forking?
- Have errors been designed as carefully as return values?
- Are extension interfaces treated as first-class APIs (documented, stable, tested)?

**Red flags**: breaking changes for minor improvements; "move fast and break things" applied to public APIs; errors as plain strings; tight coupling preventing extension.

**Compatibility pledge**: *"I'd rather skip a feature than break existing code."*

## Cross-cutting checks (both contexts)

### Errors

- Can callers distinguish error types programmatically (not by string matching)?
- Is context structured (`field=…`, `value=…`, `constraint=…`), not crammed into a message?
- Will this error help diagnose a production issue without reading the source?
- Bad: `throw Error("Invalid user")`. Good: `ValidationError(field="age", value=42, constraint="must be 18-120")`.

### Dependencies

- Is this dep worth compiling thousands of lines for one function?
- Could we implement it in 20–50 lines?
- What's the full transitive tree?
- Is it actively maintained with stable APIs?
- DIY when: simple/well-defined, core to your domain, or a "left-pad" scenario.
- Take the dep when: genuinely complex (crypto, image processing, protocols), security-sensitive, battle-tested.

### Extension points (libraries especially)

- Can users extend behavior without modifying our code?
- Are there hooks at key decision points?
- Are extension interfaces documented and stable?
- "Just fork it" is not an extension story.

## Output format

```
## Context call
Product / Library / Mixed (which parts are which)

## Summary
<one paragraph: overall verdict and the single most important issue>

## Must fix
- [file:line] <finding>. Suggested approach: <sketch>.

## Consider
- [file:line] <finding>. Tradeoff: <gained vs lost>.

## Praise
- <named, specific>

## Open questions
- <needs author context>
```

## Constructive phrasing

Always pair a critique with the next step. Instead of *"this is too complex"* → *"for a product feature, consider [sketch]; ship, validate, refactor if proven."* Instead of *"add this dependency"* → *"this dep adds N transitive deps for X; we can implement in ~Y lines: [sketch]."* Full phrasing patterns in PRINCIPLES.md.

## Reference

- [PRINCIPLES.md](PRINCIPLES.md) — full philosophy, error-design depth, modularity/extension patterns, type-system stance, language-specific notes, source quotes.
