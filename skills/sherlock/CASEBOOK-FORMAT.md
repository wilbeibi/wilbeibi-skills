# Casebook format

One file per case at `.sherlock/<case-slug>.md`. Append-mostly: new clues, tests, and status
changes go at the end of their section; a theory's status cell is edited in place. Nothing is
deleted — a dead theory with its killing clue is what stops the next session from re-running it.

````md
# Case: <one-line question>

- Opened: 2026-09-01 · Status: open | closed (confirmed | probable | unconfirmed | unanswerable)
- Question: <answerable form with a stopping condition>
- A "no" looks like: <the finding that would settle it the other way>
- Known: <observed facts; cite E-ids once logged>

## Assumptions
| assumption | why held | if wrong | status |
|---|---|---|---|
| the blog post describes the current system | it is the only architecture source | H2 revives; timeline needed | caveated |

## Clues
| id | clue | source (link, path, or command) | date | grade | obs/inf | note |
|---|---|---|---|---|---|---|
| E1 | p95 48 ms at 10M rows | own trace (DevTools HAR) | 2026-09-01 | A1 | obs | |
| E2 | "built on Postgres" | eng blog | 2023-04 | B2 | obs | may be stale |
| E3 | no cache headers on /search | own trace | 2026-09-01 | A1 | obs | absence |
| E7 | subprocessor list names no search vendor | vendor DPA page | 2026-09-01 | B2 | obs | absence |

## Theories
| id | theory | predicts (that the others do not) | status |
|---|---|---|---|
| H1 | precomputed index in the primary DB | latency flat as row count grows | live |
| H2 | external search engine | a vendor in subprocessors or job posts | dead — E7 |
| H3 | edge/HTTP cache | cold request much slower than warm; cache headers present | dead — E3, T1 |
| H0 | none of the above | | live |

## Matrix
| | H1 | H2 | H3 | H0 |
|---|---|---|---|---|
| E3 | – | – | I | – |
| E7 | C | I | – | – |

## Tests
| # | test | targets | expected if true | result | moved |
|---|---|---|---|---|---|
| T1 | cold vs warm request timing | H3 | cold ≫ warm | 47 ms / 49 ms | H3 → dead |

## Parked
- <theory or lead with its budget spent but not killed, and what would revive it>

## Verdict
<empty until convergence; then the verdict contract from SKILL.md>
````

## Rules

- **Grade every clue as you log it**, not afterwards. Letter = the source you actually touched
  (A own observation or primary record, B reliable with a track record, C usually reliable,
  D doubtful, E unreliable, F cannot judge). Number = the information (1 confirmed by an
  independent source, 2 probably true, 3 possibly true, 4 doubtful, 5 improbable, 6 cannot
  judge). A newspaper report of a registry filing is not a second source for the filing.
- **Status vocabulary:** `live`, `parked` (budget spent, not killed — say what would revive it),
  `dead — E<n>` (name the killing clue), `confirmed`. Never `dead` without a clue id.
- **Only diagnostic clues go in the matrix** — rows with at least one *I*. A row that is *C* all
  the way across stays in Clues but proves nothing; do not let it pad a favourite's column.
- **Absences are clues.** Log the missing log line, header, doc section, or job post as an
  `E<n>` with the note `absence`; they are often the most diagnostic rows.
- **Write `expected` before running.** A prediction written after the result is not a test.
  A test that changed no status still gets a row — it is the budget counter for parking a branch.
- **Assumptions get a status** — supported, caveated, or unsupported — and an `if wrong` cell that
  names the theory it would revive or kill. An unsupported assumption under the verdict is a
  residual, not a footnote.
- **Resuming a case:** read Theories and Parked first, then Tests, then Clues. Do not re-run a
  test whose result is logged; re-run only if its clue's date is now stale for the question.
