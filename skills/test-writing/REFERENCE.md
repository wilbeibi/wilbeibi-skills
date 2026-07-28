# test-writing — Reference

Patterns and worked examples referenced from `SKILL.md`.

## The check() seam

Tests that each call the API directly all break when the signature changes.

**Before** — every test coupled to the signature:
```
test_empty()     { assert binary_search([], 0) == false }
test_singleton() { assert binary_search([92], 92) == true }
// ...a dozen more
```

**After** — one seam:
```
check(haystack, needle, expected) {
  assert binary_search(haystack, needle) == expected
}

test_empty()     { check([], 0, false) }
test_singleton() { check([92], 92, true) }
```

When `binary_search` starts returning an insertion index instead of a bool, you edit `check` and every test stands. This is about refactor decoupling, not saving keystrokes — and it pays off faster than it used to, because refactors are cheap and frequent now.

The input can be data rather than arguments — a string, JSON, or a small DSL. rust-analyzer's "goto definition" tests pass a whole multi-file project as one annotated string, run the full pipeline, and finish in 4ms.

## Observability points

When the fact you need to verify is not in the output — a cache was hit, a branch was taken, a fallback did *not* fire — do not reach into internals. Make it output.

Cargo does this: cache tests enable verbose logging, then assert on the emitted cache-hit lines. The internal fact becomes part of the observable contract, so the test survives refactoring.

**Coverage marks** are the same idea for negative assertions. Tests asserting something *doesn't* happen are fragile because it often doesn't happen for the wrong reason. Emit a mark naming the reason, then assert on the mark.

## Expect tests

Inline the expected value; a dedicated run mode rewrites it in place on mismatch. Libraries: `insta` (Rust), jest snapshots (JS), `pytest-regressions`, `expect-test`.

Good for generated code, formatted output, and any result with messy structure that changes wholesale. Maintenance cost is near zero — which is exactly the trap. The update mode is an auto-approval loop unless someone reads the diff. Never run it to make a red suite green without inspecting each change.

## Beyond example-based testing

Setup cost used to rule these out. It no longer does — reach for them by default on pure functions.

- **Property testing** — generate inputs, assert an invariant. For binary search: the needle lies between the elements bracketing the insertion point.
- **Exhaustive small inputs** — better than random when the space is small. Every sorted list of length ≤7 over `0..=6`, cross-checked against linear search, settles binary search completely at the sizes where bugs live.
- **Fuzzing** — throw bytes at a parser and assert it errors rather than corrupts. Coverage-guided fuzzers reach branches you did not think of.
- **Differential testing** — run the fast path and the obvious slow path over one corpus and compare. The best oracle available when two implementations claim the same contract.

## Humble object refactor

When a method mixes domain logic with dependencies, split it so the domain part is unit-testable and only the orchestration needs integration tests.
Aim for deep business objects with few dependencies and wide orchestration objects with little logic. Code that is both complex and dependency-heavy usually needs redesign before it needs more tests.

**Before** — complex method, hard to test:
```
service.changeEmail(id, email) {
  user = db.get(id)
  if (external.validate(email)) {
    user.email = email
    db.save(user)
  }
}
```

**After** — domain logic is pure, controller is thin:
```
// Domain (unit test)
User.changeEmail(email, validator) {
  if (validator.isValid(email)) {
    this.email = email
    return EmailChanged(email)
  }
}

// Controller (integration test)
Controller.changeEmail(id, email) {
  user = db.get(id)
  event = user.changeEmail(email, validator)
  db.save(user)
  bus.publish(event)
}
```

Now the interesting branching lives in `User.changeEmail` and runs in milliseconds. The controller test only proves the wiring.
Name the tests for behaviors, such as `User_cannot_change_email_to_an_invalid_address`, not for the implementation method or class shape.

## Three-context database pattern

For DB integration tests, use three separate contexts/transactions to avoid false positives from caching or unflushed writes:

```
// Arrange context
db1.insert(user)

// Act context
db2 = newContext()
controller.update(userId, db2)

// Assert context
db3 = newContext()
assert db3.get(userId).email == expected
```

Clean data at the **start** of the test, not the end — a failed test should leave evidence in the DB.

## Testing each layer

Given `L1 <- L2 <- L3 <- L4`, the path of least resistance is to test everything through `L4`. Don't. Write tests at each layer:

```
L1 <- Tests
L1 <- L2 <- Tests
L1 <- L2 <- L3 <- Tests
L1 <- L2 <- L3 <- L4 <- Tests
```

Testing `L4` exercises `L1`–`L3` too, and that's fine — layering means only `L4` recompiles. The cost of testing `L1` exclusively through `L4` is the rebuild chain on every change to `L1`.

## Sizing tests: resources, not scope

Scope labels (unit / integration / e2e) predict cost badly — there are slow unit tests and fast functional tests. Size by what the test actually consumes:

- **Setup duration.** The dominant cost when you run one test to debug, which is most of the time. Keep setup scoped to the test that needs it; shared class-level fixtures (`@BeforeClass`, `@BeforeAll`) tax every run.
- **Resource cost.** RAM, containers, and anything billed. A local SQLite is not a cloud MySQL.
- **Hermeticity.** Can it run from a clean checkout, alone, repeatably? This is the one that decides whether a failure means anything.

The presence of IO is not itself the signal. `httptest.NewServer` on loopback touches the network and is cheap. An in-process SQLite touches a database and is cheap. A test-local temp directory touches the filesystem and is cheap. What costs you is a remote target, a shared target, or one somebody else manages.

Judge tests on these axes rather than applying a fixed ratio. Published splits like 70/20/10 are a heuristic from one codebase shape, not a target.

## Integration vs. integrated tests

The distinction worth internalizing, from Spotify's honeycomb model:

- **Integration test** — exercises your service through its real boundaries, with realistic fixtures at the edges: actual recorded API payloads, real messages onto a queue. Nothing else needs to be running. Confidence in the contract, freedom to refactor inside.
- **Integrated test** — *"will pass or fail based on the correctness of another system."* This is the property that makes it bad, not its size or slowness. It cannot tell you whether *you* broke something.

Symptoms of an integrated test: it needs several services up locally, it runs against a shared environment, or someone else's change turns it red.

Google's "minimize end-to-end tests" and Spotify's "minimize integrated tests" are the same claim. Google's reason is the one that matters most in an agentic loop: a failure that doesn't localize the defect forces the next step to be a guess, and guessing is how environments get mutated and assertions get weakened.

## Pyramid or honeycomb

They disagree because they assume different places for complexity to live.

- **Pyramid** (many unit, fewer integration, few e2e) fits code whose complexity is *inside* the process — compilers, algorithms, domain models. Deep domain tests pay off; the boundary is thin and only needs wiring proof.
- **Honeycomb** (mostly integration, few implementation-detail, almost no integrated) fits code whose complexity is *between* processes. "The biggest complexity in a Microservice is not within the service itself, but in how it interacts with others." Here the service is the unit, and testing individual classes mostly locks in structure you want to be free to change.

Pick by where your bugs actually come from. A glue service with pyramid-shaped tests is over-testing its internals and under-testing its contracts; a parser with honeycomb-shaped tests is leaving its hard part barely covered.

## A deployed environment

Prefer ephemeral (per-PR stack, compose file) over shared staging — attribution is what makes a failure actionable. A deployed environment earns only what is structurally invisible below it:

- Deployment and wiring — env vars, secrets, migration ordering, IAM, DNS, TLS, ingress
- Real behavior of the unmanaged dependencies you mocked. A communication mock asserts a contract you *assumed*; nothing has verified it until the real call happens
- Infrastructure under real latency — connection pool limits, timeouts, retry storms, cold starts
- Production-shaped data volume and legacy rows

It does not earn business logic, edge cases, or branch coverage. Push one happy path through the deployed system plus whatever cannot be observed lower down. Every edge case deferred to staging is one you failed to catch cheaply.

Do not mock inside a deployed environment. Stubbing a third party there gives you a slow integration test with worse isolation; use the vendor sandbox for real, or move the test down a tier where the mock is honest.

Accept the ceiling: you do not test your way out of the external world. Cheap patch releases, fast rollback, and real observability protect you better than a larger staging suite does.

A deployed environment earns only what is structurally invisible below it:

- Deployment and wiring — env vars, secrets, migration ordering, IAM, DNS, TLS, ingress
- Real behavior of the unmanaged dependencies you mocked. A communication mock asserts a contract you *assumed*; nothing has verified it until the real call happens
- Infrastructure under real latency — connection pool limits, timeouts, retry storms, cold starts
- Production-shaped data volume and legacy rows

It does not earn business logic, edge cases, or branch coverage. Push one happy path through the deployed system plus whatever cannot be observed lower down — the same rule that governs integration vs. unit, recursed one level up. Every edge case deferred to staging is one you failed to catch cheaply.

Do not mock inside a deployed environment. Stubbing a third party there gives you a slow integration test with worse isolation; use the vendor sandbox for real, or move the test down a tier where the mock is honest.

Accept the ceiling: you do not test your way out of the external world. Cheap patch releases, fast rollback, and real observability protect you better than a larger staging suite does.

## Slow tests

Test time is dominated by setup, real IO against remote or shared targets, and a few outliers — not by how much code runs. So:

- Print each test's execution time by default; outliers are invisible otherwise.
- Gate genuinely slow tests behind an environment variable checked at the top of the test, not behind conditional compilation or build tags — those make the tests invisible and let them rot.
- Sleeps and timeouts used for synchronization are both a slowness cause and a correctness smell. Fix the API so the work can be awaited.

## When mocking communication is OK

Communication-based assertions (`verify(service.send, once)`) are acceptable at the boundary between your system and an unmanaged dependency you can't observe directly — e.g. asserting an outbound webhook fired. They're a smell anywhere else, because they couple the test to call sequence.

## Coverage numbers

Use coverage as a diagnostic, not a target. Low coverage can reveal untested behavior worth discussing; high coverage does not prove the tests protect the product — and it is now trivially gameable, which makes it a worse metric than it used to be. Never add a test that exists only to move a percentage.
