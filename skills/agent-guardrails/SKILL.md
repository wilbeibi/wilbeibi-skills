---
name: agent-guardrails
description: Turn recurring agent mistakes in a project into enforceable constraints. Use when the user keeps correcting the same mistake or asks to prevent a repeated class of errors. Do NOT use for a single bug fix, general code review, or skill-library cleanup.
---

# agent-guardrails

Replace a repeated correction with a constraint that catches the next occurrence.

## Find the class

Read relevant project commits, reverts, review comments, instruction files, and examples supplied by the user. Stay within the current project and explicitly supplied history; do not search unrelated conversations or host memory.

Group mistakes by their cause rather than their wording. Require two distinct occurrences before calling a class recurring; multiple comments about one occurrence count once. A request to prevent a specific mistake can justify a guard without a history claim. Record the evidence and the behavior that should have happened instead.

## Choose the strongest practical constraint

Work down this order, stopping at the smallest change that prevents the demonstrated error:

1. **Ownership and architecture.** One owner for shared state, one authoritative list, an internal boundary, or removal of an obsolete example can make the mistaken path unavailable. Reject a broad redesign whose cost exceeds the recurring failure.
2. **Types and schemas.** Encode the invalid state or unsupported operation so existing validation rejects it.
3. **Lint, build, or CI.** Catch the bad pattern with an actionable error naming the supported alternative. Follow the project's existing check path. If legacy violations make adoption impractical, reject newly introduced violations without hiding the old ones.
4. **Behavioral regression.** Protect the external contract with an independent expected result. An internal-shape assertion is not a substitute for a behavior check.
5. **Project guidance.** Keep judgment calls that cannot be enforced as concise instructions, with their limit stated. Another reminder does not count as an enforced guard.

For each chosen level, say why a cheaper or stronger option did not fit. Do not add every layer for the same error.

## Prove the constraint

Recreate a representative past mistake in an isolated fixture, scratch checkout, or narrowly controlled reversible edit. Show that the normal project check rejects it for the intended reason, then that the corrected form passes. Use the same command CI will use when CI enforcement is claimed.

Test a nearby valid case too, especially for syntax or text-based rules. A check that bans legitimate code or fails for an unrelated reason is unfinished. When a real-case replay is unavailable, label the guard unverified and name what remains to run.

## Keep the change scoped

- A diagnosis-only request ends with evidence and proposed constraints. An authorized implementation fixes the selected classes within the project; it does not expand into host configuration, global agent rules, deployment, or publication.
- Preserve existing tests and project policy. Changing their contracts requires the authority applicable to that project.
- Keep any rule-to-enforcement mapping beside the project's existing guidance only when it helps maintainers find the check. Do not create another policy file or append unenforced rules by default.
- Leave judgment-only rules visible. Drop an obsolete reminder only after proving its constraint covers the original cases.

## Output

Report each class with its occurrence evidence, selected constraint and cost, failing replay, passing correction and valid case, and enforcement command. Identify any remaining judgment call or verification gap. Report only classes the evidence supports.

Adapted from [pstack/correct](https://github.com/cursor/plugins/blob/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack/skills/correct/SKILL.md), under the [MIT license](LICENSE.pstack).
