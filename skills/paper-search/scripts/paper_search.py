#!/usr/bin/env python3
"""Search papers with recency and quality signals attached.

Sources (all free, no key required):
  Semantic Scholar  relevance search, TLDR, influential citations, author h-index
  OpenAlex          FWCI (field-weighted citation impact) + field/year percentile
  arXiv             the only source that sees papers days old

Stdlib only. Set S2_API_KEY to avoid the shared-pool 429s.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

S2 = "https://api.semanticscholar.org/graph/v1"
S2_REC = "https://api.semanticscholar.org/recommendations/v1"
OPENALEX = "https://api.openalex.org/works"
ARXIV = "https://export.arxiv.org/api/query"
MAILTO = os.environ.get("OPENALEX_MAILTO", "openalex@example.com")

S2_FIELDS = (
    "title,abstract,publicationDate,year,citationCount,influentialCitationCount,"
    "venue,publicationTypes,externalIds,tldr,authors.name,authors.hIndex,openAccessPdf"
)
# The /citations and /recommendations endpoints reject tldr and authors.* — a different
# schema from /search. Pull what they allow, then backfill the rest via /paper/batch.
S2_LITE_FIELDS = (
    "title,abstract,publicationDate,year,citationCount,influentialCitationCount,"
    "venue,publicationTypes,externalIds,openAccessPdf"
)

# Venue tiers. DBLP keys (from S2 externalIds) are the cleanest signal — S2's
# `venue` string is inconsistent ("Annual Meeting of the ACL" vs "ACL").
TOP_DBLP = {
    # ML / AI
    "nips", "neurips", "icml", "iclr", "colm", "aistats", "uai", "corl", "mlsys",
    # NLP
    "acl", "emnlp", "naacl", "eacl", "coling", "tacl",
    # Vision
    "cvpr", "iccv", "eccv",
    # General AI
    "aaai", "ijcai",
    # Systems / infra / distributed
    "osdi", "sosp", "nsdi", "sigcomm", "eurosys", "usenix", "atc", "fast",
    "asplos", "isca", "micro", "hpca", "socc", "hotos", "podc", "disc",
    "ppopp", "sc", "cidr", "middleware",
    # Data
    "vldb", "pvldb", "sigmod", "icde", "kdd", "sigir", "www", "recsys",
    # PL / SE / security
    "pldi", "popl", "oopsla", "icse", "fse", "ccs", "sp", "uss", "ndss",
    # Journals
    "jmlr", "tmlr", "cacm", "tocs", "tods", "tpds",
}
TOP_NAME = re.compile(
    r"\b(neural information processing|international conference on machine learning|"
    r"learning representations|association for computational linguistics|"
    r"empirical methods in natural language|computer vision and pattern recognition|"
    r"operating systems design|operating systems principles|networked systems design|"
    r"architectural support for programming languages|conference on language modeling|"
    r"machine learning research|very large data bases|management of data|"
    r"usenix (annual technical|security)|eurosys|sigcomm|mlsys)\b",
    re.I,
)
PREPRINT_VENUES = re.compile(
    r"^(arxiv(\.org)?|corr|preprint|openreview(\.net)?|ssrn|biorxiv|research square|)$", re.I
)


def get(url, headers=None, tries=4, raw=False):
    """GET with backoff. S2's unauthenticated pool 429s constantly."""
    hdrs = {"User-Agent": "paper-search/1.0"}
    if headers:
        hdrs.update(headers)
    delay = 2.0
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=hdrs), timeout=30
            ) as r:
                return r.read() if raw else json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")


def s2_get(path, params):
    key = os.environ.get("S2_API_KEY")
    hdrs = {"x-api-key": key} if key else {}
    url = f"{path}?{urllib.parse.urlencode(params)}"
    return get(url, hdrs)


# --------------------------------------------------------------------------- #
# normalization
# --------------------------------------------------------------------------- #


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def parse_date(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(s[: len(fmt.replace("%Y", "2000"))], fmt).date()
        except ValueError:
            continue
    return None


def months_since(d, today=None):
    if not d:
        return None
    today = today or date.today()
    return max(0.5, (today - d).days / 30.44)


def venue_tier(paper):
    """TOP | PEER | PREPRINT | ? — the 'is this a nowhere paper' signal."""
    dblp = (paper.get("externalIds") or {}).get("DBLP") or ""
    # keys look like conf/acl/LiuX24 or journals/tacl/LiuLHPBPL24
    m = re.match(r"(conf|journals)/([a-z0-9]+)/", dblp)
    if m and m.group(2) in TOP_DBLP:
        return "TOP"
    venue = paper.get("venue") or ""
    if TOP_NAME.search(venue):
        return "TOP"
    if m:
        return "PEER"
    if venue and not PREPRINT_VENUES.match(venue.strip()):
        return "PEER"
    return "PREPRINT"


def from_s2(p, today=None):
    d = parse_date(p.get("publicationDate")) or parse_date(str(p.get("year") or ""))
    ext = p.get("externalIds") or {}
    authors = p.get("authors") or []
    hs = [a.get("hIndex") or 0 for a in authors]
    cites = p.get("citationCount") or 0
    age = months_since(d, today)
    return {
        "title": p.get("title") or "",
        "date": d.isoformat() if d else None,
        "age_mo": round(age, 1) if age else None,
        "cites": cites,
        "influential": p.get("influentialCitationCount") or 0,
        "velocity": round(cites / age, 1) if age else None,
        "venue": p.get("venue") or "arXiv",
        "tier": venue_tier(p),
        "authors": [a.get("name") for a in authors[:4]],
        "h_max": max(hs) if hs else 0,
        "arxiv": ext.get("ArXiv"),
        "doi": ext.get("DOI"),
        "s2_id": p.get("paperId"),
        "tldr": ((p.get("tldr") or {}).get("text")) or "",
        "pdf": (p.get("openAccessPdf") or {}).get("url") or "",
        "fwci": None,
        "pctile": None,
        "retracted": False,
        "source": "s2",
    }


def from_arxiv(entry, ns, today=None):
    def txt(tag):
        el = entry.find(f"a:{tag}", ns)
        return (el.text or "").strip() if el is not None else ""

    aid = txt("id").rsplit("/", 1)[-1]
    d = parse_date(txt("published")[:10])
    authors = [
        (a.find("a:name", ns).text or "").strip()
        for a in entry.findall("a:author", ns)
    ]
    age = months_since(d, today)
    return {
        "title": re.sub(r"\s+", " ", txt("title")),
        "date": d.isoformat() if d else None,
        "age_mo": round(age, 1) if age else None,
        "cites": 0,
        "influential": 0,
        "velocity": None,  # unknowable: too new to have been cited
        "venue": "arXiv",
        "tier": "PREPRINT",
        "authors": authors[:4],
        "h_max": 0,  # unknown without an extra lookup
        "arxiv": re.sub(r"v\d+$", "", aid),
        "doi": None,
        "s2_id": None,
        "tldr": re.sub(r"\s+", " ", txt("summary"))[:280],
        "pdf": f"https://arxiv.org/pdf/{aid}",
        "fwci": None,
        "pctile": None,
        "retracted": False,
        "source": "arxiv",
    }


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #


def search_s2(query, limit, since=None, min_cites=None, field="cs"):
    params = {"query": query, "limit": min(limit, 100), "fields": S2_FIELDS}
    if since:
        params["publicationDateOrYear"] = f"{since}:"
    if min_cites:
        params["minCitationCount"] = min_cites
    if field == "cs":
        params["fieldsOfStudy"] = "Computer Science"
    data = s2_get(f"{S2}/paper/search", params)
    return [from_s2(p) for p in data.get("data") or []]


def invert_abstract(inv):
    if not inv:
        return ""
    words = sorted((pos, w) for w, ps in inv.items() for pos in ps)
    return " ".join(w for _, w in words)


def from_openalex(w):
    d = parse_date(w.get("publication_date"))
    src = ((w.get("primary_location") or {}).get("source") or {})
    venue = src.get("display_name") or ""
    ids = w.get("ids") or {}
    doi = (ids.get("doi") or "").replace("https://doi.org/", "") or None
    arxiv = None
    for loc in w.get("locations") or []:
        landing = (loc.get("landing_page_url") or "")
        m = re.search(r"arxiv\.org/abs/([\d.]+)", landing)
        if m:
            arxiv = m.group(1)
    cites = w.get("cited_by_count") or 0
    age = months_since(d)
    is_pre = w.get("type") == "preprint" or PREPRINT_VENUES.match(venue.strip())
    return {
        "title": w.get("title") or w.get("display_name") or "",
        "date": d.isoformat() if d else None,
        "age_mo": round(age, 1) if age else None,
        "cites": cites,
        "influential": 0,  # OpenAlex has no equivalent
        "velocity": round(cites / age, 1) if age else None,
        "venue": venue or "arXiv",
        "tier": "PREPRINT" if is_pre else ("TOP" if TOP_NAME.search(venue) else "PEER"),
        "authors": [
            (a.get("author") or {}).get("display_name")
            for a in (w.get("authorships") or [])[:4]
        ],
        "h_max": 0,  # not on the works endpoint
        "arxiv": arxiv,
        "doi": doi,
        "s2_id": None,
        "tldr": invert_abstract(w.get("abstract_inverted_index"))[:280],
        "pdf": (w.get("best_oa_location") or {}).get("pdf_url") or "",
        "fwci": w.get("fwci"),
        "pctile": (w.get("citation_normalized_percentile") or {}).get("value"),
        "retracted": bool(w.get("is_retracted")),
        "source": "openalex",
    }


def search_openalex(query, since=None, min_cites=None, field="cs"):
    """Runs alongside S2 (precise where S2 is fuzzy) and carries FWCI natively."""
    filters = ["type:article|preprint"]
    if field == "cs":
        filters.append("primary_topic.field.id:fields/17")  # Computer Science
    if since:
        filters.append(f"from_publication_date:{since if len(since) > 4 else since + '-01-01'}")
    if min_cites:
        filters.append(f"cited_by_count:>{min_cites - 1}")
    # title_and_abstract.search, not the bare `search` param: the latter also matches
    # full text, which drags in papers that merely mention the words in passing.
    filters.append(f"title_and_abstract.search:{query}")
    url = f"{OPENALEX}?" + urllib.parse.urlencode(
        {
            "filter": ",".join(filters),
            # always pull the full page: OpenAlex ranks loosely, so the relevance
            # filter needs real candidates to work with, and it costs the same one call
            "per-page": 50,
            "select": "id,ids,doi,title,display_name,publication_date,type,cited_by_count,"
                      "fwci,citation_normalized_percentile,is_retracted,primary_location,"
                      "locations,best_oa_location,authorships,abstract_inverted_index",
            "mailto": MAILTO,
        }
    )
    return [from_openalex(w) for w in (get(url).get("results") or [])]


def resolve_openalex(seed):
    """seed (arXiv:2307.03172 | DOI:10.x | 10.x | Wxxx) -> OpenAlex work ids.

    Returns BOTH the preprint and published records when they exist: OpenAlex keeps
    them as separate works (Lost-in-the-Middle: 972 citations on the TACL record, 61
    on the arXiv one) and citers point at either, so using one loses half the frontier.
    """
    s = seed.strip()
    if re.fullmatch(r"W\d+", s):
        return [s]
    doi = None
    if s.lower().startswith("arxiv:"):
        doi = f"10.48550/arXiv.{s.split(':', 1)[1]}"
    elif s.lower().startswith("doi:"):
        doi = s.split(":", 1)[1]
    elif s.startswith("10."):
        doi = s
    if not doi:
        return []
    try:
        w = get(f"{OPENALEX}/doi:{doi}?"
                + urllib.parse.urlencode({"select": "id,title", "mailto": MAILTO}))
    except Exception:
        return []
    ids = [w["id"].rsplit("/", 1)[-1]]
    title = w.get("title") or ""
    if not title:
        return ids
    try:
        twins = get(f"{OPENALEX}?" + urllib.parse.urlencode(
            {"filter": f"title.search:{title}", "select": "id,title", "mailto": MAILTO}))
    except Exception:
        return ids
    for t in twins.get("results") or []:
        if norm_title(t.get("title")) == norm_title(title):
            wid = t["id"].rsplit("/", 1)[-1]
            if wid not in ids:
                ids.append(wid)
    return ids


def citing_openalex(seed, since=None, field="cs", limit=50):
    """Top-cited papers that CITE the seed — the frontier that built on a landmark.

    OpenAlex sorts server-side, which is the whole game: a landmark has thousands of
    citers and the few that matter are not the first ones the API hands back.
    (Note: `cites:W1|W2` is silently WRONG in the API — it returns unrelated papers.
    One call per id.)
    """
    out = []
    for wid in resolve_openalex(seed):
        filters = [f"cites:{wid}"]
        if field == "cs":
            filters.append("primary_topic.field.id:fields/17")
        if since:
            filters.append(
                f"from_publication_date:{since if len(since) > 4 else since + '-01-01'}")
        url = f"{OPENALEX}?" + urllib.parse.urlencode({
            "filter": ",".join(filters),
            "sort": "cited_by_count:desc",
            "per-page": min(max(limit * 2, 25), 50),
            "select": "id,ids,doi,title,display_name,publication_date,type,cited_by_count,"
                      "fwci,citation_normalized_percentile,is_retracted,primary_location,"
                      "locations,best_oa_location,authorships,abstract_inverted_index",
            "mailto": MAILTO,
        })
        try:
            out += [from_openalex(w) for w in (get(url).get("results") or [])]
        except Exception:
            continue
    return out


def citing_s2(seed, fetch=500):
    """Fallback for seeds OpenAlex cannot resolve. The S2 endpoint returns citers in
    no useful order and cannot sort, so this is a blunt deep pull ranked locally."""
    out, offset = [], 0
    while offset < fetch:
        data = s2_get(
            f"{S2}/paper/{seed}/citations",
            {"limit": min(500, fetch - offset), "offset": offset,
             "fields": S2_LITE_FIELDS},
        )
        batch = data.get("data") or []
        out += [from_s2(e["citingPaper"]) for e in batch if e.get("citingPaper")]
        if data.get("next") is None:
            break
        offset = data["next"]
    return out


def like_s2(seed, limit):
    """Semantically similar work — catches parallel efforts that never cite each other."""
    data = s2_get(
        f"{S2_REC}/papers/forpaper/{seed}",
        {"limit": min(limit * 3, 100), "fields": S2_LITE_FIELDS},
    )
    return [from_s2(p) for p in data.get("recommendedPapers") or []]


def s2_backfill(papers):
    """One POST to fill in the TLDR and author h-index that /citations and
    /recommendations refuse to return. Best-effort: never fail the search over it."""
    need = [p for p in papers if p["s2_id"] and not p["authors"]]
    if not need:
        return
    key = os.environ.get("S2_API_KEY")
    hdrs = {"Content-Type": "application/json", "User-Agent": "paper-search/1.0"}
    if key:
        hdrs["x-api-key"] = key
    req = urllib.request.Request(
        f"{S2}/paper/batch?fields=tldr,authors.name,authors.hIndex",
        data=json.dumps({"ids": [p["s2_id"] for p in need[:500]]}).encode(),
        headers=hdrs,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            rows = json.loads(r.read())
    except Exception:
        return
    for p, row in zip(need, rows):
        if not row:
            continue
        authors = row.get("authors") or []
        p["authors"] = [a.get("name") for a in authors[:4]]
        hs = [a.get("hIndex") or 0 for a in authors]
        p["h_max"] = max(hs) if hs else 0
        p["tldr"] = ((row.get("tldr") or {}).get("text")) or p["tldr"]


def search_arxiv(query, days, limit):
    """Last-N-days preprints. These are invisible to citation-based ranking."""
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    q = " AND ".join(f'abs:"{t}"' if " " in t else f"abs:{t}" for t in terms)
    url = f"{ARXIV}?" + urllib.parse.urlencode(
        {
            "search_query": q,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": min(limit * 3, 100),
        }
    )
    raw = get(url, raw=True)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    cutoff = date.today() - timedelta(days=days)
    out = []
    for e in root.findall("a:entry", ns):
        p = from_arxiv(e, ns)
        d = parse_date(p["date"])
        if d and d >= cutoff:
            out.append(p)
    return out


def enrich_openalex(papers, cap=200):
    """FWCI is the only cross-field-fair quality number here: 1.0 = exactly the
    field+year average, >2 strong, >10 exceptional. It is what lets a systems paper
    with 90 citations outrank an LLM paper with 300."""
    by_doi = {}
    for p in papers:
        doi = p.get("doi")
        if not doi and p.get("arxiv"):
            doi = f"10.48550/arXiv.{p['arxiv']}"
        if doi:
            by_doi.setdefault(doi.lower(), []).append(p)
    # OpenAlex takes 50 DOIs per OR-filter; page through the most-cited candidates.
    ranked = sorted(by_doi, key=lambda d: -max(p["cites"] for p in by_doi[d]))
    for i in range(0, min(len(ranked), cap), 50):
        chunk = ranked[i : i + 50]
        url = f"{OPENALEX}?" + urllib.parse.urlencode(
            {
                "filter": "doi:" + "|".join(chunk),
                "per-page": 50,
                "select": "doi,fwci,citation_normalized_percentile,cited_by_count,"
                          "is_retracted",
                "mailto": MAILTO,
            }
        )
        try:
            data = get(url)
        except Exception:
            return  # enrichment is best-effort; never fail the search over it
        for w in data.get("results") or []:
            doi = (w.get("doi") or "").lower().replace("https://doi.org/", "")
            for p in by_doi.get(doi, []):
                p["fwci"] = w.get("fwci")
                pct = w.get("citation_normalized_percentile") or {}
                p["pctile"] = pct.get("value")
                p["retracted"] = bool(w.get("is_retracted"))


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #


def verdict(p, median_velocity):
    """Bucket a paper. Deliberately NOT a single score — recency and quality are
    independent axes and collapsing them hides exactly the tradeoff you care about."""
    if p["retracted"]:
        return "RETRACTED"
    age, vel, fwci = p["age_mo"], p["velocity"], p["fwci"]

    # Too new to have citations. Judge on priors only, and say so.
    if age is not None and age < 4 and (p["cites"] or 0) < 5:
        if p["tier"] == "TOP" or p["h_max"] >= 30:
            return "FRESH+"  # new, but from a credible source
        return "FRESH?"  # new and unvetted — read the abstract, trust nothing

    # influential/h_max only exist on S2 records. Treat absence as unknown, never as
    # zero — otherwise an OpenAlex-only landmark gets scored as an ignored paper.
    infl = p["influential"] if p["s2_id"] else None

    # FWCI is only meaningful once a paper has aged. The expected-citation denominator
    # for the current year is tiny, so a 5-month-old paper with 7 citations scores
    # FWCI 108 — louder than a genuine landmark. Ignore FWCI below ~18 months and let
    # velocity, venue, and author track record carry the young papers.
    fw = fwci if (age is not None and age >= 18) else None

    strong = (fw is not None and fw >= 2) or (
        fw is None and vel is not None and vel >= max(1.0, 2 * median_velocity)
    )
    # A landmark must be cited *fast in absolute terms* AND not contradicted by the
    # field-normalized score. Velocity leads; FWCI confirms.
    vel_ok = vel is not None and vel >= max(5.0, 5 * median_velocity)
    huge = vel_ok and (fw is None or fw >= 20)

    if huge and p["cites"] >= 50 and (fw is not None or (infl or 0) >= 10):
        return "LANDMARK"
    if strong and (p["tier"] in ("TOP", "PEER") or (infl or 0) >= 5):
        return "STRONG"
    if age is not None and age <= 15 and strong:
        return "RISING"
    if p["tier"] == "PREPRINT" and (vel or 0) < 0.5 and (p["h_max"] or 0) < 15:
        return "THIN"  # preprint nobody cites by authors with no track record
    return "OK"


ORDER = {
    "LANDMARK": 0, "STRONG": 1, "RISING": 2, "FRESH+": 3,
    "OK": 4, "FRESH?": 5, "THIN": 6, "RETRACTED": 7,
}


def rank(papers):
    vels = sorted(p["velocity"] for p in papers if p["velocity"] is not None)
    median = vels[len(vels) // 2] if vels else 0.0
    for p in papers:
        p["verdict"] = verdict(p, median)
    papers.sort(
        key=lambda p: (
            ORDER[p["verdict"]],
            -(p["fwci"] or 0),
            -(p["velocity"] or 0),
            -(p["cites"] or 0),
        )
    )
    return papers, median


STOP = {
    "the", "a", "an", "of", "in", "on", "for", "to", "and", "or", "with", "how",
    "what", "why", "is", "are", "be", "using", "via", "from", "at", "by", "that",
    "this", "it", "as", "can", "do", "does", "paper", "papers", "study",
}


def relevance(papers, query, floor=0.4):
    """S2's relevance ranking collapses on long queries — it happily returns
    'The Darfur Sultanate' for an LLM query. Require the result to actually
    contain the query's content words before we bother scoring its quality."""
    terms = {w for w in re.findall(r"[a-z0-9]+", query.lower())
             if w not in STOP and len(w) > 2}
    if not terms:
        return papers
    phrase = query.lower().strip('"')
    kept = []
    for p in papers:
        hay = f"{p['title']} {p['tldr']}".lower()
        if phrase in hay:
            kept.append(p)
            continue
        hits = sum(1 for t in terms if t[:-1] in hay or t in hay)
        if hits / len(terms) >= floor:
            kept.append(p)
    return kept


def dedupe(papers):
    """The same paper arrives as an arXiv preprint AND a published record AND from
    two engines. Merge them: S2 brings TLDR/h-index/influential, OpenAlex brings FWCI,
    arXiv brings the true first-posted date."""
    best = {}
    for p in papers:
        k = norm_title(p["title"])[:80]
        cur = best.get(k)
        if not cur:
            best[k] = p
            continue
        # keep the record with the strongest provenance, then backfill from the other
        keep, other = (cur, p) if (cur["cites"], cur["tier"] == "TOP") >= (
            p["cites"], p["tier"] == "TOP") else (p, cur)
        for f in ("fwci", "pctile", "tldr", "doi", "arxiv", "s2_id", "pdf"):
            if not keep.get(f) and other.get(f):
                keep[f] = other[f]
        for f in ("influential", "h_max", "cites"):
            keep[f] = max(keep.get(f) or 0, other.get(f) or 0)
        keep["retracted"] = keep["retracted"] or other["retracted"]
        if keep["tier"] != "TOP" and other["tier"] == "TOP":
            keep["tier"], keep["venue"] = other["tier"], other["venue"]
        # the earliest date is when the idea actually landed — preprints lead venues
        # by 6-18 months, and in a fast field that lead is the whole story
        for d in (keep["date"], other["date"]):
            if d and (not keep.get("first_posted") or d < keep["first_posted"]):
                keep["first_posted"] = d
        if keep["first_posted"] and keep["first_posted"] != keep["date"]:
            age = months_since(parse_date(keep["first_posted"]))
            keep["age_mo"] = round(age, 1) if age else keep["age_mo"]
            if keep["age_mo"]:
                keep["velocity"] = round((keep["cites"] or 0) / keep["age_mo"], 1)
        best[k] = keep
    return list(best.values())


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #

NOTE = {
    "LANDMARK": "the paper everyone builds on — read first",
    "STRONG": "peer-reviewed and well above field average",
    "RISING": "recent and being picked up fast",
    "FRESH+": "too new to be cited; credible venue/authors",
    "OK": "real but unremarkable",
    "FRESH?": "too new to be cited AND unvetted — verify yourself",
    "THIN": "uncited preprint, no author track record — likely skip",
    "RETRACTED": "retracted",
}


def render(papers, median, query):
    if not papers:
        print("no results")
        return
    print(f"\n{len(papers)} papers for: {query}")
    print(f"(field median velocity in this result set: {median:.1f} cites/mo)\n")
    last = None
    for p in papers:
        v = p["verdict"]
        if v != last:
            print(f"── {v}  ({NOTE[v]})")
            last = v
        age = f"{p['age_mo']:.0f}mo" if p["age_mo"] else "?"
        fp = p.get("first_posted")
        if fp and fp != p["date"]:
            age += f", preprint {fp[:7]}"
        fw = f"fwci {p['fwci']:.1f}" if p["fwci"] else "fwci —"
        vel = f"{p['velocity']:.1f}/mo" if p["velocity"] is not None else "—"
        # these two only exist on S2 records; show "?" not "0" when unknown
        infl = f"{p['influential']} infl" if p["s2_id"] else "infl ?"
        hx = f"h={p['h_max']}" if p["h_max"] else "h=?"
        auth = ", ".join(a for a in p["authors"][:2] if a) + (
            "…" if len(p["authors"]) > 2 else "")
        print(f"  {p['title'][:88]}")
        print(
            f"    {p['date']}  ({age})  {p['cites']} cites ({vel}, {infl})"
            f"  {fw}  [{p['tier']}] {p['venue'][:34]}"
        )
        print(f"    {auth}  {hx}")
        if p["tldr"]:
            print(f"    → {p['tldr'][:150]}")
        link = (
            f"https://arxiv.org/abs/{p['arxiv']}"
            if p["arxiv"]
            else (p["pdf"] or f"https://www.semanticscholar.org/paper/{p['s2_id']}")
        )
        print(f"    {link}\n")


# --------------------------------------------------------------------------- #


def selftest():
    today = date(2026, 7, 13)
    base = dict(
        retracted=False, tier="TOP", h_max=40, influential=30, fwci=None, cites=0,
        age_mo=None, velocity=None, s2_id="x",
    )
    cases = [
        # brand new + credible = FRESH+, never THIN
        ({**base, "age_mo": 1.0, "cites": 0, "velocity": 0.0}, "FRESH+"),
        # brand new + no track record = FRESH?, explicitly not trusted
        ({**base, "age_mo": 1.0, "cites": 0, "velocity": 0.0, "tier": "PREPRINT",
          "h_max": 2, "influential": 0}, "FRESH?"),
        # old, huge field-normalized impact
        ({**base, "age_mo": 36, "cites": 4000, "velocity": 111.0, "fwci": 260.0}, "LANDMARK"),
        # same landmark, but OpenAlex-only: no influential count, no h-index, and a
        # citation count that lags reality. FWCI alone must still call it.
        ({**base, "age_mo": 36, "cites": 972, "velocity": 26.9, "fwci": 264.0,
          "influential": 0, "h_max": 0, "s2_id": None}, "LANDMARK"),
        # young paper with a wildly inflated FWCI (7 cites in 5mo => fwci 108 because
        # the current-year denominator is ~0). Must NOT outrank a real landmark.
        ({**base, "age_mo": 5, "cites": 7, "velocity": 1.5, "fwci": 108.9,
          "influential": 0, "tier": "PEER"}, "OK"),
        # well-cited applications paper: high FWCI, but not cited fast in absolute terms
        ({**base, "age_mo": 18, "cites": 69, "velocity": 3.8, "fwci": 96.6,
          "influential": 4, "tier": "PEER"}, "STRONG"),
        # solid peer-reviewed, above average
        ({**base, "age_mo": 24, "cites": 116, "velocity": 4.8, "fwci": 3.1,
          "influential": 9}, "STRONG"),
        # uncited preprint by unknowns = THIN
        ({**base, "age_mo": 20, "cites": 1, "velocity": 0.05, "tier": "PREPRINT",
          "h_max": 3, "influential": 0}, "THIN"),
        # a systems paper: low raw cites, but fwci says it beats its field
        ({**base, "age_mo": 30, "cites": 90, "velocity": 3.0, "fwci": 4.0,
          "influential": 6}, "STRONG"),
    ]
    fails = 0
    for p, want in cases:
        got = verdict(p, median_velocity=1.0)
        ok = got == want
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} want={want:9s} got={got}")
    assert (months_since(date(2026, 1, 13), today) or 0) > 5.9
    for venue, ext, want in [
        ("", {"DBLP": "conf/osdi/X24"}, "TOP"),          # venue lives in the DBLP key
        ("Transactions of the Association for Computational Linguistics", {}, "TOP"),
        ("arXiv", {}, "PREPRINT"),
        ("arXiv.org", {}, "PREPRINT"),                   # S2 writes it both ways
        ("npj Digital Medicine", {}, "PEER"),
    ]:
        got = venue_tier({"venue": venue, "externalIds": ext})
        if got != want:
            fails += 1
            print(f"FAIL venue_tier({venue!r}) want={want} got={got}")
    print("FAILED" if fails else "all pass")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("query", nargs="?", help="topic, e.g. 'lost in the middle long context'")
    ap.add_argument("--since", help="YYYY-MM-DD or YYYY — only papers after this")
    ap.add_argument("--fresh", type=int, metavar="DAYS",
                    help="also pull arXiv preprints from the last N days")
    ap.add_argument("--after", metavar="ID",
                    help="papers CITING this seed (arXiv:2307.03172, DOI:..., or S2 id)")
    ap.add_argument("--like", metavar="ID", help="papers semantically similar to this seed")
    ap.add_argument("--about", metavar="TEXT",
                    help="keep only --after/--like results matching these words "
                         "(a landmark is cited by every field; this keeps it on topic)")
    ap.add_argument("--min-cites", type=int)
    ap.add_argument("--field", default="cs", choices=["cs", "any"],
                    help="restrict to Computer Science (default) or search all fields")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--no-fwci", action="store_true", help="skip the OpenAlex enrichment call")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not (a.query or a.after or a.like):
        ap.error("need a query, --after, or --like")

    papers = []
    if a.after:
        papers = citing_openalex(a.after, a.since, a.field, a.limit)
        if not papers:  # seed had no OpenAlex record; fall back to the unsorted pull
            papers = citing_s2(a.after)
    if a.like:
        papers += like_s2(a.like, a.limit)
    if a.query:
        want = max(a.limit * 2, 20)
        # Both engines, always: S2 is fuzzy/semantic and misses exact-phrase hits on
        # long queries; OpenAlex is a precise title+abstract index and misses paraphrases.
        # Each covers the other's failure mode, and OpenAlex results carry FWCI natively.
        try:
            papers += search_s2(a.query, want, a.since, a.min_cites, a.field)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            print("! Semantic Scholar rate-limited (no TLDR / h-index / influential "
                  "counts this run). Set S2_API_KEY for the full signal set.",
                  file=sys.stderr)
        papers += search_openalex(a.query, a.since, a.min_cites, a.field)
        if a.fresh:
            papers += search_arxiv(a.query, a.fresh, a.limit)

    if a.since and (a.after or a.like):
        papers = [p for p in papers if p["date"] and p["date"] >= a.since]

    if a.query:
        papers = relevance(papers, a.query)
    if a.about:
        papers = relevance(papers, a.about, floor=0.34)
    papers = dedupe(papers)
    s2_backfill(papers)  # no-op unless --after/--like left holes
    if not a.no_fwci:
        enrich_openalex(papers)
    papers, median = rank(papers)
    if a.fresh:
        # Fresh papers can never win a citation-based ranking — that is the whole point
        # of asking for them. Give them their own reserved slots instead of letting
        # --limit bury them under established work.
        is_fresh = lambda p: p["verdict"].startswith("FRESH")
        papers = ([p for p in papers if not is_fresh(p)][: a.limit]
                  + [p for p in papers if is_fresh(p)][: a.limit])
    else:
        papers = papers[: a.limit]

    if a.json:
        print(json.dumps({"query": a.query or a.after or a.like,
                          "median_velocity": median, "papers": papers}, indent=2))
    else:
        render(papers, median, a.query or a.after or a.like)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            sys.exit("rate-limited by Semantic Scholar. Retry, or set S2_API_KEY "
                     "(free: https://www.semanticscholar.org/product/api#api-key-form)")
        sys.exit(f"HTTP {e.code}: {e.reason}")
    except KeyboardInterrupt:
        sys.exit(130)
