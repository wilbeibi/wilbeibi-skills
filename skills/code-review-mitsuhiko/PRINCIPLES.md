# code-review-mitsuhiko — Principles

The full philosophy behind the checklists in `SKILL.md`. Load this when you need to justify a finding, explain a principle to the author, or decide an edge case.

## Core philosophy

- **Context-appropriate design.** Different projects need different approaches. Products optimize for speed and user value; libraries optimize for stability and reusability.
- **Simplest working solution.** *"Do the dumbest thing that works."* Pragmatic choices beat theoretical perfection when validating ideas.
- **User problems over internal elegance.** Users don't see your beautiful architecture. They care whether the software solves their problem.
- **Stability is a feature.** Backward compatibility and reliability trump new features. Breaking changes have permanent cost.

## Product vs library: the deciding question

### Building products / applications

**Priority**: ship fast, solve user problems, iterate based on feedback.

**Good patterns**: direct, obvious implementations; conscious technical-debt acceptance for speed; focus on user-visible value; "will refactor later" comes with an actual trigger.

**Red flags**: building generic abstractions before the second use case; pursuing elegance users won't perceive; optimizing non-bottlenecks prematurely; "we might need this someday".

**The Flamework philosophy**: deliberately choose simple, even "ugly" solutions to ship and learn fast. Refactor when proven valuable.

### Building libraries / frameworks

**Priority**: long-term stability, clear APIs, extensibility, backward compatibility.

**Good patterns**: extensive plugin/hook systems (inspired by Trac); rich, structured error types with context; semantic-versioning discipline; clear upgrade paths, never silent breakage.

**Red flags**: breaking changes for minor improvements; "move fast and break things" applied to public APIs; errors as plain strings; tight coupling preventing extension.

**Compatibility pledge**: *"I'd rather skip a feature than break existing code."* Stability builds trust and ecosystem.

## Dependency management — "build it yourself"

Each dependency brings transitive deps, security risks, and endless upgrade churn.

**Build yourself when**:
- Functionality is simple and well-defined (terminal size, string utils, date formatting).
- It's core to your domain — worth owning.
- The dep would drag in a massive tree for a small utility.
- "Left-pad" scenarios — trivial code with large dep cost.

**Use a dependency when**:
- The problem is genuinely complex (image processing, crypto, network protocols).
- You need a battle-tested solution with security implications.
- Active community, stable APIs, clear maintenance.
- DIY would require significantly more code or domain expertise.

**Red flags**: hundred-line dep trees for trivial tasks; dozens of transitive deps; unmaintained libraries or rapid breaking changes; npm/cargo "grab everything" culture without audit.

**Goal**: zero or minimal dependencies. Code that runs unchanged for years without upgrade pressure.

## Error handling — design errors like return values

Jamming error info into strings forces callers to parse later and breaks programmatic handling.

**Principle**: *"Design error types with as much care as return values."*

**Good patterns**: specific error types/enums for distinct failure modes; structured context fields (`user_id`, `file_path`, …); error chains preserving causality; rich debug info (file:line, stack trace).

**Red flags**: `throw Error("Invalid user")` with no context; catching errors by string matching; different errors indistinguishable to the caller; messages containing only data, no context.

**Worked example**: instead of `ValueError("42 is invalid")`, use `ValidationError(field="age", value=42, constraint="must be 18-120", context={...})`.

## Modularity and extension points

Inspired by Trac: design for extensibility from day one through hooks, plugins, and clear interfaces.

**Good patterns**: event hooks for lifecycle stages; plugin registration with discovery; configuration isolated per instance/environment; extension interfaces as stable as core APIs.

**Red flags**: hardcoded behavior with no override points; "just fork it" as the extension story; global state preventing multi-instance use; extension APIs treated as second-class citizens.

## Type systems and tooling

Progressive typing works (TypeScript proved it). Types help humans *and* machines.

**Good patterns**: types on public APIs and complex functions; simple consistent patterns over clever type tricks; types that improve IDE autocomplete; explicit over magical (helps humans and AI).

**Avoid**: over-clever type gymnastics that confuse more than help. Types serve understanding.

**Language stances**:
- **Python** — fast prototyping, minimal deps, type hints where helpful; Flask-style simplicity.
- **TypeScript** — better than plain JS, but watch type complexity; mind npm dep explosion.
- **Go** — simple, explicit, AI-friendly, good for agents.
- **Rust** — accept complexity for safety/performance; still audit dep trees; zero-cost abstractions encouraged.

## Backward compatibility — the prime directive

*"I'd rather not add a feature than break existing code."*

**Compatibility checklist**:
- [ ] No silent behavior changes
- [ ] Deprecation warnings before removal (with timeline)
- [ ] Clear migration guides
- [ ] Semantic versioning strictly followed
- [ ] Compatibility tested in CI

**Breaking changes** require: a major version bump; a migration guide with examples; batching together rather than trickling; significant user benefit to justify the cost.

**Red flags**: "minor refactor" that changes behavior; removing APIs without a deprecation cycle; "just update your code" attitude; treating semver as a suggestion.

## Constructive feedback patterns

**Instead of**: "This is too complex."
**Say**: "For a product feature, consider a simpler approach: [sketch]. Ship fast, validate, refactor if proven valuable."

**Instead of**: "Add this dependency."
**Say**: "This dep adds N transitive deps for X functionality. We can implement in ~Y lines: [sketch]. Ownership benefits: [list]."

**Instead of**: "Just throw an error."
**Say**: "Let's design an error type: `class FooError` with fields `[x, y, z]`. Benefits: programmatic handling, better debugging, i18n-ready."

**Instead of**: "Breaking change needed."
**Say**: "Deprecation path: Step 1 (warnings), Step 2 (wait one major version), Step 3 (remove). Migration guide: [outline]."

## Source maxims

> "When building an application, reusability isn't that important. When building a library, it's crucial."

> "Perfect code doesn't guarantee success if it doesn't solve real user problems."

> "A little code duplication is better than a little dependency."

> "Backward compatibility is a feature, not a constraint."

> "Design your errors as carefully as your return values."

The essence: pragmatism and stability beat theoretical purity.
