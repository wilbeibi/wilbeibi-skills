---
name: explainer
description: Turn a paper, notebook, chapter, or design doc into a narrated, self-paced HTML lesson — one self-contained file with chapters, subtitles, worked numbers, pause-and-predict questions, and optional TTS narration; the finished lesson can also be filmed into one MP4. Use when asked for a tutorial/teaching video "as HTML", an explainer or lesson for a source, or to preview/teach a topic in finance, RL/ML, or distributed systems. Do NOT use for an in-chat diagram (use show-me), a chart of real data (use dataviz), a single illustration (use sketch-concept), a post or explorer showing how your own system's mechanism works (use mechanism-viz), or animation-first math video (this is not Manim).
compatibility: uv (scripts run as uv scripts, Python 3.10+); node for evaluating the lesson script (22 or newer for `video`); Chromium or Chrome for the per-beat check, screenshots and `video`; ffmpeg for narration and `video`; an OpenAI-compatible /audio/speech endpoint for narration (optional); asr.py downloads a Whisper model on first run.
---

# explainer

A lesson is a directory of small parts that `scripts/lesson.py` assembles into one HTML file (plus one mp3 if narrated).
The player, layout checks, and narration plumbing are fixed; you write the content. Read `references/authoring.md`
before intake and storyboarding, and `references/patterns.md` when choosing how to draw a scene.

## Read, then ask

Read the supplied material first: its main question, argument, prerequisites, and exercises. Inspect figures and tables
that carry the explanation. If the source is inaccessible, ask for the missing material rather than inventing its contents.
Briefly state what the material covers, then ask only unanswered questions that change the lesson: learner background,
learning goal or focus, and desired length/depth. Ground the questions and suggested answers in what you read.
Batch these into one short round; ask about language or narration only when needed. Reuse answers already given.
Wait for needed answers before storyboarding or production. If the brief is complete, proceed; if the user explicitly
delegates these choices, state your assumptions and proceed. Do not turn intake into repeated approval of every stage.

## Follow the viewer's thread

A lesson is one line of thought, not the source's sections in order. Design it from the viewer's side: what they
already hold, what they are wondering at this moment, and what would answer it. Its chapters are a chain: each is
named by the question it answers, and each after the first asks what the last answer leaves short. Before any beat
is written, `outline.md` gives that chain, and gives every scene the question the viewer arrives with and the earlier
scene that raised it. A scene opens from that question, never from a term, a model's name or a figure, and says what
it is for before its details. What the viewer already holds is recalled in a clause, not taught again. A title or a
list of topics establishes none of this. The rules and the failures behind them are in `references/authoring.md`.
Whether the thread holds is judged by a reader who has not seen the source (`references/cold-read.md`), not by the
author. Whether the lesson says what the source says is judged by a second reader who has it
(`references/source-read.md`): the picture is rendered from code, so every digit on it is the digit that was typed,
and that proves nothing about the sentence. A lesson that drops a condition teaches the wrong rule, so every scene's
row in the scene map says what it leaves out.

## Order of work

1. **Read, then ask**, as above. Extract source text in scratch space if needed; retain page or section locators.
2. After intake, `lesson.py init DIR --title "…" --lang zh|en [--slug s]` scaffolds an empty directory.
   Then save the source text to `DIR/source.txt` and fill in `DIR/outline.md`, the brief with its chapter chain and the scene map, before
   writing any beat. Follow the source's argument, not its table of contents; examples illustrate it, never replace it.
   `init DIR --gallery` gives the working pattern gallery (finance, RL, distributed systems) to copy from.
3. **Pilot the hardest scene** before expanding the lesson: its beats, data, markup, and hooks. Run `check`, take shots
   of all its beats, and inspect them. Exercise any controls. See the pilot procedure in `references/authoring.md`.
4. **`data.js`**: numbers come from here, through `V` for fixed text or a pure model for interactive results.
   Nothing numeric is typed twice.
   Claims that depend on a computed or simulated result get a `throw` when they stop holding.
5. **`script.js`**: chapters → scenes → beats. One beat = one subtitle = one spoken sentence.
   After the pilot, finish the full script and pass the thread and source gates on it before expanding the markup.
6. **`scenes.html` + `hooks.js`**: one `<section class="scene" id="…">` per scene; `data-at`/`data-to` reveal by beat;
   `HOOK.<id> = step => {…}` for anything that changes with the beat.
7. Gates, in this order. Do not skip ahead; each one is cheaper than the next.

| Gate | Command | Passes when |
|---|---|---|
| thread | `lesson.py thread DIR`, then a cold read of `DIR/thread/` (`references/cold-read.md`) | a reader who has seen neither the source nor the outline reads the chapter names as an argument, reports no scene as `no` and says the end answered the opening's question; their five worst seams are fixed, and what remains is named in the handover |
| source | a source read of the same `DIR/thread/` by a second reader given `source.txt` and the scene map (`references/source-read.md`) | no claim is `invented`; every `stretched` one is reworded to the source's strength or says the gap aloud; what a scene leaves out that would mislead is said in the lesson, the rest is in the scene map's `leaves out` cell |
| layout | `lesson.py check DIR` | `CHECK OK`: no overflow, overlap, clipped text, 3-line subtitle, dead beat |
| eyes | `lesson.py shots DIR [BEATS]`, `shots DIR waits`, then **read the contact sheets** | you looked; the checker cannot see a label sitting on a line, or a pause screen that gives its answer away in words or a drawing |
| numbers | `lesson.py numbers DIR` | every numeral on screen is in `source.txt` or `numbers.allow` (`number<TAB>reason`) |
| script | `lesson.py say DIR` | every beat has its direction, `D('direction', beat)`, written by the rules in `references/authoring.md`; the preview reads right aloud in sequence and no `warn speech` or `warn delivery` line is left; fix pronunciation in `speak.yaml` and delivery in the direction, not by editing subtitles |
| voice | `lesson.py synth DIR 1-3`, then `synth DIR changed` | clips exist; only changed beats are re-synthesized |
| ears | `asr.py DIR`, `asr.py DIR --years`, then `say DIR` | you listened to every `LISTEN`, `NUMBER`, `YEAR` and `warn pace` beat; resynthesize what is actually wrong, `--accept` the rest |
| final | `lesson.py mix DIR`, then `check DIR` | narrated `CHECK OK`; hand over `out/<slug>.html` alone: the narration is embedded in it (see Publish) |

Narration is optional: a silent lesson stops after the numbers gate. Ask before the voice gate if no TTS key or budget
is established; it is a paid API call. `say` and `synth` print the estimated minutes of sound and, with `price_audio`
in `speak.yaml`, the estimated cost: tell the user that figure before the first `synth`. Label requests in
`speak.yaml` `headers:`. The voice is Gemini with a direction per beat; how to write one is in
`references/authoring.md` under Narration, and it is the part of the narration the owner cares about most.

`lesson.py video DIR [BEATS]` films the finished lesson into one `out/<slug>.mp4` (1280×720, narration included) for
watching or sending as a single file. Nothing can be clicked in a film: each pause is held for `--hold` seconds (3) and
then answers itself. Run it after the final gate, and only when a video file is wanted; the HTML stays the lesson.
A 14-minute lesson took under 5 minutes on 4 cores, because a frame is photographed only when the stage changed.
If the film stands still where the page moves, rerun with `--every-frame`; `--scale 1.5` gives 1920×1080.

## Publish

The deliverable is one file. `build` and `mix` write the MP3 into the page as a `data:` URI, so `out/<slug>.html`
plays, seeks and subtitles on its own (a 12 MB narration makes a 16.6 MB page that opened in 2 s from disk).
The page header names the lesson directory it was built from: that directory is what gets edited, never the page.
Do not run SingleFile or monolith on it; there is nothing external left to inline.

```
r2 pri -f out/<slug>.html            # p.wilbeibi.com/<slug>.html, flat, same URL on every re-upload
r2 link <slug>.html --ttl <days>     # off-tailnet: the one link carries the whole lesson
r2 pri -f out/<slug>.mp4             # only when a film was asked for; it is a separate format, not a companion
```

`--no-embed` on `build`, `check` or `mix` restores the two-file output (`<slug>.html` + `<slug>-narration.mp3` beside
it) for a host that cannot take a 16 MB page. Experiments and comparisons go under `experiments/<name>-YYYYMMDD/`
with an `index.html` opened by its full path: the gateway has no directory index.

## Lesson directory

```
lesson.json   {title, slug, lang, speed}        speed = playback rate of the page and the film: 1 (0.85 on the fallback voice)
outline.md    brief (viewer, what they hold, opening problem, the point, chapter chain) + scene map (question, raised by, …, leaves out);
              written before script.js, read by `check` and `thread`
data.js       pure JS, no DOM: inputs, derived numbers, V = {key: 'formatted string'}
script.js     const SCRIPT = [{ch, scenes: [[sceneId, [beat, W(beat), D('direction', beat), …]]]}]   beats interpolate ${V.key}
scenes.html   <section class="scene" id="sceneId"> … <span data-v="key"></span> …
hooks.js      runs once at load; HOOK.sceneId = step => {…}; quiz('inputId','fbId', answer, tolerance)
style.css     optional, lesson-specific
speak.yaml    model, voice, say[[from, to]], rules, price_audio, pause, pause_after[], headers, key_env
              (the MiniMax fallback, assets/speak-minimax.yaml: speed_default, speed{beat: rate}, price)
source.txt, numbers.allow                       inputs to the numbers gate
asr-accept.json                                 transcripts you listened to and accepted (`asr.py --accept`)
clips/ narration.json out/ shots/ thread/ asr.json   generated; out/<slug>.html is the deliverable, out/<slug>-narration.mp3 its input
```

## Hard rules

- Beat numbers are 1-based everywhere a human sees them (player corner, `check`, `shots`, `synth`, `speak.yaml speed:`).
  `step` inside a scene is 0-based: `data-at="0"` is the scene's first beat.
- A scene is 1280×600 with 64px side margins. Position blocks with `class="layer" style="top:…px"`; two blocks that take
  turns in one place are two layers with the same `top` and complementary `data-at`/`data-to`.
- Hooks are idempotent: the screen for a step is the same however the viewer got there (seek, back, chapter jump).
- Every beat changes something on screen. Subtitles are at most two lines.
- Content you made up or computed yourself (examples, simulations, illustrative arithmetic) carries
  `<span class="tag">…</span>` saying so. Content from the source does not. The closing scene says in one `.small`
  line that an AI made the lesson from the source, that its figures were checked against it, and that tagged content
  is the author's own.
- A claim the source read marks `invented` is fixed in the sentence or the picture, never by adding to `source.txt`
  or `numbers.allow` until it passes.
- Never print or copy the TTS key. `synth` reads it from the environment (`key_env`, or `--env-file`).

## URL modes of the built page

`?check` runs the self-check and writes `#lesson-report` (what `lesson.py check` reads) · `?beat=N` opens on beat N ·
`?still` renders without transitions (what `shots` uses) · `?render=MS` never pauses and holds each pause beat MS
milliseconds instead (what `video` uses).

## What is and is not verified

`check`, `thread`, `shots`, `numbers`, `say`, `synth`, `mix`, `video`, and `asr.py` (Linux, faster-whisper) have each run
end to end on a real lesson. What the newer checks do and do not establish (measured 2026-10-12 on four Chinese lessons):

- `video`: on a 107-beat lesson the picture, the sound and the timeline ended within 0.05 s of each other, every beat
  appeared at most one frame late, and 14 minutes in the picture and the sound were the same beat. Two renders of the
  same beats gave identical frames; `--every-frame` differed from the default in 13 pixels by 1/255, cause not found.
  A lesson that draws on a canvas is photographed every frame (not tried on a real one); SMIL animation and `<video>`
  do not follow the film's clock. Linux only so far.
- `rules: zh` reproduced every hand-written pair of two finished lessons (26 pairs, 210 beats, same spoken text).
  The misreadings were heard on the Radio Host voice; the English magnitude word and the `x` multiplier on Gemini
  Charon as well. A hyphen before a figure was never synthesized. The unit of a plain dollar amount went wrong on
  Charon only (12 of 17 beats in one lesson), so that rewrite runs on a Gemini voice only.
- The pause warning compares numerals: on 16 pause screens it fired once, on a starting value that was not the answer.
  An answer shown in words or as a shape passes it.
- `asr.py` `NUMBER` skips single digits and still reports numbers Whisper wrote as homophones (7 of 340 beats) or as
  a decimal in Chinese numerals (十五点三七 for 15.37). Neither list sees a wrong unit: of 12 beats where 美元 was
  read 元, 块 or 刀, 11 scored 0.86 to 0.99 and one was listed. Read every heard line after a full `synth`.
  `--years` has confirmed digit-by-digit years on clips; its "cardinal" verdict is tested on text only.
- `say`'s cost is an estimate, not a bill. On the Gemini voice it guesses the seconds from the text (11 beats:
  2.0 minutes guessed, 1.9 made; 109 beats: 18.6 guessed, 18.9 made); `synth` then prices the seconds it made, and
  the key's usage agreed with those totals to the cent, on the day's test calls and on a whole lesson ($0.30).
- The directed Gemini voice (2026-10-13): one whole Chinese lesson was voiced with it, 109 beats and 18.9 minutes,
  through `say`, `synth`, `asr.py`, `--years`, `mix` and `video`. The film ran 19:05; picture, sound and
  timeline ended within 0.01 s of each other and every beat appeared at most one frame late.
  Nobody had listened to the whole of it when this was written, so whether 109 separately requested clips sound
  like one reading is still not known. On the 109 clips: mean loudness −15.0 to −21.8 dB (median −17.5), up to
  4.8 dB between one beat and the next, 0.1 to 0.5 s of silence at each end, 44 touching full scale; nothing is
  normalised. The clips the owner chose came from Google's own endpoint; the tool calls the same model through
  OpenRouter.
- The direction rules rest on one voice (Charon), four beats and one take per wording for pace, and four directions
  the owner heard. A short direction was never compared with the two-part form. `warn pace`'s 1.6 and 0.6 came
  from the spread of 109 MiniMax clips (0.76 to 1.53 times the median). On the Gemini lesson they named 3 of 109:
  two computations slowed on purpose (1.8 and 2.2) and one direction that had doubled its beat. With that one
  rewritten, the other 107 run 0.69 to 1.40. Sulafat and Sadaltager were heard on one beat each.
- The thread gate, one cold reader each on three finished lessons: the one whose scene map came first drew 7 `yes`,
  7 `partly`, 1 `no` over 15 scenes; two that followed their paper's section order drew 6/14/6 over 26 and 2/18/9
  over 29. They found what the author's reread had not: a skipped step in a sum, a term renamed, an opening case
  never closed, three scenes of method the lesson never used.
- One rewrite to these rules, the opening eight scenes of the 26-scene lesson redone as seven (two merged, the order
  changed, the last given only a new first beat): 1 `yes`, 5 `partly`, 2 `no` before, 3/3/1 from a new reader after.
  The `no` that remained was a list kept from the paper, so one round does not finish it. Two readers were never
  compared on one script, and nothing checks that a reader wrote `want` before opening the page: a count is a
  reading, not a score. The read sees subtitles and headings, not the picture.
- The chapter chain, four readers shown one first screen each: both lessons whose chapters were the paper's section
  nouns drew `topics`; Ploto's five names and seven question names drafted for the 26-scene lesson were each read
  back as an argument. In the drafted set the reader had to guess two names cut too short, one with no subject and
  one pointing at a ratio no earlier name gave. No lesson has been written from a chain yet. The control bar took
  seven names of 42 characters and refused seven of 52; `check` reports the overflow.
- `check`'s outline warnings see a missing row, question or `raised by`, and a chapter whose name the chain's lines
  do not contain. They cannot tell whether one question follows from the last, or an outline written after the
  script, which is why the cold read is the gate. Nothing reads the `leaves out` cell.
- The source read has not been run on any lesson. It was written (2026-10-13) after a public thread on AI-made
  explainer videos: one maker with a pipeline reported agents inventing figures to fill a data panel, and a reader
  of the thread named simplifications the author did not know they had made. `numbers` would have passed both.

The macOS branch of `asr.py` (mlx-whisper, no `--years`) and an English lesson on either voice are untested.
