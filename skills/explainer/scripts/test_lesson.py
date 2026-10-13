#!/usr/bin/env python3
"""Smoke test for the explainer skill: python3 scripts/test_lesson.py

The gallery must build and pass every check; a fresh starter must fail only on its TODO placeholders;
`check` must name the scenes the scene map leaves out and `thread` must write one page per scene;
a narrated page must survive `shots` and `numbers` byte for byte and film into an MP4 as long as its timeline;
the zh reading rules must rewrite what the voice misreads and `say` must warn when they are off; asr.py's numeral
normalisation must make spoken and written numbers compare equal. Needs uv and node; the per-beat browser pass
runs when Chromium/Chrome is installed and is skipped by lesson.py otherwise, the narrated-page test needs ffmpeg,
and the film test needs both.
"""

import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
# Half a second of silence per beat, signed the way `synth` signs a clip: enough for `mix` to build a narrated page.
FAKE_CLIPS = '''
import importlib.util, sys, wave
spec = importlib.util.spec_from_file_location("lesson", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
l = m.Lesson(sys.argv[2]); l.clips.mkdir()
for i, b in enumerate(l.beats):
    with wave.open(str(l.clips / f"{i + 1:03d}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(m.RATE); w.writeframes(bytes(m.RATE))
    (l.clips / f"{i + 1:03d}.txt").write_text(l.sig(i, b["t"]), encoding="utf-8")
'''


def lesson(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", "-q", str(HERE / "lesson.py"), *args], capture_output=True, text=True)


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    failures = []

    def expect(ok: bool, what: str, detail: str = "") -> None:
        print(("ok   " if ok else "FAIL ") + what)
        if not ok:
            failures.append(what)
            print(detail.strip()[-1500:])

    with tempfile.TemporaryDirectory() as tmp:
        gallery, starter = Path(tmp) / "gallery", Path(tmp) / "starter"
        r = lesson("init", str(gallery), "--gallery")
        expect(r.returncode == 0, "init --gallery", r.stdout + r.stderr)
        r = lesson("check", str(gallery))
        expect(r.returncode == 0 and "CHECK OK" in r.stdout, "gallery passes check", r.stdout + r.stderr)
        page = gallery / "out" / "explainer-gallery.html"
        expect(page.exists(), "gallery html is written")

        if shutil.which("ffmpeg"):
            shutil.copy(HERE.parent / "assets" / "starter" / "speak.yaml", gallery)
            (gallery / "source.txt").write_text("", encoding="utf-8")
            r = subprocess.run(["uv", "run", "-q", "--with", "PyYAML", "python", "-B", "-c", FAKE_CLIPS, str(HERE / "lesson.py"), str(gallery)],
                               capture_output=True, text=True)
            expect(r.returncode == 0, "fake clips are written", r.stdout + r.stderr)
            r = lesson("mix", str(gallery))
            narrated = page.read_bytes()
            expect(r.returncode == 0 and b'"audio": "explainer-gallery-narration.mp3"' in narrated, "mix builds a narrated page",
                   r.stdout + r.stderr)
            for gate in (("shots", str(gallery), "1"), ("numbers", str(gallery))):
                r = lesson(*gate)
                expect(page.read_bytes() == narrated, f"{gate[0]} leaves the narrated page as it was", r.stdout + r.stderr)
            if any(shutil.which(b) for b in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable")):
                r = lesson("video", str(gallery), "1-3")
                film = gallery / "out" / "explainer-gallery-1-3.mp4"
                took = re.search(r"picture ([\d.]+) s, sound ([\d.]+) s, timeline ([\d.]+) s", r.stdout)
                expect(r.returncode == 0 and film.exists() and took and took.group(1) == took.group(3) == "1.50",
                       "video films three half-second beats into 1.5 s of picture and sound", r.stdout + r.stderr)
                probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name", "-of", "json", str(film)],
                                       capture_output=True, text=True)
                codecs = [s["codec_name"] for s in json.loads(probe.stdout or "{}").get("streams", [])]
                expect(codecs == ["h264", "aac"], "the film is one h264 + aac file", probe.stdout + probe.stderr)
                expect(page.read_bytes() == narrated, "video leaves the narrated page as it was")
            else:
                print("skip film test: Chromium/Chrome not found")
        else:
            print("skip narrated-page test: ffmpeg not found")

        expect("warn outline.md is missing" in lesson("check", str(gallery), "--no-browser").stdout, "check warns when there is no outline.md")
        (gallery / "outline.md").write_text("| scene | question (viewer's words) | raised by | visual |\n|---|---|---|---|\n"
                                            "| `intro` | What is this page? | | title |\n| fsplit | How much is a bet? | intro | bar |\n"
                                            "ftable | Which inputs? | | table\nfquiz | TODO | fsplit | quiz\n", encoding="utf-8")
        r = lesson("check", str(gallery), "--no-browser")
        expect("outline.md has no scene-map row for: fbars, fmodel, rleq" in r.stdout and "outline.md gives no question for: fquiz\n" in r.stdout
               and "outline.md does not say what raises the question of: ftable\n" in r.stdout and "CHECK OK" in r.stdout,
               "check names the scenes without a row, a question or a `raised by`", r.stdout + r.stderr)
        scenes = (gallery / "scenes.html").read_text(encoding="utf-8")
        (gallery / "scenes.html").write_text(scenes.replace("<h2>What is the price paying for?</h2>", '<h2>What is <span data-v="price"></span> '
                                             'paying for?<span class="tag">author\'s example</span></h2>'), encoding="utf-8")
        r = lesson("thread", str(gallery))
        pages = sorted(f.name for f in (gallery / "thread").glob("*.txt"))
        second = (gallery / "thread" / "02.txt").read_text(encoding="utf-8") if len(pages) > 2 else ""
        expect(r.returncode == 0 and pages == [f"{i:02d}.txt" for i in range(14)] and "asks  How much is a bet?   <- intro" in r.stdout
               and "asks  (no question in the scene map)" in r.stdout and second.startswith("Chapter: 1 Finance\nOn screen: What is "),
               "thread prints each scene's question and writes one page per scene", r.stdout + r.stderr + second)
        head = second.splitlines()[1] if second else ""
        expect(re.fullmatch(r"On screen: What is \S*\d\S* paying for\?", head) is not None,
               "a page's heading carries its data-v value and not its provenance tag", head)
        (gallery / "scenes.html").write_text(scenes, encoding="utf-8")
        (gallery / "outline.md").write_text("scene | question | source\n--- | --- | ---\nintro | What is this page? | p.1\n", encoding="utf-8")
        r = lesson("check", str(gallery), "--no-browser")
        expect("outline.md scene map has no `raised by` column" in r.stdout and "does not say what raises" not in r.stdout,
               "check says so when the scene map has no `raised by` column", r.stdout + r.stderr)

        r = lesson("init", str(starter), "--title", "Smoke test", "--lang", "en")
        expect(r.returncode == 0, "init starter", r.stdout + r.stderr)
        r = lesson("say", str(starter), "1-2")
        expect(r.returncode == 0 and "2 beats" in r.stdout, "say previews beats without an API call", r.stdout + r.stderr)
        r = lesson("check", str(starter))
        problems = [line for line in r.stdout.splitlines() if line.startswith("FAIL")]
        expect(r.returncode == 1 and problems and all("TODO" in line for line in problems),
               "fresh starter fails only on its TODO placeholders", r.stdout + r.stderr)
        expect("warn outline.md gives no question for: intro, context, worked, compute, end" in r.stdout and "is missing" not in r.stdout,
               "the starter's outline is found and its unwritten questions are reported", r.stdout + r.stderr)

        zh = Path(tmp) / "zh"
        r = lesson("init", str(zh), "--title", "烟雾测试", "--slug", "smoke-zh", "--lang", "zh")
        speak = (zh / "speak.yaml").read_text(encoding="utf-8") if r.returncode == 0 else ""
        expect("rules: zh" in speak and "Radio_Host" in speak and '"explainer:smoke-zh"' in speak,
               "init --lang zh picks the Mandarin voice, the reading rules and a request label", r.stdout + r.stderr + speak)
        script = (zh / "script.js").read_text(encoding="utf-8").replace(
            "TODO the concrete situation and what we are trying to do.", "2020 年收入 $32.5 billion，利润率 −5%，估值 1.5x。")
        (zh / "script.js").write_text(script, encoding="utf-8")
        r = lesson("say", str(zh), "1")
        expect("2020年收入 三百二十五亿美元，利润率 负5%，估值 一点五倍。" in r.stdout and "warn" not in r.stdout and "about $" in r.stdout,
               "say applies the zh reading rules and prints the estimated cost", r.stdout + r.stderr)
        (zh / "speak.yaml").write_text(speak.replace("rules: zh", "rules: none").replace("price: 60", ""), encoding="utf-8")
        r = lesson("say", str(zh), "1")
        warned = [line for line in r.stdout.splitlines() if line.startswith("warn speech, beat 1")]
        expect(len(warned) == 4 and "about $" not in r.stdout and "characters" in r.stdout,
               "with the rules off, say warns about each misread class; without a price it counts characters", r.stdout + r.stderr)

    speech = module("lesson")
    for n, read in [(0, "零"), (10, "十"), (15, "十五"), (110, "一百一十"), (2005, "两千零五"), (10500, "一万零五百"), (200000, "二十万"),
                    (180000000, "一亿八千万"), (32500000000, "三百二十五亿"), (200000000, "两亿"), (1200000000000, "一万两千亿")]:
        expect(speech.zh_number(n) == read, f"zh_number: {n} -> {read}", speech.zh_number(n))
    for written, read in [("$265 billion", "两千六百五十亿美元"), ("7.5 million 用户", "七百五十万 用户"), ("1998 年到 2020年", "1998年到 2020年"),
                          ("8.3 年", "8.3年"), ("增长 −12%（−$5）", "增长 负12%（负$5）"), ("900 − 247", "900减247"), ("ROIC − WACC", "ROIC − WACC"),
                          ("2x 和 12.5x", "两倍 和 十二点五倍"), ("$1.2345678 million", "$1.2345678 million"), ("a 5x5 grid, Box2x", "a 5x5 grid, Box2x")]:
        expect(speech.read_zh(written) == read, f"read_zh: {written!r} -> {read!r}", speech.read_zh(written))

    asr = module("asr")
    for spoken, written in [("两万一千六百六十六 步", "21,666步"), ("百分之九十", "90%"), ("负100", "−100"), ("十五万", "150000"),
                            ("零点九五一", "0.951"), ("第一：<#0.18#>T D target", "第一,TD Target")]:
        expect(asr.norm(spoken) == asr.norm(written), f"asr.norm: {spoken!r} == {written!r}", f"{asr.norm(spoken)!r} != {asr.norm(written)!r}")
    for said, heard, missing in [("收入 325亿美元", "收入三百二十五亿美元", []), ("894,813美元", "89,4813美元", []), ("900美元-247美元", "900美元减247美元", []),
                                 ("利润率 负5.5%", "利润率5.5%", ["-5.5%"]), ("一共 1,250 家", "一共一千二百家", ["1250"]), ("第 4 步", "第丝步", []),
                                 ("涨到 0.64", "涨到零点六", ["0.64"])]:
        expect(asr.unheard(said, heard) == missing, f"asr.unheard: {said!r} heard as {heard!r} lacks {missing}", str(asr.unheard(said, heard)))
    for said, heard, reading in [("2020年的数字", "二零二零年的数字", "digits"), ("2020 年的数字", "二千零二十年的数字", "cardinal"),
                                 ("1998年", "一九九八年", "digits"), ("2020年的数字", "今年的数字", "unclear")]:
        expect(asr.year_readings(said, heard) == [(re.search(r"\d{4}", said).group(0), reading)], f"asr.year_readings: {heard!r} is {reading}",
               str(asr.year_readings(said, heard)))

    print("FAILED: " + "; ".join(failures) if failures else "ALL OK")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
