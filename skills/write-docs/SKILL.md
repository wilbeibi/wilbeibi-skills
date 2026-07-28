---
name: write-docs
description: Write or critique the prose that ships with a codebase — READMEs, CLI help and flag design, code comments and docstrings, AGENTS.md/CLAUDE.md agent guides, and commit or PR descriptions. Use when drafting, improving, or reviewing any of these; not for design docs or internal wikis.
---

# write-docs

Pick the artifact, read that file, then write. Do not load more than one — the conventions differ and mixing them produces documents that serve nobody.

| Writing… | Read | Reader you are serving |
|---|---|---|
| A README for a public lib, CLI, or agent tool | [READMES.md](READMES.md) | someone deciding in 30 seconds whether to use this |
| CLI flags, subcommands, `--help`, error text, output contracts | [CLI.md](CLI.md) | someone typing at a prompt, and the script that wraps them |
| Code comments, docstrings, inline rationale | [COMMENTS.md](COMMENTS.md) | the maintainer reading this during an outage |
| `AGENTS.md` / `CLAUDE.md` operating guides | [AGENTSMD.md](AGENTSMD.md) | an agent with no memory of your project |
| Commit messages, PR descriptions, changelog entries | [PR.md](PR.md) | a maintainer running `git log` in two years |

Not this skill: design docs, ADRs (use `grill-me`), internal service wikis, or authoring a skill (use `write-skill`).

## What every one of them owes the reader

These hold regardless of artifact. The lens files add the conventions specific to each.

- **Name the reader before the first sentence.** Every rule below is downstream of who is reading and what they came for. A README written for a contributor and a README written for a user are different documents.
- **Lead with what they came for.** Value and shortest path first; provenance, philosophy, and history later or not at all.
- **Evidence, not adjectives.** "Fast," "clean," "robust," and "simple" are claims the reader cannot check. Replace each with the number, the benchmark, the before/after, or delete it.
- **Say each thing once.** Repetition across sections is the most common defect in all five artifacts — it signals to the reader that nothing here is load-bearing.
- **Earn every section.** A heading that exists because the template had one costs the reader a scroll and buys nothing. Omit it.
- **State what is missing.** Known gaps, unsupported cases, and planned follow-ups read as competence; discovering them later reads as a bug.

## Reviewing rather than writing

Same lens, inverted: read the artifact against its file's conventions, then report what the target reader cannot get from it and what they are made to read twice. Lead with the defect, not with praise.
