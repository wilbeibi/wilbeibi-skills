#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "faster-whisper>=1.1; sys_platform != 'darwin'",
#   "mlx-whisper>=0.4; sys_platform == 'darwin'",
# ]
# ///
"""Listen back to a lesson's narration: transcribe every clip and compare it with the text sent to the voice.

    asr.py DIR [WHICH] [--model small] [--threshold 0.75]
    asr.py DIR [WHICH] --years
    asr.py DIR --accept WHICH

Reads DIR/clips/NNN.wav and NNN.txt (both written by `lesson.py synth`) and DIR/lesson.json for the language.
Writes DIR/asr.json and prints two lists, worst first:
  LISTEN  the transcript is unlike the spoken text (score under the threshold)
  NUMBER  a number that was said is not in the transcript; one wrong figure barely moves the score. Numbers of two
          or more characters only: Whisper writes a lone digit as a homophone too often
Both mean "listen to this clip", not "this clip is wrong": speech recognition mishears terms and numbers too.
A clean run does not prove a term was pronounced well, only that the words and the figures came out in order.

--years   A second listen for the clips that say a year (zh, faster-whisper only). Whisper writes "2020" whether the
          voice said 二零二零 or 二千零二十, so here every token containing a digit is suppressed and the transcript shows
          how the year was read. It can still confuse 四 and 十.
--accept  After listening to reported beats: record their transcripts from asr.json in DIR/asr-accept.json. A clip
          that is heard the same way again is then not reported; a re-synthesized clip that is heard differently is.

WHICH is beat numbers as the player shows them: 3,7,12 or 5-9. The first run downloads the Whisper model.
Exit 0 nothing reported, 1 some beats reported, 2 usage or missing clips.
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import sys
import wave

MLX_REPOS = {"small": "mlx-community/whisper-small-mlx", "medium": "mlx-community/whisper-medium-mlx",
             "large-v3-turbo": "mlx-community/whisper-large-v3-turbo"}
PROMPTS = {"zh": "以下是普通话的句子，夹杂英文术语。", "en": ""}   # generic on purpose: naming the lesson's terms would make it hear them
SPELLED = "以下是普通话的句子，数字一律写成汉字：一九九八年，二零零八年，三千五百，百分之十二。"   # for --years
DIGIT = {c: i for i, c in enumerate("零一二三四五六七八九")} | {"两": 2, "〇": 0}
UNIT = {"十": 10, "百": 100, "千": 1000}
ARABIC = r"\d+(?:\.\d+)?"


def zh_int(s: str) -> int | None:
    """三万 -> 30000, 两万一千六百六十六 -> 21666, 十五 -> 15, 一万亿 -> 10**12, 零五 -> 5 (digit by digit when there
    are no units). Digits may stand where numerals do, the way Whisper writes them: 7620万, 1亿8千万, 1.8亿."""
    if not any(c in UNIT or c in "万亿" for c in s):
        return int("".join(str(DIGIT[c]) for c in s)) if all(c in DIGIT for c in s) else None
    total = wan = section = digit = Decimal(0)
    for tok in re.findall(ARABIC + "|.", s):
        if tok in DIGIT:
            digit = Decimal(DIGIT[tok])
        elif tok in UNIT:
            section += (digit or 1) * UNIT[tok]
            digit = Decimal(0)
        elif tok == "万":
            wan += (section + digit) * 10 ** 4
            section = digit = Decimal(0)
        elif tok == "亿":
            total += (wan + section + digit) * 10 ** 8
            wan = section = digit = Decimal(0)
        elif tok[0].isdigit():
            digit = Decimal(tok)
        else:
            return None
    n = total + wan + section + digit
    return int(n) if n == n.to_integral_value() else None


def digits(text: str) -> str:
    """Write numbers one way, so that 「三百二十五亿美元」, 「325亿美元」 and 「$32.5 billion」 said as such compare equal."""
    def whole(m):
        n = zh_int(re.sub(r"\s", "", m.group(0)))
        return m.group(0) if n is None else str(n)
    text = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text)                          # 7,620 -> 7620
    text = re.sub(rf"\$\s*({ARABIC})", r"\1美元", text)                           # $40 is read, and heard, as 40美元
    text = re.sub(r"(\d+)\s*美元\s*,?\s*(\d{1,2})\s*美分", lambda m: f"{m.group(1)}.{int(m.group(2)):02d}美元", text)
    text = re.sub(r"百分之([零一二两三四五六七八九十百千万亿\d.点]+)", r"\1%", text)
    text = re.sub(r"(?<=[零一二两三四五六七八九十\d])点(?=[零一二三四五六七八九\d])", ".", text)
    text = re.sub(r"(?<=\.)[零一二三四五六七八九]+|[零一二两三四五六七八九](?=\.)", lambda m: "".join(str(DIGIT[c]) for c in m.group(0)), text)
    # digits with units, as Whisper writes large numbers: 7620万, 1.8亿, 1 亿 8 千万, 3亿1500万. Before the numerals-only
    # pass, which would take the 千万 of 8千万 for a number of its own.
    text = re.sub(rf"{ARABIC}(?:\s*[十百千万亿]+(?:\s*{ARABIC}(?=\s*[十百千万亿]))?)+", whole, text)
    text = re.sub(r"[零〇一二两三四五六七八九十百千万亿]{2,}|[二三四五六七八九十](?![一-鿿])", whole, text)
    return re.sub(r"[负付富]\s*(?=\d)", "-", text.replace("−", "-"))            # 付 and 富 are how Whisper writes a spoken 负


MARKUP = r"<#[\d.]+#>|<[a-z][a-z ]*>"   # pause and vocal tags in the spoken text: MiniMax <#0.18#>, Gemini <short pause>


def norm(text: str) -> str:
    text = re.sub(MARKUP, "", text)
    return re.sub(r"[^\w%.\-]|_", "", digits(text).lower())


def unheard(said: str, heard: str) -> list[str]:
    """Numbers in the spoken text that the transcript lacks. A bare single digit is not looked for: Whisper writes
    those as homophones (4 -> 丝, 0 -> 灵) too often for the list to be worth reading. A minus sign that was said must
    be heard, as 负 or as 减; a minus that was only heard is the word 减."""
    def numbers(text):
        return Counter(re.findall(rf"(?:(?<![\d%])-)?{ARABIC}%?", digits(re.sub(MARKUP, "", text))))
    heard = re.sub(r"减\s*(?=[\d零一二两三四五六七八九十])", "-", heard)
    regrouped = re.sub(r"(?<=\d),(?=\d)", "", heard)   # 894,813 heard as 89,4813
    got = numbers(heard) + numbers(regrouped)
    got += Counter({n[1:]: c for n, c in got.items() if n[0] == "-"})
    return sorted(n for n in (numbers(said) - got).elements() if len(n) > 1 and not (n == "10" and "十" in heard))


def year_readings(said: str, heard: str) -> list[tuple[str, str]]:
    """How each year in the spoken text was read, given a transcript made with digit tokens suppressed:
    (year, 'digits' | 'cardinal' | 'unclear')."""
    heard = heard.replace("〇", "零").replace(" ", "")
    out = []
    for year in re.findall(r"(?<!\d)(\d{4})\s*年", said):
        by_digit = "".join("零一二三四五六七八九"[int(d)] for d in year)
        cardinal = re.search(r"[一二两三四五六七八九]千[零一二两三四五六七八九十百]*年", heard)
        out.append((year, "digits" if by_digit + "年" in heard else "cardinal" if cardinal and zh_int(cardinal.group(0)[:-1]) == int(year) else "unclear"))
    return out


def parse_which(spec: str, n: int) -> list[int]:
    picks = []
    for part in spec.split(","):
        lo, _, hi = part.partition("-")
        picks += range(int(lo), int(hi or lo) + 1)
    bad = [i for i in picks if not 1 <= i <= n]
    if bad:
        sys.exit(f"beats {bad} are out of range 1-{n}")
    return picks


def samples(wav):
    """A clip as 16 kHz float samples. The clips are 16-bit mono PCM; decoding them here keeps PyAV (and its version
    drift) out of the path. No silence is added around the clip: on 162 clips it did not raise the mean score and it
    made Whisper write one line as a row of commas (measured 2026-10-12)."""
    import numpy as np
    with wave.open(str(wav)) as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        rate = w.getframerate()
    return pcm if rate == 16000 else np.interp(np.arange(0, len(pcm), rate / 16000), np.arange(len(pcm)), pcm).astype(np.float32)


def transcriber(model: str, lang: str, spelled: bool = False):
    """A function from a clip to its transcript. `spelled` suppresses every token that contains a digit."""
    prompt = SPELLED if spelled else PROMPTS.get(lang, "")
    if sys.platform == "darwin":
        if spelled:
            sys.exit("--years needs faster-whisper: digit-token suppression is not wired up for mlx-whisper")
        import mlx_whisper
        repo = model if "/" in model else MLX_REPOS.get(model, f"mlx-community/whisper-{model}-mlx")
        return lambda wav: mlx_whisper.transcribe(str(wav), path_or_hf_repo=repo, language=lang, initial_prompt=prompt or None)["text"].strip()
    from faster_whisper import WhisperModel
    whisper = WhisperModel(model, device="auto", compute_type="int8")
    more = {}
    if spelled:
        more["suppress_tokens"] = [-1] + sorted(i for tok, i in whisper.hf_tokenizer.get_vocab().items() if any(c in "0123456789" for c in tok))
    return lambda wav: "".join(s.text for s in whisper.transcribe(samples(wav), language=lang, initial_prompt=prompt or None, beam_size=5, **more)[0]).strip()


def said_text(wav: Path) -> str:
    return wav.with_suffix(".txt").read_text(encoding="utf-8").split("\n", 1)[1]   # line 1 is model|voice|speed, or model|voice|direction


def years(clips: list[Path], model: str, lang: str) -> int:
    with_year = [wav for wav in clips if re.search(r"(?<!\d)\d{4}\s*年", said_text(wav))]
    if lang != "zh" or not with_year:
        print("no clip says a year followed by 年: nothing to check")
        return 0
    hear, bad = transcriber(model, lang, spelled=True), 0
    for wav in with_year:
        heard = hear(wav)
        for year, reading in year_readings(said_text(wav), heard):
            bad += reading != "digits"
            print({"digits": f"ok    beat {int(wav.stem)}: {year}年 read digit by digit",
                   "cardinal": f"YEAR  beat {int(wav.stem)}: {year}年 read as a cardinal (drop the space before 年 in `say`)\n  heard: {heard}",
                   "unclear": f"year? beat {int(wav.stem)}: {year}年 not found in the transcript, listen\n  heard: {heard}"}[reading], flush=True)
    print(f"{len(with_year)} clips with a year, {bad} to look at")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir"); ap.add_argument("which", nargs="?")
    ap.add_argument("--model", default="small", help="Whisper size (small, medium, large-v3-turbo) or a model repo")
    ap.add_argument("--threshold", type=float, default=0.75, help="report beats scoring under this (0-1)")
    ap.add_argument("--years", action="store_true", help="check how years were read instead of scoring")
    ap.add_argument("--accept", metavar="WHICH", help="record these beats' transcripts from asr.json as listened to")
    args = ap.parse_args()
    lesson = Path(args.dir)
    clips = sorted((lesson / "clips").glob("[0-9][0-9][0-9].wav"))
    if not clips:
        print(f"no clips in {lesson / 'clips'}: run `lesson.py synth` first", file=sys.stderr)
        return 2
    out, accept = lesson / "asr.json", lesson / "asr-accept.json"
    accepted = json.loads(accept.read_text(encoding="utf-8")) if accept.exists() else {}
    if args.accept:
        if not out.exists():
            print(f"{out} not found: run asr.py first, listen to what it reports, then --accept", file=sys.stderr)
            return 2
        rows = {r["beat"]: r for r in json.loads(out.read_text(encoding="utf-8"))["beats"]}
        picks = parse_which(args.accept, int(clips[-1].stem))
        if missing := [b for b in picks if b not in rows]:
            print(f"beats {missing} are not in {out}", file=sys.stderr)
            return 2
        accepted.update({rows[b]["said"]: rows[b]["heard"] for b in picks})
        accept.write_text(json.dumps(accepted, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{len(picks)} accepted, {len(accepted)} in {accept}")
        return 0
    lang = json.loads((lesson / "lesson.json").read_text(encoding="utf-8")).get("lang", "en")
    wanted = set(parse_which(args.which, int(clips[-1].stem))) if args.which else None
    clips = [wav for wav in clips if not wanted or int(wav.stem) in wanted]
    if args.years:
        return years(clips, args.model, lang)
    hear = transcriber(args.model, lang)
    rows = []
    for wav in clips:
        said, heard = said_text(wav), hear(wav)
        row = {"beat": int(wav.stem), "score": round(SequenceMatcher(None, norm(said), norm(heard), autojunk=False).ratio(), 3),
               "said": said, "heard": heard, "unheard": unheard(said, heard)}
        if said in accepted and norm(accepted[said]) == norm(heard):
            row |= {"score": 1.0, "unheard": [], "accepted": True}
        rows.append(row)
        print(f"{row['beat']:3d} {row['score']:.2f}" + ("  accepted" if row.get("accepted") else "  number " + " ".join(row["unheard"]) if row["unheard"] else ""), flush=True)
    kept = {} if wanted is None or not out.exists() else {r["beat"]: r for r in json.loads(out.read_text(encoding="utf-8"))["beats"]}
    kept.update({r["beat"]: r for r in rows})
    out.write_text(json.dumps({"model": args.model, "beats": [kept[b] for b in sorted(kept)]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    flagged = sorted((r for r in rows if r["score"] < args.threshold), key=lambda r: r["score"])
    for r in flagged:
        print(f"LISTEN beat {r['beat']} ({r['score']:.2f})\n  said : {r['said']}\n  heard: {r['heard']}")
    numbers = [r for r in rows if r["unheard"] and r["score"] >= args.threshold]
    for r in numbers:
        print(f"NUMBER beat {r['beat']} ({r['score']:.2f}): {' '.join(r['unheard'])} not heard\n  said : {r['said']}\n  heard: {r['heard']}")
    print(f"{len(rows)} clips, {len(flagged)} under {args.threshold}, {len(numbers)} more with a number not heard, "
          f"{sum(bool(r.get('accepted')) for r in rows)} accepted, mean {sum(r['score'] for r in rows) / len(rows):.2f} -> {out}")
    return 1 if flagged or numbers else 0


if __name__ == "__main__":
    sys.exit(main())
