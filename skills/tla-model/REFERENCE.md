# tla-model reference

## Why the loop, not one-shot generation

- LLM-written specs parse more often than they mean anything. FormaLLM (205 specs, 30 models) reports that the best open-model strategy reached 26.6% syntactically valid and 8.6% passing TLC [9].
- Plausible and wrong: SysMoBench found models that restate textbook Raft/ZAB instead of etcd/ZooKeeper's real action split. They allow states the code cannot reach and merge steps the code does interleave [10].
- Agent specs contain their own bugs. In one K8s device-plugin report, TLC found a real lease-authorization gap *and* two bugs in the spec the agent had just written [16].
- Modeling is not automatically useful. In a 160-run Zstd rewrite experiment, agents built a TLA+ model 159 times and no model finding ever changed the Rust code: agents model where it is easy, not where bugs live [17]. Hence the brief's question slot and the event→action table.
- Counterexamples can be artifacts of the abstraction. Deciding whether a trace is reachable in the real system is the hard part [18].
- Invariant mutation is the cheapest guard against tautologies. TLA-Prover counts a property as meaningful only if a mutated property is caught [14].

## Failure modes and the gate that catches them

| Failure | Symptom | Gate |
|---|---|---|
| Parses, means nothing | SANY clean, TLC config/runtime error | run TLC every layer |
| Tautological property | green whatever you change | step 5 mutants |
| Dead model | few distinct states, action never fired | `VACUITY` flags |
| Textbook protocol instead of the code | trace validation fails; reviewers can't map actions | event→action table with file:line |
| Atomicity too coarse | race never appears | split read/write where others can interleave |
| Fairness hides a bug | adding `SF` turns it green | mechanism comment per fairness term |
| `CONSTRAINT` hides a bug | green only under bounds | list constraints as assumptions; widen the matrix |
| Small-model overreach | "2 nodes pass, so correct" | report states the bounds; parametric claims need proof |
| Agent weakens the property | property edits land alongside model edits | one change per round; property edits need sign-off |
| cfg wiring | `.tla` right, cfg checks the wrong thing | review cfgs with the spec |
| Spec–code drift | model no longer matches after refactors | trace replay in CI; mapping review on change |

## State space

- Start with the smallest non-trivial instance: 2–3 processes, 2 values, queue bound 1–2, one fault, one recovery.
- Use model values for identifiers.
- Cut variables that no property reads.
- Split a huge model into an abstract spec and a refined one.
- `SYMMETRY` is sound for safety only; never combine it with liveness.
- `CONSTRAINT` restricts what is explored, so a green result covers only the kept states; report every bound.
- `--tlc-args -simulate num=N -depth D` finds shallow bugs fast in models too large to exhaust. It is not evidence of absence.
- Liveness counterexamples are a stem plus a loop, and TLC does not guarantee they are the shortest.

## TLC gotchas

- The `-deadlock` flag turns deadlock checking **off**. `CHECK_DEADLOCK` in the cfg is the explicit switch.
- `-simulate` never reports deadlock; use BFS when deadlock matters.
- `SYMMETRY` takes a named operator (`Sym == Permutations(Nodes)`), not an inline expression.
- Model values and strings have no portable `<`; map identifiers to integers when order matters.
- Action substitution (`A <- MCA`) needs matching arity; otherwise define `MCNext`/`MCSpec` in a wrapper module.
- Without fairness, `P ~> Q` fails by stuttering; it does not pass vacuously (checked on TLC 2.19).

## Beyond TLC

- **Apalache** checks symbolically with SMT. It suits unbounded integers, larger parameter spaces, and checking that an inductive invariant `Inv` satisfies `Init => Inv` and `Inv /\ Next => Inv'`, which gives a result for all reachable states rather than a bounded search. It needs type annotations.
- **TLAPS** is for a claim that must hold for every N. Write the inductive invariant first, then check it with TLC or Apalache on small N before proving it.

## Linking spec to code

**Refinement.** Keep an abstract spec with only externally observable behavior. Map its variables from the detailed spec, then check the mapping as a temporal property:

```tla
abstractCommitted == {e \in Entries : Cardinality({n \in Nodes : e \in durableLog[n]}) >= Quorum}
A == INSTANCE AbstractSpec WITH committed <- abstractCommitted, leader <- abstractLeader
Refinement == A!Spec          \* in the detailed cfg: PROPERTY Refinement
```

Steps that exist only in the detailed spec must stutter on the abstract variables. See the Paxos → Voting refinement in tlaplus/Examples [8].

**Trace validation.**
1. Log sends, receives, durable writes, crash/recovery, and the before/after values of key variables.
2. Merge the logs into a causally ordered trace.
3. Map each event to an action and its parameters.
4. Check that the trace is a behavior the spec allows.

In the reports covered, this found spec–implementation divergence in all 7 systems [7]. A passing trace shows only that the observed runs are allowed. It cannot rule out states the spec allows that the code never reaches, which the event→action review has to catch.

**Code-level repro.** Replay a design counterexample as a deterministic test or fault-injection run before fixing the code. This follows the Specula pipeline: code analysis → spec → harness → validation → bug confirmation [13].

## Review checklist

Give the reviewer the brief, the spec, the cfgs, and the report, with no authoring context. They answer each item with evidence:

1. Does every action match an event at the cited file:line? Can anything interleave inside an action?
2. Can the code do something that no action allows?
3. Does every requirement have a property, and would each property fail on the plain-words violation in the brief?
4. Is every fairness term backed by a real mechanism? What breaks if it is removed?
5. Which behaviors are removed by bounds, `CONSTRAINT`, or exclusions? Do any of them matter for the question?
6. Does any report sentence claim more than the bounds support?
7. Was any property weakened, or any fairness or constraint added, in the same round as a model fix?

## Prior art and deliberate differences

- **tlaplus/AgentSkills** [12] (read 2026-09-23): `from-source`, `add-variable`, `split-action`. Useful edit recipes: a new variable must reach `Init`, `vars`, `TypeOK`, and every `UNCHANGED`; a split action adds a `pc` state and keeps the original destination. It proposes properties but has no mutation, vacuity, or counterexample-classification gate.
- **Specula** [13] (read 2026-09-23): the model for bug archaeology, counter-bounded faults, one hunting cfg per scenario, and mandatory executed repros. It revises invariants autonomously; this skill requires sign-off for property changes instead, because an agent weakening a property is the failure it most needs to prevent. Its gotcha that `~>` passes without fairness is wrong; see above.

## Worked example

`examples/MiniLock.tla` has comments mapping actions to events, properties to requirements, and fairness to mechanisms. It comes with separate safety (`MiniLock.cfg`) and liveness (`MiniLockLive.cfg`) configs. `scripts/test_tlc.sh` checks both configs and kills a guard mutant (Mutex) and a fairness mutant (StarvationFree). It also shows that a weakened Mutex is not caught by Consistency, and that a dead action is flagged.

## Sources

Collected 2026-09 through Hermes research; [12] and [13] were read directly. The X posts are practitioner self-reports without published specs or reproductions.

[1] TLC model checker — https://docs.tlapl.us/using:tlc:start
[2] TLC config files — https://docs.tlapl.us/using:tlc:config_file
[3] Lamport, Safety, Liveness, and Fairness — https://lamport.azurewebsites.net/tla/safety-liveness.pdf
[4] PlusCal tutorial, atomicity (session 7) — https://lamport.azurewebsites.net/tla/tutorial/session7.html
[5] PlusCal tutorial, fairness (session 9) — https://lamport.azurewebsites.net/tla/tutorial/session9.html
[6] How AWS uses formal methods — https://lamport.azurewebsites.net/tla/amazon-excerpt.html
[7] Kuppe, Validating System Executions with the TLA+ Tools (TLA+ Conf 2024) — http://conf.tlapl.us/2024/MarkusAKuppe-ValidatingSystemExecutionsWithTheTLAPlusTools.pdf
[8] Paxos refinement example — https://github.com/tlaplus/Examples/blob/master/specifications/Paxos/Paxos.tla
[9] Can LLMs Write Correct TLA+ Specifications? — https://arxiv.org/html/2606.05792
[10] Can LLMs Model Real-World Systems in TLA+? (SIGOPS) — https://www.sigops.org/2026/can-llms-model-real-world-systems-in-tla/
[11] Konnov, Interactive Symbolic Testing with TLA+, Apalache, and LLMs — https://conf.tlapl.us/2026-etaps/konnov-2026.pdf
[12] TLA+ AgentSkills — https://github.com/tlaplus/AgentSkills
[13] Specula — https://github.com/specula-org/Specula
[14] TLA-Prover — https://arxiv.org/html/2606.06133
[15] IronFleet — https://www.microsoft.com/en-us/research/wp-content/uploads/2015/10/ironfleet.pdf
[16] @bilby91, K8s device plugin — https://x.com/bilby91/status/2096982546869272828
[17] Dan Luu, agentic testing (Zstd rewrite experiment) — https://danluu.com/agentic-testing/
[18] @thegeeknarrator on counterexample realism — https://x.com/thegeeknarrator/status/2087255820077523443
[19] Vanlightly, Continuity.tla with modeling notes — https://github.com/Vanlightly/s3-wal-collection/blob/main/cursor/Continuity.tla
