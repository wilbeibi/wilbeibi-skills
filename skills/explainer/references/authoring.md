# Authoring a lesson

What to decide before writing, and the rules each beat has to meet. These came from building real lessons, from the
corrections their reader gave, and from cold reads of three of them; each rule names the failure it prevents.

## Intake and scene map

After reading the source, ask about missing choices with concrete alternatives. For a Q-learning notebook, ask whether
the learner knows Bellman backups, and whether they want to trace an update or implement the algorithm. Avoid a generic
questionnaire about every possible preference. Once needed answers arrive, fill in `outline.md` (`init` leaves the
skeleton) before writing any beat:

- **The viewer:** who they are, what they can already explain or use, and the evidence for that starting point.
  Separate confirmed knowledge, mere familiarity with a term, and assumptions about their background.
  Reuse the user's context; ask only when an uncertain prerequisite would change the explanation.
- **The opening problem**, and **the point in one line**: the answer the lesson arrives at.
- What they can do afterward; focus, exclusions, length/depth, language and narration when established.
- **The scene map**, one row per scene:
  `scene | question | raised by | likely misconception | visual action or prediction | source`.
  `question` is what the viewer is wondering as the scene starts, in their words. `raised by` is the earlier scene,
  or `opening`, that left them wondering it. Check what the viewer can infer at that point, not just which terms
  have appeared. Note a missing prerequisite where the scene needs it, before introducing its details.

Use page, section, figure, or notebook-cell locators. Mark invented examples and derived results in the scene map.
The outline is an authoring aid, not a second copy of the subtitles or a new player input. Its questions become the
opening beats, so it has to exist first: written from finished scenes it records the jumps instead of preventing them.
(Failure: a 107-beat lesson whose outline was written after its script.)

## The viewer's thread

A viewer follows one line of thought. At any moment they hold a few things and are wondering one thing. A detail
lands when it answers that; otherwise it is noise, however correct. Write each scene from that state, not from the
source's next section. The corrections behind these rules: the lesson "dives straight into details", and "the
thinking jumps".

- **Say the point early.** By the end of the first scene the viewer has the concrete problem, why the obvious approach
  falls short, and the answer in one line. Details then serve an answer they are waiting to see earned. A title, an
  author and a chapter list give none of this. (Failure: an opening that named the paper and listed its six chapters.)
- **A chain of questions, not a table of contents.** Every scene answers a question the viewer already has, because
  the opening or an earlier scene raised it: that is the `raised by` cell. If nothing raised it, add the beat that
  establishes the missing uncertainty, move the scene, or cut it. Merely appending a question to announce the next
  topic does not establish a need. Check whether the viewer could ask it before seeing that announcement.
  An opening that only works as a list item gives
  the gap away: "另一个模型是…", "还有一种…", "最后是…", "the paper then turns to…".
- **Open from what they hold.** A scene's first beat is the question in the viewer's words, the belief about to be
  corrected, or the last result turned into a question. Never a term, a model's name or a figure. Its last beat says
  what was found and what that leaves open, which is the next scene's question. (Failure: a chapter that opened
  "A 和 B 两家公司，上季末都是 1,000 个客户…"; its question, "客户数一样，生意就一样吗？", was only in the heading.)
- **Purpose in the first beat, not the last.** Why this model, metric or case is needed here comes before its name and
  its parts. (Failure: three industry measures in a row, each opened by its name: "行业稳不稳，论文看 market share
  instability", "集中度呢？HHI 是…". The viewer was asking why airlines earn nothing; that came four scenes later.)
- **Old before new.** Start each beat from something already on the table and end on the new thing. Introduce an
  object and its role before its equation or its value, and define a term where it first appears. Do not point back
  across scenes: say again in a clause what it was. (Failure: "CBCV 的三个驱动", six scenes after the label was named
  once and never spelled out.)
- **One name, one meaning.** A term keeps its name, a roadmap keeps its wording, and a word the viewer already holds
  keeps the sense they hold it in. (Failures: CLV became LTV without a word; "value creation" meant price minus cost
  to a viewer who held it as ROIC minus WACC.)
- **Recall what they understand; bridge what they only recognize.** A known concept costs a clause, not a new lesson.
  Having read a lesson, seen a symbol, or heard a term is not proof that the viewer can use it here.
  Supply the missing relation before relying on it. (Failures: re-teaching a familiar steady-state value / PVGO split;
  mentioning amortization once, then assuming the viewer understands capitalization.)
- **One step per beat, and none left out.** A figure the viewer cannot rebuild from what was said reads as a mistake.
  (Failure: "扣 $500 的 CAC，剩 $2,838" straight after $3,486; the new customer's own $3,338 was never said.)
  Before using an input, establish what it measures, what it includes, and whether it is reported, assumed, or estimated.
  If reconstructing it is outside scope, explain its basis and point to the source method. Correct arithmetic cannot
  explain an unexplained input. (Failure: a Microsoft investment total appeared before its intangible component's
  estimation basis; the viewer could subtract the numbers but could not assess them.)
- **Close what you open.** The closing scene answers the opening's question in the opening's words. An opening case
  comes back; a quiz, a real company's number and a "we will return to this" each get their verdict. (Failures: a
  Blockbuster opening never mentioned again; "哪条路更持久？" followed by a scene on government policy.)

An experiment or case needs three things before its settings, parameters or results:

- **Purpose:** what uncertainty it resolves, and why that matters here.
- **Comparison:** what is changed or compared, and what stays the same.
- **Observation:** what will be measured, and what different outcomes would mean.

"We want to find out which method learns a useful policy sooner. Both get the same task and interaction budget. We
will compare their evaluation returns as training progresses." Only then the environment, update rules, seeds and
plots. Before a plot, name its axes and the comparison to look for. After a result, return to the question: what it
supports and what remains open. Use the source's stated purpose; label inferred intent as yours.

Whether the thread holds is not the author's to judge: they know where the script is going. `lesson.py thread DIR`
prints every scene's opening beat under the beat before it and the question the scene map gives it, and writes the
pages for a reader who has seen neither the source nor the outline (`cold-read.md`). Do it on the finished script,
before drawing the scenes: rewording a beat is free then and costs a clip later.

## Pilot the hardest scene

Choose the scene most likely to fail: dense arithmetic, long labels, a message trace, or an interactive model.
Start with that scene alone in the initialized lesson: replace starter placeholders, and include only its script,
data, markup, and hooks. Write its beats before its markup. This makes ordinary `check` work without new tooling.

Run `lesson.py check DIR`, then `lesson.py shots DIR 1-N` (replace N with the pilot's beat count).
Read every pilot screenshot. Try the default and extreme control values, keyboard operation, and leaving/re-entering
the scene. Fix readability and the explanation before adding the remaining scenes. Split crowded content instead of
shrinking labels. Reuse the passing scene, then write the remaining beats before expanding the markup.
Do not synthesize pilot narration; the script is still changing. A narrow edit to an existing lesson only needs a pilot
when it introduces a new layout or interaction risk.

## Shape

- **The source's argument is the spine; its table of contents is not.** Keep its claims, their dependencies and the
  agreed focus. Order the scenes by what the viewer needs next, and record why where that departs from the source.
  A section the thread never reaches is cut, or named in the closing scene as further reading; it is not appended.
  What the lesson builds, it uses: a tool that no later scene picks up is cut too.
  A worked example illustrates a step of the argument; it is never the lesson. (Failures: a "Netflix walkthrough"
  delivered when the request was the paper; a lesson that announced "这一课按论文的顺序走" and became a list; three
  scenes on market size and the adoption curve, after which the valuation took its customer count as a bare figure.)
  A source without a continuous case does not need an invented one. Follow its argument using local examples,
  contrasts, diagrams, or stepwise reasoning. Add an illustrative case only when it resolves a specific difficulty
  within the user's scope, and label its assumptions; it supplies no evidence for the source's claims.
- **Opening:** the concrete situation, why the obvious approach is insufficient, the question to resolve, and the
  answer in one line. Take the question from the source when it states one. A roadmap comes after these, if at all.
- **One scene per complete idea.** Split where the viewer's question changes. A longer calculation may need several
  beats to make each inference visible; do not compress away those steps to meet a beat quota.
- **Closing scene:** three takeaways, the first answering the opening's question, a restart button, and what to do
  next. No new material.
- 40–110 beats has worked for full lessons (about 6–20 minutes narrated); use the agreed scope, not a minimum quota.

## Each beat

- **Plain question first, term second.** "How much of the price is a bet?" before "PVGO".
  Scene headings are questions the scene answers.
- **Make the missing relation visible.** Use the source's example, a contrast, a diagram, or a worked step that answers
  the viewer's current question. A number or invented case is not required for every abstract claim.
- **Every beat changes the screen**: a reveal, a highlight, a new row. `check` warns when one does not.
- **Do not put the narration on screen twice.** The subtitle carries the sentence; the scene carries the structure
  (the table, the grid, the formula with one part lit).
- **One highlight at a time.** Move it with the beat.
- Subtitles are at most two lines (about 92 units: CJK counts 1, ASCII 0.5). Split the sentence rather than shrink it.

## Language

- In a `zh` lesson, domain terms stay in English everywhere they are visible (subtitles, headings, labels): Q-learning,
  TD target, ROIC, NOPAT, leader, term. Chinese carries the explanation. Do not translate a term the reader will meet
  in the source untranslated.
- Controls always have a visible label. Chapter buttons show names, never bare numbers.

## Numbers

- Type no number twice. Inputs live in `data.js`; everything derived is computed there and reaches the page through `V`
  (`${V.key}` in beats, `<span data-v="key">` in scenes), or through a pure model for interactive results.
- Every numeral on screen must be findable in `source.txt` or listed in `numbers.allow` with where it comes from.
  The gate compares by value (`0.9` matches `.9`, `150,000` matches `150_000` and `150k`).
- **Label what you made.** A simulation rerun in the page, an illustrative calculation, a made-up example: each carries a
  visible `<span class="tag">`. A reader must be able to tell the source's results from yours.
- **Guard narrated claims.** If a sentence says "Q-learning's path is shorter on every seed", `data.js` throws when that is
  no longer true. Do not pick a seed until the textbook picture appears; report what the run shows.
- **Do not answer what the source leaves to the learner.** If the notebook says "predict, then run it", the lesson asks
  for the prediction and sends the viewer to the notebook.

## Interaction

- At least two pauses (`W('…')`), each asking the viewer to commit before the reveal: compute a value (`quiz`), predict
  a curve, pick an option. A pause beat shows a visible way to continue (`<button class="btn" data-go>`).
- **A pause screen must not show its answer.** Put the answer in a layer that appears on the next beat, and look at
  every pause with `shots DIR waits`. (Failure: a guess screen whose chart already drew the bar the viewer was asked
  to guess.) `check` warns when a pause already shows a figure the next line says for the first time. It compares
  numerals of two or more characters only: an answer given away in words, by a colour or by a drawn shape is yours
  to see, and a starting value that is not the answer can trigger it.
- Use the source's own exercises and self-checks as the pause questions where it has them.
- When changing an input teaches a causal relationship, let the viewer predict, then change it and inspect the result.
  Keep one pure model in `data.js`; derive the picture, values, and result sentence from the same output.
  State what stays fixed and where the simplified model stops applying. See the `fmodel` gallery pattern.
- Check interactive outcomes separately: `check` and `numbers` visit scripted defaults, not every control setting.
  Test boundaries and any threshold in the model; verify the displayed result agrees. Keep fixed narration valid
  across choices, and reset exploratory inputs on beat entry so seeking remains reproducible.

## Revisions

Edit the source parts and rebuild: content in `script.js`, arithmetic in `data.js`, pronunciation in `speak.yaml`.
Keep `outline.md` current when the learning goal or scene coverage changes, and rerun `thread` when scenes move or an
opening changes. Do not patch generated HTML as the source.

## Narration

- Finish every beat and read the whole `say` preview before synthesizing anything. Rewording after synthesis is the
  expensive path.
- Pronunciation is fixed in `speak.yaml`, never by changing the subtitle: `say:` pairs (longer strings first) for
  hyphenated and CamelCase terms, initialisms and exercise codes.
- **Probe before writing pairs for numbers.** Do not list every figure in `say:`. Synthesize three beats, listen, and
  write a pair only for what was misread. On the known-good Chinese voice below, `$900`, `$894,813`, `28,426`, `98.71%`
  and `0.037` were read correctly. Four classes were misread, and `rules: zh` (set by `init --lang zh`) rewrites them:

  | Written | Heard without the rule | With `rules: zh` |
  |---|---|---|
  | `$265 billion`, `180 million` | "265 美元 billion" | 两千六百五十亿美元, 一亿八千万 |
  | `2020 年` | a cardinal, 二千零二十年 | `2020年`, read digit by digit |
  | `−5%`, `900 − 247` (U+2212) | the sign is dropped | 负5%, 900减247 |
  | `1.5x` | "1.5 X" | 一点五倍 |

  `say:` pairs run before the rules and win. `say` and `check` print `warn speech` for a line that still holds one of
  these, or an `&` (skipped by the voice) or an ASCII hyphen before a figure (never tried on the voice). An amount the
  rule cannot write as a whole number (`$1.2345678 million`) is left for a pair. Other voices and languages have no
  rules: probe them.
- **Know the cost before `synth`.** `say` prints characters and, with `price` in `speak.yaml` (USD per million billed
  characters), the estimate for all beats and for those without a fresh clip. MiniMax on OpenRouter bills a non-ASCII
  character as two: a 107-beat Chinese lesson of 4,979 characters is about $0.47. The local turnpike does not meter
  `/audio/speech`, so `turnpike stats` shows nothing for it; the provider's own usage page is the record.
- Slow formula and arithmetic beats down a notch with `speed:`; add `pause_after:` for set-up phrases.
- Synthesize three beats first, then `changed`. Clips are cached per beat on (model, voice, speed, spoken text).
- `asr.py` reports where to listen, not what is wrong. `LISTEN`: the transcript is unlike the spoken text. `NUMBER`:
  a number that was said is missing from the transcript, which the score alone hides. `asr.py DIR --years`: a second
  pass that shows whether each year was read digit by digit (Whisper writes "2020" either way in the first pass).
  Whisper mishears English terms inside Chinese speech ("greedy" → "gradient") and writes some numbers as homophones
  (10 → 实); a term misheard the same way in every beat is the recognizer, not the voice. After listening,
  `asr.py DIR --accept 12,40` records those transcripts in `asr-accept.json`; the beats are reported again only if a
  new clip is heard differently.
- Known-good Chinese voice: `minimax/speech-2.8-turbo`, `Chinese (Mandarin)_Radio_Host`, speed 1.0–1.15.

## Before handing over

Ensure the cold read was done and answered, `check` is clean, contact sheets are read (the pause screens among them),
and `numbers` is clean. The reply says what the cold read still reports (or that none was done), which numbers are the
source's and which are yours, what was not verified, what the narration cost, and where the output files are.
