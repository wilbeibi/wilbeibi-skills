---
name: sherlock
description: Work an open question like a case — graded clues, competing theories in a consistency matrix, eliminate by evidence, backtrack, converge, with a casebook on disk for long cases. Use for puzzling bugs, reverse-engineering how a product works from public signals, or "what actually happened here". Do NOT use for planning (use karpathy-planning), repo tours (use grok-repo), or diff review.
---

# sherlock

Data before theory; several theories at once; kill by evidence, not by preference; converge only when one theory explains every clue. Keep the trail so a dead branch is never re-entered.

## The loop

1. **Frame the case.** Rewrite the ask as one answerable question with a stopping condition, and write what a *no* looks like. Split what is **known** (observed) from what is **assumed** (told, inferred, remembered); each assumption gets a status and an *if wrong* in the casebook. "Find out how X works" has no stopping condition; "which of caching / precompute / streaming makes X return in 50ms at 10M rows?" does.
2. **Observe before you theorize.** Collect clues first — logs, code, traces, pages, dates — and log each as `E<n>` with its source, its date, a grade, and whether it was **observed** or **inferred** (see the casebook format). Record **absences** as clues (the log line that should be there and isn't; the feature the docs never mention). Record the **odd detail** — the one fact that doesn't fit the obvious story is the lever, not noise. Never edit or "fix" while observing.
3. **Write the theories.** At least three `H<n>`, always including a boring one (config, cache, stale build, different user) and one that questions the premise (the report is wrong, there are two causes, the docs describe a previous architecture). For each, write what it predicts that the others do not, and the cheapest test that would show it false. Keep an explicit `H0: none of the above`.
4. **Fill the matrix.** For every clue × theory, mark **C** (consistent), **I** (inconsistent), or **–** (no bearing). Judge by column: the theory with the fewest *I* leads; the one with the most *C* means nothing, because support is easy to find for any plausible story. A clue that is C for every theory has zero diagnostic value — stop collecting that kind. Pick the next test by what **splits the live theories**, cheapest first; prefer a test that could kill your favourite.
5. **Test and branch.** Pursue the leading theory depth-first with a budget: three tests without a status change, park it and switch. One change at a time. A result that would rescue a dying theory needs an independent second source before it counts. A solid *I* kills a theory — record the killing clue and move to the next live branch. When theories multiply without new clues, stop reasoning and go get a clue — instrument, trace, fetch. If every theory dies, the set was incomplete: go back to step 3, not to the least-dead one; if that happens twice, the question is mis-framed — stop and report.
6. **Converge.** The survivor must explain every retained clue, the odd one included. If it explains most but not all, either the residual is noise (say why) or there is a second cause. Grade it — **confirmed** (two independent sources, or one authoritative record, nothing contradicting), **probable** (one strong source, alternatives tested and weaker), **unconfirmed** (a single lead) — and write what would falsify it. In a debug case the verdict is not in until the fix removes the failure *and* reverting the fix brings it back.

Eliminate only on hard evidence, never on "unlikely". Whatever remains is the truth *only if the list was complete and every kill was sound*; an improbable survivor is a signal to re-check both.

Skip the matrix when one theory and one cheap test settle it; the loop earns its cost from the first guess that fails, or from three live theories.

## Where clues hide, by case

| Case | Strongest clues (observe yourself) | Cheapest discriminating tests |
|---|---|---|
| **Debug** a failure | exact error text, stack, the first bad log line, timing, what changed (`git log`, deploys, deps, data) | minimal repro; bisect over commits, config, or input; instrument the boundary between working and broken; confirm the running code is the code you are reading; put a temporary log or assertion at the suspected cause and watch it fire |
| **Reverse-engineer** a product | your own traces (DevTools/HAR, response headers, ID formats, rate-limit and cache headers, JS bundle names), engineering blog, talks, patents, public SDK source, changelog, status-page postmortems, subprocessor list, pricing limits, job posts | `scripts/fingerprint.sh <host>` for passive DNS/header evidence; probe the edges (limits, error messages, latency at scale); compare two accounts, regions, or plans; interrogate the product itself if it talks; date every source and build a timeline — architectures change |
| **What happened** in a repo or incident | timeline from timestamps, commits, alerts, and who-did-what; reverts and follow-up fixes | for repo history run `grok-repo` change archaeology; for a live incident mitigate first (roll back, fail over) and investigate after; then reconcile the alert time against the change time before believing any narrative |

Reason **backwards**: from the effect to the mechanisms that could produce it, not forward from what you know. In reverse-engineering, first ask what design the constraints *force* (latency, scale, cost, compliance), then look for the clue that separates the two or three designs that fit.

## Casebook

Write `.sherlock/<case-slug>.md` (format: [CASEBOOK-FORMAT.md](CASEBOOK-FORMAT.md)) as soon as any of these is true: more than three test cycles, a test with side effects, more than one person or session on the case, or the user asks for notes. Append as you go — update a theory's status in place, never delete a dead one. The casebook is what lets a later session resume without re-running dead branches; the final report links it.

With three or more live theories whose tests are independent, fan out one subagent per theory, handing each its column of the matrix. Subagents return clues and C/I marks, never a verdict; only the main investigation converges.

## Verdict contract

Lead with the answer. Then, in order:

- **Verdict** — one sentence plus its grade.
- **Chain** — the clues (`E<n>`) that carry it, in causal order, each with source and date.
- **Eliminated** — each dead theory and the single clue that killed it.
- **Residuals** — clues the verdict does not explain, and what they might mean.
- **Falsifier** — the one observation that would overturn the verdict, and the next test if more certainty is needed.
- **Casebook** — path, if one exists.

## Traps

- **Theorizing before data.** Once you have a theory you twist facts to fit it. Steps 2 and 3 are in that order for a reason.
- **Circular corroboration.** Three sources agreeing is one source if they copied each other — same phrasing, same typo, same aggregator. Independent means different *collection*, not different sites.
- **Stale clue as current.** A 2021 talk describes the 2021 architecture. Every clue carries its date; a verdict about *now* needs a clue from *now*.
- **Pivot drift.** Five inferences each 90% likely compound to a coin flip. After each hop, restate which confirmed clue ties it back to the question.
- **Tool output is a lead, not evidence.** A grep hit, a search result, a scanner match — verify before it enters the matrix.
- **Observer effect.** Adding logging, attaching a debugger, or retrying changes timing and state; note it when the failure "disappears".
- **Marketing is not implementation.** "Real-time", "AI-powered", "serverless" are claims graded like any other source: low until an engineer's post or your own trace backs them.
- **The obvious fact.** Nothing is more deceptive; the clue everyone agrees on is the one least often checked.

Method, sources, and how the Holmes maxims fail in practice: [REFERENCE.md](REFERENCE.md).
