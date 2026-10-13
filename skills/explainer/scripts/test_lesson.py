#!/usr/bin/env python3
"""Smoke test for the explainer skill: python3 scripts/test_lesson.py

The gallery must build and pass every check; a fresh starter must fail only on its TODO placeholders;
`check` must name the scenes the scene map leaves out and the chapters the chain leaves out, and `thread` must write
one page per scene;
a narrated page must survive `shots` and `numbers` byte for byte and film into an MP4 as long as its timeline;
a beat's direction must reach the directed voice and no other, change that clip's signature and show in `say`;
`synth` must turn the directed voice's raw PCM into the clip format `mix` takes (against a local stand-in, no API call);
the zh reading rules must rewrite what the fallback voice misreads and `say` must warn when they are off; asr.py's numeral
normalisation must make spoken and written numbers compare equal. Needs uv and node; the per-beat browser pass
runs when Chromium/Chrome is installed and is skipped by lesson.py otherwise, the narrated-page test needs ffmpeg,
and the film test needs both.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import wave

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


# Each beat's direction, pause flag and clip signature, as lesson.py sees them.
BEATS = '''
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("lesson", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
l = m.Lesson(sys.argv[2])
print(json.dumps([[b["d"], b["wait"], l.sig(i, b["t"])] for i, b in enumerate(l.beats)]))
'''
DIRECTED = """const SCRIPT = [{ch: 'A', scenes: [['intro', [
  'plain',
  D('calm', 'one'), D('calm', 'two'), D('calm', W('three')),
  D('firm and conclusive', 'four'),
]]]}];
"""


def lesson(*args: str, **env: str) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", "-q", str(HERE / "lesson.py"), *args], capture_output=True, text=True, env={**os.environ, **env})


def beats(directory: Path) -> list:
    r = subprocess.run(["uv", "run", "-q", "--with", "PyYAML", "python", "-B", "-c", BEATS, str(HERE / "lesson.py"), str(directory)],
                       capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else [r.stderr]


class Voice(BaseHTTPRequestHandler):
    """Stands in for the speech endpoint: records each request and answers half a second of 24 kHz mono PCM."""
    asked: list = []

    def do_POST(self):
        Voice.asked.append(json.loads(self.rfile.read(int(self.headers["content-length"]))))
        self.send_response(200)
        self.send_header("content-type", "audio/pcm;rate=24000;channels=1")
        self.send_header("content-length", "24000")
        self.end_headers()
        self.wfile.write(bytes(24000))

    def log_message(self, *args):
        pass


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
        expect("warn outline.md has no chapter chain" in r.stdout, "check says so when the brief has no chapter chain", r.stdout + r.stderr)
        scenes = (gallery / "scenes.html").read_text(encoding="utf-8")
        (gallery / "scenes.html").write_text(scenes.replace("<h2>What is the price paying for?</h2>", '<h2>What is <span data-v="price"></span> '
                                             'paying for?<span class="tag">author\'s example</span></h2>'), encoding="utf-8")
        r = lesson("thread", str(gallery))
        pages = sorted(f.name for f in (gallery / "thread").glob("*.txt"))
        second = (gallery / "thread" / "02.txt").read_text(encoding="utf-8") if len(pages) > 2 else ""
        expect(r.returncode == 0 and pages == [f"{i:02d}.txt" for i in range(14)] and "asks  How much is a bet?   <- intro" in r.stdout
               and "asks  (no question in the scene map)" in r.stdout and second.startswith("Chapter: 1 Finance\nOn screen: What is "),
               "thread prints each scene's question and writes one page per scene", r.stdout + r.stderr + second)
        expect("chapters  Start → 1 Finance → 2 RL → 3 Distributed systems → Close\n" in r.stdout, "thread prints the chapter names in a row", r.stdout)
        head = second.splitlines()[1] if second else ""
        expect(re.fullmatch(r"On screen: What is \S*\d\S* paying for\?", head) is not None,
               "a page's heading carries its data-v value and not its provenance tag", head)
        (gallery / "scenes.html").write_text(scenes, encoding="utf-8")
        (gallery / "outline.md").write_text("- **Chapter chain:** one line per chapter.\n  1. Start: what is this page?\n  2. `1 Finance`: how much is a bet?\n"
                                            "- **Scope:** Close with a recap.\n\n"
                                            "scene | question | source\n--- | --- | ---\nintro | What is this page? | p.1\n", encoding="utf-8")
        r = lesson("check", str(gallery), "--no-browser")
        expect("outline.md scene map has no `raised by` column" in r.stdout and "does not say what raises" not in r.stdout,
               "check says so when the scene map has no `raised by` column", r.stdout + r.stderr)
        expect("outline.md leaves out of its chapter chain: 2 RL, 3 Distributed systems, Close\n" in r.stdout and "no chapter chain" not in r.stdout,
               "check names the chapters the chain leaves out, reading only the chain's own lines", r.stdout + r.stderr)

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
        expect("warn outline.md leaves out of its chapter chain: TODO the question, TODO what that leaves, Close\n" in r.stdout,
               "the starter's chapter chain is found and its unwritten chapters are reported", r.stdout + r.stderr)

        zh = Path(tmp) / "zh"
        r = lesson("init", str(zh), "--title", "烟雾测试", "--slug", "smoke-zh", "--lang", "zh")
        speak = (zh / "speak.yaml").read_text(encoding="utf-8") if r.returncode == 0 else ""
        expect("google/gemini-3.8-flash-tts" in speak and '"Charon"' in speak and "\nrules: zh\n" in speak and '"explainer:smoke-zh"' in speak,
               "init --lang zh sets the directed voice, the reading rules and a request label", r.stdout + r.stderr + speak)
        script = (zh / "script.js").read_text(encoding="utf-8").replace(
            "TODO the concrete situation and what we are trying to do.", "2020 年收入 $32.5 billion，利润率 −5%，估值 1.5x，每月 $60.37。")
        (zh / "script.js").write_text(script, encoding="utf-8")
        r = lesson("say", str(zh), "1-2")
        expect("  1 * 2020年收入 三百二十五亿美元，利润率 负5%，估值 一点五倍，每月 60.37美元。\n        > (no direction)\n" in r.stdout
               and "        > TODO how this turn should sound" in r.stdout and "min of sound, about $" in r.stdout and "warn speech" not in r.stdout,
               "on the directed voice, say prints each direction under its words, applies the zh reading rules (a dollar amount's unit too) and estimates the sound",
               r.stdout + r.stderr)
        (zh / "speak.yaml").write_text(speak.replace("\nrules: zh\n", "\nrules: none\n"), encoding="utf-8")
        r = lesson("say", str(zh), "1")
        warned = [line for line in r.stdout.splitlines() if line.startswith("warn speech, beat 1")]
        expect(len(warned) == 2 and "32.5 billion" in warned[0] and "1.5x" in warned[1],
               "with the rules off, the directed voice is warned about the two classes it was heard to misread", r.stdout + r.stderr)
        (zh / "speak.yaml").write_text(speak, encoding="utf-8")
        expect("warn delivery, beat 1,3,4,5,6,7,8,9,10,11,12,13,14,15: no direction" in r.stdout, "say names the beats without a direction", r.stdout)

        (zh / "script.js").write_text(DIRECTED.replace("D('calm', 'one')", "D('TODO how it sounds', 'one')"), encoding="utf-8")
        r = lesson("check", str(zh), "--no-browser")
        expect(r.returncode != 0 and "beat 2 (intro): its direction is still a TODO placeholder" in r.stdout + r.stderr,
               "check refuses a direction left as a TODO", r.stdout + r.stderr)
        (zh / "script.js").write_text(DIRECTED, encoding="utf-8")
        rows = beats(zh)
        expect([row[:2] for row in rows] == [["", False], ["calm", False], ["calm", False], ["calm", True], ["firm and conclusive", False]],
               "D() gives a beat its direction and keeps W()'s pause", str(rows))
        expect(len(rows) == 5 and rows[1][2] == "google/gemini-3.8-flash-tts|Charon|calm\none"
               and rows[0][2] == "google/gemini-3.8-flash-tts|Charon|\nplain", "the directed voice signs a clip with its direction", str(rows))
        r = lesson("say", str(zh))
        expect("warn delivery, beat 2-4: the same direction 3 times in a row: \"calm\"" in r.stdout and "warn delivery, beat 1: no direction" in r.stdout,
               "say warns about one direction three times in a row", r.stdout + r.stderr)
        if shutil.which("ffmpeg"):
            server = HTTPServer(("127.0.0.1", 0), Voice)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            (zh / "speak.yaml").write_text(speak.replace("key_env: OPENROUTER_API_KEY", "key_env: LESSON_TEST_KEY")
                                           + f"base_url: http://127.0.0.1:{server.server_port}\nworkers: 1\n", encoding="utf-8")
            r = lesson("synth", str(zh), "1-2", LESSON_TEST_KEY="not-a-key")
            server.shutdown()
            expect(r.returncode == 0 and Voice.asked == [
                {"model": "google/gemini-3.8-flash-tts", "input": "plain", "voice": "Charon", "response_format": "pcm"},
                {"model": "google/gemini-3.8-flash-tts", "input": "one", "voice": "Charon", "response_format": "pcm", "instructions": "calm"}],
                "synth sends the directed voice the direction as `instructions`, and no speed", r.stdout + r.stderr + str(Voice.asked))
            clip = zh / "clips" / "002.wav"
            if clip.exists():
                with wave.open(str(clip)) as w:
                    shape = (w.getframerate(), w.getnchannels(), w.getsampwidth(), round(w.getnframes() / w.getframerate(), 2))
            expect(clip.exists() and shape == (32000, 1, 2, 0.5) and beats(zh)[1][2] == clip.with_suffix(".txt").read_text(encoding="utf-8")
                   and "1.0 s of sound, about $0.000 at $9 per million audio tokens" in r.stdout,
                   "synth turns 24 kHz PCM into a 32 kHz clip signed with its direction, and prices the sound", r.stdout + r.stderr)
            (zh / "speak.yaml").write_text(speak, encoding="utf-8")
        (zh / "speak.yaml").write_text(speak + "speed_default: 1.0\n", encoding="utf-8")
        r = lesson("say", str(zh))
        expect(r.returncode == 2 and "is sent no speed" in r.stderr, "a speed on the directed voice is refused", r.stdout + r.stderr)
        (zh / "script.js").write_text(DIRECTED.replace("D('calm', W('three'))", "W(D('calm', 'three'))"), encoding="utf-8")
        r = lesson("say", str(zh))
        expect(r.returncode == 2 and "D goes outside W" in r.stderr, "W(D(...)) is refused with the fix", r.stdout + r.stderr)

        # the fallback voice: same words, a speed in place of the direction, and the Mandarin reading rules
        (zh / "script.js").write_text(DIRECTED, encoding="utf-8")
        speak = (HERE.parent / "assets" / "speak-minimax.yaml").read_text(encoding="utf-8")
        (zh / "speak.yaml").write_text(speak, encoding="utf-8")
        rows = beats(zh)
        expect(len(rows) == 5 and rows[1][2] == "minimax/speech-2.8-turbo|English_expressive_narrator|1.0\none",
               "the fallback voice signs a clip with its speed, as it always has", str(rows))
        r = lesson("say", str(zh))
        expect("  2 1.00 * one\n" in r.stdout and "note: 4 beats carry a direction, which minimax/speech-2.8-turbo is not sent" in r.stdout and "warn delivery" not in r.stdout,
               "on the fallback voice, say shows the speed and says the directions go unused", r.stdout + r.stderr)
        speak = speak.replace('"English_expressive_narrator"', '"Chinese (Mandarin)_Radio_Host"').replace("\nrules: none\n", "\nrules: zh\n")
        expect("Radio_Host" in speak and "rules: zh" in speak, "the fallback file still holds the voice and rules lines", speak)
        (zh / "speak.yaml").write_text(speak, encoding="utf-8")
        (zh / "script.js").write_text(script, encoding="utf-8")
        r = lesson("say", str(zh), "1")
        expect("2020年收入 三百二十五亿美元，利润率 负5%，估值 一点五倍，每月 $60.37。" in r.stdout and "warn speech" not in r.stdout and "about $" in r.stdout,
               "say applies the zh reading rules, leaves a plain dollar amount as the fallback voice reads it, and prints the estimated cost",
               r.stdout + r.stderr)
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
    for written, read in [("$900 − $247", "900美元减247美元"), ("大约 $1,190。每月 $60.37，", "大约 1,190美元。每月 60.37美元，"), ("（−$5）", "（负5美元）"),
                          ("$265 billion", "两千六百五十亿美元"), ("$1.2345678 million", "$1.2345678 million"), ("$3 万、$5K、US$9", "$3 万、$5K、US$9"),
                          ("$45, $1,2345", "45美元, $1,2345"), ("$900 美元", "$900 美元")]:
        expect(speech.read_zh(written, dollars=True) == read, f"read_zh with dollars: {written!r} -> {read!r}", speech.read_zh(written, dollars=True))

    asr = module("asr")
    for spoken, written in [("两万一千六百六十六 步", "21,666步"), ("百分之九十", "90%"), ("负100", "−100"), ("十五万", "150000"),
                            ("零点九五一", "0.951"), ("第一：<#0.18#>T D target", "第一,TD Target"),
                            ("大约 <short pause> $1,190，再<long pause>折现", "大约$1,190,再折现")]:
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
