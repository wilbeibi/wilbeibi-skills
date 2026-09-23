---
name: tla-model
description: Models concurrent and distributed designs in TLA+ or PlusCal and checks them with the TLC model checker. Use when asked to write, review, or debug a TLA+ spec, .tla/.cfg files, or TLC output, or to model-check or formally verify a protocol, lock, lease, consensus, replication, WAL, retry, or race condition. Do NOT use for unit or property-based tests (use test-writing) or for Lean, Coq, Dafny, or Verus proofs.
compatibility: uv (scripts/tlc.py runs as a uv script, Python 3.10+, no dependencies); Java 11+ and tla2tools.jar (scripts/tlc.py fetch downloads it).
---

# tla-model

The deliverable is a checked argument, not a `.tla` file: every property traces to a requirement, every action to an implementation event, and every green result survives mutation. TLC finding nothing means *no counterexample in this model at these bounds*; never call it a proof.

## Setup

```bash
scripts/tlc.py check examples/MiniLock.tla -c examples/MiniLock.cfg   # expect "result: clean", exit 0
scripts/tlc.py fetch            # if tla2tools.jar is missing; or set TLA2TOOLS_JAR
```

Missing Java: ask the user to install a JRE 11+; do not download one. `scripts/test_tlc.sh` self-tests the helper. PlusCal: run `scripts/tlc.py translate Spec.tla` before every check.

`tlc.py check` prints result, state counts, per-action coverage, the full trace, and `VACUITY:` flags. Exit 0 clean, 1 violation, 2 vacuous, 3 setup/parse error. `tlc.py mutant` applies one exact-match edit to a copy and exits 0 only when the named property catches it (`KILLED`).

A question about an existing spec or TLC output needs only `check` and the matching step below. Create files only when asked to model or verify a system. Keep that work in `spec/` beside the code: `modeling-brief.md`, `<Name>.tla`, one cfg per concern, `cex/`, `report.md`.

## Loop

1. **Brief before spec.** Fill [BRIEF-TEMPLATE.md](BRIEF-TEMPLATE.md) into `spec/modeling-brief.md`. Aim the question where bugs have lived: search `git log` and the issue tracker for fix, race, crash, deadlock, corrupt, and stale on the core files, group the hits by mechanism, and note where the code departs from the reference algorithm. Build the event→action table from the code you read, citing `file:line`, not from the paper the design resembles; a textbook Raft is not the user's Raft. List every open question and stop until the user answers. *Done:* every REQUIRED slot filled; the user has confirmed the fault model, atomicity, and exclusions.
2. **Grow the spec one layer at a time**: variables → `TypeOK` → `Init` → one named action → `Next`, then the next action. Run `check` after each layer. Give each action a comment naming its implementation event. *Done:* clean, no `VACUITY` flags, every action fired.
3. **Safety.** Add the invariants from the brief to a safety cfg with `CHECK_DEADLOCK TRUE`; turn deadlock checking off only when termination is the intended end state, and say so. Bound fault injections (crashes, drops, timeouts) with counters; leave normal operations unbounded. Run the bounds matrix from the brief, smallest first, plus one tight cfg per bug-history mechanism. A violation goes to step 6. *Done:* every brief property is enabled in at least one cfg, checked by reading the cfgs.
4. **Liveness, only after safety is clean.** Use one cfg per temporal property: TLC does not name which temporal property failed. Never use `SYMMETRY` in a liveness cfg. Each `WF`/`SF` term carries a comment naming the real mechanism behind it (FIFO queue, retransmit, lease expiry). If no mechanism exists, delete the term and report the starvation trace as a finding.
5. **Prove the properties bite.** For each invariant, delete the guard it depends on; for each liveness property, drop its fairness term:
   ```bash
   scripts/tlc.py mutant spec/Lock.tla -c spec/Safety.cfg --replace '/\ lock = None' '/\ TRUE' --expect Mutex
   ```
   `OLD` must match exactly once, so include the neighbouring text if it doesn't. A mutant that no longer parses exits 3 and proves nothing. A `SURVIVED` result means the property is too weak, redundant, or guards an unreachable action. Fix it and ask the user before changing any property's meaning. *Done:* every property has at least one `KILLED` mutant, recorded in the report.
6. **Counterexample loop.** Write each violation to `spec/cex/NNN.md` from [CEX-TEMPLATE.md](CEX-TEMPLATE.md):
   - Find the first state where things go wrong.
   - Map each step to a code event and a fault the brief allows.
   - Classify it: design, spec, property, config/bounds, mapping, or fairness/assumption.
   - REQUIRED: change exactly one of model, property, or cfg per round. Replay the trace, then rerun the whole matrix.
   - Never weaken a property, add fairness, or add a `CONSTRAINT` to turn a run green without the user's approval.
7. **Back to code.** A design-class counterexample is confirmed only when a test or fault-injection run against the implementation reproduces it and has actually been run. Otherwise report it as unconfirmed with the missing step. For high-stakes specs, add refinement or trace validation ([REFERENCE.md](REFERENCE.md#linking-spec-to-code)).
8. **Independent review.** Hand only the brief, spec, cfgs, and report to a reviewer with fresh context, such as a new session or another person. Ask them to attack it with the review checklist in [REFERENCE.md](REFERENCE.md#review-checklist). Fold the findings into step 6.

## Report (`spec/report.md`)

- Per cfg: TLC version, constants and bounds, generated/distinct states, depth, and result.
- Mutants: each property, its mutation, and KILLED/SURVIVED.
- Counterexamples: id, class, confirmed or unconfirmed, fix, and linked test or issue.
- Assumptions in force: fault model, atomicity choices, every fairness term and its mechanism, every `CONSTRAINT`.
- Not verified: behaviors outside the bounds or exclusions, and any claim that needs a parametric proof (TLAPS or an inductive invariant).

Claim only what the report shows. "No counterexample with 3 nodes, 2 values, queue ≤ 2" is the strongest sentence a green run supports.
