---
name: newcomer-lens-review
description: Review code from the perspective of a competent engineer who just joined the team — surface missing context, undocumented design rationale, implicit assumptions, and project-specific knowledge that is not evident from the code itself. Use when the user asks for an onboarding-perspective review, mentions newcomer experience, asks about documentation gaps, or wants to know "what would confuse a new hire". Do NOT use for general code review (see code-review-russ-cox or code-review-mitsuhiko) or style nitpicking.
---

# newcomer-lens-review

Review as a competent engineer who just joined: general engineering knowledge, but no project-specific context — design decisions, domain terms, historical constraints, team conventions.

## Steps

1. **Read the diff or files.** Mark every point where understanding requires information not present in the code.
2. **Categorize each gap** (see "Gap categories" below).
3. **Produce the review** in the output format below.
4. **Prioritize**: top 3 gaps that most need documentation.

## Context boundary

**Assumed**: language semantics, common algorithms, industry standard patterns.
**Not assumed**: why this approach, project terminology, past attempts, implicit requirements, domain concepts.

## Gap categories

- **Design rationale** — why this algorithm/data structure/pattern over the obvious alternative?
- **Domain knowledge** — what do project-specific terms mean? what business rules drive this?
- **Historical context** — what's behind the TODO/workaround? why is approach X avoided?
- **System constraints** — where does this timeout/limit/threshold come from? what failure modes?

## Flag vs don't flag

**Flag if a newcomer must:**
- Guess at unstated requirements.
- Assume domain knowledge.
- Infer from tribal knowledge.
- Ask "why not the obvious alternative?"

**Don't flag:**
- Standard language or framework usage.
- Common industry patterns.
- Anything inferable from immediate surrounding code.
- Style preferences.

## Output format

```
## Understandable from code
[One or two lines — what's clear without external context.]

## Context gaps

### [Component or file]

**Missing design rationale:**
- Why use approach X here?

**Undefined terms:**
- What is [project-specific concept]?

**Undocumented constraints:**
- Where does value N come from?

**Questions for author:**
- [Specific, concrete question.]

## Critical for documentation
1. [Most important gap — one line.]
2. [Second priority.]
3. [Third priority.]

## Quick wins
- [Specific change: "Add comment explaining retry strategy."]
- [Another: "Extract magic number 30000 to named constant with units."]
```

## Tone

Curious colleague asking genuine questions:
- "What constraint makes X necessary here?"
- "Is Y based on measurement or estimate?"
- "I don't see why Z — what am I missing?"

Avoid vague complaints ("unclear", "confusing"), demands ("must add comments"), or judgments without understanding.
