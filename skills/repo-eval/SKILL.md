---
name: repo-eval
description: Evaluate a public GitHub repository's momentum and maintenance health. Use when asked whether a repository is healthy, growing, declining, abandoned, or well maintained, or when vetting dependencies and OSS projects. Do NOT use for code or architecture review.
---

# repo-eval

Score a GitHub repo 0-100 on **momentum** (popularity trajectory) and **maintenance**
(how well it is run), then drop it on a quadrant. Two axes decouple: a repo can be
popular-but-abandoned or niche-but-impeccable. Read them together, never alone.

- **Momentum** comes from the [OSS Insight API](https://ossinsight.io/docs/api) (no auth):
  stargazers history, issue/PR-creator history, org breakdown.
- **Maintenance** comes from `gh` (your existing auth): time-to-first-response, time-to-merge,
  PR acceptance rate, issue half-life, open-PR backlog age, release cadence, self-merge rate,
  contributor concentration, CI. These are computed **month-by-month** over a ≥12-month window
  (`--months`, default 18) and fitted to a slope, so trends — not just current levels — drive
  the verdict (e.g. response time *creeping up* = dying, flat = mature).

The script always prints the **raw metrics** beside the scores — the verdict is auditable,
not a black box. See [REFERENCE.md](REFERENCE.md) for every metric definition, the scoring
thresholds, and the gotchas (squash-merge, bot noise, mature-vs-dying).

## Quick start

```bash
# Full evaluation (needs network for OSS Insight + an authenticated gh)
python3 scripts/repo_eval.py vercel/next.js

# One axis at a time
python3 scripts/repo_eval.py vercel/next.js --momentum-only
python3 scripts/repo_eval.py vercel/next.js --maintenance-only

# Machine-readable (includes the per-month trend series under maintenance.monthly)
python3 scripts/repo_eval.py vercel/next.js --json

# Widen the maintenance trend window, or use weekly star granularity for young repos
python3 scripts/repo_eval.py vercel/next.js --months 24
python3 scripts/repo_eval.py vercel/next.js --period week

# Verify the metric math offline (no network)
python3 scripts/repo_eval.py --selftest
```

## Steps

1. Confirm `gh auth status` is logged in (the maintenance axis needs it). OSS Insight needs
   no auth but must be reachable (some sandboxes block `api.ossinsight.io`).
2. Run `repo_eval.py OWNER/REPO`. If one axis is unreachable it degrades gracefully and the
   verdict says "Incomplete" — rerun with `--maintenance-only` / `--momentum-only` as needed.
3. Read the **verdict** (the quadrant) first, then sanity-check it against the raw metrics.
   The score is a transparent weighted average; trust the metrics over the number.
4. When interpreting, apply the REFERENCE.md rules: low momentum + steady maintenance + flat
   backlog = **mature**, not dying; green CI + recent commits that are all bot bumps =
   **neglected**, not healthy.

## Notes

- Zero third-party dependencies — stdlib + the `gh` CLI only.
- Bot accounts (`*[bot]`, dependabot, renovate, github-actions, …) are filtered before
  computing contributor, response-time, and merge stats.
- Star/contributor totals are ratchets that only climb; this skill works in **rates and
  trends**, not totals, so a rolled-over project still reads as declining.
- On hyper-active repos the issue/PR page cap can make the actual trend window shorter than
  `--months`; the report prints `*_span_months` and a `!` note when that happens, and the
  affected trends return `null` rather than a misleadingly short slope.
- For SaaS-OSS, high contributor concentration is expected (the company is the maintainer) —
  it is reported as risk, not penalized heavily. The license axis is out of scope; check it
  separately (OSI vs BSL/SSPL/source-available, and whether it changed).
