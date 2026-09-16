# Contract patterns for heavyweight workflow skills

Source: [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill), a six-phase multi-agent audit (~1,900 lines of Markdown plus two zero-dependency validators). Borrow its contracts, not its thickness. Reach for this only when a skill orchestrates subagents, produces a report artifact, or must claim coverage.

## Patterns

- **Two modes, gated in the description and the first section.** Loading the skill gives guidance only; it does not authorize the full workflow, directory creation, or file writes. The full mode runs only on an explicit "audit / full review / give me the report". If the request could mean either, ask exactly one question before creating files. Finer than `disable-model-invocation`: the skill stays auto-loadable for questions while the heavy path stays explicit.
- **Three verdicts, severity only on one.** `confirmed` / `needs_validation` / `rejected`. A `needs_validation` record names the single missing fact and a safe check that would resolve it, and carries no severity. Overall severity may not exceed demonstrated impact, and a script enforces that. Same family as code-review's `traced | inferred`; the addition is that a blocked claim must carry what unblocks it.
- **The coverage ledger is the only coverage evidence.** "An architecture summary, agent count, or generic 'auth reviewed' sentence is not coverage evidence." Each unit has a status, and each status has hard rules for which fields must be empty or nonempty. The point is to make what was *not* checked explicit so silence never reads as coverage.
- **Companion files share one skeleton and compose by anchor.** Every domain file has the same sections: when to use, a fenced core-discipline block that goes verbatim into every subagent prompt, the classes, universal moves, validation rules. The parent selects blocks as `FILE.md#section` and must copy them in full, never send names alone, because subagents share no context. Design a lens library as prompt fragments with fixed section names.
- **Fail loud instead of thinning quietly.** Reserve verifier and critic budget before spending on hunters. If the budget cannot cover the reserve, launch nothing and mark units `deferred` with an enumerated reason. A run ends in exactly one of two terminal states: every artifact written and validated, or `run_status: incomplete` with its exact reason disclosed in the report. Never treat an agent cap as evidence of completeness.
- **Adversarial, independent verification.** A fresh agent that did not produce the candidate is told to refute it, must re-read every cited location, and never sees another verifier's conclusion.
- **Platform-neutral roles defined once.** One short section defines parent, task tool, and two subagent roles; the rest of the text uses only those words, plus one sentence: use equivalent platform capabilities while preserving the boundaries. A concrete way to avoid naming any harness's tools.
- **Schema plus validator plus tests, with custom keywords.** `visibleContent: true` rejects blank or invisible-only prose fields; `fingerprint` must stay stable across verdict states and across runs so prior findings can be carried forward. Deterministic checks live in the script, never in prose.
- **Numbered anti-patterns at the end.** Each one is a concrete failure the workflow has seen ("assigning severity to needs_validation", "prose and JSON disagree"), not a value statement.

## Do not copy

- Procedures the model cannot execute (its 11-step artifact promotion with `fstat` and no-follow opens) are duplicated verbatim across three files by design. That is a curator finding, not a pattern.
- State machines, attempt archives, and wave counters only earn their prose because a validator enforces them. Without the script, a status table is noise.
- Verbatim block copying makes every subagent prompt long. Budget for that if you adopt it.
