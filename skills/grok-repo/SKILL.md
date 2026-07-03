---
name: grok-repo
description: Understand an unfamiliar codebase — either a full briefing (purpose, architecture, seams, design taste, commit-history rationale, standout code) or a scoped dataflow trace of one subsystem. Use when asked to "understand this repo", "explain this codebase", "give me a tour", "how does X work here", "trace how data flows", "where does this value come from", or "why is it designed this way". Do NOT use to assess repo health/popularity (use repo-eval) or to review a diff (use a code-review skill).
---

# grok-repo

Read a repository the way a senior engineer satisfies curiosity: purpose first, structure
second, mechanics third, history to explain the *why*, taste judgments only after evidence.
Two output modes — pick by the question, every claim cites a file path or commit:

- **Scoped question** ("how does X work?", "where does Y come from?") → a **dataflow trace**.
- **Whole-repo question** ("explain this codebase", "give me a tour") → the **full briefing**.

## Dataflow trace (scoped mode)

Answer by following one datum — a request, message, config value, file — from where it
enters to where its effect lands. No briefing boilerplate; the trace *is* the answer.

- Lead with a hop chain, one line per hop, each cited:
  `POST /jobs (api/handler.go:41) → validate → Job{} (job.go:12) → enqueue (redis) → worker.Run (worker.go:88) → status written (store.go:130)`
- At each hop say what holds the data (type/struct/schema) and what transforms it.
  Call out every **shape change or rename across a boundary** (JSON→struct, field renamed,
  enum remapped) — that's where readers get lost.
- Mark the seams crossed (serialization, queue, process/network boundary, goroutine/thread
  handoff) since each one is a place the trace can silently fork or drop.
- Close with: side flows deliberately skipped, error/edge paths worth a second trace, and
  anything surprising found along the way.
- If the *why* of a hop is odd, spot-check history: `git log -S '<symbol>'` or blame the line.

## Reading order (full briefing)

Work top-down; each layer constrains the next. On large repos, sample representative
components instead of exhausting the tree — say what you sampled.

1. **Orient** — README, docs/, top-level layout, manifest (go.mod/package.json/Cargo.toml),
   Makefile/CI config. Find the entry points (`main`, CLI commands, server bootstrap, exported API).
   If it builds/tests cheaply, run it — a passing test suite and one real invocation anchor
   everything that follows.
2. **Trace one real flow** end-to-end (a request, a command, a build) before generalizing.
   Architecture claims made without a trace are usually wrong.
3. **Map components and seams** — where modules meet: interfaces, wire protocols, DB schemas,
   queues, plugin points, process boundaries. For each seam ask *why here*: testability,
   swap-ability, deploy boundary, team boundary, or accident. Note which side owns the types.
4. **Mine git history** for rationale (commands below). History answers "why is it like this"
   when the code can't.
5. **Judge taste and pick highlights** last, from the evidence already gathered.

## Git archaeology

```bash
scripts/archaeology.sh [repo-dir]   # one-shot digest: founding commits, recent direction,
                                    # authors, hot files, biggest commits
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
5. **Beautiful code** — 1-3 pieces that are novel, dense-but-clear, or do a lot with a
   little (the `rr.go`-in-oscar standard). Quote a short excerpt and say precisely what
   makes it good: the invariant it protects, the cases it collapses, the API it keeps honest.
6. **Hooks for curiosity** — the project's own vocabulary (5-10 jargon terms → the file
   that defines each), 2-3 flows that would make good dataflow traces, and open questions
   the analysis couldn't resolve — unexplained seams, suspicious code, undocumented decisions.

## Notes

- Separate observation from inference: "X calls Y via Z" is read from code; "probably for
  testability" is a guess — label guesses.
- If docs and code disagree, the code is the truth and the disagreement is itself a finding.
- Time-box: for repos over ~100k lines, deliver the briefing from entry points + one traced
  flow + history, and list which areas were not read.
