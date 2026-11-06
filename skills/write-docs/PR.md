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
3. **Consequences** — what changes for callers: behavior, performance, API surface, migration burden. Include what got worse, with the change as its subject: “this drops X”, not “X is no longer supported”.

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
- **Write for non-native readers.** Reviewers and translation tools read this text. Give each word one meaning, and use the plain verb instead of an idiom or phrasal verb (`start`, not `spin up`). Keep sentences under 25 words.
- **No mechanical summaries.** "Updates 12 files" and "refactors the handler" tell the reader nothing they can't get from `--stat`.

## PR descriptions

A commit message serves the maintainer in two years. A PR description also serves the reviewer today, who has to act on it.

Write it as an inverted pyramid: most important first, depth last. A reader who stops after any layer should still have what matters most.

1. **Title** — the outcome, in the subject-line format above.
2. **Lead** — what the reviewer needs to act, without scrolling.
3. **View** — one picture of the outcome, when the change alters a structure.
4. **Details** — evidence and review aids, in the order the reviewer needs them.
5. **Links** — everything else.

### Lead

Write these four first, a line or two each:

1. **Context** — the situation, and why it matters now.
2. **Problem** — what is broken, missing, or at risk, in one or two sentences.
3. **Outcome** — what is true after merge. Describe the result, not the diff.
4. **Ask** — what you need from the reader: a review of a named part, a decision between named options, an action, or nothing (FYI only).

Take the why and the ask from the user, the session, or the linked issue. If none of them states it, ask the user. Do not invent a plausible motivation or a generic "please review".

If the lead does not fit in about five lines, stop and tell the user. The change probably needs a conversation or a split before it needs more text.

### View

Some changes alter a structure the reviewer would otherwise rebuild from the diff: a state machine, call order across processes, ownership, a data path, or a module layout. Show that outcome as one small view:

- a **state machine graph** for changed states or transitions;
- a **table** for before/after behavior, or for options compared;
- an **illustration** (sequence, flow, or tree) for order and structure.

Pick the exact view with `show-me`. GitHub renders Mermaid in PR descriptions; commit messages are plain text, so keep them to ASCII trees or `before:`/`after:` blocks. Remove any view the reviewer would not miss.

### Details

Give the details in this order. Expand the problem only if the lead was not enough.

1. **Approach and consequences** — from the commit body, with evidence.
2. **How to review it** — the order to read the commits in, or which file holds the actual change and which are mechanical fallout.
3. **How it was verified** — commands run and what they printed, not "tested locally."
4. **What's deliberately out of scope,** so nobody reviews for something you chose not to do.

### Links

Link the issue, design doc, or longer write-up last, for readers who want to dig in. Do not make it the message.

If the PR is one commit, do not paraphrase the commit message. Put the lead on top and the commit message below it as the details.

## Self-check

Read the message with the diff hidden. Can you tell what problem it solves and what the tradeoff was? If not, the message is describing the change instead of arguing it.

For a PR, then read only the lead. Does the reviewer know why this matters now, what is true after merge, and what you need from them?
