#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML>=6.0.2", "requests>=2.31"]
# ///
"""Build, check and narrate a self-contained HTML lesson (one .html, optionally one .mp3 beside it).

    lesson.py init DIR --title T [--lang zh|en]   scaffold a lesson directory (--gallery: the pattern gallery)
    lesson.py build DIR                           assemble DIR/out/<slug>.html from the parts + assets/player.html
    lesson.py check DIR                           build, then static checks and a headless-browser pass over every beat
    lesson.py thread DIR                          how each scene opens against what came before + DIR/thread/ pages for a cold read
    lesson.py shots DIR [BEATS|waits]             screenshots (default: last beat of every scene) + contact sheets
    lesson.py numbers DIR                         every numeral shown must be in source.txt or numbers.allow
    lesson.py say DIR [WHICH]                     print what the voice will say, and what it will cost; no API call
    lesson.py synth DIR all|changed|1,5,9         per-beat TTS clips into DIR/clips (beat numbers as the player shows them)
    lesson.py mix DIR                             clips -> out/<slug>-narration.mp3, measured timings, rebuild
    lesson.py video DIR [BEATS]                   film the lesson into one out/<slug>.mp4 (pauses become short holds)

A lesson directory holds lesson.json, outline.md (brief + scene map), scenes.html, script.js, data.js, hooks.js,
optional style.css, speak.yaml (spoken layer), optional source.txt and numbers.allow. script.js is the only place
subtitle text lives.
Exit 0 clean, 1 a check failed or a tool is missing, 2 usage or malformed lesson.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "player.html"
PARTS = ("scenes.html", "script.js", "data.js", "hooks.js")
MAX_UNITS = 92  # two subtitle lines: CJK/fullwidth = 1, ASCII = 0.5
RATE = 32000
BROWSERS = (
    "chromium", "chromium-browser", "google-chrome", "google-chrome-stable",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)
BEATS_JS = """
const fs = require('fs');
const W = t => ({t, wait: true});
// data.js is pure (no DOM), so beats may interpolate its values: `ROIC is ${V.roic}`
const SCRIPT = new Function('W', fs.readFileSync(process.argv[1], 'utf8') + '\\n' + fs.readFileSync(process.argv[2], 'utf8') + '\\nreturn SCRIPT;')(W);
process.stdout.write(JSON.stringify(SCRIPT.map(c => ({ch: c.ch, scenes: c.scenes.map(([id, lines]) =>
  [id, lines.map(l => typeof l === 'string' ? {t: l, wait: false} : {t: l.t, wait: !!l.wait})])}))));
"""
VALUES_JS = """
const V = new Function(require('fs').readFileSync(process.argv[1], 'utf8') + '\\nreturn typeof V === "undefined" ? {} : V;')();
process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(V).map(([k, v]) => [k, String(v)]))));
"""


class Fail(Exception):
    """A problem the author has to fix; printed without a traceback."""


def die(msg: str, code: int = 2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        die(f"{tool} not found on PATH (see compatibility in SKILL.md)", 1)
    return path


def units(text: str) -> float:
    return sum(0.5 if ord(c) < 128 else 1 for c in text)


# ---------- how the Mandarin voice is told to read figures ----------
# Each rule and each warning below is a misreading heard on minimax/speech-2.8-turbo, voice Chinese (Mandarin)_Radio_Host,
# on 2026-10-12. Plain figures ($894,813, 98.71%, 0.037, 28,426) were read correctly and are left alone.

ZH = "零一二三四五六七八九"
MAGNITUDE = {"million": 6, "billion": 9, "trillion": 12}
LATIN = "A-Za-z0-9_"   # \w and \b also take CJK characters for word characters, and beats run figures into CJK text


def zh_number(n: int) -> str:
    """A whole number as a Mandarin speaker says it: 26500 -> 两万六千五百, 1_800_000_000 -> 十八亿."""
    def section(n: int) -> str:   # 1..9999
        out, gap = "", False
        for unit, name in ((1000, "千"), (100, "百"), (10, "十"), (1, "")):
            d, n = divmod(n, unit)
            if d:
                out += ("零" if gap and out else "") + ("两" if d == 2 and name == "千" else ZH[d]) + name
            gap = not d
        return out

    out, gap = "", False
    for unit, name in ((10 ** 8, "亿"), (10 ** 4, "万"), (1, "")):
        q, n = divmod(n, unit)
        if q:
            part = "两" if q == 2 and name else zh_number(q) if q > 9999 else section(q)
            out += ("零" if out and (gap or q < 1000) else "") + part + name
        gap = not q
    return re.sub("^一十", "十", out) or "零"


def read_zh(text: str) -> str:
    """speak.yaml `rules: zh`: rewrite the four classes the voice misreads into words it reads correctly."""   # each class was heard misread; see authoring.md
    def amount(m):   # $32.5 billion -> 三百二十五亿美元, 180 million -> 一亿八千万
        value = Decimal(m.group(2).replace(",", "")) * 10 ** MAGNITUDE[m.group(3).lower()]
        if value != value.to_integral_value():
            return m.group(0)
        return zh_number(int(value)) + ("美元" if m.group(1) else "")

    def times(m):    # 1.5x -> 一点五倍
        whole, _, frac = m.group(1).partition(".")
        return ("两" if m.group(1) == "2" else zh_number(int(whole)) + ("点" + "".join(ZH[int(d)] for d in frac) if frac else "")) + "倍"

    text = re.sub(r"(\d)\s+年", r"\1年", text)                                     # "2020 年" is read as a cardinal
    text = re.sub(rf"([{LATIN}%)])\s*−\s*(?=\$?\d)", r"\1减", text)                # − (U+2212) is not read at all: 900 − 247
    text = re.sub(r"−(?=\s*\$?\d)", "负", text)                                   # and −5%
    text = re.sub(rf"(?<![{LATIN}.])(\$?)(\d[\d,]*(?:\.\d+)?)\s*(million|billion|trillion)(?![A-Za-z])", amount, text, flags=re.I)
    return re.sub(rf"(?<![{LATIN}.])(\d+(?:\.\d+)?)x(?![{LATIN}])", times, text)


SPEECH = (   # (pattern over the spoken text, what the voice does with it and what to write instead)
    (r"\d[\d.,]*\s*(?:million|billion|trillion)(?![A-Za-z])",
     "the English magnitude word is read as English (\"265 美元 billion\"): set `rules: zh`, or write the Chinese amount in a `say` pair"),
    (r"\d{4}\s+年", "a space before 年 turns the year into a cardinal: set `rules: zh`, or add the pair [\" 年\", \"年\"]"),
    (r"−", "the voice does not read − (U+2212): write 负 or 减 for it in a `say` pair (`rules: zh` covers − before a figure)"),
    (rf"(?<![{LATIN}.%)])-(?=\s*\$?[\d零一二两三四五六七八九十])",
     "a hyphen before a figure was never tried on the voice: write − for a negative number, 到 for a range, or listen to the beat"),
    (rf"\d(?:\.\d+)?x(?![{LATIN}])", "\"1.5x\" is read \"1.5 X\": set `rules: zh`, or write 一点五倍 in a `say` pair"),
    (r"&", "the voice skips &: spell the name in a `say` pair (AT&T -> A T and T)"),
)


def span(at: list[int]) -> str:
    return str(at[0]) if len(at) == 1 else f"{at[0]}-{at[-1]}" if at[-1] - at[0] == len(at) - 1 else ",".join(map(str, at))


def speech_warnings(lesson: "Lesson") -> list[str]:
    """Spoken lines holding something the Mandarin voice is known to misread. Chinese lessons with a speak.yaml only."""
    if lesson.meta["lang"] != "zh" or not (lesson.dir / "speak.yaml").exists():
        return []
    spoken = [re.sub(r"<#[\d.]+#>", "", lesson.spoken(b["t"])) for b in lesson.beats]
    out = []
    for pattern, what in SPEECH:
        hits = [(i + 1, m.group(0)) for i, text in enumerate(spoken) for m in [re.search(pattern, text, flags=re.I)] if m]
        if hits:
            out.append(f"speech, beat {span([i for i, _ in hits])}: \"{hits[0][1]}\": {what}")
    return out


# ---------- lesson model ----------

class Lesson:
    def __init__(self, directory: str):
        self.dir = Path(directory).resolve()
        meta_path = self.dir / "lesson.json"
        if not meta_path.exists():
            die(f"{meta_path} not found: run `lesson.py init {directory} --title ...` first")
        try:
            self.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            die(f"{meta_path}: {exc}")
        for key in ("title", "slug", "lang"):
            if not isinstance(self.meta.get(key), str) or not self.meta[key]:
                die(f"{meta_path}: \"{key}\" must be a non-empty string")
        if self.meta["lang"] not in ("zh", "en"):
            die(f"{meta_path}: lang must be \"zh\" or \"en\"")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", self.meta["slug"]):
            die(f"{meta_path}: slug must be lowercase kebab-case")
        missing = [p for p in PARTS if not (self.dir / p).exists()]
        if missing:
            die(f"{self.dir}: missing {', '.join(missing)}")
        self.slug = self.meta["slug"]
        self.out = self.dir / "out"
        self.html_path = self.out / f"{self.slug}.html"
        self.mp3_name = f"{self.slug}-narration.mp3"
        self.clips = self.dir / "clips"
        self._script = None
        self._speak = None

    def part(self, name: str) -> str:
        path = self.dir / name
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @property
    def script(self) -> list[dict]:
        if self._script is None:
            run = subprocess.run([need("node"), "-e", BEATS_JS, str(self.dir / "data.js"), str(self.dir / "script.js")],
                                 capture_output=True, text=True)
            if run.returncode:
                tail = [l for l in run.stderr.strip().splitlines() if l.strip()][-6:]
                die("data.js + script.js do not evaluate to `const SCRIPT = [{ch, scenes: [[id, [beats]]]}]` "
                    "(data.js must not touch the DOM):\n" + "\n".join(tail))
            self._script = json.loads(run.stdout)
        return self._script

    @property
    def beats(self) -> list[dict]:
        out = []
        for ci, chapter in enumerate(self.script):
            for scene, lines in chapter["scenes"]:
                for step, line in enumerate(lines):
                    out.append({"ch": ci, "scene": scene, "step": step, "t": line["t"], "wait": line["wait"]})
        return out

    @property
    def speak(self) -> dict:
        if self._speak is None:
            import yaml
            path = self.dir / "speak.yaml"
            if not path.exists():
                die(f"{path} not found: copy assets/starter/speak.yaml and set model and voice")
            self._speak = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for key in ("model", "voice"):
                if not self._speak.get(key):
                    die(f"{path}: \"{key}\" is required")
            if self._speak.get("rules", "none") not in ("none", "zh"):
                die(f"{path}: rules must be \"zh\" or \"none\"")
        return self._speak

    def spoken(self, text: str) -> str:
        cfg = self.speak
        for phrase in cfg.get("pause_after") or []:
            text = text.replace(phrase, phrase + cfg.get("pause", ""))
        for pair in cfg.get("say") or []:
            text = text.replace(str(pair[0]), str(pair[1]))
        return read_zh(text) if cfg.get("rules") == "zh" else text   # after the pairs: what the author wrote by hand wins

    def rate(self, i: int) -> float:
        """Speech speed for 0-based beat i; speak.yaml keys its overrides by the 1-based number the player shows."""
        cfg = self.speak
        return float((cfg.get("speed") or {}).get(i + 1, cfg.get("speed_default", 1.0)))

    def sig(self, i: int, text: str) -> str:
        cfg = self.speak
        return f"{cfg['model']}|{cfg['voice']}|{self.rate(i)}\n{self.spoken(text)}"

    def narration(self) -> dict | None:
        """Timings written by `mix`, or None. Raises Fail when they no longer match script.js + speak.yaml."""
        path = self.dir / "narration.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        beats = self.beats
        now = hashlib.sha256("\x00".join(self.sig(i, b["t"]) for i, b in enumerate(beats)).encode()).hexdigest()
        if data.get("sig") != now or len(data.get("durations", [])) != len(beats):
            raise Fail("narration is stale (script.js or speak.yaml changed since the last mix): "
                       "run `synth DIR changed` then `mix DIR`, or build with --silent")
        return data


# ---------- build ----------

def build(lesson: Lesson, silent: bool = False, to: Path | None = None) -> Path:
    template = TEMPLATE.read_text(encoding="utf-8")
    parts = {name: lesson.part(name) for name in PARTS}
    for name, text in parts.items():
        if name.endswith(".js") and re.search(r"</script", text, re.I):
            die(f"{name}: contains '</script', which would end the page script early")
    narration = None if silent else lesson.narration()
    meta = {
        "lang": lesson.meta["lang"],
        "speed": lesson.meta.get("speed", 1),
        "audio": lesson.mp3_name if narration else None,
        "durations": [round(d, 1) for d in narration["durations"]] if narration else None,
    }
    fill = {
        "__LANG__": "zh-CN" if lesson.meta["lang"] == "zh" else "en",
        "__TITLE__": html.escape(lesson.meta["title"]),
        "/*__STYLE__*/": lesson.part("style.css"),
        "<!--__SCENES__-->": parts["scenes.html"],
        "/*__DATA__*/": parts["data.js"],
        "/*__SCRIPT__*/": parts["script.js"],
        "/*__HOOKS__*/": parts["hooks.js"],
    }
    marker = re.compile(r"/\*__META__\*/\{[^}]*\}|" + "|".join(re.escape(k) for k in fill))
    page = marker.sub(lambda m: fill.get(m.group(0), json.dumps(meta, ensure_ascii=False)), template)
    target = to or lesson.html_path
    target.parent.mkdir(exist_ok=True)
    target.write_text(page, encoding="utf-8")
    body = page[page.index("'use strict';"):page.index("</script>", page.index("'use strict';"))]
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(body)
    try:
        run = subprocess.run([need("node"), "--check", tmp.name], capture_output=True, text=True)
    finally:
        os.unlink(tmp.name)
    if run.returncode:
        msg = run.stderr.replace(tmp.name, "page script")
        raise Fail("the assembled page script does not parse (data.js + script.js + hooks.js share one scope with the player):\n"
                   + "\n".join(msg.strip().splitlines()[:8]))
    return target


@contextmanager
def preview(lesson: Lesson):
    """A silent build in a throwaway directory. `shots` and `numbers` read the page without sound, and writing that
    build to out/ would replace a narrated lesson with a silent one."""
    with tempfile.TemporaryDirectory(prefix="lesson-preview-") as tmp:
        yield build(lesson, silent=True, to=Path(tmp) / lesson.html_path.name)


# ---------- checks ----------

def visible_text(markup: str) -> str:
    markup = re.sub(r"<!--.*?-->|<style.*?</style>|<script.*?</script>", " ", markup, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", markup))


def scene_map(lesson: Lesson) -> dict[str, dict] | None:
    """The scene map in outline.md as {scene id: {"asks": its question, "after": what raises that question}}, or None
    when there is no outline. A row is any `id | question | ...` line whose first cell is a scene of this lesson; the
    columns are found by their headers ("question", "raised by"), and "after" is None when there is no such column.
    A cell still holding its TODO counts as empty."""
    text = lesson.part("outline.md")
    if not text.strip():
        return None
    ids = {scene for chapter in lesson.script for scene, _ in chapter["scenes"]}
    rows, asks, after = {}, 1, None
    for line in text.splitlines():
        cells = [c.strip().strip("`").strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) < 2:
            continue
        if cells[0] in ids:
            cell = lambda i: "" if i >= len(cells) or cells[i] in ("-", "—", "–") or cells[i].startswith("TODO") else cells[i]
            rows.setdefault(cells[0], {"asks": cell(asks), "after": None if after is None else cell(after)})
        elif cells[0].lower().startswith("scene"):
            heads = [c.lower() for c in cells]
            asks = next((i for i, h in enumerate(heads) if i and "question" in h), 1)
            after = next((i for i, h in enumerate(heads) if "raised" in h), None)
    return rows


def static_check(lesson: Lesson) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    markup = re.sub(r"<!--.*?-->", "", lesson.part("scenes.html"), flags=re.S)   # markup quoted in a comment is not markup
    sections = re.findall(r"<section\b([^>]*)>(.*?)</section>", markup, flags=re.S)
    scenes = {}
    for attrs, inner in sections:
        if not re.search(r'class="[^"]*\bscene\b', attrs):
            continue
        m = re.search(r'\bid="([^"]+)"', attrs)
        if not m:
            errors.append("a <section class=\"scene\"> has no id")
        elif m.group(1) in scenes:
            errors.append(f"scene id \"{m.group(1)}\" is defined twice in scenes.html")
        else:
            scenes[m.group(1)] = inner
    ids = re.findall(r'\sid="([^"]+)"', markup)
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"id \"{dup}\" appears {ids.count(dup)} times in scenes.html")

    script = lesson.script
    if not script:
        errors.append("SCRIPT has no chapters")
    used = []
    for ci, chapter in enumerate(script):
        name = chapter.get("ch")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"chapter {ci + 1} has no `ch` name")
        elif re.fullmatch(r"[\d\s.]+", name):
            errors.append(f"chapter name \"{name}\" is a bare number: the chapter buttons need words")
        for scene, lines in chapter["scenes"]:
            used.append(scene)
            if scene not in scenes:
                errors.append(f"SCRIPT names scene \"{scene}\" but scenes.html has no such <section class=\"scene\">")
                continue
            if not lines:
                errors.append(f"scene \"{scene}\" has no beats")
            marks = [int(n) for n in re.findall(r'data-(?:at|to)="(\d+)"', scenes[scene])]
            if marks and max(marks) >= len(lines):
                errors.append(f"scene \"{scene}\": data-at/data-to {max(marks)} but only {len(lines)} beats (steps are 0-based)")
    for scene in scenes:
        if used.count(scene) != 1:
            errors.append(f"scene \"{scene}\" is used {used.count(scene)} times in SCRIPT (each scene exactly once)")

    plan = scene_map(lesson)
    if plan is None:
        warns.append("outline.md is missing: the brief and the scene map are written before the script (references/authoring.md)")
    else:
        for what, lacking in (("has no scene-map row for", [s for s in used if s not in plan]),
                              ("gives no question for", [s for s in used if s in plan and not plan[s]["asks"]]),
                              ("does not say what raises the question of", [s for s in used[1:] if s in plan and plan[s]["after"] == ""])):
            if lacking:
                warns.append(f"outline.md {what}: {', '.join(lacking)}")
        if plan and all(row["after"] is None for row in plan.values()):
            warns.append("outline.md scene map has no `raised by` column: which earlier scene leaves the viewer asking each question?")

    beats = lesson.beats
    for i, b in enumerate(beats):
        if not b["t"].strip():
            errors.append(f"beat {i + 1} ({b['scene']}) is empty")
        elif units(b["t"]) > MAX_UNITS:
            errors.append(f"beat {i + 1} ({b['scene']}) is {units(b['t']):g} units, over {MAX_UNITS}: split it into two beats")
    waits = sum(b["wait"] for b in beats)
    want = 2 if len(beats) >= 40 else 1
    if waits < want:
        warns.append(f"{waits} wait beat(s) in {len(beats)} beats: a lesson this long wants at least {want} stop-and-predict or you-compute pauses")

    seen = visible_text(markup) + "\n" + "\n".join(b["t"] for b in beats) + "\n" + "\n".join(c["ch"] or "" for c in script)
    for word in ("TODO", "FIXME", "XXX", "lorem ipsum"):
        if word.lower() in seen.lower():
            errors.append(f"placeholder \"{word}\" is still in visible text")
    known = set(ids) | set(re.findall(r'\bid=\\?["\']([\w-]+)', lesson.part("hooks.js") + lesson.part("data.js")))
    for ref in sorted(set(re.findall(r"""(?:\$|getElementById)\(\s*['"]([^'"]+)['"]\s*\)""", lesson.part("hooks.js")))):
        if ref not in known and ref not in PLAYER_IDS:
            warns.append(f"hooks.js uses $('{ref}') but no element with that id is in scenes.html")
    return errors, warns


PLAYER_IDS = {"fit", "stage", "chip", "hint", "sub", "subt", "cover", "big", "covert", "coverk", "bar", "play", "prev",
              "next", "track", "fill", "time", "chs", "speed", "voice"}


def browser() -> str | None:
    for name in (os.environ.get("LESSON_BROWSER"), *BROWSERS):
        if name and (shutil.which(name) or Path(name).exists()):
            return shutil.which(name) or name
    return None


def chrome(args: list[str], url: str, timeout: int = 120) -> subprocess.CompletedProcess:
    exe = browser()
    with tempfile.TemporaryDirectory(prefix="lesson-chrome-") as profile:
        cmd = [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio", "--no-first-run",
               "--allow-file-access-from-files", f"--user-data-dir={profile}", "--window-size=1296,800",
               "--force-device-scale-factor=1", *args, url]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def browser_check(page: Path) -> dict:
    run = chrome(["--virtual-time-budget=4000", "--dump-dom"], page.as_uri() + "?check")
    m = re.search(r'<script type="application/json" id="lesson-report">(.*?)</script>', run.stdout, flags=re.S)
    if not m:
        raise Fail("the page produced no check report (browser exit %d): %s" % (run.returncode, run.stderr.strip()[-400:]))
    return json.loads(m.group(1))


def cmd_check(args) -> int:
    lesson = Lesson(args.dir)
    errors, warns = static_check(lesson)
    report = None
    if not args.silent:
        warns += speech_warnings(lesson)
    if errors:
        print("static checks failed; fix these before the build and browser pass:")
    else:
        build(lesson, silent=args.silent)
        if args.no_browser or not browser():
            warns.append("browser pass skipped (%s): layout, subtitle wrapping and hooks are NOT checked"
                         % ("--no-browser" if args.no_browser else "no Chromium/Chrome found; set LESSON_BROWSER"))
        else:
            report = browser_check(lesson.html_path)
            errors += [f"page error: {e}" for e in report.get("errors", [])]
            grouped: dict[tuple, list[int]] = {}   # one line per fault, not one per beat it shows on
            for issue in report.get("issues", []):
                grouped.setdefault((issue["level"], issue["scene"], issue["what"], issue["detail"]), []).append(issue["beat"])
            for (level, scene, what, detail), at in grouped.items():
                where = f"beat {span(at)} ({scene})" if at[0] else "page"
                (errors if level == "error" else warns).append(f"{where}: {what}: {detail}")
    for line in errors:
        print("FAIL", line)
    for line in warns:
        print("warn", line)
    beats = lesson.beats
    spoken = "narrated %d s" % report["seconds"] if report and report.get("narrated") else "silent"
    print(f"{len(lesson.script)} chapters, {len({b['scene'] for b in beats})} scenes, {len(beats)} beats, "
          f"{sum(b['wait'] for b in beats)} waits, {spoken} -> {lesson.html_path if not errors or report else '(not built)'}")
    print("CHECK FAILED: %d error(s)" % len(errors) if errors else "CHECK OK" + (" (with warnings)" if warns else ""))
    return 1 if errors else 0


def cmd_build(args) -> int:
    lesson = Lesson(args.dir)
    path = build(lesson, silent=args.silent)
    print(path)
    if (lesson.out / lesson.mp3_name).exists() and not args.silent and lesson.narration():
        print(lesson.out / lesson.mp3_name)
    return 0


def cmd_thread(args) -> int:
    """The script as its viewer meets it. Printed: each scene's opening beat under the beat before it and the question
    the scene map gives it, which is where a jump shows. Written: DIR/thread/, one page per scene (00 = the first
    screen), for a reader who says what they want to know before opening the next page (references/cold-read.md)."""
    lesson = Lesson(args.dir)
    plan = scene_map(lesson) or {}
    markup = re.sub(r"<!--.*?-->", "", lesson.part("scenes.html"), flags=re.S)
    # A heading as the viewer reads it: without its provenance tag, and with the values the player puts in data-v spans.
    markup = re.sub(r'<span\b[^>]*\bclass="[^"]*\btag\b[^"]*"[^>]*>.*?</span>', "", markup, flags=re.S)
    values = {}
    if "data-v=" in markup:
        run = subprocess.run([need("node"), "-e", VALUES_JS, str(lesson.dir / "data.js")], capture_output=True, text=True)
        values = json.loads(run.stdout) if run.returncode == 0 else {}
    markup = re.sub(r'<span\b[^>]*\bdata-v="([^"]+)"[^>]*>\s*</span>', lambda m: html.escape(str(values.get(m.group(1), "…"))), markup)
    heads = {}
    for attrs, inner in re.findall(r"<section\b([^>]*)>(.*?)</section>", markup, flags=re.S):
        sid, head = re.search(r'\bid="([^"]+)"', attrs), re.search(r"<h[12]\b[^>]*>(.*?)</h[12]>", inner, flags=re.S)
        if sid and head:
            heads[sid.group(1)] = " ".join(visible_text(head.group(1)).split())
    pages = lesson.dir / "thread"
    shutil.rmtree(pages, ignore_errors=True)
    pages.mkdir()
    (pages / "00.txt").write_text(f"{lesson.meta['title']}\nChapters: {' · '.join(c['ch'] for c in lesson.script)}\n", encoding="utf-8")
    n, page, last = 0, 0, None
    for chapter in lesson.script:
        print(f"\n== {chapter['ch']}")
        for k, (scene, lines) in enumerate(chapter["scenes"]):
            page += 1
            row = plan.get(scene, {})
            print(f"{scene}  page {page:02d}, beats {n + 1}-{n + len(lines)}")
            print(f"  asks  {row.get('asks') or '(no question in the scene map)'}" + (f"   <- {row['after'] or '(nothing raises it)'}" if row.get("after") is not None and (page > 1 or row["after"]) else ""))
            if last:
                print(f"  ...{n:<4d}{last}")
            print(f"  >  {n + 1:<4d}{lines[0]['t'] if lines else ''}")
            text = [f"Chapter: {chapter['ch']}"] if k == 0 else []
            text += [f"On screen: {heads[scene]}"] if scene in heads else []
            text += [f"{n + j + 1}  {'[the lesson stops here for the viewer to answer] ' if line['wait'] else ''}{line['t']}" for j, line in enumerate(lines)]
            (pages / f"{page:02d}.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
            n += len(lines)
            last = lines[-1]["t"] if lines else last
    print(f"\n{page} scenes -> {pages}/ (00 = the first screen, then one scene per page) for the cold read, references/cold-read.md")
    return 0


def parse_which(spec: str, count: int) -> list[int]:
    """1-based beat numbers as the player chip shows them -> 0-based indices."""
    out = []
    for piece in spec.split(","):
        lo, _, hi = piece.partition("-")
        try:
            a, b = int(lo), int(hi or lo)
        except ValueError:
            die(f"bad beat list \"{spec}\": use e.g. 3,7,12-15")
        if not 1 <= a <= b <= count:
            die(f"beat {piece} is outside 1..{count}")
        out += range(a - 1, b)
    return out


def cmd_shots(args) -> int:
    lesson = Lesson(args.dir)
    if not browser():
        die("no Chromium/Chrome found; set LESSON_BROWSER", 1)
    beats = lesson.beats
    if args.which == "waits":   # what the learner sees while guessing: the answer must not be readable yet
        picks = [i for i, b in enumerate(beats) if b["wait"]]
        if not picks:
            die("this lesson has no wait beats", 1)
    elif args.which:
        picks = parse_which(args.which, len(beats))
    else:  # the last beat of each scene shows the scene fully revealed
        picks = [i for i, b in enumerate(beats) if i + 1 == len(beats) or beats[i + 1]["scene"] != b["scene"]]
    shots = lesson.dir / "shots"
    shutil.rmtree(shots, ignore_errors=True)
    shots.mkdir()
    files = []
    with preview(lesson) as page:
        for i in picks:
            path = shots / f"{i + 1:03d}-{beats[i]['scene']}.png"
            chrome([f"--screenshot={path}", "--virtual-time-budget=1500"], page.as_uri() + f"?still&beat={i + 1}")
            if not path.exists():
                die(f"screenshot of beat {i + 1} failed", 1)
            files.append(path)
    print(f"{len(files)} screenshots in {shots}")
    if shutil.which("ffmpeg") and len(files) > 1:
        for n in range(0, len(files), 6):
            group = files[n:n + 6]
            sheet = shots / f"sheet-{n // 6 + 1:02d}.png"
            inputs = [x for f in group for x in ("-i", str(f))]
            rows = (len(group) + 1) // 2
            graph = "".join(f"[{k}:v]scale=960:-1[v{k}];" for k in range(len(group)))
            graph += "".join(f"[v{k}]" for k in range(len(group))) + f"xstack=inputs={len(group)}:layout=" + "|".join(
                f"{(k % 2) * 960}_{(k // 2) * 593}" for k in range(len(group))) + f":fill=black,scale=1920:{rows * 593}"
            if len(group) == 1:
                graph = "[0:v]scale=960:-1"
            subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-frames:v", "1", str(sheet)], check=True)
            print(sheet, "=", ", ".join(f.stem for f in group))
    return 0


# ---------- numbers ----------

NUM = r"(?<![\w.])[−-]?\$?\d[\d,]*(?:\.\d+)?%?"


def cmd_numbers(args) -> int:
    lesson = Lesson(args.dir)
    source = Path(args.source) if args.source else lesson.dir / "source.txt"
    if not source.exists():
        die(f"{source} not found: extract the source to text first (e.g. pdftotext -layout), or pass --source")
    text = source.read_text(encoding="utf-8", errors="replace")
    allow = {}
    allow_path = lesson.dir / "numbers.allow"
    if allow_path.exists():
        for line in allow_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, why = line.partition("\t")
                if not why.strip():
                    die(f"numbers.allow: \"{key}\" has no reason (format: number<TAB>where it comes from)")
                allow[key.strip()] = why.strip()
    # What the viewer can read is what gets checked: the built page reports every numeral it renders, beat by beat.
    # Without a browser only the typed text is scanned, and numbers placed by data-v or hooks.js go unseen.
    seen: dict[str, str] = {}
    errors, _ = static_check(lesson)
    if errors:
        die("static checks fail; run `check` first")
    if browser():
        with preview(lesson) as page:
            for n, at in browser_check(page).get("numbers", {}).items():
                seen[n] = f"beat {at['beat']} | {at['near']}"
    else:
        print("warn no Chromium/Chrome found: scanning typed text only; numbers rendered from data.js are NOT checked")
        shown = "\n".join([visible_text(lesson.part("scenes.html")), *(b["t"] for b in lesson.beats)])
        for m in re.finditer(NUM, shown, flags=re.ASCII):   # ASCII: 涨了5% must match, and 了 is a \w otherwise
            n = m.group(0).lstrip("−-$").rstrip("%").rstrip(",")
            if n:
                seen.setdefault(n, shown[max(0, m.start() - 24):m.start() + 24].replace("\n", " "))

    # Compared by value, so 0.9 on screen matches `.9` in code, 150,000 matches 150_000, and 1.0 matches 1.
    def value(n: str):
        try:
            return Decimal(n.replace(",", "").replace("_", "")).normalize()
        except InvalidOperation:
            return None

    source_values = set()
    for m in re.finditer(r"(?<![\w.])(\d+(?:[,_]\d{3})*(?:\.\d+)?|\.\d+)(?!\.?\d)([kK]\b)?", text):   # 2.5.3 is a version, not 2.5
        v = value(m.group(1))
        source_values.add(v * 1000 if m.group(2) else v)

    def in_source(n: str) -> bool:
        return value(n) in source_values

    missing = [n for n in sorted(seen) if not in_source(n) and n not in allow]
    used_allow = sorted(n for n in allow if n in seen and not in_source(n))
    unused = sorted(n for n in allow if n not in seen)
    print(f"{len(seen)} distinct numerals on screen; {len(used_allow)} allowed by numbers.allow; {len(missing)} not in {source.name}")
    for n in missing:
        print(f"NOT IN SOURCE {n} | {seen[n]}")
    for n in unused:
        print(f"warn numbers.allow lists {n}, which is no longer on screen")
    return 1 if missing else 0


# ---------- narration ----------

def load_env(path: str | None) -> dict:
    env = dict(os.environ)
    path = path or os.environ.get("LESSON_ENV_FILE")
    if path:
        for line in Path(path).expanduser().read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Za-z_]\w*)\s*=\s*(.*?)\s*$", line)
            if m and m.group(1) not in os.environ:
                env[m.group(1)] = m.group(2).strip("'\"")
    return env


def stale(lesson: Lesson, i: int, text: str) -> bool:
    txt, wav = lesson.clips / f"{i + 1:03d}.txt", lesson.clips / f"{i + 1:03d}.wav"
    return not (txt.exists() and wav.exists() and txt.read_text(encoding="utf-8") == lesson.sig(i, text))


def cost(lesson: Lesson, texts: list[str]) -> str:
    """Size of a synth request, with a price when speak.yaml gives one. MiniMax bills a non-ASCII character as two
    (measured 2026-10-12), so the estimate runs high for CJK text on a model that counts every character once."""
    chars, price = sum(map(len, texts)), lesson.speak.get("price")
    if not price:
        return f"{chars} characters"
    return f"{chars} characters, about ${sum(1 if ord(c) < 128 else 2 for t in texts for c in t) * float(price) / 1e6:.3f}"


def cmd_say(args) -> int:
    lesson = Lesson(args.dir)
    beats = lesson.beats
    picks = parse_which(args.which, len(beats)) if args.which else range(len(beats))
    lines, new = [], []
    for i in picks:
        spoken = lesson.spoken(beats[i]["t"])
        missing = stale(lesson, i, beats[i]["t"])
        lines.append(spoken)
        new += [spoken] if missing else []
        print(f"{i + 1:3d} {lesson.rate(i):.2f} {'*' if missing else ' '} {spoken}")
    print(f"-- {len(lines)} beats, {cost(lesson, lines)}; {len(new)} without a fresh clip (*): {cost(lesson, new)}")
    for line in speech_warnings(lesson):
        print("warn", line)
    return 0


def cmd_synth(args) -> int:
    import requests
    lesson = Lesson(args.dir)
    beats, cfg = lesson.beats, lesson.speak
    if args.which == "all":
        picks = list(range(len(beats)))
    elif args.which == "changed":
        picks = [i for i, b in enumerate(beats) if stale(lesson, i, b["t"])]
    else:
        picks = parse_which(args.which, len(beats))
    if not picks:
        print("all clips are fresh")
        return 0
    env = load_env(args.env_file)
    key_name = cfg.get("key_env", "OPENROUTER_API_KEY")
    if not env.get(key_name):
        die(f"${key_name} is not set (export it, or pass --env-file / set LESSON_ENV_FILE)", 1)
    url = (cfg.get("base_url") or env.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/") + "/audio/speech"
    headers = {"Authorization": "Bearer " + env[key_name], **{str(k): str(v) for k, v in (cfg.get("headers") or {}).items()}}
    need("ffmpeg")
    lesson.clips.mkdir(exist_ok=True)

    def one(i: int):
        stem = lesson.clips / f"{i + 1:03d}"
        body = {"model": cfg["model"], "input": lesson.spoken(beats[i]["t"]), "voice": cfg["voice"],
                "response_format": "mp3", "speed": lesson.rate(i)}
        for attempt in range(5):
            r = requests.post(url, headers=headers, json=body, timeout=180)
            if r.status_code == 200 and "json" not in r.headers.get("content-type", "") and len(r.content) > 1000:
                break
            if r.status_code not in (429, 500, 502, 503, 504):
                raise Fail(f"beat {i + 1}: HTTP {r.status_code} {r.text[:300]}")
            time.sleep(3 * (attempt + 1))
        else:
            raise Fail(f"beat {i + 1}: gave up after 5 attempts")
        stem.with_suffix(".mp3").write_bytes(r.content)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(stem.with_suffix(".mp3")), "-ar", str(RATE), "-ac", "1",
                        "-c:a", "pcm_s16le", str(stem.with_suffix(".wav"))], check=True)
        stem.with_suffix(".txt").write_text(lesson.sig(i, beats[i]["t"]), encoding="utf-8")
        with wave.open(str(stem.with_suffix(".wav"))) as w:
            return i, w.getnframes() / RATE

    print(f"synthesizing {len(picks)} of {len(beats)} beats with {cfg['model']} / {cfg['voice']}: "
          f"{cost(lesson, [lesson.spoken(beats[i]['t']) for i in picks])}", flush=True)
    with ThreadPoolExecutor(max_workers=int(cfg.get("workers", 2))) as pool:
        for i, seconds in pool.map(one, picks):
            print(f"{i + 1:3d} {seconds:5.1f}s", flush=True)
    return 0


def cmd_mix(args) -> int:
    lesson = Lesson(args.dir)
    beats = lesson.beats
    bad = [i + 1 for i, b in enumerate(beats) if stale(lesson, i, b["t"])]
    if bad:
        die(f"stale or missing clips for beats {bad}: run `synth DIR changed` first", 1)
    need("ffmpeg")
    lesson.out.mkdir(exist_ok=True)
    durations = []
    joined = lesson.clips / "all.wav"
    with wave.open(str(joined), "wb") as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(RATE)
        for i in range(len(beats)):
            with wave.open(str(lesson.clips / f"{i + 1:03d}.wav")) as w:
                if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (RATE, 1, 2):
                    die(f"clip {i + 1} is not {RATE} Hz mono 16-bit: resynthesize it", 1)
                durations.append(w.getnframes() * 1000 / RATE)
                out.writeframes(w.readframes(w.getnframes()))
    mp3 = lesson.out / lesson.mp3_name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-c:a", "libmp3lame", "-q:a", "3", str(mp3)], check=True)
    joined.unlink()
    sig = hashlib.sha256("\x00".join(lesson.sig(i, b["t"]) for i, b in enumerate(beats)).encode()).hexdigest()
    (lesson.dir / "narration.json").write_text(json.dumps({"sig": sig, "durations": durations}), encoding="utf-8")
    build(lesson)
    print(f"{len(beats)} beats, {sum(durations) / 1000:.1f} s, longest {max(durations) / 1000:.1f} s, shortest {min(durations) / 1000:.1f} s")
    print(lesson.html_path)
    print(mp3)
    return 0


# ---------- video ----------

def cmd_video(args) -> int:
    lesson = Lesson(args.dir)
    exe = browser()
    if not exe:
        die("no Chromium/Chrome found; set LESSON_BROWSER", 1)
    node, ffmpeg = need("node"), need("ffmpeg")
    beats = lesson.beats
    picks = parse_which(args.which, len(beats)) if args.which else list(range(len(beats)))
    if picks != list(range(picks[0], picks[-1] + 1)):
        die("video films one run of beats, e.g. 12-20")
    narration = None if args.silent else lesson.narration()
    speed = float(lesson.meta.get("speed", 1))
    lesson.out.mkdir(exist_ok=True)
    target = lesson.out / (f"{lesson.slug}.mp4" if len(picks) == len(beats) else f"{lesson.slug}-{picks[0] + 1}-{picks[-1] + 1}.mp4")
    with tempfile.TemporaryDirectory(prefix="lesson-video-") as tmp:
        page = build(lesson, silent=narration is None, to=Path(tmp) / lesson.html_path.name)
        sound_in, sound_out = [], ["-an"]
        if narration:
            # The page keeps time by the clip lengths `mix` measured, so the sound is those same clips, with silence where
            # the film holds on a pause. Both run at the lesson's own speed: the page's clock and atempo below.
            wav = Path(tmp) / "sound.wav"
            with wave.open(str(wav), "wb") as out:
                out.setnchannels(1); out.setsampwidth(2); out.setframerate(RATE)
                for i in picks:
                    clip = lesson.clips / f"{i + 1:03d}.wav"
                    if stale(lesson, i, beats[i]["t"]):
                        die(f"stale or missing clip for beat {i + 1}: run `synth DIR changed` and `mix DIR` first", 1)
                    with wave.open(str(clip)) as w:
                        if abs(w.getnframes() * 1000 / RATE - narration["durations"][i]) > 1:
                            die(f"clip {i + 1} is not the one `mix` timed: run `mix DIR` again", 1)
                        out.writeframes(w.readframes(w.getnframes()))
                    if beats[i]["wait"] or i == len(beats) - 1:
                        out.writeframes(b"\0\0" * round(args.hold * speed * RATE))
            sound_in = ["-i", str(wav)]
            sound_out = [*(["-filter:a", f"atempo={speed}"] if speed != 1 else []), "-c:a", "aac", "-b:a", "128k"]
        trace = Path(tmp) / "trace.json"
        spec = {"browser": exe, "url": f"{page.as_uri()}?render={round(args.hold * 1000)}", "first": picks[0] + 1, "last": picks[-1] + 1,
                "fps": args.fps, "scale": args.scale, "everyFrame": args.every_frame, "trace": str(trace)}
        film = subprocess.Popen([node, str(SKILL / "scripts" / "capture.mjs"), json.dumps(spec)], stdout=subprocess.PIPE)
        encode = subprocess.run([ffmpeg, "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(args.fps), "-c:v", "png", "-i", "-",
                                 *sound_in, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                                 *sound_out, "-movflags", "+faststart", str(target)], stdin=film.stdout)
        film.stdout.close()
        if film.wait() or encode.returncode or not trace.exists():
            target.unlink(missing_ok=True)
            raise Fail("filming stopped before the end (see the message above); no video was written")
        seen = json.loads(trace.read_text(encoding="utf-8"))
    if seen["last"] != seen["expected_last"]:
        raise Fail(f"the film ended on beat {seen['last']}, not {seen['expected_last']}: {target} is not the whole run")
    probe = subprocess.run([need("ffprobe"), "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(target)],
                           capture_output=True, text=True, check=True)
    length = {x["codec_type"]: float(x["duration"]) for x in json.loads(probe.stdout)["streams"]}
    print(f"beats {picks[0] + 1}-{picks[-1] + 1}, {seen['frames']} frames at {args.fps} fps ({seen['captured']} photographed), "
          f"each beat appears {seen['late_ms'][0]:.0f}-{seen['late_ms'][1]:.0f} ms after its time")
    print("picture %.2f s" % length["video"] + (", sound %.2f s" % length["audio"] if "audio" in length else ", no sound")
          + f", timeline {seen['seconds']:.2f} s")
    if abs(length["video"] - seen["seconds"]) > 0.1 or abs(length.get("audio", length["video"]) - length["video"]) > 0.1:
        raise Fail(f"picture, sound and timeline differ by more than 0.1 s: do not publish {target}")
    print(target)
    return 0


# ---------- init ----------

def cmd_init(args) -> int:
    target = Path(args.dir)
    if target.exists() and any(target.iterdir()):
        die(f"{target} exists and is not empty")
    source = SKILL / "assets" / ("gallery" if args.gallery else "starter")
    shutil.copytree(source, target, dirs_exist_ok=True)
    meta_path = target / "lesson.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if not args.gallery:
        if not args.title:
            die("--title is required")
        slug = args.slug or re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")
        if not slug:
            die("--slug is required when the title has no ASCII letters or digits")
        meta.update(title=args.title, slug=slug, lang=args.lang)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        speak_path = target / "speak.yaml"
        speak = speak_path.read_text(encoding="utf-8")
        swaps = [('"explainer:todo"', f'"explainer:{slug}"')]
        if args.lang == "zh":
            swaps += [('voice: "English_expressive_narrator"     # zh: "Chinese (Mandarin)_Radio_Host"', 'voice: "Chinese (Mandarin)_Radio_Host"'),
                      ("\nrules: none\n", "\nrules: zh\n")]
        for old, new in swaps:
            if speak.count(old) != 1:
                die(f"assets/starter/speak.yaml no longer holds `{old.strip()}`: update cmd_init with it")
            speak = speak.replace(old, new)
        speak_path.write_text(speak, encoding="utf-8")
    print(target.resolve())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("dir"); p.add_argument("--title"); p.add_argument("--slug")
    p.add_argument("--lang", choices=("zh", "en"), default="en"); p.add_argument("--gallery", action="store_true")
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("build"); p.add_argument("dir"); p.add_argument("--silent", action="store_true", help="ignore narration")
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser("check"); p.add_argument("dir"); p.add_argument("--silent", action="store_true")
    p.add_argument("--no-browser", action="store_true"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("thread"); p.add_argument("dir"); p.set_defaults(fn=cmd_thread)
    p = sub.add_parser("shots"); p.add_argument("dir"); p.add_argument("which", nargs="?"); p.set_defaults(fn=cmd_shots)
    p = sub.add_parser("numbers"); p.add_argument("dir"); p.add_argument("--source"); p.set_defaults(fn=cmd_numbers)
    p = sub.add_parser("say"); p.add_argument("dir"); p.add_argument("which", nargs="?"); p.set_defaults(fn=cmd_say)
    p = sub.add_parser("synth"); p.add_argument("dir"); p.add_argument("which"); p.add_argument("--env-file")
    p.set_defaults(fn=cmd_synth)
    p = sub.add_parser("mix"); p.add_argument("dir"); p.set_defaults(fn=cmd_mix)
    p = sub.add_parser("video"); p.add_argument("dir"); p.add_argument("which", nargs="?", help="one run of beats, e.g. 12-20")
    p.add_argument("--fps", type=int, default=30); p.add_argument("--hold", type=float, default=3, help="seconds to stay on a pause")
    p.add_argument("--scale", type=float, default=1, help="1 = 1280x720, 1.5 = 1920x1080")
    p.add_argument("--every-frame", action="store_true", help="photograph every frame instead of only changed ones")
    p.add_argument("--silent", action="store_true", help="ignore narration"); p.set_defaults(fn=cmd_video)
    args = ap.parse_args()
    try:
        return args.fn(args)
    except Fail as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
