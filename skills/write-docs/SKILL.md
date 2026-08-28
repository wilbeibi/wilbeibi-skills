---
name: write-docs
description: Write or critique prose that ships with a codebase — READMEs, developer guides and runbooks, CLI text, code comments, agent guides, and commit or PR descriptions. Use when drafting, improving, or reviewing these artifacts. Do NOT use for design docs or internal wikis.
---

# write-docs

Pick the artifact, read that file, then write. Do not load more than one — the conventions differ and mixing them produces documents that serve nobody.

| Writing… | Read | Reader you are serving |
|---|---|---|
| A README for a public lib, CLI, or agent tool | [READMES.md](READMES.md) | someone deciding in 30 seconds whether to use this |
| A developer guide, tutorial, runbook, migration, or deprecation | [GUIDES.md](GUIDES.md) | someone trying to complete a task without guessing |
| CLI flags, subcommands, `--help`, error text, output contracts | [CLI.md](CLI.md) | someone typing at a prompt, and the script that wraps them |
| Code comments, docstrings, inline rationale | [COMMENTS.md](COMMENTS.md) | the maintainer reading this during an outage |
| `AGENTS.md` / `CLAUDE.md` operating guides | [AGENTSMD.md](AGENTSMD.md) | an agent with no memory of your project |
| Commit messages, PR descriptions, changelog entries | [PR.md](PR.md) | a maintainer running `git log` in two years |

Not this skill: design docs, ADRs (use `grill-me`), internal service wikis, or authoring a skill (use `write-skill`).

## Workflow

1. Read the implementation, schema, tests, `--help`, or diff that establishes the facts.
2. Name the reader and the action this document must enable.
3. Choose one canonical term for each repeated concept. Preserve exact API names and identifiers.
4. Draft through the selected artifact lens.
5. Check that every claim, command, caveat, and boundary still matches the source.
6. Apply the clarity mode below, then run the checker. Treat heuristic findings as questions, not automatic edits.

## Clarity modes

- **Strict** — procedures, safety rules, agent workflows, CLI help, and recovery instructions. Also any text whose reader cannot ask a follow-up question: tool and function descriptions, error messages, and output another agent or script parses. Put conditions before commands. Use imperative steps, one action per step, direct verbs, simple tenses, and sentences of at most 20 words.
- **Natural** — README narrative, explanations, comments, and PR rationale. Keep terminology and actors clear, but allow contractions, semicolons, sentence rhythm, and passive voice when the actor is unknown or irrelevant.

Apply modes by content block. A README quickstart can be strict while its motivation remains natural.

## Shared rules

- Lead with the reader's goal and shortest path. Put provenance and history later or omit them.
- Be genuine. Write as a maintainer helping a reader, not as a product sheet imitating confidence.
- Use evidence instead of quality adjectives. Give the measurement, example, or boundary behind the claim.
- Use one name for one thing. Do not rotate synonyms unless they identify different concepts.
- Prefer a direct verb to a noun phrase: “analyze the log,” not “perform an analysis.”
- Break noun stacks of four or more words: “calibration of the connection resistance,” not “connection resistance calibration procedure.”
- Say each fact once. Omit template sections that do not change the reader's next action.
- State unsupported cases and tradeoffs. Simpler wording must not erase precise technical meaning.

## Check the draft

```bash
python3 scripts/prose_lint.py --mode strict <path>
python3 scripts/prose_lint.py --mode natural <path>
```

Use `-` for stdin and `--json` for structured findings. Exit 1 means strict errors; review-only findings return 0. Add `<!-- prose-lint-ignore -->` to ignore one line. The checker cannot detect synonym rotation without project context, so check terminology manually. This is not an STE certification or a substitute for factual review. See [CLARITY-REFERENCE.md](CLARITY-REFERENCE.md) for rationale and sources.

## Reviewing rather than writing

Same lens, inverted: verify the artifact against its source, then report what the target reader cannot do, cannot trust, or must read twice. Lead with the defect and its location, not with praise.
