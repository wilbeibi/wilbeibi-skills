---
name: grok-repo
description: Explain an unfamiliar codebase through a repository briefing, dataflow trace, or reconstruction of why and how a change was made. Use when asked for a repo tour, design tradeoffs, how something works, where a value comes from, or why a feature changed. Not for repo health (use repo-eval).
---

# grok-repo

Read declared intent, structure, mechanics, then history for the *why*; judge taste only after evidence.
Pick one mode by the question; keep claims traceable to code and first-party sources:

- **Scoped question** ("how does X work?", "where does Y come from?") → a **dataflow trace**.
- **Change question** ("why was X added?", "how did this feature evolve?") → **change archaeology**.
- **Whole-repo question** ("explain this codebase", "give me a tour") → the **full briefing**.

## DeepWiki for open-source repositories

For a public open-source repository, check its existing DeepWiki when accessible. Use the
actual repository's `owner/repo`: with DeepWiki MCP, start with `read_wiki_structure`, then
read relevant sections from `read_wiki_contents`; use `ask_wiki_question` for focused gaps.
The website at `https://deepwiki.com/<owner>/<repo>` is another reading route.

Record the indexed revision or date when shown and compare it with the checkout. If absent,
date it yourself: pick a symbol the wiki names that is gone at HEAD and `git log -S '<symbol>'`
finds its removal; failing that, treat the wiki's version as unknown. Use its explanations of flows, data representations,
and lifecycles to find missed questions and clearer ways to explain the system. Verify
consequential claims against the pinned code, tests, and first-party history, especially
when the wiki compresses a guarantee or disagrees with the initial model. Cite those
verified sources for design conclusions; keep generated explanations distinct from author intent.

If unavailable or unindexed, continue with primary sources. Start indexing only when the
user explicitly requests it.

## Dataflow trace (scoped mode)

Follow one datum — request, message, config value, file — from entry to effect. The trace is the answer.

- Lead with a hop chain, one line per hop, each cited:
  `POST /jobs (api/handler.go:41) → validate → Job{} (job.go:12) → enqueue (redis) → worker.Run (worker.go:88) → status written (store.go:130)`
  That cited form is for the notes. The human reads the same chain in words (hop, holder, what
  changed shape) with the files available on request.
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
   Releases bound the search: `git tag --contains <sha>` names the first release carrying a commit,
   and `git log <prev-tag>..<tag> -- <path>` narrows the range when the question is version-shaped
   ("when did X change?", "why did upgrading break Y?").
3. **Read commits, not just subjects** — `git show` the introduction and its parent. Bodies,
   tests, deleted code, and nearby fixes are evidence; diffs alone imply.
4. **Search the issue tracker** — the pressure for a change is usually filed before it is
   committed, so search issues by the same literals used against `git log -S`, and read
   closed ones: a rejected proposal explains a design as well as an accepted one.
   ```bash
   gh issue list --search '<term>' --state all --limit 30
   gh issue view <n> --comments
   ```
   Weak git history (shallow, squashed, imported) shifts the rationale here — go to the
   tracker first, not last. A tracker with under ~10 issues is not the record either: the
   arguments then live in PR review threads (the most-commented merged PRs; closed-unmerged
   PRs are its not-planned issues) and in status-headed design docs. Use an available GitHub connector/API if `gh` is unavailable;
   if the tracker cannot be accessed, say so rather than presenting git-only evidence as
   the whole record. An open issue is a historical claim: check whether current code and
   tests still exhibit it before treating it as an unresolved defect.
5. **Pull the review thread** — the argument for a change usually outlives the commit message
   in its PR. Recover the number from the merge that carried the commit, then read the
   discussion, not just the description:
   ```bash
   git log --merges --ancestry-path --oneline <sha>..HEAD | tail -1
   gh pr view <n> --json body,comments,reviews   # --comments cannot combine with --json; follow "Fixes #n" back
   gh pr list --state merged --limit 200 --json number,title,comments --jq 'sort_by(-(.comments|length))[:10]'
   ```
6. **Trace the arc** — inspect follow-up fixes, refactors, reverts, and blame on surviving lines.

Lead with **before → pressure/evidence → introduction → corrections/reversals → current form**.
Cite SHA + path per stage in the notes, dates and PR numbers for the human; close with supported rationale, rejected alternatives, unresolved
context, and history limits. Never turn commit order into causality or invent motivation.

## Reading order (full briefing)

Work top-down. Pin the repository revision and sample representative components on large
repos; say what you sampled.

1. **Orient** — read relevant first-party prose before code: README/docs and any architecture,
   design-principle, ADR/RFC, or governance docs. Verify their goals, non-goals, invariants, and
   rejected alternatives against code and history. A tracked `AGENTS.md` evidences workflow and
   conventions within its scope, not automatically product intent. Rank docs by their status
   headers (`Status:`, `Decision:`, `Superseded`, `Draft`) and any unpublished list before
   trusting them equally. A repo written for agents (AGENTS.md, repo skills, AI-assistance lines
   in commits) usually has long commit bodies (`git log --format='%h %s%n%b'`), bot-style
   severity-tiered reviews and a near-empty tracker; report that as a process finding. Then
   scan layout, manifests, build/CI, and entry points; run it if cheap.
2. **Trace one real flow** end-to-end (a request, a command, a build) before generalizing.
   Architecture claims made without a trace are usually wrong.
   Then choose one important promise and trace a failure or boundary case that could break
   it: partial failure, cancellation, lost response after commit, or competing ownership.
   Identify the authoritative state and the invariant at the boundary; distinguish the
   guarantee implemented in code from the cases tested and any production evidence.
   On repos over ~200k lines, hand the two traces to two subagents with a fixed deliverable:
   a hop chain naming the holder type and seam at each hop, the authoritative state, and
   listed open questions; run history, taste and DeepWiki yourself in parallel.
3. **Map components and seams** — where modules meet: interfaces, wire protocols, DB schemas,
   queues, plugin points, process boundaries. For each seam ask *why here*: testability,
   swap-ability, deploy boundary, team boundary, or accident. Note which side owns the types.
4. **Mine git history** for rationale (commands below). First check whether history is shallow,
   squashed, imported, generated, or vendor-heavy; weak history produces clues, not rationale,
   and pushes the *why* into the issue tracker, or, when that is barely used, into PR review
   threads and commit bodies. The digest's HISTORY, BODIES and TRACKER lines say which.
5. **Explain decisions and pick highlights** last. For consequential findings, connect
   constraint → mechanism → code/history evidence → benefit → cost or failure condition →
   reusable lesson. Look for a counterexample or reversal that could change the judgment;
   no need to print these fields mechanically for every finding.

When a key mechanism crosses a dependency boundary, follow the pinned implementation or
fork and inspect its actual delta; stop at the verified contract if source is unavailable.
For a consequential comparison or novelty claim, check the same mechanism in a small
number of relevant alternatives. Distinguish a new algorithm from reuse, a new combination,
or adaptation to a workload; label unverified comparisons. Compare guarantees and constraints,
not just features. Add this evidence where it explains a decision, rather than a separate
mandatory competitor survey.

## Git archaeology

```bash
scripts/archaeology.sh [repo-dir]         # digest first, then drill into what it surfaces
git show --stat <sha>                     # read the big commits' messages in full
git log --follow --oneline -- <hot-file>  # evolution of a load-bearing file
git log -S '<symbol>' --oneline           # when/why a concept appeared or died
```

- Find "key changes" by their effect on behavior, invariants, or constraints. Size, recency,
  and words like "refactor" or "redesign" are leads; a small durability fix may matter more
  than a large rewrite. Commit messages can explain tradeoffs — read them with the diff.
- Cross-reference **frequently touched × fix-touched** to choose files for closer reading.
  This is a lead, not proof of fragility: formatting, generated code, and long-lived files
  can dominate counts.
- **Reverts are possible negative rationale**: verify that a rollback concerns the current
  design before using it to explain why an alternative did not survive.
- Test a "team boundary" seam hypothesis with `git shortlog -sn -- <dir>` on each side:
  disjoint author sets support but do not establish it; the same names weaken the hypothesis.
- `git blame` a surprising line before calling it a wart; it often has a fix-commit story.
- For a public repo, if its history leaves consequential rationale unresolved, check project-specific
  first-party posts by core maintainers—identified by governance/ownership and sustained contribution—
  in blogs, talks, GitHub discussions, or X/Twitter. Cite author, date, and direct URL; treat individual
  or retrospective statements as context unless repository evidence corroborates them.

## Briefing contract

A full briefing is two deliverables. The **briefing** is for a human's attention: about 1,000
words, read in one sitting. Open with a short provenance paragraph (revision, history depth,
size with the command that counted it, stack, which flows were traced, the one hedge). Then
five to seven groups
named by domain, three or four bullets each, every bullet one idea the reader could repeat
afterwards. Close with "Most relevant to <reader purpose>": three ranked items and an offer to
go deeper. The **notes** are for the agent that answers follow-ups: hop chains with file:line,
compare-site tables, the vocabulary → file map, evidence grade per claim, coverage and unread
areas, open questions with issue links. Every briefing claim must resolve in the notes on the
first question; detail the human did not ask for stays there.

Choose the briefing's shape from the reader's purpose, independently of the research mode.
For **code navigation**, print the sections below in order and point concepts at the files
that teach them. For **design analysis**, group by domain and use the sections as a coverage
checklist, not as headings. Lead each group with the sentence to remember. Prefer decisions
and their consequences to inventories. A surprise (a doc the code contradicts, a guarantee
checked unevenly) goes in the group where it matters, as one sentence, not in a list at the end.

**Language.** Open each bullet with a label of at most ten words, then a period. One fact per
sentence, 10-18 words; variants as parallel sentences, never a semicolon list. Order: the
choice, how it works, what it prevents or costs, one concrete anchor (a literal or a number
that is the point), at most one citation at the end in parentheses: a bare doc path or PR
number, never file:line. Make a component or "they" the
subject; code does not describe itself. Attach a consequence with one "so". Introduce a
project term once in quotes with a plain gloss, then use it bare. Hedge once, in the
provenance paragraph; afterwards the citation form carries the evidence grade (doc path, PR
number, "traced", "my guess"), never a tag. A bullet over ~90 words is two mechanisms: split
it or move one to the notes. No file:line, hop chain, table or code excerpt in the briefing.
`scripts/prose-check.py <briefing.md>` measures these bands; it is advisory.

Coverage checklist (the notes hold the detail; the briefing keeps what a reader would repeat):

0. **Problem & users** — what pain it removes, for whom, and what the project deliberately
   does *not* do (non-goals are often stated in README/docs or early commits). Issues closed as
   not-planned state non-goals more bluntly than docs do: `gh issue list --state closed --search
   'reason:not-planned'`, plus the project's own refusal label if it has one (`--label wontfix`).
   GitHub issue search has no `OR`, so run one qualifier at a time. Cite the issue number.
1. **Architecture** — the 3-7 major components and the shape connecting them (pipeline,
   hub-and-spoke, layered, plugin host…). One paragraph plus a compact diagram or list.
   Check that the reader can distinguish the user-facing interface from internal contracts,
   name what crosses important boundaries, and locate authoritative state. Mark process or
   network boundaries where library boxes could look like separate services. Follow the
   representative operation through the map; add another view only when changes over time
   or in data representation remain unclear. Keep concept and implementation labels together
   when they denote one role.
2. **Design taste** — the authors' consistent choices, each backed by two or more examples:
   dependency policy, error-handling style, abstraction depth, naming, testing philosophy,
   concurrency model. Taste is what repeats; one instance is noise.
   Explain which states or special cases a choice removes, and where complexity moves;
   fewer lines or dependencies alone do not establish simplicity.
3. **Components & seams** — per component: responsibility, its inbound/outbound seams, and
   why the boundary sits there. Flag seams that leak (imports crossing the "wrong" way).
4. **History & rationale** — 3-6 pivotal commits/eras and what each reveals about why the
   design is what it is (e.g. "storage was swapped behind an interface in PR #212, after X"; the SHA goes in the notes).
5. **Beautiful code** — if evidence warrants it, show 1-3 pieces that are novel,
   dense-but-clear, or do a lot with a little. Quote a short excerpt in the notes when useful and explain what
   makes it good: the invariant it protects, the cases it collapses, or the API it keeps honest.
   Include small utilities and test harnesses when useful, not just core algorithms. State
   the assumptions and costs that determine where a technique can be reused.
   If none stands out in the sampled code, say so instead of manufacturing praise.
6. **Hooks for curiosity** — the project's own vocabulary (5-10 jargon terms → the file
   that defines each, kept in the notes), 2-3 flows that would make good dataflow traces, and open questions
   the analysis couldn't resolve — unexplained seams, suspicious code, undocumented decisions.
   Check the open issues before writing this section: they say which of your questions the
   maintainers already know about (link the issue) and which are genuinely unexamined, and
   the oldest open ones often mark the design's real soft spots. Note if the tracker is
   unused or disabled — that is itself a finding about how the project is maintained.

## Notes

- Separate observation from inference: "X calls Y via Z" is read from code; "probably for
  testability" is a guess — label guesses.
- Docs evidence stated intent; code determines current behavior. If they disagree, report both.
- Time-box large repos around entry points, one normal and one failure/boundary trace, and
  history. Stop when the model explains those paths and important judgments have evidence;
  list unresolved questions and unread areas rather than filling every section with guesses.
- Close the notes, not the briefing, with the revision and coverage: what was inspected, what
  was sampled or skipped, which claims depend on inference, and whether tests or a real
  invocation were run. Count with a stated command and check it: filter non-members,
  de-duplicate `name/` and `name.rs`, and recount every number the briefing states. Keep "worth learning from" separate from "ready to adopt"; defer full health scoring
  to repo-eval.
