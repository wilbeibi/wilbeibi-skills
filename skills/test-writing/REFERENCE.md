# test-writing — Reference

Patterns and worked examples referenced from `SKILL.md`.

## The long-lasting form

From Russ Cox's "Go Testing By Example": *separate test cases from test logic*, *make it easy to add new test cases*, *make test failures readable*. The test function is a dumb driver written once; the knowledge lives in the cases.

```go
var searchTests = []struct {
	in     []int
	needle int
	want   bool
}{
	{nil, 0, false},
	{[]int{92}, 92, true},
	// the next bug is one more line here
}

func TestSearch(t *testing.T) {
	for _, tt := range searchTests {
		if got := Search(tt.in, tt.needle); got != tt.want {
			t.Errorf("Search(%v, %d) = %v, want %v", tt.in, tt.needle, got, tt.want)
		}
	}
}
```

When the signature changes, you edit one call, not a dozen tests. The same shape scales past tables:

- **`testdata` files** when cases are large inputs. One file per case; the driver globs the directory.
- **txtar archives** for multi-file cases: a whole config tree, repo, or cluster layout in one file.
- **Script tests** (`rsc.io/script`, `testscript`) for CLIs and services: each file is a readable session of commands and expected output, and adding a scenario needs no Go code.
- **Golden files with an update flag** when the answer can legitimately change (formatted output, generated code). `-update` rewrites them; read every diff before committing, or it is an auto-approval loop.
- **Parsers and printers** for your own types, so cases are written as text rather than struct literals.

The input to the driver can be a whole world: rust-analyzer passes a multi-file project as one annotated string and runs the full pipeline in milliseconds.

## Exploration and what to keep

Execution can grow without bound; the committed suite should not.

| Commit | Run per change, then discard |
|---|---|
| Contract tests at the seam | Generated example batteries |
| Invariant and property tests | Fuzzing and mutation runs |
| Compatibility fixtures | Differential runs against a reference |
| Failure and recovery semantics | Fault-injection and random op sequences |
| Minimized historical regressions | Throwaway probes written while debugging |

A deterministic exhaustive or differential test whose oracle lives in the repo (a reference implementation, an obvious slow path) is a committed invariant test, not exploration. What gets discarded is random batteries and runs against an external or old build.

Techniques, cheapest oracle first:

- **Exhaustive small inputs** beat random when the space is small: every sorted list of length ≤7 over `0..=6`, cross-checked against linear search, settles binary search where bugs live.
- **Differential** — fast path vs. obvious slow path, new vs. old version, yours vs. another implementation. The best oracle when two things claim one contract.
- **Properties** — round-trip, idempotence, monotonicity, conservation (nothing acknowledged is lost).
- **Fuzzing** — throw bytes at parsers and decoders; assert they error rather than corrupt.

When exploration finds a bug, commit the **minimized input as data**, not the seed. A seed replays only while the code consumes randomness identically; the next unrelated change sends it down a different path and the test silently stops testing anything. Go fuzzing stores the input itself under `testdata/fuzz/`; a Hypothesis `@example` pins the value. proptest regression files store seeds, so copy the shrunk value into a case. For simulation, commit the shrunk operation sequence.

## State-machine tests for stores and protocols

For anything with state behind a seam — a KV store, snapshot store, log, lease — the durable test is a single model check:

1. Model: the simplest thing that is obviously correct (a map, a list, a counter).
2. Generate a random sequence of operations: `Write`, `Read`, `Save`, `Restore`, plus `Crash`, `Restart`, `DropMessage`, `PartialWrite`.
3. Apply each to both the system and the model; after each, compare observable results and check invariants (acknowledged writes survive a crash; reads never see a torn write).
4. On failure, shrink the sequence and commit it as a regression case.

Libraries: Hypothesis stateful testing, `proptest-state-machine`, `rapid`. The model is the oracle, so it must come from the spec, not from the implementation's behavior. Crash semantics the model cannot express ("what does Read return after a crash mid-Save?") are spec questions — ask, do not guess. A protocol whose correctness is the question belongs in `tla-model` first.

## Compatibility fixtures

On-disk formats, wire protocols, snapshot layouts: keep bytes written by old versions under `testdata/` and assert the new code reads them. These are the one kind of golden file you never regenerate — `-update` on a compatibility fixture deletes the promise it records. Add a fixture per released format version.

## Observability points

When the fact you need is not in the output — a cache was hit, a fallback did *not* fire — make it output rather than reaching into internals. Cargo's cache tests enable verbose logging and assert on the emitted cache-hit lines. For negative assertions, emit a mark naming the reason and assert on the mark; "it didn't happen" often holds for the wrong reason. Add such a point only when the contract needs it.

## Pruning an existing suite

Only on request, and only as a proposal the user approves. Candidates:

- Tests that pin internals: private methods, call order, mocks of your own collaborators, one file per source file.
- Near-duplicate examples — collapse into rows of one table rather than deleting coverage.
- Tests of the framework (the ORM saves, the stdlib sorts) and tests that cannot fail.
- Snapshot tests nobody reads.

Before proposing a deletion, break the behavior the test claims to protect and check that another test fails. If none does, the test stays or gets rewritten at the seam. Coverage finds untested code; it does not decide what to keep.

## Humble object

Code that is both complex and dependency-heavy usually needs a split before it needs more tests. Move branching into a dependency-free domain object (unit-tested, milliseconds) and leave a thin orchestrator that only wires IO (one integration test). Name tests for behavior — `user_cannot_change_email_to_invalid_address` — not for methods.

## Databases

Arrange, act, and assert in three separate contexts or transactions, so caching and unflushed writes cannot produce a false pass. Clean data at the start of a test, not the end, so a failure leaves evidence.

## Sizing tests: resources, not scope

Unit/integration/e2e labels predict cost badly. Size by what the test consumes:

- **Setup duration** — dominant when you rerun one test to debug. Scope setup to the test; class-level fixtures tax every run.
- **Resource cost** — RAM, containers, anything billed.
- **Hermeticity** — runs from a clean checkout, alone, repeatably. This decides whether a failure means anything.

`httptest.NewServer` on loopback, in-process SQLite, and a temp dir are cheap. A remote, shared, or someone-else-managed target is not. Fixed ratios like 70/20/10 describe one codebase shape, not a target.

## Integration vs. integrated

- **Integration test** — your service through its real boundaries with realistic fixtures (recorded payloads, real messages). Nothing else needs to be running.
- **Integrated test** — passes or fails based on the correctness of another system (Spotify). That property, not size, is what makes it bad: it cannot tell you whether *you* broke something, and in an agentic loop an unlocalized failure makes the next step a guess.

Pyramid-shaped suites fit complexity inside the process; honeycomb-shaped suites (mostly integration) fit complexity between processes. Pick by where your bugs come from.

## A deployed environment

Prefer ephemeral (per-PR stack, compose file) over shared staging; attribution is what makes a failure actionable. A deployed environment earns only what is structurally invisible below it:

- Deployment and wiring — env vars, secrets, migration ordering, IAM, DNS, TLS, ingress.
- Real behavior of unmanaged dependencies you mocked lower down; a communication mock asserts a contract you *assumed*.
- Infrastructure under real latency — pool limits, timeouts, retry storms, cold starts.
- Production-shaped data volume and legacy rows.

It does not earn business logic, edge cases, or branch coverage: push one happy path through plus whatever cannot be observed lower down. Do not mock inside a deployed environment; use the vendor sandbox or move the test down a tier. You do not test your way out of the external world — cheap rollback and real observability protect you better than a larger staging suite.

## Slow tests

- Print per-test time by default; outliers are invisible otherwise.
- Gate genuinely slow tests behind an environment variable checked at the top of the test, not build tags — hidden tests rot.
- Sleeps used for synchronization are a slowness cause and a correctness smell. Make the work awaitable.
