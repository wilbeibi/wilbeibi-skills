#!/usr/bin/env python3
"""Search papers with recency and quality signals attached.

Sources (free, no key, no auth):
  OpenAlex   search, citation counts, FWCI (field-weighted impact), author h-index
  arXiv      the only source that sees papers days old

Stdlib only. Set OPENALEX_MAILTO=<your email> for OpenAlex's faster polite pool.
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

OPENALEX = "https://api.openalex.org/works"
AUTHORS = "https://api.openalex.org/authors"
INSTITUTIONS = "https://api.openalex.org/institutions"
SOURCES = "https://api.openalex.org/sources"
TOPICS = "https://api.openalex.org/topics"
ARXIV = "https://export.arxiv.org/api/query"
MAILTO = os.environ.get("OPENALEX_MAILTO", "openalex@example.com")
CS_FIELD = "primary_topic.field.id:fields/17"

WORK_FIELDS = (
    "id,ids,doi,title,display_name,publication_date,type,cited_by_count,fwci,"
    "citation_normalized_percentile,is_retracted,primary_location,locations,"
    "best_oa_location,authorships,abstract_inverted_index,primary_topic,topics,keywords"
)

VENUE_ALIASES = {
    "fast": "File and Storage Technologies",
    "osdi": "Operating Systems Design and Implementation",
    "sosp": "Operating Systems Principles",
    "nsdi": "Networked Systems Design and Implementation",
    "eurosys": "European Conference on Computer Systems",
    "atc": "USENIX Annual Technical Conference",
    "asplos": "Architectural Support for Programming Languages and Operating Systems",
    "socc": "Symposium on Cloud Computing",
    "sigcomm": "Special Interest Group on Data Communication",
    "mlsys": "Machine Learning and Systems",
    "neurips": "Neural Information Processing Systems",
    "icml": "International Conference on Machine Learning",
    "iclr": "International Conference on Learning Representations",
    "acl": "Association for Computational Linguistics",
    "emnlp": "Empirical Methods in Natural Language Processing",
    "naacl": "North American Chapter of the Association for Computational Linguistics",
    "colm": "Conference on Language Modeling",
    "aamas": "Autonomous Agents and Multiagent Systems",
    "tmlr": "Transactions on Machine Learning Research",
    "vldb": "Very Large Data Bases",
    "sigmod": "Management of Data",
    "cidr": "Conference on Innovative Data Systems Research",
    "icde": "International Conference on Data Engineering",
}

# The venue name is the only tier signal OpenAlex gives, so keep this generous —
# a miss here silently demotes a good paper to PEER.
TOP_NAME = re.compile(
    r"\b(neural information processing|international conference on machine learning|"
    r"learning representations|association for computational linguistics|"
    r"empirical methods in natural language|north american chapter of the association|"
    r"computer vision and pattern recognition|international conference on computer vision|"
    r"european conference on computer vision|conference on language modeling|"
    r"operating systems design|operating systems principles|networked systems design|"
    r"architectural support for programming languages|computer architecture|"
    r"programming language design|principles of programming languages|"
    r"proceedings of the acm on programming languages|software engineering|"
    r"machine learning research|very large data bases|management of data|"
    r"knowledge discovery and data mining|research and development in information retrieval|"
    r"computer and communications security|usenix (annual technical|security)|"
    r"symposium on security and privacy|"
    r"file and storage technologies|principles of distributed computing|"
    r"transactions on computer systems|innovative data systems research|"
    r"internet measurement conference|emerging networking experiments|"
    r"machine learning and systems|"
    r"high performance computing, networking, storage|"
    r"principles and practice of parallel programming|"
    r"dependable systems and networks|"
    r"international joint conference on artificial|"
    # AI / agents. AAMAS is filed under its non-official name in OpenAlex.
    r"adaptive agents and multi|autonomous agents and multiagent|"
    r"automated planning and scheduling|conference on robot learning|"
    r"robotics: science and systems|robotics and automation|"
    r"artificial intelligence and statistics|conference on learning theory|"
    r"uncertainty in artificial intelligence|"
    r"pattern analysis and machine intelligence|"
    r"acm web conference|the web conference|"
    r"neurips|iclr|icml|acl|emnlp|naacl|cvpr|iccv|eccv|aaai|ijcai|colm|tmlr|jmlr|"
    r"aamas|icaps|corl|aistats|uai|tpami|"
    r"osdi|sosp|nsdi|sigcomm|eurosys|mlsys|asplos|isca|micro|hpca|socc|"
    r"podc|cidr|conext|ppopp|"
    r"vldb|sigmod|icde|kdd|sigir|pldi|popl|oopsla|icse|ndss)\b",
    re.I,
)
PREPRINT_VENUES = re.compile(
    r"^(arxiv|corr|preprint|openreview|ssrn|biorxiv|research square|)"
    r"(\.org|\.net| \(cornell university\))?$",
    re.I,
)


def get(url, tries=3, raw=False):
    delay = 2.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-search/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read() if raw else json.loads(r.read())
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt == tries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def oa(params):
    return get(f"{OPENALEX}?" + urllib.parse.urlencode({**params, "mailto": MAILTO}))


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
    return max(0.5, ((today or date.today()) - d).days / 30.44)


def invert_abstract(inv):
    if not inv:
        return ""
    return " ".join(w for _, w in sorted(
        (pos, w) for w, ps in inv.items() for pos in ps))


def from_openalex(w):
    d = parse_date(w.get("publication_date"))
    venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    doi = ((w.get("ids") or {}).get("doi") or "").replace("https://doi.org/", "") or None
    arxiv = None
    for loc in w.get("locations") or []:
        m = re.search(r"arxiv\.org/abs/([\d.]+)", loc.get("landing_page_url") or "")
        if m:
            arxiv = m.group(1)
    cites = w.get("cited_by_count") or 0
    age = months_since(d)
    is_pre = w.get("type") == "preprint" or PREPRINT_VENUES.match(venue.strip())
    auth = (w.get("authorships") or [])[:4]
    return {
        "title": w.get("title") or w.get("display_name") or "",
        "date": d.isoformat() if d else None,
        "age_mo": round(age, 1) if age else None,
        "cites": cites,
        "velocity": round(cites / age, 1) if age else None,
        "venue": venue or "arXiv",
        "tier": "PREPRINT" if is_pre else ("TOP" if TOP_NAME.search(venue) else "PEER"),
        "authors": [(a.get("author") or {}).get("display_name") for a in auth],
        "author_ids": [((a.get("author") or {}).get("id") or "").rsplit("/", 1)[-1]
                       for a in auth if (a.get("author") or {}).get("id")],
        # Free (already in the payload) and, unlike h-index, immune to name conflation.
        # For a paper too new to be cited, the lab is the most honest prior available.
        "affil": list(dict.fromkeys(
            i.get("display_name") for a in auth
            for i in (a.get("institutions") or []) if i.get("display_name")))[:4],
        "h_max": 0,  # filled in by enrich_authors()
        "arxiv": arxiv,
        "doi": doi,
        "abstract": invert_abstract(w.get("abstract_inverted_index"))[:280],
        "topic": ((w.get("primary_topic") or {}).get("display_name") or ""),
        "topics": [t.get("display_name") for t in (w.get("topics") or [])
                   if t.get("display_name")],
        "keywords": [k.get("display_name") for k in (w.get("keywords") or [])
                     if k.get("display_name") and (k.get("score") or 0) >= 0.5][:5],
        "categories": [],
        "query_hits": [],
        "best_query_rank": 10**9,
        "pdf": (w.get("best_oa_location") or {}).get("pdf_url") or "",
        "fwci": w.get("fwci"),
        "pctile": (w.get("citation_normalized_percentile") or {}).get("value"),
        "retracted": bool(w.get("is_retracted")),
    }


def from_arxiv(entry, ns):
    def txt(tag):
        el = entry.find(f"a:{tag}", ns)
        return (el.text or "").strip() if el is not None else ""

    aid = txt("id").rsplit("/", 1)[-1]
    d = parse_date(txt("published")[:10])
    age = months_since(d)
    return {
        "title": re.sub(r"\s+", " ", txt("title")),
        "date": d.isoformat() if d else None,
        "age_mo": round(age, 1) if age else None,
        "cites": 0,
        "velocity": None,  # unknowable: too new to have been cited
        "venue": "arXiv",
        "tier": "PREPRINT",
        "authors": [(a.find("a:name", ns).text or "").strip()
                    for a in entry.findall("a:author", ns)][:4],
        "author_ids": [],
        "affil": [],  # arXiv's API does not expose affiliations
        "h_max": 0,
        "arxiv": re.sub(r"v\d+$", "", aid),
        "doi": None,
        "abstract": re.sub(r"\s+", " ", txt("summary"))[:280],
        "topic": "",
        "topics": [],
        "keywords": [],
        "categories": [c.get("term") for c in entry.findall("a:category", ns)
                       if c.get("term")],
        "query_hits": [],
        "best_query_rank": 10**9,
        "pdf": f"https://arxiv.org/pdf/{aid}",
        "fwci": None,
        "pctile": None,
        "retracted": False,
    }


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #


def search(query, since=None, min_cites=None, field="cs", scope_filters=None):
    # The `search` param, NOT `title_and_abstract.search` — the latter is a strict AND
    # match that drops the landmark paper on any query longer than a few words.
    filters = ["type:article|preprint"]
    if field == "cs":
        filters.append(CS_FIELD)
    if since:
        filters.append(f"from_publication_date:{since if len(since) > 4 else since + '-01-01'}")
    if min_cites:
        filters.append(f"cited_by_count:>{min_cites - 1}")
    filters += scope_filters or []
    r = oa({"search": query, "filter": ",".join(filters),
            "per-page": 50, "select": WORK_FIELDS})
    out = [from_openalex(w) for w in r.get("results") or []]
    for rank_no, paper in enumerate(out, 1):
        paper["query_hits"] = [query]
        paper["best_query_rank"] = rank_no
    return out


def resolve_entities(endpoint, values, prefix, aliases=None):
    """Resolve user-facing names to stable OpenAlex IDs, preferring exact matches."""
    resolved = []
    aliases = aliases or {}
    for value in values or []:
        value = value.strip()
        if re.fullmatch(fr"{prefix}\d+", value, re.I):
            resolved.append((value.upper(), value))
            continue
        lookup = aliases.get(value.lower(), value)
        r = get(f"{endpoint}?" + urllib.parse.urlencode({
            "search": lookup, "per-page": 10, "select": "id,display_name", "mailto": MAILTO
        }))
        candidates = r.get("results") or []
        if not candidates:
            raise ValueError(f"no OpenAlex match for {value!r}")
        exact = [x for x in candidates if norm_title(x.get("display_name")) == norm_title(lookup)]
        match = (exact or candidates)[0]
        resolved.append((match["id"].rsplit("/", 1)[-1], match.get("display_name") or value))
    return resolved


def scope_filters(institutions=None, institution_type=None, venues=None, topics=None):
    filters = []
    resolved = {"institutions": [], "institution_type": institution_type,
                "venues": [], "topics": []}
    if institutions:
        resolved["institutions"] = resolve_entities(INSTITUTIONS, institutions, "I")
        filters.append("authorships.institutions.lineage:" +
                       "|".join(i for i, _ in resolved["institutions"]))
    if institution_type:
        filters.append(f"authorships.institutions.type:{institution_type}")
    if venues:
        resolved["venues"] = resolve_entities(SOURCES, venues, "S", VENUE_ALIASES)
        filters.append("primary_location.source.id:" +
                       "|".join(i for i, _ in resolved["venues"]))
    if topics:
        resolved["topics"] = resolve_entities(TOPICS, topics, "T")
        filters.append("topics.id:" + "|".join(i for i, _ in resolved["topics"]))
    return filters, resolved


def resolve(seed):
    """seed (arXiv:2307.03172 | DOI:10.x | 10.x | Wxxx) -> OpenAlex work ids.

    Returns BOTH the preprint and published records when they exist: OpenAlex keeps them
    as separate works (Lost-in-the-Middle has 972 citations on the TACL record and 61 on
    the arXiv one) and citers point at either, so using one loses half the frontier.
    """
    s = seed.strip()
    if re.fullmatch(r"W\d+", s):
        return [s]
    if s.lower().startswith("arxiv:"):
        doi = f"10.48550/arXiv.{s.split(':', 1)[1]}"
    elif s.lower().startswith("doi:"):
        doi = s.split(":", 1)[1]
    elif s.startswith("10."):
        doi = s
    else:
        return []
    try:
        w = get(f"{OPENALEX}/doi:{doi}?"
                + urllib.parse.urlencode({"select": "id,title", "mailto": MAILTO}))
    except Exception:
        return []
    ids, title = [w["id"].rsplit("/", 1)[-1]], w.get("title") or ""
    if not title:
        return ids
    try:
        twins = oa({"filter": f"title.search:{title}", "select": "id,title"})
    except Exception:
        return ids
    for t in twins.get("results") or []:
        wid = t["id"].rsplit("/", 1)[-1]
        if norm_title(t.get("title")) == norm_title(title) and wid not in ids:
            ids.append(wid)
    return ids


def citing(seed, since=None, field="cs", scope_filters=None):
    """Top-cited papers that CITE the seed — the frontier that built on a landmark.

    Sorting server-side is the whole game: a landmark has thousands of citers and the
    few that matter are not the ones the API hands back first.
    (`cites:W1|W2` is silently WRONG in the API — it returns unrelated papers. One call
    per id.)
    """
    out = []
    for wid in resolve(seed):
        filters = [f"cites:{wid}"]
        if field == "cs":
            filters.append(CS_FIELD)
        if since:
            filters.append(
                f"from_publication_date:{since if len(since) > 4 else since + '-01-01'}")
        filters += scope_filters or []
        try:
            r = oa({"filter": ",".join(filters), "sort": "cited_by_count:desc",
                    "per-page": 50, "select": WORK_FIELDS})
            out += [from_openalex(w) for w in r.get("results") or []]
        except Exception:
            continue
    return out


def arxiv_query(query, categories=None):
    terms = [t for t in re.findall(r"[a-z0-9][a-z0-9+.-]*", query.lower())
             if t not in STOP and len(t) > 2]
    q = " AND ".join(f"all:{t}" for t in terms)
    if categories:
        cats = " OR ".join(f"cat:{c}" for c in categories)
        q = f"({q}) AND ({cats})" if q else f"({cats})"
    return q


def search_arxiv(query, days, categories=None):
    """Last-N-days preprints. These are invisible to any citation-based ranking."""
    q = arxiv_query(query, categories)
    raw = get(f"{ARXIV}?" + urllib.parse.urlencode({
        "search_query": q, "sortBy": "submittedDate",
        "sortOrder": "descending", "max_results": 60}), raw=True)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    cutoff = date.today() - timedelta(days=days)
    out = []
    for rank_no, e in enumerate(ET.fromstring(raw).findall("a:entry", ns), 1):
        p = from_arxiv(e, ns)
        p["query_hits"] = [query]
        p["best_query_rank"] = rank_no
        d = parse_date(p["date"])
        if d and d >= cutoff:
            out.append(p)
    return out


def enrich_authors(papers, cap=150):
    """Author h-index. Only papers whose bucket depends on it need this — the young ones
    (FRESH+ vs FRESH?) and the uncited preprints (THIN). Skip the rest, save the calls."""
    need = [p for p in papers if not p["h_max"] and p["author_ids"]
            and ((p["age_mo"] or 99) < 6 or (p["velocity"] or 0) < 0.5)]
    ids = list(dict.fromkeys(i for p in need for i in p["author_ids"]))[:cap]
    if not ids:
        return
    h = {}
    for i in range(0, len(ids), 50):
        try:
            r = get(f"{AUTHORS}?" + urllib.parse.urlencode({
                "filter": "openalex_id:" + "|".join(ids[i : i + 50]),
                "select": "id,summary_stats", "per-page": 50, "mailto": MAILTO}))
            for a in r.get("results") or []:
                h[a["id"].rsplit("/", 1)[-1]] = (a.get("summary_stats") or {}).get(
                    "h_index") or 0
        except Exception:
            return  # best-effort
    for p in need:
        p["h_max"] = max((h.get(i, 0) for i in p["author_ids"]), default=0)


# --------------------------------------------------------------------------- #
# scoring
# --------------------------------------------------------------------------- #


def verdict(p, median_velocity):
    """Bucket a paper. Deliberately NOT one score — recency and quality are independent
    axes, and collapsing them hides exactly the tradeoff that matters in a fast field."""
    if p["retracted"]:
        return "RETRACTED"
    age, vel = p["age_mo"], p["velocity"]

    # Too new to have citations. Judge on priors only, and say so.
    if age is not None and age < 4 and p["cites"] < 5:
        return "FRESH+" if (p["tier"] == "TOP" or p["h_max"] >= 30) else "FRESH?"

    # FWCI is only meaningful once a paper has aged: the expected-citation denominator
    # for the current year is tiny, so a 5-month-old paper with 7 citations scores
    # FWCI 108 — louder than a real landmark. Below ~18 months, let velocity and venue
    # carry it instead.
    fw = p["fwci"] if (age is not None and age >= 18) else None

    strong = (fw is not None and fw >= 2) or (
        fw is None and vel is not None and vel >= max(1.0, 2 * median_velocity))
    # A landmark is cited fast in absolute terms AND not contradicted by the
    # field-normalized score. Velocity leads; FWCI confirms.
    vel_ok = vel is not None and vel >= max(5.0, 5 * median_velocity)

    if vel_ok and (fw is None or fw >= 20) and p["cites"] >= 50:
        return "LANDMARK"
    if strong and p["tier"] in ("TOP", "PEER"):
        return "STRONG"
    if age is not None and age <= 15 and strong:
        return "RISING"
    if p["tier"] == "PREPRINT" and (vel or 0) < 0.5 and p["h_max"] < 15:
        return "THIN"  # preprint nobody cites, by authors with no track record
    return "OK"


ORDER = {"LANDMARK": 0, "STRONG": 1, "RISING": 2, "FRESH+": 3,
         "OK": 4, "FRESH?": 5, "THIN": 6, "RETRACTED": 7}

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

STOP = {"the", "a", "an", "of", "in", "on", "for", "to", "and", "or", "with", "how",
        "what", "why", "is", "are", "be", "using", "via", "from", "at", "by", "that",
        "this", "it", "as", "can", "do", "does", "about", "find", "recent", "research",
        "paper", "papers", "study", "studies", "work"}


def relevance(papers, query, floor=0.6):
    """OpenAlex ranks loosely and a famous paper is cited by every field. Require the
    result to actually contain the query's content words before scoring its quality."""
    terms = {w for w in re.findall(r"[a-z0-9]+", query.lower())
             if w not in STOP and len(w) > 2}
    if not terms:
        return papers
    phrase = query.lower().strip('"')
    required = (len(terms) if len(terms) <= 2 else
                max(2, int(len(terms) * floor + 0.999)))
    out = []
    for p in papers:
        literal = f"{p['title']} {p['abstract']}".lower()
        hay = f"{literal} {' '.join(p.get('topics', []))} " \
              f"{' '.join(p.get('keywords', []))}".lower()
        literal_hits = sum(1 for t in terms if t[:-1] in literal or t in literal)
        hits = sum(1 for t in terms if t[:-1] in hay or t in hay)
        if phrase in literal or (literal_hits and hits >= required):
            out.append(p)
    return out


def dedupe(papers):
    """A paper exists as an arXiv preprint AND a published record, with separate citation
    counts. Merge them, and keep the EARLIEST date: preprints lead venues by 6-18 months
    and in a fast field that lead is the whole story."""
    best = {}
    for p in papers:
        k = norm_title(p["title"])[:80]
        cur = best.get(k)
        if not cur:
            best[k] = p
            continue
        keep, other = (cur, p) if (cur["cites"], cur["tier"] == "TOP") >= (
            p["cites"], p["tier"] == "TOP") else (p, cur)
        for f in ("fwci", "pctile", "abstract", "doi", "arxiv", "pdf", "author_ids",
                  "affil", "topic"):
            if not keep.get(f) and other.get(f):
                keep[f] = other[f]
        for f in ("topics", "keywords", "categories", "query_hits"):
            keep[f] = list(dict.fromkeys((keep.get(f) or []) + (other.get(f) or [])))
        keep["best_query_rank"] = min(keep.get("best_query_rank", 10**9),
                                      other.get("best_query_rank", 10**9))
        keep["cites"] = max(keep["cites"], other["cites"])
        keep["h_max"] = max(keep["h_max"], other["h_max"])
        keep["retracted"] = keep["retracted"] or other["retracted"]
        if keep["tier"] != "TOP" and other["tier"] == "TOP":
            keep["tier"], keep["venue"] = other["tier"], other["venue"]
        for d in (keep["date"], other["date"]):
            if d and (not keep.get("first_posted") or d < keep["first_posted"]):
                keep["first_posted"] = d
        if keep.get("first_posted") and keep["first_posted"] != keep["date"]:
            age = months_since(parse_date(keep["first_posted"]))
            keep["age_mo"] = round(age, 1) if age else keep["age_mo"]
            if keep["age_mo"]:
                keep["velocity"] = round(keep["cites"] / keep["age_mo"], 1)
        best[k] = keep
    return list(best.values())


def rank(papers):
    vels = sorted(p["velocity"] for p in papers if p["velocity"] is not None)
    median = vels[len(vels) // 2] if vels else 0.0
    for p in papers:
        p["verdict"] = verdict(p, median)
    papers.sort(key=lambda p: (ORDER[p["verdict"]], -len(p.get("query_hits") or []),
                               p.get("best_query_rank", 10**9), -(p["fwci"] or 0),
                               -(p["velocity"] or 0), -p["cites"]))
    return papers, median


def render(papers, median, query):
    if not papers:
        print("no results (try --field any, a shorter query, or --fresh N)")
        return
    print(f"\n{len(papers)} papers for: {query}")
    print(f"(median velocity in this result set: {median:.1f} cites/mo)\n")
    last = None
    for p in papers:
        if p["verdict"] != last:
            last = p["verdict"]
            print(f"── {last}  ({NOTE[last]})")
        age = f"{p['age_mo']:.0f}mo" if p["age_mo"] else "?"
        fp = p.get("first_posted")
        if fp and fp != p["date"]:
            age += f", preprint {fp[:7]}"
        fw = f"fwci {p['fwci']:.1f}" if p["fwci"] else "fwci —"
        vel = f"{p['velocity']:.1f}/mo" if p["velocity"] is not None else "—"
        auth = ", ".join(a for a in p["authors"][:2] if a) + (
            "…" if len(p["authors"]) > 2 else "")
        who = f"{auth}  h={p['h_max'] or '?'}"
        if p.get("affil"):
            who += "  @ " + ", ".join(p["affil"])
        print(f"  {p['title'][:88]}")
        print(f"    {p['date']}  ({age})  {p['cites']} cites ({vel})  {fw}"
              f"  [{p['tier']}] {p['venue'][:34]}")
        print(f"    {who}")
        labels = (([p["topic"]] if p.get("topic") else p.get("categories") or []) +
                  (p.get("keywords") or [])[:3])
        if labels:
            print("    # " + " · ".join(dict.fromkeys(labels)))
        if len(p.get("query_hits") or []) > 1:
            print(f"    matched {len(p['query_hits'])} query variants")
        if p["abstract"]:
            print(f"    → {p['abstract'][:150]}")
        print(f"    {'https://arxiv.org/abs/' + p['arxiv'] if p['arxiv'] else p['pdf'] or ''}\n")


# --------------------------------------------------------------------------- #


def selftest():
    base = dict(retracted=False, tier="TOP", h_max=40, fwci=None, cites=0,
                age_mo=None, velocity=None)
    cases = [
        # brand new + credible = FRESH+, never THIN
        ({**base, "age_mo": 1.0, "velocity": 0.0}, "FRESH+"),
        # brand new + no track record = FRESH?, explicitly not trusted
        ({**base, "age_mo": 1.0, "velocity": 0.0, "tier": "PREPRINT", "h_max": 2},
         "FRESH?"),
        # old, huge field-normalized impact
        ({**base, "age_mo": 36, "cites": 972, "velocity": 26.9, "fwci": 264.0},
         "LANDMARK"),
        # young paper with a wildly inflated FWCI (7 cites in 5mo => fwci 108, because
        # the current-year denominator is ~0). Must NOT outrank a real landmark.
        ({**base, "age_mo": 5, "cites": 7, "velocity": 1.5, "fwci": 108.9,
          "tier": "PEER"}, "OK"),
        # well-cited applications paper: high FWCI, but not cited fast in absolute terms
        ({**base, "age_mo": 18, "cites": 69, "velocity": 3.8, "fwci": 96.6,
          "tier": "PEER"}, "STRONG"),
        # uncited preprint by unknowns
        ({**base, "age_mo": 20, "cites": 1, "velocity": 0.05, "tier": "PREPRINT",
          "h_max": 3}, "THIN"),
        # systems paper: low raw citations, but FWCI says it beats its own field
        ({**base, "age_mo": 30, "cites": 90, "velocity": 3.0, "fwci": 4.0}, "STRONG"),
    ]
    fails = 0
    for p, want in cases:
        got = verdict(p, median_velocity=1.0)
        fails += got != want
        print(f"{'ok  ' if got == want else 'FAIL'} want={want:9s} got={got}")
    for venue, want in [
        ("Transactions of the Association for Computational Linguistics", "TOP"),
        ("Conference on Neural Information Processing Systems", "TOP"),
        ("arXiv", "PREPRINT"), ("arXiv.org", "PREPRINT"),
        ("arXiv (Cornell University)", "PREPRINT"),  # OpenAlex writes it this way
        ("npj Digital Medicine", "PEER"),
    ]:
        w = {"primary_location": {"source": {"display_name": venue}}, "type": "article"}
        got = from_openalex(w)["tier"]
        fails += got != want
        if got != want:
            print(f"FAIL tier({venue!r}) want={want} got={got}")
    p = from_openalex({"title": "Generic storage capacity survey"})
    assert relevance([p], "computational storage") == []
    p["topics"] = ["Computational Storage Systems"]
    assert relevance([p], "computational storage") == [p]
    assert arxiv_query("papers about agent runtime", ["cs.AI", "cs.OS"]) == (
        "(all:agent AND all:runtime) AND (cat:cs.AI OR cat:cs.OS)")
    p1 = from_openalex({"title": "One paper", "cited_by_count": 1})
    p2 = from_openalex({"title": "One paper", "cited_by_count": 2})
    p1["query_hits"], p1["best_query_rank"] = ["agent runtime"], 4
    p2["query_hits"], p2["best_query_rank"] = ["AI agent systems"], 2
    merged = dedupe([p1, p2])[0]
    assert merged["query_hits"] == ["AI agent systems", "agent runtime"]
    assert merged["best_query_rank"] == 2
    assert VENUE_ALIASES["fast"] == "File and Storage Technologies"
    filters, _ = scope_filters(["I1"], "company", ["S2"], ["T3"])
    assert filters == ["authorships.institutions.lineage:I1",
                       "authorships.institutions.type:company",
                       "primary_location.source.id:S2", "topics.id:T3"]
    assert (months_since(date(2026, 1, 13), date(2026, 7, 13)) or 0) > 5.9
    print("FAILED" if fails else "all pass")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("query", nargs="?", help="topic, e.g. 'lost in the middle long context'")
    ap.add_argument("-q", "--query", dest="query_variants", action="append", default=[],
                    help="additional query variant; repeat to improve recall")
    ap.add_argument("--since", help="YYYY-MM-DD or YYYY — only papers after this")
    ap.add_argument("--fresh", type=int, metavar="DAYS",
                    help="also pull arXiv preprints from the last N days")
    ap.add_argument("--after", metavar="ID",
                    help="papers CITING this seed (arXiv:2307.03172, DOI:..., Wxxx)")
    ap.add_argument("--about", metavar="TEXT",
                    help="keep only --after results matching these words (a landmark is "
                         "cited by every field; this keeps the frontier on topic)")
    ap.add_argument("--min-cites", type=int)
    ap.add_argument("--field", default="cs", choices=["cs", "any"],
                    help="restrict to Computer Science (default) or search all fields")
    ap.add_argument("--institution", action="append", default=[], metavar="NAME_OR_ID",
                    help="works affiliated with this institution or its descendants; repeatable")
    ap.add_argument("--institution-type", metavar="TYPE",
                    help="affiliated institution type, e.g. company or education")
    ap.add_argument("--venue", action="append", default=[], metavar="NAME_OR_ID",
                    help="publication venue; accepts aliases such as FAST, OSDI, and NeurIPS")
    ap.add_argument("--topic", action="append", default=[], metavar="NAME_OR_ID",
                    help="OpenAlex topic; use a displayed topic name or T-number")
    ap.add_argument("--category", action="append", default=[], metavar="ARXIV_CATEGORY",
                    help="arXiv category for --fresh, e.g. cs.OS or cs.AI; repeatable")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="offline; no network")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    queries = ([a.query] if a.query else []) + a.query_variants
    if not (queries or a.after):
        ap.error("need a query or --after")

    filters, resolved = scope_filters(a.institution, a.institution_type, a.venue, a.topic)
    for kind in ("institutions", "venues", "topics"):
        entities = resolved[kind]
        for entity_id, name in entities:
            print(f"{kind[:-1]}: {name} ({entity_id})", file=sys.stderr)
    if a.institution_type:
        print(f"institution type: {a.institution_type}", file=sys.stderr)
    if a.fresh and filters:
        print("warning: skipping arXiv --fresh results because arXiv cannot enforce "
              "the requested OpenAlex scope filters", file=sys.stderr)
    papers = []
    if a.after:
        papers += citing(a.after, a.since, a.field, filters)
    for query in queries:
        hits = search(query, a.since, a.min_cites, a.field, filters)
        papers += relevance(hits, query)
        if a.fresh and not filters:
            papers += relevance(search_arxiv(query, a.fresh, a.category), query)

    if a.about:
        papers = relevance(papers, a.about, floor=0.34)
    papers = dedupe(papers)
    enrich_authors(papers)  # must precede rank(): the buckets use h-index
    papers, median = rank(papers)

    if a.fresh:
        # Fresh papers can never win a citation-based ranking — that is the whole point
        # of asking for them. Reserve slots instead of letting --limit bury them.
        fresh = [p for p in papers if p["verdict"].startswith("FRESH")]
        papers = ([p for p in papers if not p["verdict"].startswith("FRESH")][: a.limit]
                  + fresh[: a.limit])
    else:
        papers = papers[: a.limit]

    if a.json:
        print(json.dumps({"query": queries or a.after, "scope": resolved,
                          "median_velocity": median,
                          "papers": papers}, indent=2))
    else:
        render(papers, median, " | ".join(queries) if queries else a.after)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as e:
        sys.exit(f"OpenAlex/arXiv HTTP {e.code}: {e.reason}")
    except ValueError as e:
        sys.exit(str(e))
    except KeyboardInterrupt:
        sys.exit(130)
