---
name: paper-search
description: Find research papers on a topic with publication date and quality signals attached, so recent work and credible work can be told apart from noise. Use when asked to "find papers on X", "what's the research on Y", "is there a paper about Z", "what's new in <field> since <date>", "what superseded this paper", or when a claim about AI/ML/systems should be grounded in literature. Do NOT use for general web search (use a web-search skill) or to evaluate a GitHub repo (use repo-eval).
---

# paper-search

Search Semantic Scholar + OpenAlex + arXiv at once, then rank by **impact relative to
the paper's own field and age** — not raw citation counts, which always favor old papers
and always bury the work published last month.

```bash
scripts/paper_search.py "lost in the middle long context"        # topic search
scripts/paper_search.py "kv cache compression" --since 2025-06   # only recent work
scripts/paper_search.py "agent memory" --fresh 60                # + arXiv, last 60 days
scripts/paper_search.py --after arXiv:2307.03172 --about "position bias"  # what built on it
scripts/paper_search.py --like arXiv:2307.03172                  # parallel work
scripts/paper_search.py "raft consensus" --field any --limit 25  # non-CS, or wider
scripts/paper_search.py --selftest                               # offline; no network
```

`--json` for machine output. `--after` takes `arXiv:ID`, `DOI:x`, or an OpenAlex `Wxxx`.

## Setup

Works with zero config. Two env vars are worth setting (this repo is public — keep them
in the environment, never in a file here):

- `S2_API_KEY` — **strongly recommended.** Semantic Scholar's unauthenticated pool is
  shared and 429s constantly. Without it, runs randomly lose TLDRs, author h-index, and
  influential-citation counts; the script warns and degrades to OpenAlex instead of dying.
  Free key: <https://www.semanticscholar.org/product/api#api-key-form>
- `OPENALEX_MAILTO` — your email; gets you OpenAlex's faster polite pool.

## Reading the output

Papers are bucketed, best first. The buckets are the point — **recency and quality are
independent axes**, and collapsing them into one score hides exactly the tradeoff that
matters in a fast field.

| Bucket | Means |
|---|---|
| `LANDMARK` | cited fast *and* far above its field — read this first |
| `STRONG` | peer-reviewed, comfortably above field average |
| `RISING` | recent and being picked up quickly |
| `FRESH+` | too new to be cited, but credible venue or authors |
| `OK` | real, unremarkable |
| `FRESH?` | too new to be cited **and** unvetted — verify it yourself |
| `THIN` | uncited preprint, authors with no track record — usually skip |

Each line shows `date (age) · citations (velocity, influential) · fwci · [tier] venue ·
authors h=<max h-index>`. **FWCI** is field-weighted citation impact: 1.0 = exactly the
average for that field and year, so it lets a systems paper with 90 citations correctly
outrank an LLM paper with 300. `[TOP]` = top-tier venue (NeurIPS/ICML/ACL/OSDI/SOSP/VLDB/…),
detected from the DBLP key, not the messy venue string.

## Traps

- **Citation counts are a lagging indicator.** In AI/infra, the paper that matters may be
  6 weeks old with zero citations. Never conclude "nothing exists" from a citation-ranked
  list — run `--fresh 60` before saying a topic is unexplored.
- **FWCI is noise for papers under ~18 months** (the expected-citation denominator is near
  zero, so 7 citations can score FWCI 108). The script already ignores FWCI below that age;
  don't reintroduce it by reading the raw number on a young paper.
- **Preprint date ≠ publication date.** A 2024 TACL paper may be a 2023 arXiv paper; the
  idea landed 8 months before the venue date, and in a fast field that lead is the story.
  Output shows `preprint YYYY-MM` when they differ — cite the earlier one for priority.
- **A landmark is cited by every field.** `--after` on a famous paper returns medical and
  legal applications too; pass `--about "<keywords>"` to keep the frontier on topic.
- **`--field cs` is the default** and filters to Computer Science. Pass `--field any` for
  anything else, or the search will look mysteriously empty.
- Both engines have junk: OpenAlex carries spam records with impossible citation counts.
  Sanity-check any single number before repeating it; the raw metrics are printed so you can.

## Workflow for a fast-moving topic

1. `paper_search.py "<topic>"` — find the LANDMARK and what is established.
2. `paper_search.py --after <landmark-id> --about "<topic>" --since <~12mo ago>` — what
   built on it since, ranked by impact. This is how you avoid citing a superseded result.
3. `paper_search.py "<topic>" --fresh 45` — what dropped in the last few weeks, which
   step 1 structurally cannot see.
4. Read TLDRs, then the two or three papers that actually earned it.
