---
name: paper-ingest
description: Ingest research papers into source-preserving Obsidian notes with engineering learning guides. Use when asked to ingest a paper or PDF, or refresh a paper's generated guide. Do NOT use for literature search or whole books.
compatibility: An Obsidian vault with scripts/paper-ingest, uv, and the script's configured model credentials.
---

# paper-ingest

Help a senior infrastructure engineer learn unfamiliar ideas, explain mechanisms,
and assess transfer to work without assuming an academic background.

## Run

Resolve the vault from the current workspace or OBSIDIAN_VAULT_ROOT; read its
AGENTS.md and `scripts/paper-ingest --help`. The vault owns the executable;
do not create a second copy here. If absent, report the missing prerequisite.

1. Verify title, authors, venue/year and canonical source against the publisher
   or author page. Search the vault for the title and source before importing.
2. Use a local PDF, fetching the verified original when needed. Run a dry run,
   then ingest with explicit `--vault` and `--source`. Preserve the default model.

```bash
scripts/paper-ingest --vault /path/to/Vault --dry-run paper.pdf
scripts/paper-ingest --vault /path/to/Vault --source https://publisher/paper paper.pdf
scripts/paper-ingest --vault /path/to/Vault --context "OCI blob GC; shared immutable layers" paper.pdf
```

`--context` is optional task context, not evidence or a replacement for the
general learning goal. Run `--help` for other flags. Born-digital extraction
stays deterministic; scanned figures, equations and numbers need visual checks.

## Review the guide

- Lead with the insight and what is worth learning, not the institution or hype.
- Walk through a concrete mechanism and its correctness intuition. Explain new
  domain terms; keep familiar engineering details compact. Proofs are optional.
- Expose assumptions, shifted costs, failure modes and cases where it loses.
- Bind important results to workload, baseline, metric and verified section or
  figure. Distinguish phase speedup from end-to-end benefit and combined gains
  from individual optimizations. Check numbers against the original PDF when
  extraction is ambiguous; never invent a locator to make a claim look sourced.
- Separate paper findings, explanatory examples and application hypotheses.
  A useful new mental model is sufficient; do not force a work or AI application.
- When an application is credible, propose a small falsifiable experiment with
  a baseline and observable outcome. Include a short route back into the paper.

Treat generated text as a draft. Check its central mechanism, assumptions and
2-4 consequential claims against the source before calling the note reviewed.
Correct unsupported claims and incomplete protocol explanations in the generated
guide; remove its pending-review callout only after these checks. Checksums are
error detection, not a proof; a benchmark win is not a universal ordering.
Mark incomplete source coverage or failed generation explicitly; length and
valid JSON do not establish factual correctness.

## Save

Keep source text and attachments intact. For an existing note, replace only
the generated guide on an explicit refresh request; preserve user annotations.
Follow vault placement and frontmatter validation, then report each touched note
and any unverified claims. Observe the vault's bulk-edit checkpoint.
