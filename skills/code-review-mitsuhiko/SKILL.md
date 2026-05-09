---
name: code-review-mitsuhiko
description: Code review guidance based on Armin Ronacher's pragmatic philosophy. Use for reviewing web frameworks, libraries, API design, error handling, and dependency management. Emphasizes context-appropriate design (product vs library), minimal dependencies, backward compatibility, and solving real user problems over theoretical elegance.
---

# Code Review: Armin Ronacher's Philosophy

Apply mitsuhiko's practical engineering principles to build sustainable software that solves real problems.

## Core Philosophy

**Context-appropriate design**: Different projects need different approaches. Products optimize for speed and user value; libraries optimize for stability and reusability.

**Simplest working solution**: "Do the dumbest thing that works" - pragmatic choices beat theoretical perfection when validating ideas.

**User problems over internal elegance**: Users don't see your beautiful architecture. They care whether the software solves their problem.

**Stability is a feature**: Backward compatibility and reliability trump new features. Breaking changes have permanent cost.

## The Context Question: Product vs Library

### Building Products/Applications

**Priority**: Ship fast, solve user problems, iterate based on feedback.

**Review questions**:
- Does this solve a real user problem we've validated?
- Can we ship this faster with a simpler approach?
- Are we over-engineering for hypothetical future needs?
- Would a "dumb but working" solution let us validate faster?

**Good patterns**:
- Direct, obvious implementations
- Accept technical debt consciously for speed
- Focus on user-visible value
- Document "will refactor later" with actual plan

**Red flags**:
- Building generic abstractions before second use case
- Pursuing elegance that users won't perceive
- Optimizing non-bottlenecks prematurely
- "We might need this someday" features

**Example**: The Flamework philosophy - deliberately choose simple, even "ugly" solutions to ship and learn fast. Refactor when proven valuable.

### Building Libraries/Frameworks

**Priority**: Long-term stability, clear APIs, extensibility, backward compatibility.

**Review questions**:
- Will this API still make sense in 5 years?
- Does this break existing code?
- Can users extend this without forking?
- Have we designed error types as carefully as return values?

**Good patterns**:
- Extensive plugin/hook systems (inspired by Trac)
- Rich, structured error types with context
- Semantic versioning discipline
- Clear upgrade paths, never silent breakage

**Red flags**:
- Breaking changes for minor improvements
- "Move fast and break things" for public APIs
- Errors as plain strings
- Tight coupling preventing extensions

**Compatibility pledge**: "I'd rather skip a feature than break existing code." Stability builds trust and ecosystem.

## Dependency Management: "Build It Yourself"

**The dependency treadmill**: Each dependency brings transitive deps, security risks, and endless upgrade churn.

**Review questions**:
- Is this dependency worth compiling thousands of lines for one function?
- Can we implement this in 20-50 lines ourselves?
- What's the full transitive dependency tree?
- Is this dependency actively maintained with stable APIs?
- Are we adding this out of laziness or genuine complexity?

**When to build yourself**:
- Simple, well-defined functionality (terminal size, string utils, date formatting)
- Core to your domain, worth owning
- Dependency would drag in massive tree for small utility
- "Left-pad" scenarios - trivial code with large dep cost

**When to use dependencies**:
- Genuinely complex problems (image processing, cryptography, protocols)
- Battle-tested solutions with security implications
- Active community, stable APIs, clear maintenance
- Significantly more code/expertise needed to DIY

**Red flags**:
- Hundred-line dependency trees for trivial tasks
- Dependencies with dozens of transitive deps
- Unmaintained libraries or rapid breaking changes
- npm/cargo "grab everything" culture without audit

**Goal**: Zero or minimal dependencies. Code that runs unchanged for years without upgrade pressure.

## Error Handling: Design Errors Like Return Values

**The string error trap**: Jamming error info into strings forces parsing later and breaks programmatic handling.

**Principle**: "Design error types with as much care as return values."

**Review questions**:
- Can callers distinguish error types programmatically?
- Is context information structured (not in error strings)?
- Will this error help diagnose production issues?
- Can we internationalize/format without parsing strings?

**Good patterns**:
- Specific error types/enums for different failure modes
- Structured context fields (user_id, file_path, etc.)
- Error chains preserving causality
- Rich debug information (file:line, stack traces)

**Red flags**:
- `throw Error("Invalid user")` without context
- Catching errors by string matching
- Different errors indistinguishable to caller
- Error messages containing only data, no context

**Example**: Instead of `ValueError("42 is invalid")`, use `ValidationError(field="age", value=42, constraint="must be 18-120", context={...})`.

## Modularity and Extension Points

**Inspired by Trac**: Design for extensibility from day one through hooks, plugins, and clear interfaces.

**Review questions**:
- Can users extend this without modifying our code?
- Have we provided hooks at key decision points?
- Are extension interfaces documented and stable?
- Can multiple plugins coexist without conflicts?

**Good patterns**:
- Event hooks for lifecycle stages
- Plugin registration with discovery
- Configuration isolated per instance/environment
- Extension interfaces as stable as core APIs

**Red flags**:
- Hardcoded behavior with no override points
- "Just fork it" as the extension story
- Global state preventing multi-instance
- Extension APIs treated as second-class citizens

## Type Systems and Tooling

**Progressive typing**: TypeScript proved gradual types work. Types help humans AND machines.

**Review questions**:
- Do type hints clarify intent or add noise?
- Are types helping catch real bugs?
- Is complexity hurting AI/tooling understanding?
- Are we using types to document contracts?

**Good patterns**:
- Types for public APIs and complex functions
- Simple, consistent patterns over clever type tricks
- Types that improve IDE autocomplete
- Explicit over magical (helps humans and AI)

**Language preferences**:
- Python: Fast prototyping, minimal deps, type hints where helpful
- TypeScript: Better than plain JS, but watch complexity
- Go: Simple, explicit, AI-friendly, good for agents
- Rust: When performance/safety critical, accept complexity cost

**Avoid**: Over-clever type gymnastics that confuse more than help. Types serve understanding.

## Backward Compatibility: The Prime Directive

**Principle**: "I'd rather not add a feature than break existing code."

**Compatibility checklist**:
- [ ] No silent behavior changes
- [ ] Deprecation warnings before removal (with timeline)
- [ ] Clear migration guides
- [ ] Semantic versioning strictly followed
- [ ] Compatibility tested in CI

**Breaking changes**:
- Require major version bump
- Need migration guide with examples
- Should batch together, not trickle
- Must justify with significant user benefit

**Red flags**:
- "Minor refactor" that changes behavior
- Removing APIs without deprecation cycle
- "Just update your code" attitude
- Treating semver as suggestions

## Universal Review Principles

### The User Value Test
Does this solve a real problem users have, or just satisfy our aesthetic preferences?

### The Five-Year Test
Will maintaining this for 5 years cost more than the value it provides?

### The Dependency Audit
For each new dependency: Can we build it in <50 lines? Is the maintenance burden worth it?

### The Error Quality Test
Can production errors be diagnosed from the error alone, or do you need to read code?

### The Extension Test
If a user needs slightly different behavior, can they extend it or must they fork?

## Review Checklist

**Context assessment**:
- [ ] Is this a product (optimize for speed) or library (optimize for stability)?
- [ ] Are we solving a validated user problem?
- [ ] Is the approach appropriately simple/robust for context?

**Code quality**:
- [ ] Errors are structured types with rich context
- [ ] Dependencies justified (or eliminated)
- [ ] Extension points where users might need them
- [ ] Backward compatible (or properly versioned)
- [ ] Clear, explicit code over clever magic

**API design** (for libraries):
- [ ] Intuitive, consistent naming
- [ ] Documented with examples
- [ ] Stable, committed for long-term
- [ ] Type hints/signatures clear

## Constructive Feedback Patterns

**Instead of**: "This is too complex"
**Say**: "For a product feature, consider simpler approach: [sketch]. Ship fast, validate, refactor if proven valuable."

**Instead of**: "Add this dependency"
**Say**: "This dependency adds N transitive deps for X functionality. We can implement in ~Y lines: [sketch]. Ownership benefits: [list]."

**Instead of**: "Just throw an error"
**Say**: "Let's design error type: `class FooError` with fields [x, y, z]. Benefits: programmatic handling, better debugging, i18n-ready."

**Instead of**: "Breaking change needed"
**Say**: "Deprecation path: Step 1 (warnings), Step 2 (wait one major version), Step 3 (remove). Migration guide: [outline]."

## Language-Specific Notes

**Python**: Rich stdlib, type hints for clarity, avoid over-abstraction, Flask-style simplicity

**JavaScript/TypeScript**: Use TS for maintainability, but avoid type complexity. Watch npm dependency explosion.

**Rust**: Acceptable complexity for safety/performance. Still audit dependency trees. Zero-cost abstractions encouraged.

**Go**: Simple, explicit, great for AI-assisted development. Limited magic by design.

## Key Maxims

> "When building an application, reusability isn't that important. When building a library, it's crucial."

> "Perfect code doesn't guarantee success if it doesn't solve real user problems."

> "A little code duplication is better than a little dependency."

> "Backward compatibility is a feature, not a constraint."

> "Design your errors as carefully as your return values."

**Remember**: The goal is sustainable software that solves real problems. Pragmatism and stability beat theoretical purity.
