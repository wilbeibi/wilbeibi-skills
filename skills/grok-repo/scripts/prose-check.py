#!/usr/bin/env python3
"""prose-check.py [--lines] <briefing.md>

Advisory readability check for a human-facing repo briefing. Measures the body
(text before the first `---` rule) against bands taken from a briefing that
readers found easy: short labelled bullets, short sentences, no code clutter.
Prints the offenders, not just counts. Always exits 0; the bands are advice.
Two bands are stricter than the reference text on purpose: it has two sentences
over 30 words and long openers on a quarter of its bullets; past 30 words a
reader loses the subject, and an opener is a label, not a thesis.

--lines  one bullet per line, no list markers (the first line is the provenance paragraph).
Stdlib only.
"""
import re
import statistics
import sys

BANDS = {
    "body words": (None, 1200),
    "bullets": (15, 25),
    "words per bullet, median": (40, 60),
    "words per bullet, max": (None, 95),
    "words per sentence, mean": (13, 17),
    "sentences over 30 words": (None, 0),
    "code tokens per 100 words": (None, 1.0),
    "path:line citations": (None, 0),
    "evidence tags [code]/[doc]/...": (None, 0),
    "citations per bullet, mean": (None, 1.0),
    "openers over 10 words, % of bullets": (None, 33),
}
CITE = re.compile(r"\(([^()]*?(?:\.md|\.rs|\.py|\.go|\.toml|#\d+|Appendix)[^()]*)\)")
PATHLINE = re.compile(r"[\w./-]+\.\w+:\d+(?:-\d+)?")
TAG = re.compile(r"\*\*\[(?:code|doc|hist|infer)\]\*\*")


MARK = re.compile(r"^(- |\* |\d+\. )")


def units(text, line_mode):
    """Yield (text, is_bullet). A bullet starts with a list marker or a bold opener;
    anything else (the provenance paragraph, a closing paragraph) is prose and is
    measured for sentences but exempt from the opener and bullet-length bands."""
    out, cur = [], []

    def flush():
        if cur:
            u = " ".join(cur)
            out.append((MARK.sub("", u).strip(), bool(MARK.match(u)) or u.startswith("**")))
            cur.clear()

    for ln in text.split("\n"):
        if ln.startswith("#") or not ln.strip():
            flush()
            continue
        if line_mode or MARK.match(ln):
            flush()
            cur.append(ln.strip())
        else:
            cur.append(ln.strip())
    flush()
    kept = [(u, b) for u, b in out if len(u.split()) >= 12]
    if line_mode:  # one line per bullet, no markers: only the opening provenance line is prose
        kept = [(u, i > 0) for i, (u, _) in enumerate(kept)]
    return kept


def split_opener(unit):
    m = re.match(r"\*\*(.+?)\*\*\s*(.*)", unit, re.S)
    if m:
        return m.group(1).rstrip(".:"), m.group(2)
    first, _, rest = unit.partition(". ")
    return first, rest


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+(?![a-z)])", text) if s.strip()]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    line_mode = "--lines" in sys.argv
    if len(args) != 1:
        sys.exit(__doc__)
    text = open(args[0], encoding="utf-8").read()
    cut = text.find("\n---\n")
    body = text if cut < 0 else text[:cut]
    all_units = units(body, line_mode)
    us = [u for u, b in all_units if b]
    if not all_units:
        sys.exit("no bullets or paragraphs of 12+ words found")
    if not us:
        sys.exit("no bullets found (a bullet starts with '- ', '1. ' or a bold opener)")
    total = sum(len(u.split()) for u, _ in all_units)
    words = [len(u.split()) for u in us]
    sents, long_sents, long_openers, long_units = [], [], [], []
    for u, is_bullet in all_units:
        opener, rest = split_opener(u) if is_bullet else ("", u)
        if len(opener.split()) > 10:
            long_openers.append(opener)
        if is_bullet and len(u.split()) > BANDS["words per bullet, max"][1]:
            long_units.append(u)
        for s in sentences(rest):
            sents.append(len(s.split()))
            if len(s.split()) > 30:
                long_sents.append(s)
    cites = sum(len(CITE.findall(u)) for u in us)
    pathlines = [m.group(0) for u, _ in all_units for m in PATHLINE.finditer(u)]
    tags = sum(len(TAG.findall(u)) for u, _ in all_units)
    values = {
        "body words": total,
        "bullets": len(us),
        "words per bullet, median": statistics.median(words),
        "words per bullet, max": max(words),
        "words per sentence, mean": round(statistics.mean(sents), 1) if sents else 0,
        "sentences over 30 words": len(long_sents),
        "code tokens per 100 words": round(100 * sum(u.count("`") // 2 for u, _ in all_units) / total, 1),
        "path:line citations": len(pathlines),
        "evidence tags [code]/[doc]/...": tags,
        "citations per bullet, mean": round(cites / len(us), 2),
        "openers over 10 words, % of bullets": round(100 * len(long_openers) / len(us)),
    }
    print(f"{args[0]}  (body before first ---; {len(all_units) - len(us)} prose paragraphs measured for sentences only)")
    for key, (lo, hi) in BANDS.items():
        v = values[key]
        flag = "" if (lo is None or v >= lo) and (hi is None or v <= hi) else "  <-- outside band"
        band = f"{lo or ''}-{hi if hi is not None else ''}".strip("-") or ""
        print(f"  {key:36s} {v:>8}   band {band:>8}{flag}")

    def show(title, items, width=140):
        if items:
            print(f"\n{title}:")
            for it in items:
                print(f"  - {it[:width]}{'...' if len(it) > width else ''}")

    show("sentences over 30 words", long_sents)
    show("bullets over the max (two mechanisms? split or move one to notes)", long_units)
    show("openers over 10 words (label it, then explain)", long_openers)
    show("path:line citations (belong in the agent's notes, not the briefing)", sorted(set(pathlines)))
    print("\nBands are advisory. Sentence splitting is heuristic: a sentence that starts lowercase"
          " (btrfs, zstd, a flag) is joined to the one before it, so check a flagged long sentence by eye.")


if __name__ == "__main__":
    main()
