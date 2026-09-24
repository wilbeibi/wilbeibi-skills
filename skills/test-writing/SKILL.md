---
name: test-writing
description: Writes, reviews, and prunes tests so the committed suite protects contracts and invariants rather than implementation. Use when writing or reviewing tests, choosing a test seam, scope, or mocks, adding property, fuzz, or regression tests, fixing brittle tests, auditing a bloated suite, or deciding whether a failing test means the code or the test is wrong. Do NOT use for TLA+ model checking (use tla-model).
---

# test-writing

Verify aggressively; commit sparingly. A generated test costs nothing to write and still costs every future refactor and reader. The committed suite holds contracts, invariants, failure and recovery semantics, compatibility, and real regressions — a generated test is not a repo test.

## Workflow

1. **Find the seam.** Name the interface that survives a full internal rewrite: for a store, `Open/Read/Write/Save/Restore`, not the fetcher, cache, retryer, or chunk layout beneath it. Done when you can say what a rewrite behind it is free to change.
2. **State the oracle first.** For each expected value, name its source: requirement, design doc, API contract, reference implementation, or hand computation. Done when no expected value comes from running the code under test.
3. **Explore ephemerally.** Properties, fuzzing, differential runs, fault injection, random operation sequences against a simple model — run them in the loop, in test files you will delete before the report. Done when every exploration file is either admitted by step 4 or gone.
4. **Admit or discard.** A test enters the repo only if every answer is yes:
   - It protects a contract, invariant, failure/recovery semantic, compatibility promise, or a bug that happened.
   - Its oracle is independent of the implementation.
   - It survives an internal rewrite behind the seam.
   - No existing test already says it.

   Exploration found a bug → shrink it to the smallest stable case and admit only that. Found nothing → delete it.
5. **Write it in long-lasting form.** Test logic once; cases as data — table rows, `testdata` files, txtar archives, scripts. Failures print input, got, and want. Golden files regenerate through an update flag, and every regenerated diff is read. Done when the next regression is a one-line or one-file addition.

## Existing suites

New tests beside existing ones follow the workflow. Changing, merging, or deleting existing tests — including ones that pin internals — requires the user's confirmation: propose each change with its reason, then apply only what they approve. Never propose deleting a regression test whose bug you cannot identify.

## Routing

Place the suite where the complexity lives:

- **Inside the process** — algorithms, parsers, domain rules. Test deeply through the public API; prefer properties or exhaustive small inputs over hand-picked examples.
- **At the boundaries** — services, glue, orchestration. The service is the unit; test from its edges with realistic fixtures.
- **In the state space** — storage, replication, recovery, concurrency. Random operation sequences against a sequential model, with crash, restart, and injected faults as operations. For the design itself, use `tla-model`.

Widen the boundary until setup gets expensive or the test stops being hermetic, then stop. IO is not the criterion: loopback HTTP, in-process SQLite, and a temp dir are cheap; a shared or remote target is not. A deployed environment earns only wiring and real third-party behavior. Trivial glue gets no test.

## Traps

- **Repairing the test instead of the code.** Never weaken an assertion, add a mock, or skip to reach green. Changing a test and its code in one commit needs a stated reason both were wrong.
- **Trusting your own oracle.** A failing property is a hypothesis: the code, the property, or the generator is wrong. Recheck the property against the spec before calling it a bug.
- **Mutating the environment to get green.** Seeding rows, flipping flags, restarting services, or draining queues passes nothing that matters. Reproduce a shared-environment failure hermetically, or say you could not.
- **Blind-accepting snapshots.** Running update mode without reading the diff is an untested change.
- **Hiding failures.** No retries or exception handling that turn broken behavior green; bounded waits on a public completion signal are fine. Inject the clock.
- **Mocking by default.** Real local dependencies when cheap and deterministic; fakes at unmanaged boundaries; communication mocks only for outbound calls you cannot observe otherwise.

## Report (REQUIRED)

End every test-writing task with:

- **Kept:** each committed test — the behavior it protects and its oracle source.
- **Explored:** what ran and was discarded, and what it found.
- **Proposed:** changes to existing tests awaiting confirmation.

## Quality bar

A test earns its place when it fails when behavior breaks, stays green through refactors, and names one cause when it fails. A test that locks in the wrong shape is worse than none, because it will be believed; in an agentic loop the suite is the acceptance criteria being optimized against.

See [REFERENCE.md](REFERENCE.md) for the long-lasting form, exploration and what to keep from it, state-machine and compatibility tests, pruning, test sizing, and deployed environments.
