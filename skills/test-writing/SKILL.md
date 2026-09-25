---
name: test-writing
description: Writes, reviews, and prunes tests so the committed suite protects contracts and invariants rather than implementation. Use when writing or reviewing tests, choosing a test seam, scope, or mocks, adding property, fuzz, or regression tests, fixing brittle tests, auditing a bloated suite, or deciding whether a failing test means the code or the test is wrong. Do NOT use for TLA+ model checking (use tla-model).
---

# test-writing

Verify aggressively; commit sparingly. A generated test costs nothing to write and still costs every future refactor and reader. A test that locks in the wrong shape is worse than none: it will be believed, and in an agentic loop the suite is the acceptance criteria being optimized against.

## Workflow

1. **Find the seam.** Name the interface that survives a full internal rewrite: for a store, `Open/Read/Write/Save/Restore`, not the fetcher, cache, retryer, or chunk layout beneath it. Done when you can say what a rewrite behind it is free to change. An export, flag, or hook that only tests call is not a seam; test through its production caller.
2. **State the oracle first.** For each expected value, name its source: requirement, design doc, API contract, reference implementation, or hand computation. Done when no expected value comes from running the code under test.
3. **Explore ephemerally.** Properties, fuzzing, differential runs, fault injection, random operation sequences against a simple model — run them in the loop, in test files you will delete before the report. Done when every exploration file is either admitted by step 4 or gone.
4. **Admit or discard.** A test enters the repo only if every answer is yes; the same gate judges existing tests:
   - It protects a contract, invariant, failure/recovery semantic, compatibility promise, or a bug that happened.
   - Its oracle is independent of the implementation.
   - It survives an internal rewrite behind the seam.
   - It is the contract's one owner, at the strongest boundary. Another layer earns a test only for a risk the owner cannot reach.
   - Its name claims no more than its input exercises.

   Exploration found a bug → shrink it to the smallest stable case and admit only that. Found nothing → delete it.
5. **Write it in long-lasting form.** Test logic once; cases as data — table rows, `testdata` files, txtar archives, scripts. Failures print input, got, and want. Golden files regenerate through an update flag, and every regenerated diff is read. Done when the next regression is a one-line or one-file addition.
6. **See it fail.** Break the behavior — revert the fix for a regression, otherwise mutate the line the contract rests on — and run the suite. The test fails for its stated reason, and its failure names one cause. An existing test also going red means yours is a duplicate unless it reaches a risk that owner cannot; drop or move it. For a negative assertion, remove the guard under test: still green means it passed on another guard. Restore the code and rerun green. Done when every kept test has been red for its own reason.

## Existing suites

An existing test that fails the gate is suspect, not deletable: it may be the only guard of a contract. Changing, merging, or deleting one requires the user's confirmation — propose each with the evidence in REFERENCE, then apply only what they approve.

## Routing

Place the suite where the complexity lives:

- **Inside the process** — algorithms, parsers, domain rules. Test deeply through the public API; prefer properties or exhaustive small inputs over hand-picked examples.
- **At the boundaries** — services, glue, orchestration. The service is the unit; test from its edges with realistic fixtures.
- **In the state space** — storage, replication, recovery, concurrency. Random operation sequences against a sequential model, with crash, restart, and injected faults as operations. For the design itself, use `tla-model`.

Widen the boundary until setup gets expensive or the test stops being hermetic, then stop. IO is not the criterion: loopback HTTP, in-process SQLite, and a temp dir are cheap; a shared or remote target is not. A deployed environment earns only wiring and real third-party behavior. Trivial glue gets no test.

## Traps

- **Repairing the test instead of the code.** A failing test is a bug report until shown otherwise. Never weaken an assertion, add a mock, or skip to reach green. Changing a test and its code in one commit needs a stated reason both were wrong.
- **Trusting your own oracle.** A failing property is a hypothesis: the code, the property, or the generator is wrong. Recheck the property against the spec before calling it a bug.
- **Mutating the environment to get green.** Seeding rows, flipping flags, restarting services, or draining queues passes nothing that matters. Reproduce a shared-environment failure hermetically, or say you could not.
- **Hiding failures.** No retries or exception handling that turn broken behavior green; bounded waits on a public completion signal are fine. Inject the clock.
- **Mocking by default.** Real local dependencies when cheap and deterministic; fakes at unmanaged boundaries; communication mocks only for outbound calls you cannot observe otherwise.

## Report (REQUIRED)

End every test-writing task with:

- **Kept:** each committed test — the behavior it protects, its oracle source, and the break that turned it red.
- **Explored:** what ran and was discarded, and what it found.
- **Proposed:** changes to existing tests awaiting confirmation.

See [REFERENCE.md](REFERENCE.md) for case formats, exploration, state-machine and compatibility tests, pruning evidence, test sizing, and deployed environments.
