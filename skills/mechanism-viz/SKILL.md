---
name: mechanism-viz
description: Plan and build a trace-grounded explanation of how a mechanism in your own system works, as a post with animated figures, an interactive explorer that replays one real instance, and benchmark charts. Use when writing a deep-dive or launch post for your own system, or visualizing how a request, lock, scheduler, cache, protocol, storage engine, or concurrent data structure behaves step by step. Do NOT use for a narrated lesson built from someone else's source (use explainer), an in-chat diagram (use show-me), a single illustration (use sketch-concept), or a standalone chart (use dataviz).
---

# mechanism-viz

Show one real instance passing through the mechanism, drawn from the system's own trace, with cost counted in a
unit the reader can see. The system describes itself; the viewer only reads and draws.

## Slots (REQUIRED before drawing anything)

Write each slot down. An empty slot is the usual reason a figure shows state without showing the idea.

| Slot | Fill with | bbtree example |
|---|---|---|
| Reader baseline | What they already know; teach only the delta | knows B-trees, not bbtree |
| Payoff | 2-3 concrete outcomes with numbers, shown first | 5x std BTreeMap, 30% less memory |
| Cost model | Unit price of each cost, levers ranked by it | miss ~100 ns, instruction ~0.5 ns, coherence >100 ns |
| Instance | The single thing the reader follows | one key's lookup |
| Cost unit | What gets drawn so the reader can count it | 64-byte cache line, solid dot = read |
| Trace source | Read-only inspect/trace API of the real system | `inspect` views, `trace_many` with a no-op watch |
| Views | Structure / resource / state, linked by one hover | path cards / memory map / slot table |
| Invariants | Shown in place, next to what they constrain | fences beside each node |
| Scenarios | Curated happy, contended, failure/recovery cases | "lookups worth seeing" |
| Time axis | For ordering or concurrency: lanes or time-runs-down | `batch-lanes`, `version-lock` |

For your own system, the cost unit is often an RPC, round trip, fsync, page, lock handoff, retry, or queue hop. For
a mechanism that is mostly about ordering, the time-axis slot carries the explanation. See
`references/bbtree-case.md` for the full mapping with a blank column to fill.

## Workflow

1. **Expose the trace.** Add a read-only inspect/trace interface to the system. The viewer consumes events and
   computes no semantics (offsets, decisions, which branch). Done when a test fails if the viewer and the code
   disagree, and the instrumentation adds no hot-path work, or its cost is measured and reported.
2. **Write the post skeleton.**
   - *What can it do?* The payoff with numbers and the charts.
   - *How it works.* The cost model, then the levers in ranked order. Each lever follows the same order:
     1. A toy thought experiment: the smallest case where the effect is countable, two alternatives side by
        side, one animation step per cost unit.
     2. How the lever applies to the real system.
     3. The measured results.
     4. Optionally, a bonus.
   - *How do we know it is correct?* The guards, each with a link: a reference implementation diffed under
     fuzzing, model checking or deterministic simulation, proofs, and the accountable human.
   - *Reviewers.*

   Done when every lever has a toy figure and a result number, and every number on screen traces to a data file.
3. **Draw the figures.** Each figure is one self-contained file. Motion either explains a step or enacts the
   measured quantity; nothing else moves. Done when reduced motion shows the complete final frame, and the
   legend defines the cost unit and what one step or turn is.
4. **Build the explorer** when readers gain from choosing their own instance. Give it one screen at a stated
   viewport, the URL as full state with a deterministic seed, curated scenarios, and step and play controls.
   Done when a copied link reproduces the same picture.
5. **Present the evidence.** Run `benchmark-checklist` on every claim. Highlight your own implementation in one
   color and keep the competitors in muted grey. Demote reference-only rows that have different semantics.
   Name the cells you lose. Compute the headline sentence from the data, not by hand. Done when the charts read
   raw result files directly.
6. **Audit and log.** After each iteration, critique against a heuristic list and score it. Append a dated
   decision to a design log: what was tried, why it was dropped, and whether it was the author's call or an
   audit finding. Done when the log has one entry per visual change.

## Gates

- One instance at a time; never the whole system rendered at once.
- Nothing drawn that the instrument cannot observe. A simulated duration, an inferred wait, or a modeled speedup
  is out, or it is labeled illustrative.
- Order is shown, not time, unless the time was measured.
- Every animation passes the motion test in step 3; decorative transitions fail.
- Text is at least 11 px, secondary text keeps 4.5:1 contrast, and touch targets on mobile are 44 px.
- Lower-is-better metrics read "23.7% fewer", not "1.3x fewer".

## Failure -> fix (from bbtree's design log)

| Tried | What went wrong | Fix |
|---|---|---|
| Whole structure drawn at scale | Read as color strips; said nothing | Follow one instance |
| State shown without the idea | No legend, views unlinked, no motion | Legend, terms explained in place, shared hover, scenarios |
| Step-by-step guide panel | Took half the space to repeat the inspector | Delete it; explain in place |
| Cost model simulated timing | Drawn speedups disagreed with measurements | Draw order only |
| Marked where threads wait | The trace cannot know (non-blocking) | Delete it |
| Per-op latency with fenced timers | The fences were half of what was measured | Report the back-to-back mean |

## References

- `references/implementation.md`: self-contained SVG figures, the step-based motion model, the single-variable
  playback timeline, URL state, chart motion, and post layout.
- `references/bbtree-case.md`: source pointers and the bbtree -> general -> yours mapping table.
