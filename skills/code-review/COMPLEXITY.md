# Lens: Complexity gate — ownership, coupling, value

Use before a substantial design change, when explicitly asked, or when the product/necessity call is contested mid-review. This lens judges a *proposed* change; the other lenses judge a finished one.

Identify the layer that owns the behavior, then assess whether the proposed complexity earns its cost.
Use this lens for contested design choices; it is not a ceremony before routine edits.

## Decision criteria

- Locate where the invariant is established. A fix repeated across callers may belong beneath them.
- Try composing existing functions, types, or configuration before adding a new mechanism.
- Compare extending existing behavior with a separate implementation. Folding in can reduce duplication,
  but coupling across ownership or trust boundaries may cost more than a small copy.
- Judge coupling and admitted invalid states, not line count. A larger change at the correct layer can be simpler.
- Use the project's idioms. Prefer types or constructors that prevent invalid states where practical.

## Review the proposed change

Look for new cross-module dependencies, duplicated concepts, shared mutable state, and branches that defend invalid combinations.
Resolve relevant concerns by moving behavior to its owner, reusing a primitive, simplifying the state model,
or explaining the concrete outcome that justifies the addition.

Report only material tradeoffs or unresolved choices. Do not require spoken answers to every criterion,
a fixed output template, or unrelated refactoring.

For deeper analysis of a contested decision, read [COMPLEXITY-REFERENCE.md](COMPLEXITY-REFERENCE.md).
