#!/usr/bin/env python3
"""Evaluate a public GitHub repo on two axes: momentum and maintenance.

Momentum  (popularity trajectory) -> OSS Insight public API, no auth.
Maintenance (how well it is run)   -> the `gh` CLI (uses your existing auth).

Both axes are computed as month-by-month trends, not just a snapshot:
  - momentum reads OSS Insight's monthly history and fits slopes;
  - maintenance paginates the last N months of issues/PRs, buckets them by
    month, and fits slopes on response time, merge time, PR acceptance, and
    issue close time -- so "responsiveness creeping up" (dying) is measured,
    not guessed.

The two axes are scored 0-100 and placed on a quadrant. Raw metrics are always
printed alongside the scores so the verdict is auditable, never a black box.

Zero third-party dependencies (stdlib only). Network is reached via urllib
(OSS Insight) and `gh` (GitHub). Run --selftest to verify the metric math
offline with synthetic series, no network required.

Usage:
    repo_eval.py OWNER/REPO [--period day|week|month] [--months N] [--json]
    repo_eval.py OWNER/REPO --momentum-only
    repo_eval.py OWNER/REPO --maintenance-only
    repo_eval.py --selftest

See REFERENCE.md for metric definitions, scoring thresholds, and gotchas.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median

OSSINSIGHT_BASE = "https://api.ossinsight.io/v1"
HTTP_TIMEOUT = 30

# Maintenance trend window / cost guards.
DEFAULT_MONTHS = 18          # >= 12 so a monthly slope is stable
MAX_PAGES = 12               # GraphQL pages (100 items each) per issue/PR fetch
MIN_PER_MONTH = 2            # months with fewer items are dropped (noise)
MIN_MONTHS_FOR_TREND = 4     # need this many months before a slope is reported
WORSENING_TREND = 0.30       # >30% rise across the window == "slipping"

# Logins that pollute contributor / response-time / issue-velocity stats.
BOT_SUFFIX = "[bot]"
KNOWN_BOTS = {
    "dependabot", "dependabot-preview", "renovate", "renovate-bot",
    "github-actions", "github-actions[bot]", "mergify", "mergify[bot]",
    "stale", "stale[bot]", "codecov", "codecov-commenter", "greenkeeper",
    "snyk-bot", "allcontributors", "imgbot", "pre-commit-ci",
}


# --------------------------------------------------------------------------
# small pure helpers (covered by --selftest)
# --------------------------------------------------------------------------
def is_bot(login: str | None) -> bool:
    if not login:
        return True  # anonymous / deleted -> treat as noise
    low = login.lower()
    return low.endswith(BOT_SUFFIX) or low in KNOWN_BOTS


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    try:
        # OSS Insight gives "2024-01-01"; GitHub gives "2024-01-01T12:00:00Z".
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def linear_slope(values: list[float]) -> float:
    """Least-squares slope of values vs their index. 0 if <2 points."""
    n = len(values)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    num = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    den = sum((i - mean_x) ** 2 for i in range(n))
    return num / den if den else 0.0


def auto_delta(values: list[float]) -> list[float]:
    """If a series is cumulative (monotonic non-decreasing), return its
    period-over-period deltas; otherwise return it unchanged. OSS Insight's
    stargazers/history is cumulative; creator histories are per-period."""
    if len(values) < 3:
        return values
    if all(b >= a for a, b in zip(values, values[1:])):
        return [b - a for a, b in zip(values, values[1:])]
    return values


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def trend_score(slope: float, scale: float) -> float:
    """Map a slope to 0..1 where 0.5 == flat. `scale` is the slope magnitude
    that saturates toward 0 or 1. Linear, clamped — intentionally legible."""
    if scale <= 0:
        return 0.5
    return clamp01(0.5 + 0.5 * (slope / scale))


def gini(values: list[float]) -> float:
    """Gini coefficient of contribution concentration. 0 = perfectly even,
    ->1 = one author owns everything. Empty/zero -> 0."""
    xs = sorted(v for v in values if v > 0)
    n = len(xs)
    if n == 0:
        return 0.0
    total = sum(xs)
    if total == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * cum) / (n * total) - (n + 1) / n


def month_key(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def monthly_median(items: list[tuple[datetime, float | None]]) -> list[tuple[str, float]]:
    """Bucket (created_dt, value) pairs by created-month, drop sparse months,
    return an ascending [(month, median)] series."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for dt, val in items:
        if dt is not None and val is not None:
            buckets[month_key(dt)].append(val)
    return [(m, median(vs)) for m, vs in sorted(buckets.items())
            if len(vs) >= MIN_PER_MONTH]


def monthly_rate(items: list[tuple[datetime, bool | None]]) -> list[tuple[str, float]]:
    """Bucket (created_dt, bool) pairs by month, return ascending monthly
    fraction-true series (None values are ignored)."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for dt, val in items:
        if dt is not None and val is not None:
            buckets[month_key(dt)].append(1.0 if val else 0.0)
    return [(m, sum(vs) / len(vs)) for m, vs in sorted(buckets.items())
            if len(vs) >= MIN_PER_MONTH]


def trend_fraction(series: list[tuple[str, float]]) -> float | None:
    """Approximate fractional change across a monthly series: slope * span /
    mean. +0.4 == ~40% higher at the end than the start. None if too few
    months to be meaningful."""
    vals = [v for _, v in series]
    if len(vals) < MIN_MONTHS_FOR_TREND:
        return None
    mean = sum(vals) / len(vals)
    if mean == 0:
        return 0.0
    return round(linear_slope(vals) * (len(vals) - 1) / mean, 3)


# --------------------------------------------------------------------------
# transport
# --------------------------------------------------------------------------
def fetch_ossinsight(path: str, params: dict | None = None) -> list[dict]:
    """GET an OSS Insight endpoint and return data.rows as a list of dicts.
    Numeric-looking string values are converted to float."""
    url = OSSINSIGHT_BASE + path
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        payload = json.loads(resp.read().decode())
    rows = payload.get("data", {}).get("rows", [])
    out = []
    for row in rows:
        conv = {}
        for k, v in row.items():
            if isinstance(v, str):
                try:
                    conv[k] = float(v)
                    continue
                except ValueError:
                    pass
            conv[k] = v
        out.append(conv)
    return out


def gh_api(path: str) -> object:
    """Call `gh api PATH` and return parsed JSON."""
    res = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {res.stderr.strip()}")
    return json.loads(res.stdout or "null")


def gh_graphql(query: str, **variables: str | None) -> dict:
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, val in variables.items():
        if val is None:
            continue  # omit -> GraphQL sees null (used for the first page cursor)
        cmd += ["-f", f"{key}={val}"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        raise RuntimeError(f"gh api graphql failed: {res.stderr.strip()}")
    payload = json.loads(res.stdout)
    if payload.get("errors"):
        raise RuntimeError(f"graphql errors: {payload['errors']}")
    return payload["data"]


# --------------------------------------------------------------------------
# momentum axis (OSS Insight)
# --------------------------------------------------------------------------
def momentum_metrics(owner: str, repo: str, period: str) -> dict:
    m: dict = {"available": False, "notes": []}
    try:
        stars = fetch_ossinsight(
            f"/repos/{owner}/{repo}/stargazers/history", {"period": period}
        )
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        m["error"] = f"OSS Insight unreachable: {e}"
        return m

    star_series = _series(stars, ("total", "stargazers", "count"))
    adds = auto_delta(star_series)
    if adds:
        recent = adds[-3:] if len(adds) >= 3 else adds
        peak = max(adds) if adds else 0.0
        cur = sum(recent) / len(recent)
        window = adds[-12:] if len(adds) >= 12 else adds
        avg = (sum(adds) / len(adds)) or 1.0
        m["star_adds_per_period_recent"] = round(cur, 1)
        m["star_adds_per_period_peak"] = round(peak, 1)
        m["star_pct_of_peak"] = round(cur / peak, 3) if peak else None
        m["star_rate_slope"] = round(linear_slope(window), 3)
        m["_s_peak"] = clamp01(cur / peak) if peak else 0.5
        m["_s_starslope"] = trend_score(linear_slope(window), abs(avg) * 0.25)

    # issue + PR creators per period == usage / engagement proxy
    eng_slopes = []
    for label, path in (
        ("issue_creators", f"/repos/{owner}/{repo}/issue_creators/history"),
        ("pr_creators", f"/repos/{owner}/{repo}/pull_request_creators/history"),
    ):
        try:
            rows = fetch_ossinsight(path, {"period": period})
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
        s = auto_delta(_series(rows, ("total", "count", label)))
        if len(s) >= 2:
            avg = (sum(s) / len(s)) or 1.0
            slope = linear_slope(s[-12:] if len(s) >= 12 else s)
            m[f"{label}_per_period_recent"] = round(s[-1], 1)
            m[f"{label}_slope"] = round(slope, 3)
            eng_slopes.append(trend_score(slope, abs(avg) * 0.25))
    m["_s_engagement"] = sum(eng_slopes) / len(eng_slopes) if eng_slopes else 0.5

    # org concentration of contributors (employee-vs-community proxy)
    try:
        orgs = fetch_ossinsight(
            f"/repos/{owner}/{repo}/pull_request_creators/organizations"
        )
        shares = _series(orgs, ("percentage", "proportion", "ratio", "count"))
        if shares:
            top = max(shares)
            top = top / sum(shares) if sum(shares) > 1.5 else top  # counts->share
            m["top_org_pr_share"] = round(top, 3)
    except (urllib.error.URLError, TimeoutError, OSError, KeyError):
        pass

    m["available"] = "_s_peak" in m
    return m


def _series(rows: list[dict], y_keys: tuple[str, ...]) -> list[float]:
    """Extract the first matching numeric column from OSS Insight rows."""
    if not rows:
        return []
    key = next((k for k in y_keys if k in rows[0]), None)
    if key is None:  # fall back to the first non-date numeric column
        for k, v in rows[0].items():
            if isinstance(v, (int, float)) and "date" not in k and "day" not in k:
                key = k
                break
    if key is None:
        return []
    return [float(r[key]) for r in rows if isinstance(r.get(key), (int, float))]


# --------------------------------------------------------------------------
# maintenance axis (gh)
# --------------------------------------------------------------------------
META_GQL = """
query($owner:String!, $name:String!) {
  repository(owner:$owner, name:$name) {
    isArchived
    pushedAt
    openPRs: pullRequests(first:80, states:OPEN,
        orderBy:{field:CREATED_AT, direction:ASC}) {
      totalCount
      nodes { createdAt }
    }
    releases(first:30, orderBy:{field:CREATED_AT, direction:DESC}) {
      nodes { createdAt isPrerelease }
    }
  }
}
"""

ISSUES_GQL = """
query($owner:String!, $name:String!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    issues(first:100, after:$cursor, orderBy:{field:CREATED_AT, direction:DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        createdAt closedAt state
        author { login }
        comments(first:10) { totalCount nodes { createdAt author { login } } }
      }
    }
  }
}
"""

PRS_GQL = """
query($owner:String!, $name:String!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    pullRequests(first:100, after:$cursor, orderBy:{field:CREATED_AT, direction:DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        createdAt closedAt mergedAt merged state authorAssociation
        author { login }
        mergedBy { login }
        comments(first:10) { totalCount nodes { createdAt author { login } } }
        reviews(first:10) { totalCount nodes { createdAt author { login } } }
      }
    }
  }
}
"""


def _paginate(query: str, conn_key: str, owner: str, repo: str,
              cutoff: datetime) -> tuple[list[dict], bool]:
    """Page newest-first through an issues/PRs connection until items fall
    before `cutoff` or MAX_PAGES is hit. Returns (items >= cutoff, truncated)
    where truncated means the page cap stopped us before reaching the cutoff
    (so the window is shorter than requested)."""
    nodes: list[dict] = []
    cursor: str | None = None
    truncated = True
    for _ in range(MAX_PAGES):
        data = gh_graphql(query, owner=owner, name=repo, cursor=cursor)
        conn = data["repository"][conn_key]
        page = conn["nodes"]
        nodes.extend(page)
        oldest = parse_dt(page[-1]["createdAt"]) if page else None
        if (oldest and oldest < cutoff) or not conn["pageInfo"]["hasNextPage"]:
            truncated = False  # reached the cutoff or ran out of items
            break
        cursor = conn["pageInfo"]["endCursor"]
    kept = [n for n in nodes if (d := parse_dt(n["createdAt"])) and d >= cutoff]
    return kept, truncated


def _span_months(nodes: list[dict], now: datetime) -> float:
    dates = [d for n in nodes if (d := parse_dt(n.get("createdAt")))]
    return round((now - min(dates)).days / 30, 1) if dates else 0.0


def _first_response_hours(created: str, author: str | None, events: list) -> float | None:
    c = parse_dt(created)
    if not c:
        return None
    times = []
    for ev in events:
        login = (ev.get("author") or {}).get("login")
        if is_bot(login) or login == author:
            continue
        t = parse_dt(ev.get("createdAt"))
        if t and t >= c:
            times.append(t)
    if not times:
        return None
    return (min(times) - c).total_seconds() / 3600.0


def _hours_between(a: str | None, b: str | None) -> float | None:
    da, db = parse_dt(a), parse_dt(b)
    return (db - da).total_seconds() / 3600.0 if da and db else None


def maintenance_metrics(owner: str, repo: str, months: int) -> dict:
    m: dict = {"available": False, "notes": []}
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=months * 30)
    try:
        meta = gh_graphql(META_GQL, owner=owner, name=repo)["repository"]
        issues, iss_trunc = _paginate(ISSUES_GQL, "issues", owner, repo, cutoff)
        prs, pr_trunc = _paginate(PRS_GQL, "pullRequests", owner, repo, cutoff)
    except (RuntimeError, FileNotFoundError, KeyError) as e:
        m["error"] = f"gh failed: {e}"
        return m
    m["archived"] = meta["isArchived"]
    m["requested_window_months"] = months
    m["issues_analyzed"] = len(issues)
    m["prs_analyzed"] = len(prs)
    m["issues_span_months"] = _span_months(issues, now)
    m["prs_span_months"] = _span_months(prs, now)
    # A very active repo hits the page cap before reaching the cutoff, so the
    # actual trend window is shorter than requested. Say so rather than hide it.
    if pr_trunc and m["prs_span_months"] < months * 0.8:
        m["notes"].append(
            f"PR trend window truncated to ~{m['prs_span_months']}mo by the "
            f"{MAX_PAGES * 100}-PR page cap; PR-only trends cover less than the "
            f"requested {months}mo")
    if iss_trunc and m["issues_span_months"] < months * 0.8:
        m["notes"].append(
            f"issue trend window truncated to ~{m['issues_span_months']}mo by "
            f"the {MAX_PAGES * 100}-issue page cap")

    # ---- per-item series we will both aggregate and bucket by month ----
    resp_items: list[tuple] = []        # (created_dt, first_response_hours)
    merge_items: list[tuple] = []       # (created_dt, merge_hours)  merged only
    accept_items: list[tuple] = []      # (created_dt, accepted_bool) decided PRs
    issue_close_items: list[tuple] = []  # (created_dt, close_hours)  closed issues
    interactions: list[float] = []
    merge_internal, merge_external, self_merges, merged_total = [], [], 0, 0
    closed_unmerged_hours: list[float] = []

    for it in issues:
        cdt = parse_dt(it["createdAt"])
        author = (it.get("author") or {}).get("login")
        fr = _first_response_hours(it["createdAt"], author, it["comments"]["nodes"])
        resp_items.append((cdt, fr))
        if it["state"] == "CLOSED":
            ch = _hours_between(it["createdAt"], it["closedAt"])
            issue_close_items.append((cdt, ch))

    for pr in prs:
        cdt = parse_dt(pr["createdAt"])
        author = (pr.get("author") or {}).get("login")
        ev = pr["comments"]["nodes"] + pr["reviews"]["nodes"]
        resp_items.append((cdt, _first_response_hours(pr["createdAt"], author, ev)))
        interactions.append(pr["comments"]["totalCount"] + pr["reviews"]["totalCount"])

        if pr["merged"]:
            merged_total += 1
            ttm = _hours_between(pr["createdAt"], pr["mergedAt"])
            merge_items.append((cdt, ttm))
            accept_items.append((cdt, True))
            if (pr["authorAssociation"] or "") in ("OWNER", "MEMBER", "COLLABORATOR"):
                if ttm is not None:
                    merge_internal.append(ttm)
            elif ttm is not None:
                merge_external.append(ttm)
            merger = (pr.get("mergedBy") or {}).get("login")
            if author and merger and author == merger and not is_bot(author):
                self_merges += 1
        elif pr["state"] == "CLOSED":  # closed without merging
            accept_items.append((cdt, False))
            ch = _hours_between(pr["createdAt"], pr["closedAt"])
            if ch is not None:
                closed_unmerged_hours.append(ch)

    # ---- snapshot aggregates over the whole window ----
    resp_vals = [v for _, v in resp_items if v is not None]
    if resp_vals:
        m["median_first_response_hours"] = round(median(resp_vals), 1)
        m["_s_response"] = clamp01(1 - median(resp_vals) / (30 * 24))  # 0 at ~30d
    if merge_internal:
        m["median_merge_hours_internal"] = round(median(merge_internal), 1)
    if merge_external:
        m["median_merge_hours_external"] = round(median(merge_external), 1)
    if merged_total:
        m["self_merge_rate"] = round(self_merges / merged_total, 3)
        m["_s_selfmerge"] = clamp01(1 - self_merges / merged_total)
    decided = [v for _, v in accept_items]
    if decided:
        rate = sum(1 for v in decided if v) / len(decided)
        m["pr_acceptance_rate"] = round(rate, 3)
        m["_s_acceptance"] = clamp01(rate)
    if closed_unmerged_hours:
        m["median_pr_close_hours_unmerged"] = round(median(closed_unmerged_hours), 1)
    issue_close_vals = [v for _, v in issue_close_items if v is not None]
    if issue_close_vals:
        m["median_issue_close_hours"] = round(median(issue_close_vals), 1)
    if interactions:
        m["median_pr_interactions"] = round(median(interactions), 1)

    # ---- monthly trends (the whole point of the >=12 month window) ----
    fr_series = monthly_median(resp_items)
    merge_series = monthly_median(merge_items)
    accept_series = monthly_rate(accept_items)
    iclose_series = monthly_median(issue_close_items)
    m["first_response_trend"] = trend_fraction(fr_series)   # + = slower (worse)
    m["merge_time_trend"] = trend_fraction(merge_series)    # + = slower (worse)
    m["acceptance_trend"] = trend_fraction(accept_series)   # + = more accepting
    m["issue_close_trend"] = trend_fraction(iclose_series)  # + = slower (worse)
    m["monthly"] = {
        "first_response_hours": fr_series,
        "merge_hours": merge_series,
        "pr_acceptance_rate": accept_series,
        "issue_close_hours": iclose_series,
    }

    # ---- open PR backlog (inherently a current snapshot) ----
    open_ages = [(now - d).days for pr in meta["openPRs"]["nodes"]
                 if (d := parse_dt(pr["createdAt"]))]
    m["open_pr_count"] = meta["openPRs"]["totalCount"]
    if open_ages:
        m["open_pr_median_age_days"] = int(median(open_ages))
        m["open_pr_oldest_age_days"] = max(open_ages)
        m["_s_backlog"] = clamp01(1 - median(open_ages) / 180)  # 0 at ~6 months

    # ---- releases ----
    rels = [d for x in meta["releases"]["nodes"] if (d := parse_dt(x["createdAt"]))]
    if rels:
        last = max(rels)
        m["days_since_last_release"] = (now - last).days
        m["_s_release"] = clamp01(1 - (now - last).days / 365)
        if len(rels) >= 2:
            srt = sorted(rels, reverse=True)
            m["median_release_gap_days"] = int(median(
                [(a - b).days for a, b in zip(srt, srt[1:])]))
    else:
        m["days_since_last_release"] = None

    pushed = parse_dt(meta["pushedAt"])
    if pushed:
        m["days_since_last_push"] = (now - pushed).days

    # ---- contributor concentration / bus factor (REST) ----
    try:
        contribs = gh_api(f"repos/{owner}/{repo}/contributors?per_page=100")
        counts = [c["contributions"] for c in contribs
                  if isinstance(c, dict) and not is_bot(c.get("login"))]
        counts.sort(reverse=True)
        total = sum(counts) or 1
        if counts:
            m["contributors_counted"] = len(counts)
            m["top1_commit_share"] = round(counts[0] / total, 3)
            m["top3_commit_share"] = round(sum(counts[:3]) / total, 3)
            m["contributor_gini"] = round(gini(counts), 3)
    except (RuntimeError, KeyError, TypeError):
        m["notes"].append("contributor stats unavailable")

    # ---- CI presence ----
    try:
        wf = gh_api(f"repos/{owner}/{repo}/actions/workflows")
        m["ci_workflows"] = wf.get("total_count", 0) if isinstance(wf, dict) else 0
    except (RuntimeError, KeyError, TypeError):
        pass

    m["available"] = any(k in m for k in ("_s_response", "_s_release",
                                          "_s_backlog", "_s_acceptance"))
    return m


# --------------------------------------------------------------------------
# scoring + quadrant
# --------------------------------------------------------------------------
MOMENTUM_WEIGHTS = {"_s_peak": 0.40, "_s_starslope": 0.35, "_s_engagement": 0.25}
MAINT_WEIGHTS = {"_s_response": 0.30, "_s_acceptance": 0.15, "_s_release": 0.15,
                 "_s_backlog": 0.15, "_s_selfmerge": 0.10, "_s_busfactor": 0.15}


def weighted_score(metrics: dict, weights: dict) -> float | None:
    parts = [(w, metrics[k]) for k, w in weights.items() if k in metrics]
    if not parts:
        return None
    wsum = sum(w for w, _ in parts)
    return round(100 * sum(w * v for w, v in parts) / wsum, 1)


def quadrant(momentum: float | None, maintenance: float | None, maint: dict) -> str:
    # hard abandonment override
    dsp = maint.get("days_since_last_push")
    dsr = maint.get("days_since_last_release")
    if maint.get("archived"):
        return "Archived (read-only)"
    if dsp is not None and dsp > 180 and (dsr is None or dsr > 365):
        return "Likely abandoned — no recent human pushes or releases"
    if momentum is None or maintenance is None:
        return "Incomplete — one axis could not be measured"
    hi_m, hi_q = momentum >= 50, maintenance >= 50
    if hi_m and hi_q:
        return "Rising & well-maintained"
    if hi_m and not hi_q:
        return "Popular but under-maintained — interest outpacing upkeep"
    if not hi_m and hi_q:
        rt = maint.get("first_response_trend")
        backlog_flat = (maint.get("open_pr_median_age_days") or 0) < 90
        slipping = rt is not None and rt > WORSENING_TREND
        if backlog_flat and not slipping:
            return ("Mature / niche & well-tended "
                    "(slow != dying: backlog flat, responsiveness steady)")
        return "Cooling — maintained but responsiveness or backlog slipping"
    return "Stalling / at risk — low momentum and weak upkeep"


def build_report(owner, repo, period, months, want_mom, want_maint) -> dict:
    rep: dict = {"repo": f"{owner}/{repo}"}
    mom = momentum_metrics(owner, repo, period) if want_mom else {"available": False}
    maint = (maintenance_metrics(owner, repo, months) if want_maint
             else {"available": False})

    if "_s_busfactor" not in maint and "contributor_gini" in maint:
        # lower concentration -> higher score (expected high for SaaS-OSS; low weight)
        maint["_s_busfactor"] = clamp01(1 - maint["contributor_gini"])

    rep["momentum"] = {k: v for k, v in mom.items() if not k.startswith("_")}
    rep["maintenance"] = {k: v for k, v in maint.items() if not k.startswith("_")}
    rep["momentum_score"] = weighted_score(mom, MOMENTUM_WEIGHTS) if mom.get("available") else None
    rep["maintenance_score"] = weighted_score(maint, MAINT_WEIGHTS) if maint.get("available") else None
    rep["verdict"] = quadrant(rep["momentum_score"], rep["maintenance_score"], maint)
    return rep


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def render(rep: dict) -> str:
    out = [f"\n{rep['repo']}", "=" * len(rep["repo"])]
    ms, qs = rep["momentum_score"], rep["maintenance_score"]
    out.append(f"  Momentum    : {ms if ms is not None else 'n/a':>5}/100  (popularity trajectory)")
    out.append(f"  Maintenance : {qs if qs is not None else 'n/a':>5}/100  (how well it is run)")
    out.append(f"  Verdict     : {rep['verdict']}")
    for axis in ("momentum", "maintenance"):
        block = rep[axis]
        if block.get("error"):
            out.append(f"\n  [{axis}] {block['error']}")
            continue
        rows = {k: v for k, v in block.items()
                if k not in ("available", "notes", "error") and v is not None
                and not isinstance(v, (dict, list))}
        if rows:
            out.append(f"\n  {axis} metrics:")
            for k, v in rows.items():
                out.append(f"    - {k}: {v}")
        for note in block.get("notes", []):
            out.append(f"    ! {note}")
    return "\n".join(out)


# --------------------------------------------------------------------------
# offline self-test (no network)
# --------------------------------------------------------------------------
def selftest() -> int:
    fails = []

    def check(name, cond):
        if not cond:
            fails.append(name)

    check("is_bot suffix", is_bot("dependabot[bot]") and is_bot("Renovate"))
    check("is_bot human", not is_bot("torvalds"))
    check("is_bot anon", is_bot(None))

    check("parse_dt Z", parse_dt("2024-01-01T00:00:00Z").year == 2024)
    check("parse_dt date", parse_dt("2016-10-01").month == 10)
    check("parse_dt bad", parse_dt("nonsense") is None)

    check("slope up", linear_slope([1, 2, 3, 4]) > 0)
    check("slope down", linear_slope([4, 3, 2, 1]) < 0)
    check("slope flat", abs(linear_slope([5, 5, 5])) < 1e-9)

    cum = [10, 30, 60, 100]
    check("auto_delta cumulative", auto_delta(cum) == [20, 30, 40])
    perp = [5, 9, 3, 7]
    check("auto_delta per-period", auto_delta(perp) == perp)

    check("trend flat=0.5", abs(trend_score(0, 10) - 0.5) < 1e-9)
    check("trend up>0.5", trend_score(5, 10) > 0.5)
    check("clamp", clamp01(2) == 1 and clamp01(-1) == 0)

    check("gini even~0", gini([5, 5, 5, 5]) < 0.05)
    check("gini skewed", gini([100, 1, 1, 1]) > 0.6)

    check("month_key", month_key(parse_dt("2024-03-15T00:00:00Z")) == "2024-03")

    items = [(parse_dt("2024-01-10T00:00:00Z"), 2.0),
             (parse_dt("2024-01-20T00:00:00Z"), 4.0),
             (parse_dt("2024-02-10T00:00:00Z"), 10.0),
             (parse_dt("2024-02-20T00:00:00Z"), 20.0)]
    series = monthly_median(items)
    check("monthly_median months", [k for k, _ in series] == ["2024-01", "2024-02"])
    check("monthly_median vals", [v for _, v in series] == [3.0, 15.0])

    rate = monthly_rate([(parse_dt("2024-01-01T00:00:00Z"), True),
                         (parse_dt("2024-01-15T00:00:00Z"), False),
                         (parse_dt("2024-02-01T00:00:00Z"), True),
                         (parse_dt("2024-02-15T00:00:00Z"), True)])
    check("monthly_rate", rate == [("2024-01", 0.5), ("2024-02", 1.0)])

    inc = [("2024-01", 10.0), ("2024-02", 12.0), ("2024-03", 14.0), ("2024-04", 16.0)]
    flat = [("2024-01", 10.0), ("2024-02", 10.0), ("2024-03", 10.0), ("2024-04", 10.0)]
    check("trend positive", trend_fraction(inc) > 0)
    check("trend flat ~0", abs(trend_fraction(flat)) < 1e-9)
    check("trend too few -> None", trend_fraction(inc[:3]) is None)

    h = _first_response_hours(
        "2024-01-01T00:00:00Z", "alice",
        [{"createdAt": "2024-01-01T00:30:00Z", "author": {"login": "alice"}},
         {"createdAt": "2024-01-01T01:00:00Z", "author": {"login": "dependabot[bot]"}},
         {"createdAt": "2024-01-01T05:00:00Z", "author": {"login": "maint"}}],
    )
    check("first_response picks human", h == 5.0)
    check("hours_between", _hours_between("2024-01-01T00:00:00Z",
                                         "2024-01-02T00:00:00Z") == 24.0)

    check("weighted_score", weighted_score({"_s_peak": 1.0}, {"_s_peak": 0.4}) == 100.0)
    check("quadrant abandoned",
          "abandoned" in quadrant(80, 80, {"days_since_last_push": 400,
                                           "days_since_last_release": 400}).lower())
    check("quadrant rising", quadrant(70, 70, {}) == "Rising & well-maintained")
    check("quadrant mature",
          quadrant(20, 70, {"open_pr_median_age_days": 30,
                            "first_response_trend": 0.0}).startswith("Mature"))
    check("quadrant cooling (response slipping)",
          quadrant(20, 70, {"open_pr_median_age_days": 30,
                            "first_response_trend": 0.9}).startswith("Cooling"))
    check("quadrant stalling", "Stalling" in quadrant(20, 20, {}))

    if fails:
        print("SELFTEST FAILED:")
        for f in fails:
            print("  x", f)
        return 1
    print("selftest: all checks passed")
    return 0


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Score a GitHub repo on momentum x maintenance.")
    ap.add_argument("repo", nargs="?", help="OWNER/REPO, e.g. vercel/next.js")
    ap.add_argument("--period", choices=("day", "week", "month"), default="month",
                    help="OSS Insight history granularity (momentum axis)")
    ap.add_argument("--months", type=int, default=DEFAULT_MONTHS,
                    help=f"maintenance trend window in months (default {DEFAULT_MONTHS}, min 12)")
    ap.add_argument("--momentum-only", action="store_true")
    ap.add_argument("--maintenance-only", action="store_true")
    ap.add_argument("--json", action="store_true", help="emit raw JSON report")
    ap.add_argument("--selftest", action="store_true", help="run offline math checks")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.repo or "/" not in args.repo:
        ap.error("provide OWNER/REPO (e.g. vercel/next.js) or --selftest")

    months = max(12, args.months)  # a stable monthly slope needs >= 12 points
    owner, repo = args.repo.split("/", 1)
    want_mom = not args.maintenance_only
    want_maint = not args.momentum_only
    rep = build_report(owner, repo, args.period, months, want_mom, want_maint)

    if args.json:
        print(json.dumps(rep, indent=2, default=str))
    else:
        print(render(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
