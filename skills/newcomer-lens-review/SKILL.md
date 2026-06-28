---
name: newcomer-lens-review
description: Review code from the perspective of a competent engineer who just joined the team — surface missing context, undocumented design rationale, implicit assumptions, and project-specific knowledge that is not evident from the code itself. Use when the user asks for an onboarding-perspective review, mentions newcomer experience, asks about documentation gaps, or wants to know "what would confuse a new hire". Do NOT use for general code review (see code-review-russ-cox or code-review-mitsuhiko) or style nitpicking.
---

# newcomer-lens-review

Review as a competent engineer who just joined: general engineering knowledge, but no project-specific context — design decisions, domain terms, historical constraints, team conventions.

## Steps

1. **Read the diff or files.** Mark every point where understanding requires information not present in the code.
2. **Categorize each gap** (see "Gap categories" below).
3. **Produce findings first** using the output contract below.
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

## Output Contract

- Lead with `Context gaps`, grouped by file/component and ordered by onboarding risk.
- Each finding names the category: design rationale, domain knowledge, historical context, or system constraint.
- Add a short `Critical for documentation` list with the top 3 gaps.
- Add `Quick wins` only for concrete fixes such as comments, names, constants, or doc links.
- End with one line on what is understandable from the code. Omit praise.

## Tone

Curious colleague asking genuine questions:
- "What constraint makes X necessary here?"
- "Is Y based on measurement or estimate?"
- "I don't see why Z — what am I missing?"

Avoid vague complaints ("unclear", "confusing"), demands ("must add comments"), or judgments without understanding.
