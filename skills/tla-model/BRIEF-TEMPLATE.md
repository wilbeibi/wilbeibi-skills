# Modeling brief: <system / component>

Write this before any TLA+. Every REQUIRED slot must be filled and confirmed by the user.

## Question (REQUIRED)
The one design question this model answers, e.g. "Can two writers both believe they own the WAL after a lease handoff?"
The component, protocol phase, or concurrency structure in scope.

## Bug history (REQUIRED)
| Mechanism | Evidence (commit, issue, file:line) | Modeled by |
|---|---|---|
| Non-atomic persist then ack: crash window | abc123, #412 | Persist split into Write + Fsync |

Group by mechanism, not by file. Also list deviations from the reference algorithm. "None found" needs the search you ran.

## Bad outcomes (REQUIRED, 3–7)
| id | Must never / must eventually happen | Why it matters |
|---|---|---|
| R1 | Two nodes commit different values at the same index | Data loss |

## Fault and environment model (REQUIRED, answer every row)
| Aspect | Allowed? | Source (code, config, SLA) |
|---|---|---|
| Message loss / duplication / reordering | | |
| Process crash; restart with which state (disk, memory) | | |
| Storage: what is durable after a crash; torn writes | | |
| Clocks and timeouts: trusted? bounded skew? | | |
| Concurrent clients or operations | | |
| Partial failure of external dependencies (object store, DB) | | |

## State (REQUIRED)
| Code field or resource | TLA+ variable | Abstraction and why | Observable from logs? |
|---|---|---|---|

## Events → actions (REQUIRED, from the code, cite file:line)
| Implementation event | file:line | TLA+ action | Atomic in code? What can interleave inside it? |
|---|---|---|---|

Split an action wherever another process can observe or act between its read and its write.
Merge steps only when nothing can observe the intermediate state.

## Properties (REQUIRED)
| Req | Property name | Kind (invariant / action property / liveness) | Violating behavior in plain words |
|---|---|---|---|
| R1 | NoDivergentCommit | invariant | n1 commits v1 at i=3, then n2 commits v2 at i=3 |

For each liveness property, name the fairness it needs and the mechanism that provides it.

## Out of scope (REQUIRED)
What is deliberately not modeled, and why that is safe for this question.

## Bounds matrix
| cfg | Constants | Faults on | Covers which edge case |
|---|---|---|---|
| small | 2 nodes, 2 values, queue ≤ 1 | crash ×1 | basic handoff |
| wide | 3 nodes, 2 values, queue ≤ 2 | crash ×1, dup | quorum overlap |

## Open questions for the user
- …
