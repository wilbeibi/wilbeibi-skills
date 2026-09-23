#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Run TLC and report results, coverage, and vacuity signals; check that a mutant is killed.

  tlc.py fetch                              download tla2tools.jar into the cache
  tlc.py translate Spec.tla                 translate PlusCal in place (pcal.trans)
  tlc.py check Spec.tla [-c Model.cfg]      model-check; print summary, trace, dead actions
  tlc.py mutant Spec.tla -c Model.cfg --replace OLD NEW --expect Mutex|deadlock|<Property>

Exit: 0 clean (check) or killed (mutant); 1 violation (check) or survived (mutant);
2 vacuity or ambiguous result; 3 setup, parse, or TLC error.
"""
import argparse
import functools
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

JAR_URL = "https://github.com/tlaplus/tlaplus/releases/latest/download/tla2tools.jar"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "tla-model"
MSG = re.compile(r"@!@!@STARTMSG (\d+):(\d) @!@!@\n(.*?)@!@!@ENDMSG \1 @!@!@", re.S)
COVER = re.compile(r"^<(\w+) line (\d+).*?>: (\d+):(\d+)$")
STATS = re.compile(r"([\d,]+) states generated, ([\d,]+) distinct states found, ([\d,]+) states left")
DEPTH = re.compile(r"depth of the complete state graph search is (\d+)")
# Tested with TLC 2.19 (-tool message codes). Exit codes 11/12/13/150 observed; 10 from TLC docs.
# Messages are parsed first; exit codes are the fallback.
EXIT_KIND = {10: "assumption", 11: "deadlock", 12: "safety", 13: "liveness", 150: "parse"}


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(3)


@functools.cache
def java_bin():
    # Run each candidate: macOS ships /usr/bin/java as a stub that exists but fails without a JRE.
    for cand in (os.environ.get("JAVA"),
                 os.environ.get("JAVA_HOME") and str(Path(os.environ["JAVA_HOME"]) / "bin" / "java"),
                 shutil.which("java")):
        if cand and Path(cand).exists() and subprocess.run([cand, "-version"], capture_output=True).returncode == 0:
            return cand
    die("java not found: install a JRE 11+ (Arch: jre-openjdk-headless; macOS: brew install openjdk, "
        "which is keg-only, so also set JAVA=/opt/homebrew/opt/openjdk/bin/java) or set JAVA / JAVA_HOME")


def jar_path():
    env = os.environ.get("TLA2TOOLS_JAR")
    if env:
        if not Path(env).is_file():
            die(f"TLA2TOOLS_JAR={env} does not exist")
        return env
    cached = CACHE / "tla2tools.jar"
    if cached.is_file():
        return str(cached)
    die(f"tla2tools.jar not found: run `{sys.argv[0]} fetch` or set TLA2TOOLS_JAR")


def fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = CACHE / "tla2tools.jar.part"
    with urllib.request.urlopen(JAR_URL, timeout=60) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    tmp.replace(CACHE / "tla2tools.jar")
    print(CACHE / "tla2tools.jar")


def translate(spec):
    spec = Path(spec).resolve()
    proc = subprocess.run([java_bin(), "-cp", jar_path(), "pcal.trans", "-nocfg", spec.name],
                          cwd=spec.parent, capture_output=True, text=True)
    print((proc.stdout + proc.stderr).strip())
    sys.exit(0 if proc.returncode == 0 else 3)


def cfg_properties(cfg):
    """Names listed under PROPERTY/PROPERTIES in a TLC config (for attributing temporal failures)."""
    text = re.sub(r"\\\*.*", "", Path(cfg).read_text())
    text = re.sub(r"\(\*.*?\*\)", "", text, flags=re.S)
    keywords = r"(SPECIFICATION|INIT|NEXT|CONSTANTS?|INVARIANTS?|PROPERTY|PROPERTIES|CONSTRAINTS?|" \
               r"ACTION_CONSTRAINTS?|SYMMETRY|VIEW|CHECK_DEADLOCK|POSTCONDITION|ALIAS)\b"
    props, current = [], None
    for tok in re.split(r"\s+", text):
        if not tok:
            continue
        if re.fullmatch(keywords, tok):
            current = tok
        elif current in ("PROPERTY", "PROPERTIES"):
            props.append(tok)
    return props


def run_tlc(spec, cfg, workers, extra):
    spec = Path(spec).resolve()
    cfg = Path(cfg).resolve() if cfg else spec.with_suffix(".cfg")
    if not cfg.is_file():
        die(f"config not found: {cfg}")
    with tempfile.TemporaryDirectory(prefix="tlc-meta-") as meta:
        cmd = [java_bin(), "-XX:+UseParallelGC", "-cp", jar_path(), "tlc2.TLC", "-tool",
               "-coverage", "1", "-workers", workers, "-metadir", meta,
               "-config", str(cfg), *extra, spec.name]
        proc = subprocess.run(cmd, cwd=spec.parent, capture_output=True, text=True)
    return parse(proc.stdout + proc.stderr, proc.returncode), cfg


def parse(out, code):
    msgs = [(int(c), int(sev), body.strip()) for c, sev, body in MSG.findall(out)]
    r = {"exit": code, "kind": None, "violated": None, "errors": [], "trace": [],
         "coverage": [], "generated": None, "distinct": None, "left": None, "depth": None}
    for c, sev, body in msgs:
        if c == 2772:  # per-action coverage: <Action line N ...>: distinct:total
            m = COVER.match(body)
            if m:
                r["coverage"].append((m[1], int(m[2]), int(m[3]), int(m[4])))
        elif c in (2217, 2218):
            r["trace"].append(body)
        elif c in (2199, 2200):
            m = STATS.search(body)
            if m:
                r["generated"], r["distinct"], r["left"] = (int(x.replace(",", "")) for x in m.groups())
        elif c == 2194:
            m = DEPTH.search(body)
            r["depth"] = int(m[1]) if m else None
        elif sev == 1:
            r["errors"].append(body)
            m = re.match(r"(?:Invariant|Action property) (\S+) is violated", body)
            if m:
                r["kind"], r["violated"] = "safety", m[1]
            elif body.startswith("Deadlock reached"):
                r["kind"] = "deadlock"
            elif body.startswith("Temporal properties were violated"):
                r["kind"] = "liveness"
    if r["kind"] is None and code:
        r["kind"] = EXIT_KIND.get(code, "error")
        if code == 150 or not r["errors"]:  # SANY parse errors print outside tool messages
            r["errors"].append("\n".join(l for l in out.splitlines()
                                         if l and not l.startswith(("@!@!@", "Parsing file", "Semantic processing")))[-3000:])
    return r


def summarize(r, cfg, min_distinct):
    status = r["kind"] or "clean"
    target = f" ({r['violated']})" if r["violated"] else ""
    print(f"result: {status}{target}   cfg: {cfg.name}   exit: {r['exit']}")
    if r["distinct"] is not None:
        print(f"states: {r['generated']} generated, {r['distinct']} distinct, {r['left']} left on queue"
              + (f", depth {r['depth']}" if r["depth"] is not None else ""))
    if r["coverage"]:
        print("coverage (action: new distinct / times fired):")
        for name, _, d, t in r["coverage"]:
            print(f"  {name:<24} {d}:{t}" + ("   <- NEVER FIRED" if t == 0 else ""))
    for e in r["errors"]:
        print("error: " + e)
    if r["trace"]:
        print(f"trace ({len(r['trace'])} states):")
        for s in r["trace"]:
            print(s)
    flags = []
    if r["kind"] is None:
        dead = [n for n, _, _, t in r["coverage"] if t == 0]
        if dead:
            flags.append(f"actions never fired: {', '.join(dead)}")
        if r["distinct"] is not None and r["distinct"] < min_distinct:
            flags.append(f"only {r['distinct']} distinct states (< --min-distinct {min_distinct})")
        if r["left"]:
            flags.append(f"{r['left']} states left on queue: search did not finish")
        if not r["coverage"] and r["distinct"] is not None:
            flags.append("no action coverage reported")
    for f in flags:
        print("VACUITY: " + f)
    if r["kind"] == "liveness":
        print("note: TLC does not name the violated temporal property; use a cfg with one PROPERTY to attribute it.")
    return flags


def check(a):
    r, cfg = run_tlc(a.spec, a.config, a.workers, a.tlc_args)
    flags = summarize(r, cfg, a.min_distinct)
    if r["kind"] in ("safety", "deadlock", "liveness", "assumption"):
        sys.exit(1)
    if r["kind"]:
        sys.exit(3)
    sys.exit(2 if flags else 0)


def mutant(a):
    src = Path(a.spec).resolve()
    text = src.read_text()
    n = text.count(a.old)
    if n != 1:
        die(f"--replace OLD must match exactly once in {src.name}; matched {n} times")
    cfg = Path(a.config).resolve()
    with tempfile.TemporaryDirectory(prefix="tla-mutant-") as tmp:
        work = Path(tmp) / "m"
        work.mkdir()
        for f in [*src.parent.glob("*.tla"), *src.parent.glob("*.cfg")]:  # all TLC needs; avoid copying a repo
            shutil.copy2(f, work)
        (work / src.name).write_text(text.replace(a.old, a.new))
        wcfg = work / cfg.relative_to(src.parent) if cfg.is_relative_to(src.parent) else cfg
        r, _ = run_tlc(work / src.name, wcfg, a.workers, a.tlc_args)
    exp = a.expect
    print(f"mutant: {a.old!r} -> {a.new!r}   expect: {exp}")
    print(f"TLC: {r['kind'] or 'clean'}" + (f" ({r['violated']})" if r["violated"] else ""))
    if r["kind"] in ("parse", "error"):
        print("MUTANT INVALID: mutant does not parse or TLC errored; pick a mutation that stays well-formed")
        for e in r["errors"]:
            print("error: " + e)
        sys.exit(3)
    if r["kind"] == "safety" and r["violated"] == exp:
        verdict = "KILLED"
    elif r["kind"] == "deadlock" and exp == "deadlock":
        verdict = "KILLED"
    elif r["kind"] == "liveness":
        props = cfg_properties(cfg)
        if props == [exp]:
            verdict = "KILLED"
        elif exp in props:
            print(f"AMBIGUOUS: temporal violation, but {cfg.name} checks {props}; TLC cannot say which failed")
            sys.exit(2)
        else:
            verdict = "SURVIVED"
    else:
        verdict = "SURVIVED"
    if verdict == "SURVIVED" and r["kind"]:
        print(f"note: mutant failed a different check than {exp}; the targeted property did not catch it")
    if r["trace"] and a.trace:
        print("\n".join(r["trace"]))
    print(verdict)
    sys.exit(0 if verdict == "KILLED" else 1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="download tla2tools.jar into $XDG_CACHE_HOME/tla-model")
    sub.add_parser("translate", help="translate a PlusCal algorithm to TLA+ in place").add_argument("spec")
    for name in ("check", "mutant"):
        s = sub.add_parser(name)
        s.add_argument("spec")
        s.add_argument("-c", "--config", required=(name == "mutant"))
        s.add_argument("--workers", default="auto")
        s.add_argument("--tlc-args", nargs=argparse.REMAINDER, default=[],
                       help="remaining args go to TLC verbatim, e.g. --tlc-args -simulate num=1000 -depth 50")
    sub.choices["check"].add_argument("--min-distinct", type=int, default=2,
                                      help="flag vacuity below this many distinct states (default 2)")
    m = sub.choices["mutant"]
    m.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"), required=True)
    m.add_argument("--expect", required=True, help="invariant/action-property name, temporal property name, or 'deadlock'")
    m.add_argument("--trace", action="store_true", help="print the killing trace")
    a = p.parse_args()
    if a.cmd == "fetch":
        return fetch()
    if a.cmd == "translate":
        return translate(a.spec)
    if a.cmd == "mutant":
        a.old, a.new = a.replace
        return mutant(a)
    return check(a)


if __name__ == "__main__":
    main()
