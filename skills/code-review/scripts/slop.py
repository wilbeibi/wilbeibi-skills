#!/usr/bin/env python3
"""Sloppiness probe for a change: clone, complexity, and slop-rule findings
restricted to touched lines, plus base-vs-head metrics for the changed files.

    slop.py [BASE] [--scope DIR] [--all]

Compares the working tree against BASE (default: HEAD). Output is file:line
leads for the reviewer; a lead is not a finding until it names the tangle.

Backends: scb-check (SlopCodeBench's tool) for the languages it parses, lizard
for the rest (Go, Java, C#, ...). Lizard's clone detector is weaker and its
verbosity counts only clones, so its numbers are comparable to a repo's own
history, not to scb-check's.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCB = ["uvx", "scb-check", "check"]
SCB_EXT = {".py", ".rs", ".js", ".jsx", ".ts", ".tsx", ".zig", ".hs",
           ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h"}
LIZARD_LANG = {".go": "go", ".java": "java", ".c": "cpp", ".cs": "csharp",
               ".swift": "swift", ".kt": "kotlin", ".rb": "ruby", ".php": "php",
               ".scala": "scala", ".lua": "lua", ".m": "objectivec"}
# Used only when the repo has no scb-check config of its own; minified vendor
# bundles make clone detection run for minutes.
DEFAULT_EXCLUDE = ["**/vendor/**", "**/third_party/**", "**/*.min.js", "**/*.min.css"]
HEADER = re.compile(r"^([A-Za-z_-]+)(?:\[([\w-]+)\])?: (.+)$")
LOC = re.compile(r"^\s*┌─ (.+?):(\d+)(?::\d+)?\s*$")
METRIC = re.compile(r"^\s*= (.+)$")
LIZ_FUNC = re.compile(r"^\s*(\d+)\s+(\d+)\s+\d+\s+\d+\s+\d+\s+(\S+?)@(\d+)-(\d+)@(.+)$")
LIZ_DUP = re.compile(r"^(.+?):(\d+) ~ (\d+)$")
CC_THRESHOLD = 10
CONFIG = []  # temp scb-check config path, set once in main


def die(msg):
    print(f"slop.py: {msg}", file=sys.stderr)
    sys.exit(1)


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode:
        die(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def strip_prefix(text, tmp):
    for prefix in (os.path.realpath(tmp), tmp):
        text = text.replace(prefix + os.sep, "")
    return text


# --- scb-check backend -------------------------------------------------------

def default_config(root):
    """Path to a temp scb-check.toml, or None if the repo configures scb-check."""
    if os.path.exists(os.path.join(root, "scb-check.toml")):
        return None
    try:
        with open(os.path.join(root, "pyproject.toml")) as f:
            if "[tool.scb-check]" in f.read():
                return None
    except OSError:
        pass
    path = os.path.join(tempfile.mkdtemp(prefix="slop-cfg-"), "scb-check.toml")
    with open(path, "w") as f:
        f.write("exclude = " + json.dumps(DEFAULT_EXCLUDE) + "\n")
    return path


def scb(path, as_json=False):
    cmd = SCB + [path] + (["--output-format", "json"] if as_json else [])
    if CONFIG and CONFIG[0]:
        cmd += ["--config", CONFIG[0]]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode and not r.stdout.strip():
        tail = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else f"exit {r.returncode}"
        # Last line only: rich tracebacks quote this message as source context.
        if "no supported source files" in tail:
            return {} if as_json else ""
        raise RuntimeError(f"scb-check on {path}: {tail}")
    return json.loads(r.stdout) if as_json else r.stdout


def parse_scb(text):
    """Yield (kind, rule, msg, [(path, line)...], metric_str)."""
    cur = None
    for line in text.splitlines():
        m = HEADER.match(line)
        if m and not line.startswith(" "):
            if cur:
                yield cur
            cur = [m.group(1), m.group(2), m.group(3), [], ""]
            continue
        if not cur:
            continue
        m = LOC.match(line)
        if m:
            cur[3].append((os.path.normpath(m.group(1)), int(m.group(2))))
            continue
        m = METRIC.match(line)
        if m:
            cur[4] = m.group(1).split(" (threshold")[0]
    if cur:
        yield cur


def scb_metrics(files, base):
    with Materialized(files, base) as tmp:
        try:
            return scb(tmp, as_json=True)
        except RuntimeError as e:
            die(str(e))


def scb_findings(files, scope):
    try:
        return list(parse_scb(scb(scope)))
    except RuntimeError as e:
        # scb-check aborts the whole scan on one unparsable file; degrade to the
        # changed files so the reviewer still gets leads, minus cross-repo clones.
        print(f"full scb-check scan failed ({e}); its findings cover changed files"
              " only, clones against unchanged code are not detected")
    with Materialized(files, None) as tmp:
        try:
            return list(parse_scb(strip_prefix(scb(tmp), tmp)))
        except RuntimeError as e:
            die(str(e))


# --- lizard backend ----------------------------------------------------------

def lizard(path, files):
    """Parsed lizard run over `path`, languages taken from `files`' extensions."""
    cmd = ["uvx", "lizard", "-Eduplicate"]
    for lang in sorted({LIZARD_LANG[os.path.splitext(f)[1]] for f in files}):
        cmd += ["-l", lang]
    for pat in DEFAULT_EXCLUDE:
        cmd += ["-x", pat.replace("**/", "*/")]
    r = subprocess.run(cmd + [path], capture_output=True, text=True)
    if r.returncode and not r.stdout.strip():
        tail = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else f"exit {r.returncode}"
        die(f"lizard on {path}: {tail}")
    return parse_lizard(r.stdout)


def parse_lizard(text):
    """Return (functions, clone_groups): functions as (file, name, start, end,
    cc, nloc); clone_groups as lists of (file, start, end)."""
    funcs, groups, cur = {}, [], None
    for line in text.splitlines():
        m = LIZ_FUNC.match(line)
        if m:  # over-threshold functions are listed again in a warnings section
            nloc, cc, name, start, end, path = m.groups()
            key = (os.path.normpath(path), int(start))
            funcs[key] = (key[0], name, key[1], int(end), int(cc), int(nloc))
            continue
        if line.startswith("Duplicate block:"):
            cur = []
            groups.append(cur)
            continue
        m = LIZ_DUP.match(line)
        if m and cur is not None:
            cur.append((os.path.normpath(m.group(1)), int(m.group(2)), int(m.group(3))))
    return list(funcs.values()), [g for g in groups if g]


def lizard_metrics(files, base):
    with Materialized(files, base) as tmp:
        funcs, groups = lizard(tmp, files)
    if not funcs:
        return {}
    mass = [(cc, cc * math.sqrt(nloc)) for _, _, _, _, cc, nloc in funcs]
    total = sum(m for _, m in mass)
    clone_lines = {(f, i) for g in groups for f, a, b in g for i in range(a, b + 1)}
    total_loc = sum(nloc for *_, nloc in funcs)
    return {
        "files_scanned": len({f for f, *_ in funcs}),
        "total_loc": total_loc,
        "high_cc_functions": sum(1 for cc, _ in mass if cc > CC_THRESHOLD),
        "clone_loc": len(clone_lines),
        "verbosity_flagged_loc": len(clone_lines),
        "erosion": sum(m for cc, m in mass if cc > CC_THRESHOLD) / total if total else 0,
        "verbosity": len(clone_lines) / total_loc if total_loc else 0,
    }


def lizard_findings(files, scope):
    funcs, groups = lizard(scope, files)
    out = []
    for path, name, start, end, cc, nloc in funcs:
        if cc > CC_THRESHOLD:
            out.append(("erosion", None, f"function `{name}` exceeds complexity threshold",
                        [(path, start)], f"complexity: {cc}, sloc: {nloc}"))
    for g in groups:
        n = g[0][2] - g[0][1] + 1
        out.append(("duplicate-structure", None,
                    f"duplicated block ({n} lines, {len(g)} instances)",
                    [(f, a) for f, a, _ in g], ""))
    return out


# --- shared ------------------------------------------------------------------

class Materialized:
    """Temp dir holding `files` from `base` (git archive) or the working tree."""

    def __init__(self, files, base):
        self.files, self.base = files, base

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="slop-")
        if self.base is not None:
            existing = git("ls-tree", "-r", "--name-only", self.base, "--", *self.files).split()
            if existing:
                tar = subprocess.run(["git", "archive", self.base, "--", *existing],
                                     capture_output=True)
                subprocess.run(["tar", "-x", "-C", self.tmp], input=tar.stdout, check=True)
            return self.tmp
        for f in self.files:
            try:
                os.makedirs(os.path.dirname(os.path.join(self.tmp, f)) or self.tmp, exist_ok=True)
                shutil.copy(f, os.path.join(self.tmp, f))
            except FileNotFoundError:
                continue  # deleted in the working tree
        return self.tmp

    def __exit__(self, *exc):
        shutil.rmtree(self.tmp, ignore_errors=True)


def touched_ranges(base):
    """{path: [(start, end), ...]} of head-side line ranges the diff touches."""
    out = {}
    path = None
    for line in git("diff", "--no-prefix", "-U0", base, "--", ".").splitlines():
        if line.startswith("+++ "):
            path = None if line == "+++ /dev/null" else line[4:]
        elif line.startswith("@@") and path:
            hunk = line.split("+", 1)[1].split()[0]
            start, _, n = hunk.partition(",")
            start, n = int(start), int(n) if n else 1
            out.setdefault(path, []).append((start, max(start, start + n - 1)))
    for path in git("ls-files", "--others", "--exclude-standard").split("\n"):
        if path:
            out[path] = [(1, 1 << 30)]
    return out


def span(kind, msg, metric, line):
    """Head-side line range a finding covers, for overlap with the diff."""
    if kind in ("erosion", "cog_erosion"):
        m = re.search(r"sloc: (\d+)", metric)
    else:
        m = re.search(r"\((\d+) lines", msg)
    n = int(m.group(1)) if m else 1
    return line, line + n - 1


def overlaps(a, ranges):
    return any(s <= a[1] and a[0] <= e for s, e in ranges)


def parse_args(argv):
    base, scope, show_all = "HEAD", ".", False
    args = iter(argv)
    for a in args:
        if a == "--scope":
            scope = next(args, None) or die("--scope needs a DIR")
        elif a == "--all":
            show_all = True
        elif a.startswith("-"):
            die(f"unknown flag {a}")
        else:
            base = a
    return base, scope, show_all


def format_hits(findings, ranges, show_all):
    """(lines to print, count hidden). A finding is kept if any of its
    locations overlaps a touched range; the anchor is the touched one."""
    hits, skipped = [], 0
    for kind, rule, msg, locs, metric in findings:
        in_diff = [(p, l) for p, l in locs
                   if p in ranges and overlaps(span(kind, msg, metric, l), ranges[p])]
        if not in_diff and not show_all:
            skipped += 1
            continue
        anchor = in_diff[0] if in_diff else locs[0]
        others = [f"{p}:{l}" for p, l in locs if (p, l) != anchor]
        tag = f"{kind}[{rule}]" if rule else kind
        parts = [f"  {anchor[0]}:{anchor[1]} {tag}: {msg}"]
        if metric:
            parts.append(f"[{metric}]")
        if others:
            parts.append("also at " + ", ".join(others[:3]))
        hits.append(" ".join(parts))
    return hits, skipped


def line_delta(base, ranges):
    numstat = git("diff", "--numstat", base, "--", ".").splitlines()
    added = sum(int(l.split()[0]) for l in numstat if l.split()[0].isdigit())
    deleted = sum(int(l.split()[1]) for l in numstat if l.split()[1].isdigit())
    for f, r in ranges.items():
        if r == [(1, 1 << 30)]:  # untracked: numstat does not see it
            try:
                with open(f, "rb") as fh:
                    added += sum(1 for _ in fh)
            except OSError:
                pass
    return added, deleted


def print_metrics(label, b, h):
    if not h.get("files_scanned"):
        return
    print(f"changed files ({label}), base -> head:")
    for name, key in (("functions CC>10", "high_cc_functions"),
                      ("clone loc", "clone_loc"),
                      ("flagged loc", "verbosity_flagged_loc"),
                      ("total loc", "total_loc")):
        print(f"  {name}: {b.get(key, 0)} -> {h.get(key, 0)}")
    print(f"  erosion: {b.get('erosion', 0):.2f} -> {h['erosion']:.2f}"
          f"   verbosity: {b.get('verbosity', 0):.2f} -> {h['verbosity']:.2f}")


def main(argv):
    base, scope, show_all = parse_args(argv)
    if not shutil.which("uvx"):
        die("uvx not found (scb-check and lizard run via uvx)")
    root = git("rev-parse", "--show-toplevel").strip()
    os.chdir(root)
    CONFIG.append(default_config(root))

    ranges = touched_ranges(base)
    files = sorted(ranges)
    if not files:
        print(f"no changes vs {base}")
        return
    added, deleted = line_delta(base, ranges)
    print(f"diff vs {base}: {len(files)} files, +{added} -{deleted}")

    backends = []
    scb_files = [f for f in files if os.path.splitext(f)[1] in SCB_EXT]
    liz_files = [f for f in files if os.path.splitext(f)[1] in LIZARD_LANG]
    if scb_files:
        backends.append(("scb-check", scb_files, scb_metrics, scb_findings))
    if liz_files:
        backends.append(("lizard", liz_files, lizard_metrics, lizard_findings))
    if not backends:
        print("changed files: none in a language either backend scans")
        return
    findings = []
    for label, subset, metrics, find in backends:
        print_metrics(label, metrics(subset, base), metrics(subset, None))
        findings += find(subset, scope)

    hits, skipped = format_hits(findings, ranges, show_all)
    print(f"findings on touched lines ({scope}): {len(hits)}"
          + (f", {skipped} elsewhere hidden (--all)" if skipped else ""))
    for line in hits:
        print(line)
    print("leads only: a finding must name the tangle or divergence, not the number")


if __name__ == "__main__":
    main(sys.argv[1:])
