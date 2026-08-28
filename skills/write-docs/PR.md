# Commits and PRs

A commit message is not a label for the diff — the diff already says what changed. It exists to answer the question a maintainer will have in two years: *why does this code look like this?* Write for the reader running `git log` during an outage.

Read the complete diff and verification output before drafting. Use **natural** mode: clarity and consistent terminology matter, but a mechanical procedural voice does not.

## Subject line

`affected/package: short lowercase summary`

- Name the package, module, or subsystem the change lands in, then a colon.
- Lowercase after the colon; no trailing period; imperative mood (`fix`, `add`, `drop` — not `fixed`, `adds`).
- Under ~70 characters. If it won't fit, the change is probably two commits.
- Scope by what the change *affects*, not where the file happens to live.

## Body: problem → approach → consequences

1. **Problem** — what was wrong or missing, stated so it's understandable without the diff. If a reader can't tell why anyone would want this, nothing else in the message matters.
2. **Approach** — what you did and, when a reasonable person would have done something else, why not that.
3. **Consequences** — what changes for callers: behavior, performance, API surface, migration burden. Include what got worse.

## Evidence, not adjectives

Replace every claim of quality with the thing that would prove it.

| Don't write | Write |
|---|---|
| "significantly faster" | the benchmark, before and after, with units |
| "fixes a bug" | the failing input and the wrong output it produced |
| "cleaner" / "more robust" | the count that dropped — call sites, branches, lines, dependencies |
| "should be safe" | the test that covers it, or an explicit statement that it isn't covered |

Paste real output. A pasted `before:`/`after:` block is worth more than any sentence about improvement.

## Rules

- **Deletion is a headline.** If the change removes code, a dependency, or a concept, lead with that — it's the most valuable thing in the message.
- **Deviations get bullets.** If the implementation diverged from an agreed design or a review comment, list each divergence explicitly. Never let a reviewer discover it in the diff.
- **Hedge honestly.** Uncertainty stated with a planned follow-up ("this doesn't handle X; issue #123") reads as competence. Uncertainty hidden reads as a bug.
- **Link the issue,** and say what the link contains so the reader can decide whether to open it.
- **No mechanical summaries.** "Updates 12 files" and "refactors the handler" tell the reader nothing they can't get from `--stat`.

## PR descriptions

Same structure, plus what a reviewer needs that a commit message doesn't:

- **How to review it** — the order to read the commits in, or which file holds the actual change and which are mechanical fallout.
- **How it was verified** — commands run and what they printed, not "tested locally."
- **What's deliberately out of scope,** so nobody reviews for something you chose not to do.

If the PR is one commit, the description *is* the commit message — write it once, well, and don't paraphrase it in two places.

## Self-check

Read the message with the diff hidden. Can you tell what problem it solves and what the tradeoff was? If not, the message is describing the change instead of arguing it.
