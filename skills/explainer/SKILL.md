---
name: explainer
description: Turn a paper, notebook, chapter, or design doc into a narrated, self-paced HTML lesson — one self-contained file with chapters, subtitles, worked numbers, pause-and-predict questions, and optional TTS narration; the finished lesson can also be filmed into one MP4. Use when asked for a tutorial/teaching video "as HTML", an explainer or lesson for a source, or to preview/teach a topic in finance, RL/ML, or distributed systems. Do NOT use for an in-chat diagram (use show-me), a chart of real data (use dataviz), a single illustration (use sketch-concept), or animation-first math video (this is not Manim).
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
already hold, what they are wondering at this moment, and what would answer it. Before any beat is written,
`outline.md` gives every scene the question the viewer arrives with and the earlier scene that raised it. A scene
opens from that question, never from a term, a model's name or a figure, and says what it is for before its details.
Recall established knowledge in a clause; a term appearing earlier does not establish understanding. Each transition
comes from an unresolved question, not a question appended to justify the next topic. Use source examples where they
help; an abstract source does not require an invented case. The rules are in `references/authoring.md`.
Whether the thread holds is judged by a reader who has not seen the source (`references/cold-read.md`), not by the author.

## Order of work

1. **Read, then ask**, as above. Extract source text in scratch space if needed; retain page or section locators.
2. After intake, `lesson.py init DIR --title "…" --lang zh|en [--slug s]` scaffolds an empty directory.
   Then save the source text to `DIR/source.txt` and fill in `DIR/outline.md`, the brief and the scene map, before
   writing any beat. Follow the source's argument, not its table of contents; examples illustrate it, never replace it.
   `init DIR --gallery` gives the working pattern gallery (finance, RL, distributed systems) to copy from.
3. **Pilot the hardest scene** before expanding the lesson: its beats, data, markup, and hooks. Run `check`, take shots
   of all its beats, and inspect them. Exercise any controls. See the pilot procedure in `references/authoring.md`.
4. **`data.js`**: numbers come from here, through `V` for fixed text or a pure model for interactive results.
   Nothing numeric is typed twice.
   Claims that depend on a computed or simulated result get a `throw` when they stop holding.
5. **`script.js`**: chapters → scenes → beats. One beat = one subtitle = one spoken sentence.
   After the pilot, finish the full script and pass the thread gate on it before expanding the markup.
6. **`scenes.html` + `hooks.js`**: one `<section class="scene" id="…">` per scene; `data-at`/`data-to` reveal by beat;
   `HOOK.<id> = step => {…}` for anything that changes with the beat.
7. Gates, in this order. Do not skip ahead; each one is cheaper than the next.

| Gate | Command | Passes when |
|---|---|---|
| thread | `lesson.py thread DIR`, then a cold read of `DIR/thread/` (`references/cold-read.md`) | a reader who has seen neither the source nor the outline reports no scene as `no` and says the end answered the opening's question; their five worst seams are fixed, and what remains is named in the handover |
| layout | `lesson.py check DIR` | `CHECK OK`: no overflow, overlap, clipped text, 3-line subtitle, dead beat |
| eyes | `lesson.py shots DIR [BEATS]`, `shots DIR waits`, then **read the contact sheets** | you looked; the checker cannot see a label sitting on a line, or a pause screen that gives its answer away in words or a drawing |
| numbers | `lesson.py numbers DIR` | every numeral on screen is in `source.txt` or `numbers.allow` (`number<TAB>reason`) |
| script | `lesson.py say DIR` | the spoken text reads right aloud and no `warn speech` line is left; fix in `speak.yaml`, not by editing subtitles |
| voice | `lesson.py synth DIR 1-3`, then `synth DIR changed` | clips exist; only changed beats are re-synthesized |
| ears | `asr.py DIR`, then `asr.py DIR --years` | you listened to every `LISTEN`, `NUMBER` and `YEAR` beat; resynthesize what is actually wrong, `--accept` the rest |
| final | `lesson.py mix DIR`, then `check DIR` | narrated `CHECK OK`; hand over `out/<slug>.html` + `out/<slug>-narration.mp3` together |

Narration is optional: a silent lesson stops after the numbers gate. Ask before the voice gate if no TTS key or budget
is established; it is a paid API call. `say` and `synth` print the character count and, with `price` in `speak.yaml`,
the estimated cost: tell the user that figure before the first `synth`. Label requests in `speak.yaml` `headers:`.

`lesson.py video DIR [BEATS]` films the finished lesson into one `out/<slug>.mp4` (1280×720, narration included) for
watching or sending as a single file. Nothing can be clicked in a film: each pause is held for `--hold` seconds (3) and
then answers itself. Run it after the final gate, and only when a video file is wanted; the HTML stays the lesson.
A 14-minute lesson took under 5 minutes on 4 cores, because a frame is photographed only when the stage changed.
If the film stands still where the page moves, rerun with `--every-frame`; `--scale 1.5` gives 1920×1080.

## Lesson directory

```
lesson.json   {title, slug, lang, speed}        speed = default playback rate (0.85 for dense material)
outline.md    brief (viewer, what they hold, opening problem, the point) + scene map (question, raised by, …);
              written before script.js, read by `check` and `thread`
data.js       pure JS, no DOM: inputs, derived numbers, V = {key: 'formatted string'}
script.js     const SCRIPT = [{ch, scenes: [[sceneId, [beat, W(beat), …]]]}]   beats interpolate ${V.key}
scenes.html   <section class="scene" id="sceneId"> … <span data-v="key"></span> …
hooks.js      runs once at load; HOOK.sceneId = step => {…}; quiz('inputId','fbId', answer, tolerance)
style.css     optional, lesson-specific
speak.yaml    model, voice, speed_default, speed{beat: rate}, say[[from, to]], rules, price, pause, pause_after[], headers, key_env
source.txt, numbers.allow                       inputs to the numbers gate
asr-accept.json                                 transcripts you listened to and accepted (`asr.py --accept`)
clips/ narration.json out/ shots/ thread/ asr.json   generated
```

## Hard rules

- Beat numbers are 1-based everywhere a human sees them (player corner, `check`, `shots`, `synth`, `speak.yaml speed:`).
  `step` inside a scene is 0-based: `data-at="0"` is the scene's first beat.
- A scene is 1280×600 with 64px side margins. Position blocks with `class="layer" style="top:…px"`; two blocks that take
  turns in one place are two layers with the same `top` and complementary `data-at`/`data-to`.
- Hooks are idempotent: the screen for a step is the same however the viewer got there (seek, back, chapter jump).
- Every beat changes something on screen. Subtitles are at most two lines.
- Content you made up or computed yourself (examples, simulations, illustrative arithmetic) carries
  `<span class="tag">…</span>` saying so. Content from the source does not.
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
  The misreadings were heard on the Radio Host voice only. A hyphen before a figure was never synthesized.
- The pause warning compares numerals: on 16 pause screens it fired once, on a starting value that was not the answer.
  An answer shown in words or as a shape passes it.
- `asr.py` `NUMBER` skips single digits and still reports numbers Whisper wrote as homophones (7 of 340 beats).
  `--years` has confirmed digit-by-digit years on clips; its "cardinal" verdict is tested on text only.
- `say`'s cost is an estimate from a measured price, not a bill.
- The thread gate, one cold reader each on three finished lessons: the one whose scene map came first drew 7 `yes`,
  7 `partly`, 1 `no` over 15 scenes; two that followed their paper's section order drew 6/14/6 over 26 and 2/18/9
  over 29. The readers named 18 of the 22 jumps the author had listed beforehand and rated two of the other four
  scenes `yes`. They also found what the author's reread had not: a skipped step in a sum, a term renamed, an opening
  case never closed, three scenes of method the lesson never used.
- One rewrite to these rules, the opening eight scenes of the 26-scene lesson redone as seven (two merged, the order
  changed, the last given only a new first beat): 1 `yes`, 5 `partly`, 2 `no` before, 3/3/1 from a new reader after.
  The `no` that remained was a list kept from the paper, so one round does not finish it. Two readers were never compared on one script, and nothing checks that a reader wrote `want` before
  opening the page: a count is a reading, not a score. The read sees subtitles and headings, not the picture.
- `check`'s outline warnings see a missing row, question or `raised by`. They cannot tell an outline written after
  the script, which is why the cold read is the gate.

The macOS branch of `asr.py` (mlx-whisper, no `--years`) and the English voice name in the starter `speak.yaml` are
untested.
