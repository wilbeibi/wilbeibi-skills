---
name: test-writing
description: Write and repair tests that verify observable behavior, not implementation. Use when writing or reviewing tests, choosing test scope or mocks, fixing brittle tests, or deciding whether a failing test means the code is wrong or the test is.
---

# test-writing

Test behavior through the widest boundary that stays hermetic and cheap to set up.

Choose verification proportional to the change and complete the project's required checks.
Do not expand production scope merely to follow a preferred testing style.

## Habits to correct

- **Writing the test from the code you just wrote.** Reading the implementation and asserting what it does bakes in its bugs. Derive expected values from the requirement and compute them by hand. If you cannot state the expected answer without running the code, you do not understand the behavior well enough to test it yet.
- **Copying actual output into expected.** Running the test, seeing it fail, and pasting the actual value produces a recording, not a test. Same for widening a tolerance until it passes.
- **Mirroring code structure.** One test file per source file and one test per public method is a unit-of-*code* suite. Test units of *behavior*; how many classes implement one is irrelevant.
- **Mocking by default.** Prefer real local dependencies when cheap and deterministic. Use a fake or mock at external boundaries when it gives a reliable signal; its presence alone does not justify a redesign.
- **Repairing the test instead of the code.** A failing test is a hypothesis about the code until proven otherwise. Never weaken an assertion, add a mock, or skip a test to reach green. Changing a test and the code it covers in one commit needs a stated reason why both were wrong.
- **Mutating the environment to get green.** Seeding a row by hand, flipping a flag, restarting a service, or draining a queue is the deployment-tier version of weakening an assertion — it passes, nothing is fixed, and the shared state has drifted for everyone else.
- **Debugging against a shared environment by trial and error.** A red run there is ambiguous by construction: your change, someone else's, stale data, or a broken env. Reproduce it locally in a hermetic test first; if you cannot, say so rather than guessing.
- **Blind-accepting snapshots.** Running the update mode without reading the diff turns the expect-test loop into an auto-approval loop. Treat an unreviewed snapshot update as an untested change.
- **Generating volume.** Cheap tests become near-duplicates that break together and bury the one real failure. Coverage percentage and test count are not goals.
- **Hiding failures.** Avoid retries or exception handling that turn a broken behavior green. Bounded waits and timeouts are appropriate for asynchronous behavior when failures remain clear.
- **Testing the framework.** Asserting that the ORM saves or the stdlib sorts tests someone else's code.

In an agentic loop the suite is not a safety net — it is the acceptance criteria being optimized against. A tautological suite does not merely miss bugs, it steers the work wrong.

## Routing

First ask where the complexity actually lives, because it sets the shape of the whole suite:

- **Inside the process** — algorithms, domain rules, parsers. Test deeply at the domain layer; boundary tests only prove wiring.
- **At the boundaries** — services, glue, orchestration. The contract is the product, so test from the edges with realistic fixtures and keep implementation-detail tests to the few genuinely complex isolated pieces.

Then:

1. Trivial glue/getters? Skip — a test that cannot fail is noise in the failure signal.
2. Pure logic, few dependencies? Test through the public API. Prefer property or exhaustive tests over hand-picked examples.
3. Orchestration, real I/O, controller/database/filesystem behavior? Integration test — the module or service in isolation, its own dependencies real, its collaborators faked at the edge.
4. Complex *and* dependency-heavy? Extract the domain logic and test that; leave a thin orchestrator for integration tests.
5. Deployment, wiring, real third-party behavior, or infrastructure under load? Only that needs a deployed environment. Prefer ephemeral (per-PR stack, compose file) over shared staging.

Widen the boundary until setup gets expensive or the test stops being hermetic, then stop. IO is not the criterion — loopback HTTP and an in-process SQLite are cheap, while a shared remote database is not. What costs you is setup time, resource footprint, and anything you do not control.

## Rules

- Keep routine tests independent of shared external services. Use explicitly scoped integration or end-to-end checks when verifying a real external contract is the task; report environment failures separately.
- A failure must localize the defect. A red result that only says "something in the system is wrong" is nearly worthless in a loop, because the next step is a guess.
- One test = one scenario a domain expert would recognize. Name it for the behavior, not the method.
- Prefer output-based tests, then state-based; use communication mocks only for compatibility-sensitive external calls.
- Prefer fakes for unmanaged dependencies and real local databases/filesystems where practical. Match the boundary to the behavior under test.
- Prefer an injected clock or the project's established fake-timer mechanism for time-dependent behavior. Await asynchronous work or observe its completion through a bounded public signal.
- Arrange, Act, Assert. Keep Act to one operation. Assert narrowly, so a failure names one cause.
- Keep setup scoped to the test that needs it. Shared class-level fixtures tax every individual test run, which is how you debug.
- Prefer existing public observability for behavior such as cache hits or fallback use. Add instrumentation only when the requested contract needs it, not merely to assert an implementation branch.

## Red Flags

- Expected value traceable to actual output rather than to a requirement.
- Test duplicates production logic instead of hardcoding the answer.
- Test breaks on refactor because it checks internals, private methods, call order, or class layout.
- Passing requires several services running, or a shared environment to be healthy.
- Database/filesystem behavior mocked away.
- Unbounded sleeps/retries or conditionals that suppress failures.
- A test changed in the same commit as the code it covers, with no explanation.

## Quality Bar

Judge a test by whether it is a trustworthy verification signal: it fails when behavior breaks, stays green through refactors, and names one obvious cause when it fails. Resistance to refactoring matters most — it is what makes a green suite mean anything. A test that locks in the wrong shape is worse than no test, because it will be believed.

See [REFERENCE.md](REFERENCE.md) for test sizing, the pyramid/honeycomb choice, the check() seam, observability points, expect tests, property and fuzz testing, humble-object refactors, and database patterns.
