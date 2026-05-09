---
name: code-review-russ-cox
description: Code review guidance based on Russ Cox's philosophy of simplicity, orthogonality, and anti-bloat. Use when reviewing code in any language, conducting design reviews, dependency audits, or complexity analysis. Emphasizes the four root causes of software bloat - feature creep, wrong-layer fixes, dependency explosion, and low quality standards.
---

# Code Review: Russ Cox's Philosophy

Apply Russ Cox's engineering principles to build maintainable software through vigilance and discipline.

## Core Philosophy

**Maintenance cost vastly exceeds implementation cost.** Every decision optimizes for long-term sustainability, not short-term convenience.

**Orthogonality principle**: Programming features should be basis vectors in a high-dimensional space. They should:
- Cover the problem space efficiently
- Interact predictably when combined  
- Avoid creating multiple redundant paths to the same solution

**Simplicity is complicated**: Simple solutions require more thought than complex ones. The goal is to make the problem simpler, not just move complexity around.

## The Four Root Causes of Bloat

### 1. Feature Creep: "Useful" ≠ "Worth It"

**The useful fallacy**: A feature can be useful but still not worth the permanent maintenance burden.

**Review questions**:
- What problem does this solve that can't be solved by composing existing features?
- What is the 5-year maintenance cost vs. the user value?
- Does this break orthogonality (adding a second way to do something)?
- Is this driven by actual need or by "competitor X has it"?

**Red flags**:
- "Nice to have" features without clear ROI
- Duplicate functionality with different syntax
- Features added for resume building or promotion
- Solutions looking for problems

**Good patterns**:
- Small, composable primitives that combine powerfully
- Features that enable new capabilities, not replicate old ones
- Clear value proposition exceeding long-term cost
- Willing to say "no" to reasonable requests

### 2. Wrong-Layer Fixes: Band-Aids on Band-Aids

**The wrapping trap**: When facing a problem, we often wrap/patch at a higher layer instead of fixing the root cause at the correct layer.

**Review questions**:
- At which layer should this logic actually live?
- Are we treating symptoms or causes?
- How many indirection layers separate intent from implementation?
- Could we eliminate this entire module by fixing the underlying issue?

**Red flags**:
- Wrapper functions that only forward to other wrappers
- "Adapter" or "bridge" patterns without clear architectural boundaries
- Need to modify 5+ files to change one behavior
- Error handling scattered across multiple abstraction levels

**Good patterns**:
- Fix at the source, not at the symptoms
- Minimal layers between problem and solution
- Clear ownership of responsibility at each layer
- Each abstraction earns its keep

**Example**: Instead of wrapping validation errors three layers up, add proper constraints at the data layer and validation at the input boundary.

### 3. Dependency Explosion: The Hidden Iceberg

**The transitive trap**: Every dependency brings its own dependencies. You're responsible for maintaining all of them.

**Review questions**:
- What does this dependency actually do? (Read the code, not just the README)
- How many transitive dependencies does it bring?
- Can we implement this in 20-50 lines instead?
- What happens when this dependency breaks/updates/is abandoned?
- Is this dependency's stability and maintenance history solid?

**Red flags**:
- "Left-pad syndrome" - huge dependency for tiny utility
- Dependencies with their own complex dependency trees
- Unmaintained libraries (no commits in 2+ years)
- Dependencies that depend on multiple competing libraries
- Choosing dependencies by download count, not code quality

**Good patterns**:
- Default to standard library/language primitives
- Implement simple functionality directly
- Audit full dependency tree before adding
- Prefer dependencies with minimal transitive deps
- Document why each dependency is necessary

**Dependency audit checklist**:
- [ ] Reviewed transitive dependency tree
- [ ] Verified active maintenance
- [ ] Confirmed no simpler alternative
- [ ] Understood security implications
- [ ] Documented cost-benefit decision

### 4. Low Quality Standards: "Ship Now, Fix Later"

**The technical debt lie**: "We'll clean this up later" almost never happens. The debt compounds with interest.

**Review questions**:
- Would we be proud to have this code reviewed publicly?
- Will someone unfamiliar understand this in 6 months?
- Are we accepting this because of time pressure or actual quality?
- What's our concrete plan to fix this if we merge it?

**Red flags**:
- "Works on my machine" code
- Complex logic without explanation
- Missing or superficial tests
- Clever tricks requiring domain expertise to understand
- Comments explaining what code does instead of why

**Good patterns**:
- Code is merge-ready before review, not "almost there"
- Clarity over cleverness, always
- Self-documenting code with comments explaining "why", not "what"
- Comprehensive tests that document behavior
- Refusal to merge until quality bar is met

## Universal Review Principles

### Simplicity Test
Can you explain this to a smart junior developer in 2 minutes? If not, it's probably too complex.

### Deletion Test  
What happens if we delete this? If "nothing bad", delete it.

### Composition Test
Can existing primitives combine to solve this? If yes, don't add new ones.

### Future-Self Test
Will I understand this code at 2am during an outage in 6 months? If no, simplify.

### Abstraction Test
Do we have 3+ concrete use cases for this abstraction? If no, it's premature. Solve directly first.

## Review Checklist

**Before detailed review**:
- [ ] Understand the actual problem being solved
- [ ] Verify this is necessary (not just useful)
- [ ] Check for simpler alternatives
- [ ] Assess maintenance burden vs. benefit

**Architecture & design**:
- [ ] Logic at appropriate abstraction layer
- [ ] Minimal indirection
- [ ] Dependencies justified
- [ ] Code is composable
- [ ] No premature abstraction

**Code quality**:
- [ ] Clear and self-documenting
- [ ] Complexity justified
- [ ] Meaningful tests
- [ ] Proper error handling
- [ ] Will be understandable later

**Dependencies**:
- [ ] New dependencies fully justified
- [ ] Transitive tree reviewed
- [ ] Standard library considered
- [ ] Security assessed
- [ ] Documented decision

## Constructive Feedback Patterns

**Instead of**: "This is too complex"
**Say**: "This has X layers of indirection. Could we solve directly: [sketch]. Benefits: [list]. Trade-offs: [list]."

**Instead of**: "Don't add this dependency"  
**Say**: "This adds N dependencies. Alternative: [standard lib / 20 lines of code]. For our use case, simpler approach wins because [reason]."

**Instead of**: "This abstraction is wrong"
**Say**: "We have 1 use case, this adds abstraction for future needs. Suggest: solve directly now, abstract when pattern emerges (3+ uses)."

**Instead of**: "Rewrite this"
**Say**: "Current approach: [analysis]. Maintenance implications: [list]. Alternative: [sketch]. Which approach better fits our long-term goals?"

## Common Anti-Patterns

**The kitchen sink**: Adding features "because we might need them someday"
- *Solution*: YAGNI (You Aren't Gonna Need It). Build for today's requirements.

**The golden hammer**: Using familiar pattern even when inappropriate
- *Solution*: Choose tools based on problem, not familiarity.

**The framework fever**: Adopting frameworks for simple problems
- *Solution*: Use libraries, not frameworks, for most problems. Compose don't adopt.

**The perfect system**: Over-engineering for hypothetical scale
- *Solution*: Build for 10x current scale, not 1000x. Premature optimization is evil.

**The busy work**: Changes that increase code size without proportional value
- *Solution*: Measure value by code deleted, not code added.

## When to Compromise Principles

**Legitimate reasons**:
- Hard business deadlines with documented technical debt plan
- Regulatory/compliance requirements (GDPR, accessibility, security certs)
- Vendor lock-in with conscious decision (document trade-offs)
- Team skill constraints (but invest in training)

**How to compromise well**:
- Document the decision and reasoning explicitly
- Create concrete plan to address tech debt (with dates)
- Minimize scope of compromise
- Review decision quarterly

**Never compromise on**:
- Security vulnerabilities
- Data integrity
- Silent failures
- Critical path without tests

## Language-Specific Notes

**Go**: Strong standard library, explicit error handling, small interfaces, composition over inheritance

**Python**: Rich standard library, avoid Django for simple needs, prefer composition, type hints for clarity

**JavaScript/TypeScript**: Beware npm dependency explosion, prefer standard APIs, TypeScript for maintainability

**Rust**: Strong std lib, cargo minimizes dependency pain but still audit trees, zero-cost abstractions are fine

**Java**: Rich JDK, avoid framework soup (Spring for everything), prefer simple servlets for simple needs

**C/C++**: Minimal dependencies by culture, STL/standard library first, avoid NIH but also avoid dependency hell

*The philosophy applies universally - adjust tactics per language ecosystem.*

## Success Metrics

A good review achieves:
- ✅ Simpler solution than originally proposed
- ✅ Fewer dependencies with clear justification
- ✅ Appropriate abstraction level
- ✅ Both reviewer and author learned something
- ✅ Code is more maintainable than before review

**Remember**: Perfect is the enemy of good. The goal is sustainable, maintainable software - not theoretical perfection.

## Key Questions for Every Review

1. **Necessity**: Is this necessary or just useful?
2. **Layer**: Is this at the right abstraction level?
3. **Dependencies**: Can we avoid adding this dependency?
4. **Clarity**: Will this make sense in 6 months?
5. **Composition**: Can existing pieces combine to solve this?
6. **Cost**: Does benefit exceed 5-year maintenance cost?

## Russ Cox's Wisdom

> "A little copying is better than a little dependency." - Go Proverbs

> "Make it correct, make it clear, make it concise, make it fast. In that order." - Wes Dyer

The essence: **Build software that humans can understand and machines can execute, not the reverse.**
