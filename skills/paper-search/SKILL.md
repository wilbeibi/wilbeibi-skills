---
name: paper-search
description: Find research papers on a topic with publication date and quality signals attached, so recent work and credible work can be told apart from noise. Use when asked to "find papers on X", "what's the research on Y", "is there a paper about Z", "what's new in <field> since <date>", "what superseded this paper", or when a claim about AI/ML/systems should be grounded in literature. Do NOT use for general web search (use a web-search skill) or to evaluate a GitHub repo (use repo-eval).
---

# paper-search

Search OpenAlex + arXiv and rank by **impact relative to the paper's own field and age** —
not raw citation counts, which always favor old papers and always bury the work published
last month. No API key, no auth.

```bash
scripts/paper_search.py "lost in the middle long context"        # topic search
scripts/paper_search.py "kv cache compression" --since 2025-06   # only recent work
scripts/paper_search.py "agent memory" --fresh 60                # + arXiv, last 60 days
scripts/paper_search.py --after arXiv:2307.03172 --about "position bias"  # what built on it
scripts/paper_search.py "raft consensus" --field any --limit 25  # non-CS, or wider
scripts/paper_search.py --selftest                               # offline; no network
```

`--json` for machine output. `--after` takes `arXiv:ID`, `DOI:x`, or an OpenAlex `Wxxx`.
Set `OPENALEX_MAILTO=<your email>` for OpenAlex's faster polite pool (optional).

## Reading the output

Papers are bucketed, best first. The buckets are the point — **recency and quality are
independent axes**, and collapsing them into one score hides exactly the tradeoff that
matters in a fast-moving field.

| Bucket | Means |
|---|---|
| `LANDMARK` | cited fast *and* far above its field — read this first |
| `STRONG` | peer-reviewed, comfortably above field average |
| `RISING` | recent and being picked up quickly |
| `FRESH+` | too new to be cited, but credible venue or authors |
| `OK` | real, unremarkable |
| `FRESH?` | too new to be cited **and** unvetted — verify it yourself |
| `THIN` | uncited preprint, authors with no track record — usually skip |

Each line shows `date (age) · citations (velocity) · fwci · [tier] venue · authors h=<max
h-index>`. **FWCI** is field-weighted citation impact: 1.0 = exactly the average for that
field and year, so it lets a systems paper with 90 citations correctly outrank an LLM
paper with 300. `[TOP]` = top-tier venue (NeurIPS/ICML/ACL/OSDI/SOSP/VLDB/…).

## Traps

- **Citation counts are a lagging indicator.** In AI/infra, the paper that matters may be
  6 weeks old with zero citations. Never conclude "nothing exists" from a citation-ranked
  list — run `--fresh 60` before saying a topic is unexplored.
- **FWCI is noise for papers under ~18 months** (the expected-citation denominator is near
  zero, so 7 citations can score FWCI 108). The script already ignores FWCI below that age;
  don't reintroduce it by reading the raw number off a young paper.
- **Preprint date ≠ publication date.** A 2024 TACL paper may be a 2023 arXiv paper; the
  idea landed 8 months before the venue date, and in a fast field that lead is the story.
  Output shows `preprint YYYY-MM` when they differ — cite the earlier one for priority.
- **h-index is name-conflated, so read `@ affiliation` instead.** OpenAlex merges authors
  with common names — "Kevin Lin" reports h=75 across 825 works, several different people.
  `h=` is the max across the authors, which is the value conflation inflates. Treat a high
  `h=` on a common name as unproven; the `@ Stanford, Berkeley` affiliation next to it is
  free of that problem and is the better prior on a paper too new to be cited.
- **`--fresh` arXiv hits show `h=?` and no affiliation, and that is not a bug.** arXiv's
  API exposes no institutions, and resolving authors by name is worse than useless
  ("Feng Wang" matches 4,865 OpenAlex authors, so you would attach a stranger's h-index).
  A days-old preprint has no trustworthy machine signal — hence `FRESH?`, "verify
  yourself". Open the PDF and judge it; that is the only real option, so budget for it.
- **A landmark is cited by every field.** `--after` on a famous paper returns medical and
  legal applications too; pass `--about "<keywords>"` to keep the frontier on topic.
- **`--field cs` is the default** and filters to Computer Science. Pass `--field any` for
  anything else, or results will look mysteriously empty.
- OpenAlex venue metadata is imperfect: a paper published at EMNLP may still be tagged
  `[PREPRINT] arXiv`. Trust the citation numbers over the tier label; check the PDF link.

## Workflow for a fast-moving topic

1. `paper_search.py "<topic>"` — find the LANDMARK and what is established.
2. `paper_search.py --after <landmark-id> --about "<topic>" --since <~12mo ago>` — what
   built on it since, ranked by impact. This is how you avoid citing a superseded result.
3. `paper_search.py "<topic>" --fresh 45` — what dropped in the last few weeks, which
   step 1 structurally cannot see.
4. Read the abstracts, then the two or three papers that actually earned it.
