# repo-eval reference

Metric definitions, scoring, and the traps that make naive repo analysis wrong.
Borrows vocabulary from [CHAOSS](https://chaoss.community/kb-metrics-and-metrics-models/)
(Linux Foundation Community Health Analytics) so the terms are vetted, not invented.

## The two axes (why they are separate)

Popularity and upkeep **decouple**. Measure them independently:

- **Momentum** — is usage/interest growing, flat, or past its peak?
- **Maintenance** — is the project responsive, releasing, and tended?

A viral tool whose author left is popular+abandoned. A niche lib one person tends
carefully is unpopular+maintained. Reporting a single "health" number hides this; the
quadrant keeps them apart.

## Momentum metrics (OSS Insight, no auth)

Everything here works in **rates/trends**, never totals — stars, contributor counts, and
downloads are ratchets that keep climbing long after a project rolls over.

| Metric | Source endpoint | Meaning |
|---|---|---|
| `star_adds_per_period_recent` | `/stargazers/history` | New stars/period, mean of last 3 periods. History is cumulative, so the script diffs consecutive points. |
| `star_adds_per_period_peak` | same | Best period ever — the denominator for "past peak". |
| `star_pct_of_peak` | same | recent ÷ peak. Near 1.0 = still near its best; near 0 = long past peak. |
| `star_rate_slope` | same | Least-squares slope of the new-stars series over the trailing 12 periods. Negative = decelerating. |
| `issue_creators_slope` / `pr_creators_slope` | `/issue_creators/history`, `/pull_request_creators/history` | Trend in distinct people opening issues/PRs — a real-usage proxy that (unlike stars) actually falls when people leave. |
| `top_org_pr_share` | `/pull_request_creators/organizations` | Share of PR authors from the single top org — employee-vs-community proxy. |

Series that are monotonic non-decreasing are treated as cumulative and differenced
automatically; series with dips are taken as already per-period.

## Maintenance metrics (`gh`)

Pulled in one GraphQL query (recent 40 issues + 40 PRs + open PRs + releases) plus two REST
calls (contributors, workflows). Bots are filtered first.

| Metric | Meaning / why |
|---|---|
| `median_first_response_hours` | Median time to first **human, non-author** comment/review on issues+PRs in the window. The single best living-project signal (CHAOSS *Time to First Response*). |
| `median_merge_hours_internal` vs `_external` | Time-to-merge for maintainer PRs vs outside PRs. For SaaS-OSS the tell: if employee PRs merge in hours and community PRs rot, "open" is cosmetic. |
| `pr_acceptance_rate` | Merged ÷ (merged + closed-without-merge), over *decided* PRs. Low = most contributions get rejected/stale (CHAOSS *Change Request Closure*). |
| `median_pr_close_hours_unmerged` | How fast rejected/stale PRs are actually closed out (vs left hanging). |
| `median_issue_close_hours` | Issue half-life — median time-to-close for closed issues. |
| `median_pr_interactions` | Comments + reviews per PR — review depth / back-and-forth, not just a rubber-stamp merge. |
| `self_merge_rate` | Fraction of merged PRs where author == merger. High = weak review or effectively solo. |
| `open_pr_count`, `open_pr_median_age_days`, `open_pr_oldest_age_days` | Backlog of mergeable contributions nobody is acting on — the saddest neglect signal. |
| `days_since_last_release`, `median_release_gap_days` | Release recency and regularity. |
| `days_since_last_push` | Recency of any commit; feeds the abandonment override. |
| `top1_commit_share`, `top3_commit_share`, `contributor_gini` | Bus factor / concentration. Gini 0 = even, →1 = one author owns everything. |
| `ci_workflows` | Whether CI exists at all. |

## Trends (month-by-month, the `--months` window)

The maintenance axis paginates the last N months (default 18, min 12) of issues and PRs,
buckets them by **created-month** (months with <2 items are dropped as noise), and fits a
slope. Each `*_trend` is a **fractional change across the window**: `slope · span / mean`, so
`+0.40` ≈ 40% higher at the end than the start. A trend needs ≥4 qualifying months or it
returns `null`.

| Trend | + means | Reads as |
|---|---|---|
| `first_response_trend` | responses getting **slower** | rising = attention slipping (dying signal) |
| `merge_time_trend` | merges getting **slower** | rising = review bandwidth shrinking |
| `acceptance_trend` | **more** PRs accepted | rising = opening up; falling = closing down |
| `issue_close_trend` | issues closing **slower** | rising = backlog pressure building |

The full per-month series is in `maintenance.monthly` in `--json` output. `requested_window_months`,
`issues_span_months`, and `prs_span_months` report what was actually covered; a `!` note fires
when the page cap (`MAX_PAGES`×100 items) truncated a hyper-active repo's window below request —
in that case the truncated axis's PR-only trends will be `null` rather than misleadingly short.

## Scoring (transparent weighted averages, 0-100)

Subscores are clamped to 0..1 with **legible linear breakpoints**, then weighted. The exact
weights and breakpoints live at the top of `repo_eval.py` (`MOMENTUM_WEIGHTS`,
`MAINT_WEIGHTS`) — change them there, they are deliberately not hidden.

**Momentum** = 0.40·pct-of-peak + 0.35·star-rate-slope + 0.25·engagement-slope.
(slope→score: 0.5 means flat; saturates at ±25% of the series mean per period.)

**Maintenance** = 0.30·response + 0.15·acceptance + 0.15·release-recency + 0.15·backlog-age
+ 0.10·self-merge + 0.15·bus-factor. Breakpoints: response 0 at ~30 days, release 0 at ~365
days, backlog 0 at ~180-day median open-PR age, acceptance taken as the rate itself.

The maintenance **score is a level** (how well-run right now); the **trends drive the verdict**
(trajectory) — see the quadrant below. A subscore is dropped (and weights renormalized) when
its data is missing, so a repo with no releases is not punished for lacking that component.

## The quadrant (read this, not the number)

| Momentum | Maintenance | Verdict |
|---|---|---|
| high | high | Rising & well-maintained |
| high | low | Popular but under-maintained — interest outpacing upkeep |
| low | high | Mature / niche & well-tended (backlog flat **and** response trend steady) — slow ≠ dying |
| low | high | Cooling — maintained but `first_response_trend` rising >30% or backlog aging |
| low | low | Stalling / at risk |

Overrides: `archived` repos and repos with no human push in >180 days **and** no release in
>365 days are flagged abandoned regardless of score.

## Gotchas (where naive analysis goes wrong)

- **Mature vs dying look identical on a commit graph.** Declining commits = feature-complete
  *or* dying. Disambiguate by holding maintenance constant: steady response time + flat
  backlog + releases still shipping = mature; rising response time + growing backlog +
  contributors leaving = dying. The skill makes this **data-driven**: the low-momentum verdict
  splits Mature vs Cooling on `first_response_trend` (> +0.30 over the window = slipping), not
  a guess.
- **Green-CI vanity.** Recent commits and passing CI can be entirely Dependabot bumps while
  every human issue rots. Bot filtering + the human-response metric guard against this.
- **Squash-merge masks commit volume.** Raw commit counts are workflow artifacts (1 commit/PR
  vs 20). This skill counts merged PRs and contributor *shares*, not raw commits.
- **author-date vs commit-date** diverge under rebase/force-push; GitHub timestamps used here
  are event times, which is what you want for timelines.
- **Stars lag and spike on launches/funding.** pct-of-peak and the slope deseasonalize the
  spike; downloads (npm/pypi/crates) are a better usage signal if you have them — out of
  scope here but worth pairing manually.
- **SaaS-OSS license risk is the dominant risk and is NOT measured here.** Check separately
  whether it is OSI-licensed vs BSL/SSPL/source-available, whether the license *changed*, and
  whether the open repo tracks the real product or is a stripped community edition.

## Rate limits

OSS Insight: 600 req/hr per IP, no auth. `gh`: your authenticated GitHub quota (REST 5000
req/hr; GraphQL is point-budgeted, 5000 points/hr). One full evaluation is ~6 OSS Insight
calls + (1 meta + up to `MAX_PAGES` issue pages + up to `MAX_PAGES` PR pages) GraphQL + 2 REST.
With the default cap that is ≤25 GraphQL calls; a normal repo stops paging far sooner once it
reaches the cutoff date.
