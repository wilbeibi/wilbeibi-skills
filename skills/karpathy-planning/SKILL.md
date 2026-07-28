---
name: karpathy-planning
description: Plan non-trivial coding work by surfacing assumptions, minimizing scope, and defining success criteria and verification. Use when asked to plan or when implementation scope is ambiguous. Do NOT use for interactive interviews (use grill-me) or value-versus-complexity checks on existing code (use complexity-budget).
---

# karpathy-planning

Plan a coding task the way it should be planned: name what you're unsure about, pick the smallest solution, and define how you'll know it worked — all before touching code.

## Quick start

Before writing any code for a non-trivial request, produce a short plan with four parts:

1. **Assumptions & ambiguities** — what you're taking for granted, and any forks in interpretation.
2. **Approach** — the simplest design that solves the *stated* problem.
3. **Success criteria** — declarative, verifiable outcomes (not "make it work").
4. **Verification loop** — the steps you'll run to confirm each criterion, looping until green.

Keep it to a screenful. Then either ask the blocking questions or proceed.

## The four checks

**1. Think before coding.** Don't assume; don't hide confusion. State assumptions explicitly. When two valid readings of the request exist, present both and let the user pick rather than guessing. If a simpler solution exists than what was asked, say so.

**2. Simplicity first.** Plan the minimum code that solves the problem — nothing speculative. No features beyond scope, no abstractions for single-use logic, no error handling for scenarios that can't occur. Ask: would a senior engineer call this overcomplicated? If yes, cut it.

**3. Surgical scope.** Plan to touch only what the request requires. Preserve existing style; don't refactor unrelated sections. Note pre-existing issues you spot, but don't fix them unless asked. Every planned change should trace to the request.

**4. Goal-driven execution.** Turn the request into declarative goals, each paired with a verification step:
   - action → how it's verified
   - action → how it's verified

Strong, checkable criteria let you work independently to completion; weak ones force constant clarification.

## Notes

- **Surface, then proceed.** Raise blocking ambiguities up front. If none are blocking, state your assumptions and continue — don't stall on trivia.
- **Match effort to the task.** A one-line fix doesn't need a four-part plan; bias the ritual toward changes where scope or requirements are genuinely uncertain.
- **Declarative beats imperative.** "Tests in X pass and the endpoint returns 200 for Y" is a success criterion; "implement the handler" is just a restated instruction.
- Adapted from [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills).
