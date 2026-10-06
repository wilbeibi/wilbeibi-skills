# Code comments

Comments exist to say what the code *can't*: the contract a caller relies on, the reason behind a choice, and the coupling a local edit would miss. Agents err toward too many comments, not too few, so the default is no comment.

Read the surrounding implementation and callers before writing. Match the file's existing comment density. Preserve exact domain terms and identifiers. Use **natural** mode for rationale; use short, contract-like sentences for API guarantees and warnings.

## The litmus test

Before writing an inline comment: **can the reader understand this without the comment?** If yes → don't write it; improve the name instead. If no → identify the gap below and fill it. Function and API comments are exempt: they state the contract so the reader can skip the body.

## Match the gap to the type

| Information missing | Comment type | Where it goes |
|---|---|---|
| What contract does this obey: inputs, results, side effects, errors? | **Function** | Top of function/type |
| Why this architecture? What alternatives were rejected? | **Design** | Top of file/package |
| Why this line, when something else looks more natural? Which variant of a known algorithm, and where does it deviate? | **Why** | Inline, above the line |
| If I change this, what else must I update? | **Checklist** | Inline, as a warning |

Why comments are the ones an agent most needs to write. The reasoning lives in the session that produced the code and ends with it. Neither the code nor a later reader can rebuild it.

Before writing a checklist comment, try to make the coupling enforce itself with a test, an exhaustive match, or a type. Comment only what cannot be enforced.

Do not teach generic domain knowledge (what a Bloom filter is); the reader can look it up. Do not put section headings over blocks; extract a named function instead.

**Never write:**
- **Trivial** — "increment the counter" for `i++`. The comment costs more to read than the code.
- **Narration** — "Now we loop over…", "First, check…". It restates the code in sequence.
- **Edit history** — "Changed from X to Y", "Fixed per review", "New helper". That belongs in the commit message.
- **Session-addressed** — "as requested", "you'll want to…". The reader was not in the conversation.
- **Emphasis** — "IMPORTANT:", "CRITICAL:". If it matters, state the consequence instead.
- **Backup** — commented-out old code "just in case." Git has it.
- **Debt** — bare `TODO`, `FIXME`. If one is unavoidable, link the issue that tracks it.

## Rules

- **Full sentences.** Capital letter, period, subject + verb.
- **A comment is a claim.** When you change code, update or delete its comments in the same edit. A stale comment is worse than none, because readers, agents especially, trust it literally.
- **Inline: explain why, not what.** If the inline what is unclear, fix the code, not the comment. Function comments state what by design.
- **Prefer fixing the name over an inline comment.** A name cannot carry preconditions, side effects, or error behavior; those go in the function comment.
- **On structs/APIs: more comments than code.** Document field lifecycle — who initializes, who mutates, when fields become obsolete.
- **If a reviewer asks a question, add a comment.** The next reader will have the same question.
- **If the comment is hard to write, suspect the code.** A contract you cannot state crisply usually means the design is not settled.

## Self-check

After writing: read the comment without the code. Does it stand alone as a claim about the system? If not, it's probably too vague. Then read the code without the comment. Is anything non-obvious unexplained? If not, the comment may be redundant.

## Source

The taxonomy follows antirez, [Writing system software: code comments](https://antirez.com/news/124) (2018), which argued against too few comments. Agents write too many, so this file departs from it. It drops Guide comments, which decay into narration. It folds Teacher comments into Why, keeping only project-specific knowledge. It makes Debt stricter and adds the agent failure modes above.
