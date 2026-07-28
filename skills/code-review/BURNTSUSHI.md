# Lens: BurntSushi — honest invariants and costs

> "Is there a reasonable expectation that the code will behave as advertised?" — BurntSushi

A code review should ask: is this code *honest* about its invariants, failure modes, costs, and semantics? Not just: does it work?

## Steps

1. **State the change** — what is this patch doing in one sentence? If unclear, ask first.
2. **Walk all ten general axes** from [BURNTSUSHI-REFERENCE.md](BURNTSUSHI-REFERENCE.md) in order. The axes are a search checklist, not a finding quota — most axes will be clean on most patches, and saying so is the correct result.
3. **If Rust:** also apply the two Rust-specific axes (encoding invariants, ownership/allocation).
4. **Emit findings** using the router's output contract.

## Output — this lens

Beyond the router's contract: name the invariant, failure mode, or hidden cost precisely — "this can panic" is not a finding; "this panics on empty input because X" is.

Do not complain about `unwrap`/assertions on static programmer invariants — only flag panics when the failure source is runtime, user, or environment.

See [BURNTSUSHI-REFERENCE.md](BURNTSUSHI-REFERENCE.md) for all axes with examples and model comments.
