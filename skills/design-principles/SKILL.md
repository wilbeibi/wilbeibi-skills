---
name: design-principles
description: Runs named systems-design checks (single writer, never reuse a name, converge on rerun, survive the rollout, implicit state machines) when a change adds state or a mechanism, touches lifecycle, delete, GC, lock, or migration code, changes a shape another process reads, or patches the same function twice. Use when the user says "triggers", "check single writer", or another principle name, or for design and lifecycle review. Do NOT use for a general diff review (use code-review), tracing what a change breaks (use blast-radius), or naming and glossary work (use domain-modeling).
---

# design-principles

When an event below happens, run its check and put the result in the same message or commit, unasked. On "triggers", run every check against the current diff and design and report each as fired or not, with its result. Principle definitions: `references/principles.md`.

## Triggers

| Event | Check |
|---|---|
| New state or mechanism (table, field, status, flag, env var, process, queue, lock, retry, fence) | Name its one job, the worst case without it, and the existing primitive tried first. A worst case of "slower" or "one more refetch" makes it an optimization: defer it. Never trims safety. |
| New transitional status or awaited attempt (`pausing`, `flushing`, a job a row waits on) | **attempt is not status**: name the attempt and the writer of every exit, failure included. Key exits on the attempt id; never fake a terminal status to pass an ordering rule. |
| Phase start or milestone | Restate non-negotiable invariants and a diff budget. Stop and ask when the diff passes it, or at the first placeholder, compat branch, or out-of-scope file. |
| Second fix to one function or predicate, a regression from the last fix, or a change spreading past the named files | Stop coding. In one sentence, name the missing owner, the name doing two jobs, or the right layer; offer one design-level alternative. If it changes design or scope, ask first. |
| Reviewing lifecycle, storage, or status code | **implicit state machines**: for each mutable field, file, or map with no written transition table, list states and transitions with writer (`path:line`) and guard. Walk happy path, attempt failure, ambiguous timeout, crash at each step, late or duplicate executor, concurrent writer, delete mid-flight. Report states with no exit, transitions with two writers, fields whose readers disagree. |
| Several findings at once | Group by shared cause before fixing any, using the principles as classifier. Reproduce each at the real boundary or label it inference. |
| Delete, cleanup, unlink, GC, ack, or nak code | List every reader and writer of the name (late executors, crash restart, sweepers) and what proves each is done. If the name can later denote another object, fix naming first. |
| Periodic publisher, queue message, lock, or timed call | Write rate x hold time against the hard limit (queue cap, IOPS, library timeout) and the lock order. |
| Change to a shape another process or stored record reads | **survive the rollout**: walk old writer -> new reader, new writer -> old reader, rollback reading new data. State deploy order and the later contract step. Use blast-radius for the wider trace. |
| Tests for a new mechanism or fix | **fails at the boundary**: include one case at the real boundary (real responder, production-shaped data, a fake slower than the timeout, duplicate delivery). |

## Output

- Name each principle applied and the decision it changed. A name with no changed decision was not applied.
- Weigh each principle's cost; state the tradeoff instead of applying it as a rule.
