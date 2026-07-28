# Lens reference: BurntSushi — Axes

Ten general axes apply to any language. Two Rust-specific axes follow.

For each axis: the question to ask, a canonical bad example with a model comment, and the skill rule. Direct quotes from BurntSushi are marked with ›.

---

## General Axes

### Axis 1 — Worst-case contract

**Ask:** Does this patch change worst-case complexity? Does a new feature introduce unbounded backtracking, unbounded memory growth, hidden recursion, or pathological input sensitivity? Is the new worst case documented, opt-in, or isolated?

› *"these regex engines...will often provide a guarantee that all searches...will complete in linear time."*

**Bad example:**
```rust
fn match_pattern(input: &str, pattern: &str) -> bool {
    backtracking_match(input, pattern) // was previously DFA-backed
}
```

**Comment:** This changes the performance contract from linear to potentially unbounded. Either make the backtracking path opt-in, document the new worst-case explicitly, or isolate it behind a separate engine. Callers who relied on the previous guarantee now have none.

**Skill rule:** If a patch adds expressive power, check whether it also adds a new worst-case cost. Require opt-in, documentation, benchmarks, or isolation — not just "it's usually fast."

---

### Axis 2 — Invariant honesty

**Ask:** Do types and abstractions accurately represent reality? Does a name like `Valid`, `Parsed`, `Normalized`, `NonEmpty`, or `Trusted` correspond to actual enforced validation? Are assumptions about input shape explicit rather than implicit?

**Bad example:**
```python
def parse_log_line(line: str) -> Event:
    # assume well-formed input
    ...
```

**Comment:** If `line` arrives from a socket, file, or subprocess, the "well-formed" assumption may not hold. Either validate at the boundary and document the guarantee, or accept raw bytes and validate inside. The type should make the contract explicit, not hide it in a comment.

**Skill rule:** Do not let types or names pretend reality is cleaner than it is. If a type encodes a proof obligation (validated, normalized, trusted), find where that proof is constructed and verify it holds for all entry points.

> **Rust note:** `String`/`&str` carry a UTF-8 guarantee callers must provide. If input is bytes from an external source, consider `&[u8]` and validate before converting. Check that newtypes (`NonEmpty<T>`, `ValidPath`) have constructors that enforce the invariant.

---

### Axis 3 — Error vs. bug boundary

**Ask:** Is a panic, assertion, or unchecked operation used on user input, IO, network, env vars, config, clocks, filesystem, or external services? If yes, it should return a structured error. Do not flag assertions on static programmer invariants or in tests.

› *"Is it a bug if the program couldn't build a regular expression from a static string literal? Yup. The programmer typed that regex."*

**Bad example:**
```python
port = int(os.environ["PORT"])  # unhandled KeyError/ValueError
```

**Comment:** `PORT` is a runtime condition, not a programmer invariant. Failure is expected and should surface a structured error with context, not an unhandled exception.

**Okay example:**
```rust
let re = Regex::new(r"^[a-z0-9_-]+$").unwrap();
```

**No issue:** Static programmer-provided regex. Failure means miswritten code, not a runtime input error.

**Also check — error richness:** Does the error carry enough structured context for callers to react appropriately? Errors should preserve data, not degrade to bare strings. Prefer `Result<T, E>` with a contextualized message over `Option<T>` when the absence has a reason the caller might want to know.

› *"the key to ergonomic error handling is reducing the amount of explicit case analysis the programmer has to do while keeping code composable"*

**Skill rule:** Panic for bugs (violated programmer expectations). `Result` with structured context for runtime/environment/user failures. Errors should carry enough information that callers can react, not just report.

---

### Axis 4 — Hidden reusable cost

**Ask:** Does this function reconstruct expensive state on every call? Are regex compilation, schema validation, connection setup, parsing, or buffer allocation costs hidden inside a per-call API? Can callers amortize the cost?

**Bad example:**
```python
def contains_pattern(haystack: str, pattern: str) -> bool:
    return re.match(pattern, haystack) is not None  # compiles on every call
```

**Comment:** Regex compilation is non-trivial. If called repeatedly with the same pattern, expose a compiled matcher type so callers can amortize construction. The current API hides cost that scales with call frequency.

**Better shape:**
```python
class Matcher:
    def __init__(self, pattern: str): self._re = re.compile(pattern)
    def is_match(self, haystack: str) -> bool: return bool(self._re.match(haystack))
```

**Skill rule:** If setup cost is non-trivial, the API must expose a way to construct once and reuse many times. Hidden per-call construction is a contract lie.

---

### Axis 5 — API layering

**Ask:** Does this patch add expert knobs to a simple API, forcing ordinary users to understand engine/config/cache/buffer/tuning details? Can the common API remain boring while expert controls live in a builder, options struct, or separately versioned crate?

› *"by targeting the crate toward 'expert' use cases, we make no show of trying to keep the API small and simple."*
› *"The complexity isn't contained."* (on traits/generics that infect calling code)

**Bad example:**
```go
func Search(query, path string,
    useDFA bool, enablePrefilter bool,
    scratchSize int, unicodeMode UnicodeMode,
    mmapPolicy MmapPolicy) ([]Match, error)
```

**Comment:** This conflates a common-case operation with engine tuning. Keep `Search(query, path)` as the stable front door; move controls into `SearchOptions` or an advanced module. Ordinary callers should never see `mmapPolicy`.

**Also check — generics/traits:** Does this patch introduce a trait or type parameter that callers will need to carry everywhere? A trait that "infects" public API surface should be justified by concrete, multiple use cases — not by theoretical future extensibility.

**Skill rule:** Common API must be boring. Expert controls exist but behind builder/config/options/advanced modules. Generics and traits must contain their complexity — if they don't, a concrete type is better.

---

### Axis 6 — Pit-of-success defaults

**Ask:** Do defaults lead users toward correctness, not just convenience? Are surprising, expensive, or lossy behaviors opt-in? Does the API make the right thing easy and the wrong thing awkward?

› *"Jiff tries to do the right thing by default"* / *"guide you into the pit of success"*
› *"Removing `PartialEq`/`Eq` from `Span`...made it very easy to commit subtle bugs"*

**Bad example:**
```python
for root, dirs, files in os.walk("."):
    for f in files:
        search(os.path.join(root, f))
```

**Comment:** For a code-search tool, scanning everything by default surprises users: `.git`, build output, hidden files, and binaries dominate runtime. Respecting ignore files by default and adding an explicit `--no-ignore` flag leads users toward a correct result rather than a noisy one.

**Also check:** Does the API return `Option<T>` when it could return `Result<T, E>` with a reason? Silently returning `None` for a failure that has a cause discards context the user needs.

**Skill rule:** Defaults encode correct intent for the common case. Surprising behaviors are opt-in. APIs that make the wrong thing easy are design bugs, not usage bugs.

---

### Axis 7 — Testability across strategies

**Ask:** If this codebase has multiple engines, backends, or fast paths that claim the same semantics, do they share a test corpus? Are internal strategies independently testable via public APIs? Are there property, fuzz, or cross-implementation equivalence tests?

› *"all of the strategies used internally are not part of any public API, and that makes them difficult to independently test"* (on the motivation for `regex-automata`)

**Bad example:**
```rust
#[test]
fn test_dfa_match() {
    assert!(dfa_match("abc", "a.c"));
}
// NFA, SIMD, and fallback paths have no shared test corpus
```

**Comment:** Semantic drift is invisible when each engine is tested in isolation. A shared corpus that runs the same cases across all strategies prevents one path from silently diverging.

**Skill rule:** When multiple implementations claim the same semantics, tests must be semantic and shared, not implementation-local. Internal engines should be reachable via public APIs so that strategies are independently testable.

---

### Axis 8 — Fast-path honesty

**Ask:** Does an optimization change boundary behavior for empty input, invalid input, Unicode, case folding, overflow, or error propagation? Is a heuristic named as a heuristic, or presented as a principled algorithm? Is there an oracle — slow path, shared corpus, fuzz target — to verify the fast path?

› *"literal extraction is one big heuristic. A dark art, if you will."*
› *"the benchmarks I'm presenting here are curated, and...therefore also biased"*

**Bad example:**
```c
if (is_ascii(haystack)) {
    fast_ascii_search(haystack, needle);
} else {
    unicode_search(haystack, needle);
}
// no tests comparing the two paths at boundary inputs
```

**Comment:** The ASCII fast path needs tests against the unicode path for boundary cases: empty needle, non-ASCII transition points, invalid UTF-8 sequences, and case folding. Without these, the fast path is unverified.

**Also check — benchmark honesty:** If performance numbers are cited, are they accompanied by caveats about what they do and don't measure? Summary statistics (geomean, "X% faster") should not substitute for examining specific cases.

**Skill rule:** Every fast path needs a semantic oracle. Heuristics must be named as heuristics. Performance claims must name what they measure and what they don't.

---

### Axis 9 — Complexity containment

**Ask:** Does this patch introduce abstractions — traits, type parameters, generic bounds — that callers will need to carry everywhere? Does the complexity stay inside the library, or does it leak into every API surface that touches this type?

› *"if `TimeZone` were a trait, then `Zoned` would not be a concrete type...anyone using a `Zoned` in their own types or APIs needs to think about the `TimeZone` trait...The complexity isn't contained."*
› *"being able to just write `Zoned` as a concrete type without any generics is a huge win for comprehensibility"*

**Bad example:**
```rust
pub struct Searcher<E: Engine, S: Strategy, B: Buffer> { ... }
```

**Comment:** Every caller who stores or passes a `Searcher` now carries three type parameters. If a concrete type could cover the common cases — possibly with runtime dispatch for the exotic ones — the complexity stays inside the library instead of infecting calling code.

**Skill rule:** Generics and traits must justify their cost: do they enable concrete multiple use cases today, or only theoretical future ones? When a concrete type serves the common case, prefer it. Open extension points that infect call sites are design debt.

---

### Axis 10 — Documentation of tradeoffs

**Ask:** Does this public API have behavioral contracts callers must understand? Do docs explain *why* the API is shaped this way — failure modes, complexity bounds, allocation behavior, panic conditions, when NOT to use this — not just usage syntax?

› *"Compilation can take an exponential amount of time and space...For this reason, untrusted patterns should not be compiled with this library."* (stated prominently in README)

**Comment template:** This API has an important behavioral contract but the docs only show usage. Add: what inputs are accepted, when this can allocate, whether the operation is bounded, what guarantees callers can rely on, and when they should use a different API instead.

**Skill rule:** If an API encodes a tradeoff, docs explain the tradeoff — not just the syntax. Limitations should be prominent, not buried. A DESIGN.md that explains *why* the API is shaped this way is worth more than API docs that describe *what* it does.

---

## Rust-Specific Axes

### Rust Axis A — Encoding invariants

**Ask:** Is `String`/`&str` used where input may be arbitrary bytes? Is `Path` silently converted to `str`? Does a newtype (`NonEmpty<T>`, `ValidPath`, `TrustedInput`) have a constructor that enforces the invariant, or is it just a name?

**Bad example:**
```rust
fn parse_log_line(line: String) -> Event { ... }
// where `line` arrives from a raw socket
```

**Comment:** `String` forces callers to prove UTF-8 before parsing. If logs may contain arbitrary bytes, consider `&[u8]` and convert to `str` only after validation at the boundary.

**Skill rule:** Every encoding-constrained type carries a proof obligation. Find where that proof is constructed and verify it holds for all call sites, not just the happy path.

---

### Rust Axis B — Ownership and allocation

**Ask:** Does this API take ownership or allocate where borrowing would suffice? Is a large object cloned accidentally? Should this return an iterator instead of collecting into `Vec`?

**Bad example:**
```rust
pub fn lines(input: String) -> Vec<String> {
    input.lines().map(|s| s.to_string()).collect()
}
```

**Comment:** This eagerly allocates one `String` per line and takes ownership of the whole input. If callers only iterate, return a borrowing iterator. If callers need owned data, make that explicit (`into_lines() -> Vec<String>`) so the allocation is visible at the call site.

**Skill rule:** Ownership and allocation are part of the cost model and must be visible in the API shape. Taking ownership or collecting should be intentional, not accidental.
