# Named principles

Short names let the user steer with one phrase ("check single writer").

- **second fix, wrong layer.** When a bug or finding surfaces, name the problem it is a symptom of before a targeted fix. A fix that patches an earlier fix, or invents a mechanism the platform already has, means the cause is upstream.
- **right layer.** Before adding a link, field, or state, ask which layer already knows the fact. A copy of another layer's fact is a second truth to keep in sync.
- **explicit state machine.** Every mutable stored field belongs to an explicit state machine with one transition owner and a written transition table; every other field is write-once. Fix normalization debt now, not as a later optimization.
- **single writer.** One writer per fact or resource, including one executor for destructive work such as GC. N code paths writing the same fields is a smell to consolidate.
- **same problem, same mechanism.** Solve the same kind of problem the same way; symmetry is simplicity.
- **one name, one job.** When a name, field, or status starts a second job (identity and location, status and progress, cache and backing store), split it. Probe: ask what it means to each reader; two answers means two things. Record the vocabulary with domain-modeling.
- **never reuse a name.** Never reuse the name of anything deletable. Give each incarnation its own name, keep one pointer to the current one, and let one collector delete what nothing points to. When stale executors keep needing fences or waits, look for a reused name first.
- **ownership first.** Establish ownership, lifetimes, and invariants before coordination. List holders and release conditions before GC protocols. Prefer explicit ownership over timestamps or grace periods.
- **acquire before use.** Acquire references before use and hold them while any user needs the data. On handoff: acquire receiver refs, publish, then release sender refs. Require evidence the lifetime ended before cleanup; logical deletion or process exit may not suffice.
- **safety is not retention.** Separate safety invariants from retention policy; verify safety, liveness, and performance independently. When lifetime is uncertain, retain and reconcile later, and account for the capacity cost.
- **converge on rerun.** Every state-changing step reaches the same end state when run twice or rerun after a crash at any point. Derive steps from existing state, not from what the last run meant to do; leave nothing a rerun cannot recognize as stale.
- **survive the rollout.** During rolling deploys and rollbacks, old and new code share every shape (RPC body, queue message, token, stored row, file format). New readers accept old shapes; new writers write what old readers accept until all readers upgrade; a later release drops the old shape (expand, then contract).
- **fails at the boundary.** A test for a mechanism includes one case that can fail at the real boundary. A mutation check breaks the invariant, not only the patch.
