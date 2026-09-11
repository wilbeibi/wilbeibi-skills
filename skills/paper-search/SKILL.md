---
name: paper-search
description: Find and rank research papers by relevance, recency, field-adjusted impact, venue, and author affiliation. Use when searching AI, agents, runtimes, storage, databases, infrastructure, recent or superseding work, company or lab research, or evidence for technical claims. Do NOT use for general web search or GitHub repository evaluation.
---

# paper-search

Search OpenAlex + arXiv, fuse compact query variants, then rank by relevance and **impact
relative to the paper's own field and age**. No API key or auth.

```bash
python3 scripts/paper_search.py "agent runtime" -q "LLM agent infrastructure"
python3 scripts/paper_search.py "distributed storage" --institution Alibaba
python3 scripts/paper_search.py "crash consistency" --venue FAST
python3 scripts/paper_search.py "agent memory" --fresh 60 --category cs.AI
python3 scripts/paper_search.py --after arXiv:2307.03172 --about "position bias"
python3 scripts/paper_search.py --selftest
```

Repeat `-q` for alternate terminology; papers matching several variants rank higher within
their quality bucket. `--institution` resolves a lab/company and includes its descendants;
`--institution-type company` searches industry broadly. Venue aliases include FAST, OSDI,
SOSP, NSDI, MLSys, NeurIPS, ICML, ICLR, VLDB, and SIGMOD. `--after` takes `arXiv:ID`,
`DOI:x`, or an OpenAlex `Wxxx`. Feed a useful displayed topic back through `--topic`.
Use `--json` for machine output and `--help` for all flags.

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
paper with 300. `#` shows OpenAlex's inferred topic and high-confidence keywords; use them
to refine a query, not as ground truth. `[TOP]` includes FAST and the major AI/systems venues.

## Traps

- **Citation counts are a lagging indicator.** In AI/infra, the paper that matters may be
  6 weeks old with zero citations. Never conclude "nothing exists" from a citation-ranked
  list — run `--fresh 60` before saying a topic is unexplored.
- **FWCI is noise below ~18 months** — the expected-citation denominator is near zero, so
  7 citations can score FWCI 108. The script ignores it below that age; don't reintroduce
  it by reading the raw number off a young paper.
- **Preprint date ≠ publication date.** A 2024 TACL paper may be a 2023 arXiv paper; the
  idea landed 8 months before the venue date, and in a fast field that lead is the story.
  Output shows `preprint YYYY-MM` when they differ — cite the earlier one for priority.
- **Author credibility is the weakest signal here; don't lean on it.** OpenAlex conflates
  common names ("Kevin Lin": h=75 across 825 works, several people), and `h=` is the max
  across authors — the value conflation inflates. Prefer the `@ Stanford, Berkeley`
  affiliation beside it. On `--fresh` arXiv hits both are absent by design: arXiv exposes
  no institutions, and name lookup is worse than useless ("Feng Wang" → 4,865 authors, so
  you'd attach a stranger's h-index). That is what `FRESH?` means — open the PDF.
- **A landmark is cited by every field.** `--after` on a famous paper returns medical and
  legal applications too; pass `--about "<keywords>"` to keep the frontier on topic.
- **Affiliation is a scope, not a quality score.** Resolve a named lab/company with
  `--institution`; use `--institution-type company` only when industry-wide recall is wanted.
- **Topics and keywords are inferred and sometimes polysemous.** Expand only labels that
  fit the paper's title/abstract. Never promote a result solely because a tag matches.
- **`--field cs` is the default.** Pass `--field any` for anything else, or results look
  mysteriously empty. Venue metadata is imperfect regardless — a paper published at EMNLP
  may still read `[PREPRINT] arXiv`, so trust the citation numbers over the tier label.

## Workflow for a fast-moving topic

1. Turn the question into 2–4 short variants: canonical phrase, acronym, alternate community
   term, and mechanism. Pass them separately with `-q`; do not make one long synonym query.
2. Inspect the first pass's titles, topics, and keywords. Rerun only useful discovered terms;
   add `--topic`, `--institution`, `--institution-type company`, `--venue`, or `--category`
   when asked.
3. `paper_search.py --after <landmark-id> --about "<topic>" --since <~12mo ago>` — what
   built on it since, ranked by impact. This is how you avoid citing a superseded result.
4. `paper_search.py "<topic>" --fresh 45` — what dropped in the last few weeks, which
   step 1 structurally cannot see.
5. Read the abstracts, then the two or three papers that actually earned it.
