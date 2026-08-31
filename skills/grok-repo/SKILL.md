---
name: grok-repo
description: Explain an unfamiliar codebase through a repository briefing, dataflow trace, or change-history reconstruction. Use when asked for a repo tour, how something works, where a value comes from, or why and how a feature or change was introduced. Do NOT use for repository health (use repo-eval) or diff review.
---

# grok-repo

Read purpose, structure, mechanics, then history for the *why*; judge taste only after evidence.
Pick one mode by the question; every claim cites a file path or commit:

- **Scoped question** ("how does X work?", "where does Y come from?") → a **dataflow trace**.
- **Change question** ("why was X added?", "how did this feature evolve?") → **change archaeology**.
- **Whole-repo question** ("explain this codebase", "give me a tour") → the **full briefing**.

## Dataflow trace (scoped mode)

Follow one datum — request, message, config value, file — from entry to effect. The trace is the answer.

- Lead with a hop chain, one line per hop, each cited:
  `POST /jobs (api/handler.go:41) → validate → Job{} (job.go:12) → enqueue (redis) → worker.Run (worker.go:88) → status written (store.go:130)`
- At each hop name its holder (type/struct/schema), transformation, and every **shape change
  or rename** (JSON→struct, field rename, enum remap).
- Mark seams crossed: serialization, queue, process/network boundary, goroutine/thread handoff.
- Close with skipped side flows, error/edge paths worth a second trace, and surprises.
- If the *why* of a hop is odd, spot-check history: `git log -S '<symbol>'` or blame the line.

## Change archaeology (history mode)

Reconstruct one feature or decision, not the repository's entire chronology:

1. **Anchor the current concept** — find present symbols, paths, config names, tests, and user
   vocabulary. State what it does now before explaining how it arrived.
2. **Find its introduction** — use `git log -S '<literal>'` for appearance/disappearance,
   `git log -G '<regex>'` for matching changed lines, and `--follow` for renamed files. Try old names.
3. **Read commits, not just subjects** — `git show` the introduction and its parent. Bodies,
   tests, deleted code, issue/PR references, and nearby fixes are evidence; diffs alone imply.
4. **Trace the arc** — inspect follow-up fixes, refactors, reverts, and blame on surviving lines.

Lead with **before → pressure/evidence → introduction → corrections/reversals → current form**.
Cite SHA + path per stage; close with supported rationale, rejected alternatives, unresolved
context, and history limits. Never turn commit order into causality or invent motivation.

## Reading order (full briefing)

Work top-down. On large repos, sample representative components and say what you sampled.

1. **Orient** — README, docs/, top-level layout, manifest (go.mod/package.json/Cargo.toml),
   Makefile/CI config. Find the entry points (`main`, CLI commands, server bootstrap, exported API).
   If it builds/tests cheaply, run it — a passing test suite and one real invocation anchor
   everything that follows.
2. **Trace one real flow** end-to-end (a request, a command, a build) before generalizing.
   Architecture claims made without a trace are usually wrong.
3. **Map components and seams** — where modules meet: interfaces, wire protocols, DB schemas,
   queues, plugin points, process boundaries. For each seam ask *why here*: testability,
   swap-ability, deploy boundary, team boundary, or accident. Note which side owns the types.
4. **Mine git history** for rationale (commands below). First check whether history is shallow,
   squashed, imported, generated, or vendor-heavy; weak history produces clues, not rationale.
5. **Judge taste and pick highlights** last, from the evidence already gathered.

## Git archaeology

Resolve `scripts/archaeology.sh` relative to this `SKILL.md`, then run:

```bash
bash <skill-dir>/scripts/archaeology.sh [repo-dir]  # history digest and reading candidates
```

Then drill into what the digest surfaces:

```bash
git show --stat <sha>                     # read the big commits' messages in full
git log --follow --oneline -- <hot-file>  # evolution of a load-bearing file
git log -S '<symbol>' --oneline           # when/why a concept appeared or died
```

- Find "key changes" by size and message, not recency: rewrites, "refactor", "redesign",
  version-bump commits, and any commit whose message explains a tradeoff. Good projects
  hide design docs in commit messages — quote them.
- Cross-reference **frequently touched × fix-touched** to choose files for closer reading.
  This is a lead, not proof of fragility: formatting, generated code, and long-lived files
  can dominate counts.
- **Reverts are possible negative rationale**: verify that a rollback concerns the current
  design before using it to explain why an alternative did not survive.
- Test a "team boundary" seam hypothesis with `git shortlog -sn -- <dir>` on each side:
  disjoint author sets support but do not establish it; the same names weaken the hypothesis.
- `git blame` a surprising line before calling it a wart; it often has a fix-commit story.

## Briefing contract

The briefing is a map for the reader to learn the code themselves, not a substitute for
reading it — every concept must point at the file that teaches it. Produce these sections,
in this order; cite `path:line` or short SHAs throughout.

0. **Problem & users** — what pain it removes, for whom, and what the project deliberately
   does *not* do (non-goals are often stated in README/docs or early commits).
1. **Architecture** — the 3-7 major components and the shape connecting them (pipeline,
   hub-and-spoke, layered, plugin host…). One paragraph plus a compact diagram or list.
2. **Design taste** — the authors' consistent choices, each backed by two or more examples:
   dependency policy, error-handling style, abstraction depth, naming, testing philosophy,
   concurrency model. Taste is what repeats; one instance is noise.
3. **Components & seams** — per component: responsibility, its inbound/outbound seams, and
   why the boundary sits there. Flag seams that leak (imports crossing the "wrong" way).
4. **History & rationale** — 3-6 pivotal commits/eras and what each reveals about why the
   design is what it is (e.g. "storage was swapped behind an interface in <sha> after X").
5. **Beautiful code** — if evidence warrants it, show 1-3 pieces that are novel,
   dense-but-clear, or do a lot with a little. Quote a short excerpt and say precisely what
   makes it good: the invariant it protects, the cases it collapses, or the API it keeps honest.
   If none stands out in the sampled code, say so instead of manufacturing praise.
6. **Hooks for curiosity** — the project's own vocabulary (5-10 jargon terms → the file
   that defines each), 2-3 flows that would make good dataflow traces, and open questions
   the analysis couldn't resolve — unexplained seams, suspicious code, undocumented decisions.

## Notes

- Separate observation from inference: "X calls Y via Z" is read from code; "probably for
  testability" is a guess — label guesses.
- If docs and code disagree, the code is the truth and the disagreement is itself a finding.
- Time-box: for repos over ~100k lines, deliver the briefing from entry points + one traced
  flow + history, and list which areas were not read.
- Close full briefings with coverage: what was inspected, what was sampled or skipped, which
  claims depend on inference, and whether tests or a real invocation were run.
