# code-review-russ-cox — Reference

Full philosophy behind the passes and audit dimensions in `SKILL.md`. Load this to justify a finding, decide an edge case, or explain a principle to the author.

Exemplars cite golang.org/x/oscar (the Go team's contributor agent). Oscar is evidence, not a standard: each exemplar is one Go-shaped instantiation of a portable principle, and most codebases will differ in language, scale, and shape. When writing a finding, extract the spirit and demand its local translation — "panic for bugs" means fail fast on impossible states in whatever form the language gives you; "txtar fixtures" means any diffable, hand-editable fixture format; "doc.go architecture tour" means one living document that explains the design and records its doubts, wherever that lives. If a principle costs more than it buys in this codebase, say so and move on.

## Core philosophy

**Maintenance cost vastly exceeds implementation cost.** Every decision optimizes for long-term sustainability, not short-term convenience.

**Orthogonality**: features should be basis vectors — covering the problem space efficiently, combining predictably, with no redundant paths to the same solution.

**Simplicity is complicated.** Simple solutions require *more* thought than complex ones. Make the problem simpler; don't just move complexity around.

**Small bespoke infrastructure is fine when it buys portability + testability.** Oscar hand-rolls ordered key encoding, timed/incremental storage, an action log, and HTTP record/replay: "a small amount of code to maintain, and the benefits to both portability and testability are significant."

## Change review — the four root causes of bloat

### 1. Feature creep — the "useful" fallacy

A feature can be useful but still not worth its permanent maintenance burden.

**Red flags**: nice-to-haves without clear ROI; duplicate functionality with different syntax; resume-driven features; solutions looking for problems.

**Good patterns**: small composable primitives; features that enable new capabilities rather than replicate old ones; willingness to say "no" to reasonable requests.

### 2. Wrong-layer fixes — the wrapping trap

Patching at a higher layer instead of fixing the root cause at the layer that owns the behavior.

**Red flags**: wrappers that only forward to other wrappers; "adapter"/"bridge" without a real architectural boundary; touching 5+ files to change one behavior; error handling scattered across abstraction levels.

**Good patterns**: fix at the source; minimal layers between problem and solution; clear ownership per layer; each abstraction earns its keep.

### 3. Dependency explosion — the hidden iceberg

Every dependency brings its own tree; you maintain all of it.

**Red flags**: huge dep for a tiny utility; unmaintained libraries; deps that pull in competing libraries; choosing by download count.

**Heuristic — import hard, own core, copy small**: import real machinery you couldn't reasonably write (storage engines, cloud SDKs, telemetry) but quarantine each behind a home-owned interface in a leaf package; DIY the small infrastructure that defines your architecture (outsourcing it means importing someone else's architecture); copy small stable code verbatim — a ~250-line file is cheaper than a dep ("A little copying is better than a little dependency"). No frameworks where a library composes.

**Audit checklist**: transitive tree reviewed; active maintenance verified; no simpler alternative; security implications understood; cost-benefit documented.

### 4. Low quality standards — the technical-debt lie

"We'll clean this up later" almost never happens; debt compounds.

**Red flags**: complex logic without explanation; missing or superficial tests; clever tricks requiring domain expertise; comments explaining *what* instead of *why*.

**Good patterns**: merge-ready before review; clarity over cleverness; tests that document behavior; refusal to merge until the bar is met.

## Package audit — dimension exemplars

### Seams

Gaby defines its *own* minimal interface for everything it needs from the environment — `storage.DB`, `llm.Embedder`, `secret.DB`, `queue.Queue` — with multiple implementations (in-memory, disk, GCP), so it runs "from a Raspberry Pi to a hosted cloud". Interfaces stay minimal on purpose: `storage.DB` is Get/Set/Scan/Delete/Batch/Lock, "avoiding, for example, a requirement on SQL, to admit as many implementations as possible." Structure you need (ordering, timestamps) is built *on top of* the seam, not demanded from it. Core packages never import the heavy implementations.

### Composition payoff

A design metric, not an aesthetic: oscar's embeddocs package "has very little to it, given the abstractions of a document store with incremental scanning, an LLM embedder, and a vector database." When a new unit is nearly trivial, the abstractions below it are right. Corollary: judge refactors by what they delete — one oscar refactor's headline benefit was deleting four packages.

Control flow as representation: explicit state is sometimes accidental machinery. A `state` field, iterator stack, pending queue, or state machine may only be simulating the program counter or call stack. In that case, prefer a direct loop, recursion, callback traversal, generator/coroutine, or small adapter that lets the natural control flow carry the state. Keep state as data when it must be serialized, inspected externally, persisted, shared across processes, or updated by unpredictable events.

Constructor shape: `New(lg, db, gh, vdb, docs, name)` for required deps, then `p.EnableProject(...)`, `p.SkipTitleSuffix(...)` for policy. Deps are positional; config is methods.

Also from oscar's design: prefer deterministic code, and confine the fuzzy/probabilistic part (LLM calls, heuristics) to proposing; deterministic, reviewable code acts — with a human-approval log for irreversible actions.

### Error regimes

Choose by *whose bug it is*:

- **Panic for "can't happen"**: oscar's DB interface panics on storage failure — "if storage has failed you'd rather crash your program than try to proceed through typically untested code paths." Marshaling errors panic because they indicate a bug at the call site. The panic policy is documented on the interface itself.
- **Errors for the environment**: `fmt.Errorf` with context; `%w` only where callers actually match with `errors.Is/As`. Sentinel errors package-private.
- **Log-and-continue in long-running loops**: one bad item must not kill a sync pass — log with structured attrs and `continue`; these paths are explicitly expected to be tested.
- Resilience over blame: when a cloud scan times out, restart from the last key rather than fail.

### Observability

- Structured logging only; the logger is a constructor dependency (first arg), never a global — logs become testable and per-component.
- Message strings are stable lowercase identifiers, often `package.Type action` shaped ("bisect.Bisect finished"); variable data goes in attrs, never interpolated into the message.
- In tests, route the logger through `t.Log` so output appears only on failure; capture to a buffer when a test asserts on logs.

### Testing

"It is an explicit requirement in this repo to test all the code, even (and especially) when testing is difficult."

- **A fake at every interface**, shipped in the production package and advertised in the interface doc ("See [QuoteEmbedder] for a semantically useless embedder... and [gcp/gemini] for a real implementation"). A deterministic, semantically-useless fake is often good enough.
- **Record/replay for network** (oscar's httprr): record once against the real service, replay forever; secrets scrubbed before disk; no hand-written service fakes, no network in CI. The whole setup for testing a real cloud LLM client is ~12 lines:

  ```go
  func newTestClient(t *testing.T, rrfile string) *Client {
  	check := testutil.Checker(t) // err-checks become one line
  	lg := testutil.Slogger(t)    // slog through t.Log: shown only on failure

  	rr, err := httprr.Open(rrfile, http.DefaultTransport)
  	check(err)
  	rr.ScrubReq(Scrub) // strip secrets before the trace hits disk
  	sdb := secret.ReadOnlyMap{"ai.google.dev": "nokey"}
  	if rr.Recording() { // real creds only when re-recording (-httprecord flag)
  		sdb = secret.Netrc()
  	}
  	c, err := NewClient(ctx, lg, sdb, rr.Client(), DefaultEmbeddingModel, DefaultGenerativeModel)
  	check(err)
  	return c
  }
  ```
- **Human-editable fixtures** (txtar-style text files) so test data is diffable and hand-writable; mutations diverted to an in-memory edit log tests assert against.
- **Conformance suites**: a new implementation of a shared interface runs the shared test suite.
- **Coverage as a review tool, not a vanity number**: list untested lines; untested error paths get tests or a justified `// Unreachable` / `// Untested` marker.
- **Determinism**: no dependence on timing or the race detector.

### Docs & style

- Every package gets a real package doc, one sentence minimum; the binary/main package's `doc.go` is the full architecture tour with doc links.
- Doc comments state the **contract**: complete sentences starting with the identifier, edge cases and ownership spelled out ("Delete of an unset key is a no-op", "Set does not retain any reference to key or val after returning"). Non-obvious APIs get a runnable example *inside* the doc comment — oscar's lazy `Scan` iterator is the model:

  ```go
  // Scan returns an iterator over all key-value pairs with start ≤ key ≤ end.
  // The second value in each iteration pair is a function returning the value,
  // not the value itself:
  //
  //	for key, getVal := range db.Scan([]byte("aaa"), []byte("zzz")) {
  //		val := getVal()
  //		fmt.Printf("%q: %q\n", key, val)
  //	}
  //
  // In iterations that only need the keys or only need the values for a subset
  // of keys, some DB implementations may avoid work when the value function is
  // not called.
  Scan(start, end []byte) iter.Seq2[[]byte, func() []byte]
  ```

  Contract, example, and the performance escape hatch — all where the reader's cursor already is.
- Inline comments are *why*-only: `w = w[:len(v)] // make "i in range for v" imply "i in range for w" to remove bounds check`.
- TODOs are signed and argued — a considered tradeoff, not a vague wish: `TODO(rsc): float64 is slightly higher precision... may not be worth the type conversions`.
- **Admit uncertainty in writing**: "It remains to be seen whether this decision is kept." Design docs that only assert are lying about confidence.

### Commit/PR messages (when polish includes history or PR text)

`affected/package: short lowercase summary`, then a body that argues the change: problem → approach → consequences; evidence, not adjectives (paste real before/after output and measured numbers); deviations from the agreed design as explicit bullets; deletion as a headline benefit; honest hedging with planned follow-ups; issue links.

## Constructive phrasing patterns

- Instead of "This is too complex": "This has N layers of indirection. Could we solve directly: [sketch]. Benefits: [list]. Tradeoffs: [list]."
- Instead of "Don't add this dependency": "This adds N transitive deps. Alternative: [stdlib / 20 lines]. The simpler approach wins here because [reason]."
- Instead of "This abstraction is wrong": "We have 1 use case; suggest solving directly now and abstracting when the pattern emerges (3+ uses)."
- Instead of "Rewrite this": "Current approach: [analysis]. Maintenance implications: [list]. Alternative: [sketch]. Which fits our long-term goals?"

## When to compromise

**Legitimate**: hard deadlines with a documented debt plan; regulatory/compliance requirements; vendor lock-in chosen with eyes open; team-skill constraints paired with training.

**How**: document the decision; write a dated paydown plan; minimize scope; review quarterly.

**Never**: security vulnerabilities, data integrity, silent failures, untested critical paths.
