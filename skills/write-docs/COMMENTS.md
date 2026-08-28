# Code comments

Comments exist to say what the code *can't*. If the code alone answers the question, you don't need a comment. If it doesn't, identify what's missing and pick the type.

Read the surrounding implementation and callers before writing. Preserve exact domain terms and identifiers. Use **natural** mode for rationale; use short, contract-like sentences for API guarantees and warnings.

## The litmus test

Before writing: **can the reader understand this without the comment?** If yes → delete the comment, improve the name instead. If no → identify the gap below and fill it.

## Match the gap to the type

| Information missing | Comment type | Where it goes |
|---|---|---|
| What contract does this function obey, and what are its side effects? | **Function** | Top of function/type |
| Why this architecture? What alternatives were rejected? | **Design** | Top of file/package |
| Why this specific line, when something else looks more natural? | **Why** | Inline, above the line |
| What domain knowledge (math, protocol, algorithm) does the reader need? | **Teacher** | Inline or top of function |
| If I change this, what else must I update? | **Checklist** | Inline, as a warning |
| What does this block of 5–20 lines accomplish? (cognitive chunking) | **Guide** | Inline, above the block |

**Never write:**
- **Trivial** — "increment the counter" for `i++`. The comment costs more to read than the code.
- **Backup** — commented-out old code "just in case." Git has it.
- **Debt** — `TODO`, `FIXME` inline. Put in an issue tracker or design comment instead.

## Rules

- **Full sentences.** Capital letter, period, subject + verb.
- **Explain why, not what.** The code already says what. If it doesn't, fix the code, not the comment.
- **Prefer fixing the name.** If you're about to write a comment explaining what a function does, try a better name first.
- **On structs/APIs: more comments than code.** Document field lifecycle — who initializes, who mutates, when fields become obsolete.
- **If a reviewer asks a question, add a comment.** The next reader will have the same question.

## Self-check

After writing: read the comment without the code. Does it stand alone as a claim about the system? If not, it's probably too vague. Then read the code without the comment. Is anything non-obvious unexplained? If not, the comment may be redundant.
