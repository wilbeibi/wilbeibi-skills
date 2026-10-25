# Authoring a lesson

What to decide before writing, and the rules each beat has to meet. These came from building real lessons, from the
corrections their reader gave, and from cold reads of three of them; each rule names the failure it prevents.

## Intake and scene map

After reading the source, ask about missing choices with concrete alternatives. For a Q-learning notebook, ask whether
the learner knows Bellman backups, and whether they want to trace an update or implement the algorithm. Avoid a generic
questionnaire about every possible preference. Once needed answers arrive, fill in `outline.md` (`init` leaves the
skeleton) before writing any beat:

- **The viewer:** who they are, what they already hold and where they got it (an earlier lesson in the series, their
  job), and what starts from zero for them.
- **The opening problem**, and **the point in one line**: the answer the lesson arrives at.
- What they can do afterward; focus, exclusions, length/depth, language and narration when established.
- **The scene map**, one row per scene:
  `scene | question | raised by | likely misconception | visual action or prediction | source | leaves out`.
  `question` is what the viewer is wondering as the scene starts, in their words. `raised by` is the earlier scene,
  or `opening`, that left them wondering it. `leaves out` is what the source says on this point that the scene will
  not: the condition dropped, the case not covered, the step skipped, where the simplified picture stops applying.
  `—` when nothing is dropped. The author does not know what they left out until they write it down, and a viewer
  who knows only the scene will take the simplification for the whole: "光速很快" is not a shorter "光速不变".
  What would mislead is said in the scene in a clause, or named in the closing scene; the rest stays in the cell.

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
  author and a list of topics give none of this. (Failure: an opening that named the paper and listed its six
  chapters.)
- **A chain of questions, not a table of contents.** At both sizes. A chapter is named by the question it answers,
  and each chapter after the first asks what the last one's answer leaves short, so the names read in a row are the
  argument. Ploto's film on retiring early runs 46 minutes on four: "攒多少钱，才能不上班 → 财务自由怎么算 →
  年支出乘以二十五，就够了吗 → 安全边际从哪里来 → 最难的不是 FI，是 RE". Ours read "一个客户 · 客户数 · 留存 · 成本 ·
  AT&T 案例 · 取舍": the paper's sections in the paper's order, and a cold reader found one of them never used again
  and another going back to the subject of the one before. Chapters that could trade places with only a roadmap line
  changing are a list. Write the chain in the brief, before the scene map. The names share the control bar, and
  `check` fails when they overflow it (seven names of 42 characters fit, seven of 52 did not), so each is its question
  cut short ("×25 够吗"), the full wording heads the chapter's first scene, and fewer chapters leave each name more room. A name
  cut short keeps its subject and leans only on names before it: a reader could not tell who "还来多少、多贵" was about,
  or which ratio "只看比率行吗" meant. Inside a chapter, every scene answers a question the viewer already has, because
  the opening or an earlier scene raised it: that is the `raised by` cell. If nothing raised it, add the beat that
  does to the end of the scene before, move the scene, or cut it. An opening that only works as a list item gives
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
- **What they already hold costs a clause.** Recall it by where they met it ("ROIC 那课里的 steady-state value") and
  move on. (Failure: a scene re-deriving the steady-state value / PVGO split for a viewer the brief said had finished
  that lesson.)
- **One step per beat, and none left out.** A figure the viewer cannot rebuild from what was said reads as a mistake.
  (Failure: "扣 $500 的 CAC，剩 $2,838" straight after $3,486; the new customer's own $3,338 was never said.)
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
prints the chapter names in a row, then every scene's opening beat under the beat before it and the question the
scene map gives it, and writes the pages for a reader who has seen neither the source nor the outline (`cold-read.md`). Do it on the finished script,
before drawing the scenes: rewording a beat is free then and costs a clip later.

Whether the lesson says what the source says is not the author's to judge either, and the cold reader cannot: a
second reader with the source checks every claim on the same pages (`source-read.md`), straight after the thread
gate. The picture being right proves nothing about the sentence under it: every digit on screen is the digit that
was typed, and `numbers` sees figures only, not names, labels, mechanisms or conclusions.

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
- **Opening:** the concrete situation, why the obvious approach is insufficient, the question to resolve, and the
  answer in one line. Take the question from the source when it states one. A roadmap comes after these, if at all,
  and shows the chapters' questions.
- **One scene per complete idea.** If a scene needs more than about five beats, it holds two ideas.
- **Closing scene:** three takeaways, the first answering the opening's question, a restart button, and what to do
  next. No new material. One `.small` line says the lesson was made by an AI from the source (its citation), that
  its figures were checked against it, and that the tagged examples are the author's own; a viewer who sees it later
  in a feed has no other way to know, and content made this way is labelled by law in China (《人工智能生成合成内容
  标识办法》, in force since 2025-09-01).
- 40–110 beats has worked for full lessons (about 6–20 minutes narrated); use the agreed scope, not a minimum quota.

## Each beat

- **Plain question first, term second.** "How much of the price is a bet?" before "PVGO".
  Scene headings are questions the scene answers.
- **Every abstract claim gets a number or a worked case** within the same scene.
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

Edit the source parts and rebuild: content and delivery in `script.js`, arithmetic in `data.js`, pronunciation in
`speak.yaml`.
Keep `outline.md` current when the learning goal or scene coverage changes, and rerun `thread` when scenes move or an
opening changes. Do not patch generated HTML as the source.

## Narration

The standing voice is `google/gemini-3.8-flash-tts` through OpenRouter, with a written direction on every beat. The
owner chose it by ear on 2026-10-13 over the same voice undirected and over MiniMax: an even reading loses the
listener. What was chosen is the directions, so they get the care the sentences get. Stay on this model; a cheaper
Flash-Lite voice was ruled out the same day.

### Voice

One voice per lesson, picked for its subject. The owner approved these three and said to choose by content. The last
column is a reading of Google's one-word labels, not something heard: each alternate was heard on one beat.

| Voice | Google's label | Reach for it when |
|---|---|---|
| `Charon` | Informative | the default: a lesson that works through an argument or a calculation |
| `Sadaltager` | Knowledgeable | dense expert material, where the lesson reports what a field has settled |
| `Sulafat` | Warm | the subject is personal: habits, health, a decision about one's own money or work |

### Directions

A direction says how one sentence is read. It sits beside the sentence in `script.js`, as `D('direction', beat)` or
`D('direction', W(beat))`, is sent to the voice with that beat only, and never appears on screen.

- Write them in one pass, in order, once the words are final, with the chapter chain open. A direction comes from
  what the sentence does at that point: asks, turns, computes, concedes, concludes, hands over to the next scene.
- The form that was heard and chosen has two parts: a stance toward the listener, then where the reading changes
  inside the beat, located by the beat's own content.

  | The sentence | Its direction |
  |---|---|
  | turns from the usual method to a puzzle | `curious, like posing a puzzle to a friend; brisk at first, then slower and pointed on the contrast between the two companies` |
  | multiplies three figures, then adds a caveat | `speaking slowly and deliberately, every figure clear; a slight lift on the caveat in the last sentence` |
  | reports an exception to an earlier claim | `matter-of-fact, then mild surprise at the exception; the final sentence calm and reassuring` |
  | names the first of five mistakes | `firm and conclusive, naming a mistake; brisk, with a clear turn at the objection` |

- A direction that could move to another beat unchanged is filler: `clear and engaging` fits every sentence, so it
  varies nothing. Name the thing in this sentence that the reading turns on.
- Delivery only: tone, pace, weight, where it turns. No persona, age, gender, accent or scene ("you are a teacher");
  Google names long profile text as the commonest cause of a drifting voice. One line, in English, under 160 characters.
- Neighbours differ. Three beats that honestly take the same direction are usually one thought cut in three: say
  what each one adds.
- One delivery per beat, with one or two turns in it, each tied to a part of the sentence (`after the colon`,
  `the last sentence`), as in the table above. A beat that needs a third turn is two beats.
- Ask for stress in the direction (`pointed on the contrast`), never with capitals or punctuation in the sentence.
  The subtitle is not edited for the voice.
- A momentary event is a tag in the spoken text, added through `pause_after:` or a `say:` pair in `speak.yaml`:
  `<short pause>` or `<long pause>` (only the first was tried). Use few. One tag made a 0.8 s gap; two in one beat
  put a gap after nearly every phrase.
- Pace words are coarse. Charon, one take per wording, against the same beat undirected; two takes of one wording
  differ by about 4%.

  | Wording | Length |
  |---|---|
  | tone only: `curious, posing a puzzle`, `lively` | +13% |
  | `a little quicker than usual` | −11% |
  | `brisk`, `speaking rapidly` | −32% to −34% |
  | asks for care with figures: `natural pace, landing each number clearly`, `steady, careful with the numbers`, `measured, every figure clear` | +37% to +68% |
  | `speaking slowly` | +63% to +94% |
  | one `<short pause>`, no direction | +22% |
  | two `<short pause>`, no direction | +46% |
  | slow wording and two tags together | +86% |

  There is no "slightly slower": a figures beat keeps its pace or runs half as long again. Spend the slow direction
  on the beats where the viewer is meant to compute, not on every beat that holds a number, and never stack slow
  wording on pause tags.
- Weight words slow a beat as much as pace words do. A 59-character beat directed `revealing the answer soberly,
  letting the size of the drop sink in` ran 20.4 s, 8.6 s of it pauses; `with weight on how little is left` ran
  20.8 s; `plain and direct, giving the answer without drama` ran 11.0 s. On another beat `quick on the first
  sentence` gave 10.8 s with one pause in the whole clip, and `easy on the first sentence` 12.8 s with four.
- Keep `speed` in `lesson.json` at 1. It stretches every clip alike, on the page and in the film, and the voice
  was chosen at its own speed. A lesson still carrying the fallback voice's 0.85 filmed 18.9 minutes of narration
  as 22:25.
- `say` prints every beat with its direction under it. Read that preview top to bottom as the listener before
  `synth`: it is the only place the deliveries are seen in sequence. `warn delivery` names a beat with no direction
  (the voice then picks its own reading), one direction three times in a row, and a direction over 160 characters.
  `check` refuses a direction left as a `TODO`.
- After `synth`, `say` adds `warn pace` for a clip that takes 1.6 times, or 0.6 times, the lesson's usual time for a
  line that long. It says where to listen, not that the beat is wrong: a slowed computation is meant to stand out.
  On the first whole lesson (109 beats) it named three: two slowed computations and the `sink in` beat above.
- Changing a direction re-synthesizes that one clip. There is no seed: a new clip is a new take. To take a beat again
  under the same direction, move its `clips/NNN.wav` and `NNN.txt` out of the lesson and run `synth DIR changed`.
  A take can differ in level as well as pace: one came back 7.5 dB louder than the beat before it.

### Pronunciation

- Finish every beat and read the whole `say` preview before synthesizing anything. Rewording after synthesis is the
  expensive path.
- Pronunciation is fixed in `speak.yaml`, never by changing the subtitle.
- **Probe before writing pairs.** Apart from the rules below, the voice is sent the text as written. Synthesize
  three beats, listen, and write a `say:` pair (longer strings first) only for what was misread. Read right by
  Charon inside Chinese sentences with no pair and the rules off, as far as a transcript shows: `AT&T`, `SG&A`,
  `LTV/CAC`, `NPV`, `TAM`, `25%`, `8.3 年`, and `2021 年` digit by digit. Three clips do not settle a class that is
  read differently from take to take: `$77` was right in the probe, and plain dollar amounts then came out five
  ways across the lesson (next rule). Read every transcript of the full run.
- **A Chinese lesson keeps `rules: zh`** (set by `init --lang zh`). As written, a dollar amount with `billion` came
  out three ways in three clips ("32.5 billion dollar", "32.5 个 billion 元", "2.2 个 billion 美金") and `1.5x` as
  "1.5 x". The rule speaks them 三百二十五亿美元 and 一点五倍, heard exact in four clips. It also closes the space
  between a number and 年 (`2021 年`, `8.3 年`) and writes a − before a figure as 负 or 减. Charon read both 年 forms
  right without the rule; `2021年` was heard with it, `8.3年` was not; a transcript cannot tell how the − was read.
  On a Gemini voice the rule also gives a plain dollar amount its unit. In one lesson 17 beats held an amount written
  like `$653`, and in 12 of them Charon read 元, 块钱, 刀 or no unit at all; spoken `653美元`, all 31 amounts in the 17
  were transcribed 美元. An amount followed by a letter or by 万 or 亿 (`$5K`, `$3 万`) is left for a pair. The
  fallback voice read `$900` right and is sent it as written.
  `say:` pairs run before the rules and win. With the rules off, `say` and `check` print `warn speech` for an English
  magnitude word or an `x` multiplier. An amount the rule cannot write as a whole number (`$1.2345678 million`) is
  left for a pair. English lessons have no rules: probe them.
- `asr.py` reports where to listen, not what is wrong. `LISTEN`: the transcript is unlike the spoken text. `NUMBER`:
  a number that was said is missing from the transcript, which the score alone hides. `asr.py DIR --years`: a second
  pass that shows whether each year was read digit by digit (Whisper writes "2020" either way in the first pass).
  Whisper mishears English terms inside Chinese speech ("greedy" → "gradient") and writes some numbers as homophones
  (10 → 实); a term misheard the same way in every beat is the recognizer, not the voice. After listening,
  `asr.py DIR --accept 12,40` records those transcripts in `asr-accept.json`; the beats are reported again only if a
  new clip is heard differently. Pause tags are dropped before the comparison.

### Cost

- `say` prints the estimated minutes and, with `price_audio` in `speak.yaml` (USD per million audio tokens), the
  estimated cost of all beats and of those without a fresh clip. `synth` prints the seconds it made and what they
  cost. Tell the user the estimate before the first `synth`.
- The voice bills 25 audio tokens per second of sound: $0.0135 a minute at $9, Google's price until 2026-12-31, and
  $18 from 2027. The text sent adds under 1%. Measured: 15 directed clips, 157 s, $0.035. A 109-beat Chinese lesson
  was estimated at 18.6 minutes and $0.25 and made 18.9 minutes; the 25 clips made again after the first pass (the
  dollar rule, three changed directions, five retakes) added $0.07.
- Directed beats run longer than an even reading: the 109 beats took 15% more time than on MiniMax (18.9 against
  16.4 minutes), from 0.83 to 1.78 times beat by beat, median 1.16.
- The local turnpike does not meter `/audio/speech`, so `turnpike stats` shows nothing for it. The record is the
  OpenRouter key's usage, which matched `synth`'s own totals a few minutes later.
- Synthesize three beats first, then `changed`. Clips are cached per beat on (model, voice, direction, spoken text).

### The fallback voice

`assets/speak-minimax.yaml` is the earlier voice (`minimax/speech-2.8-turbo`), kept for when Gemini cannot be used:
copy it over the lesson's `speak.yaml`. It reads evenly and is not sent the directions.

- Pace is a number: `speed_default`, then `speed: {17: 1.0}` to slow formula and arithmetic beats a notch. The pause
  markup is `<#0.18#>`. Clips are cached on (model, voice, speed, spoken text).
- Known-good Chinese voice: `Chinese (Mandarin)_Radio_Host`, speed 1.0–1.15, with `rules: zh`. On it `$900`,
  `$894,813`, `28,426`, `98.71%` and `0.037` were read correctly, and four classes were misread:

  | Written | Heard without the rule | With `rules: zh` |
  |---|---|---|
  | `$265 billion`, `180 million` | "265 美元 billion" | 两千六百五十亿美元, 一亿八千万 |
  | `2020 年` | a cardinal, 二千零二十年 | `2020年`, read digit by digit |
  | `−5%`, `900 − 247` (U+2212) | the sign is dropped | 负5%, 900减247 |
  | `1.5x` | "1.5 X" | 一点五倍 |

  It also skips `&` (spell the name in a pair: `AT&T` → `A T and T`), and an ASCII hyphen before a figure was never
  tried on it. `say` and `check` print `warn speech` for each of these.
- Cost is per character: `price` in `speak.yaml` is USD per million billed characters, and MiniMax on OpenRouter
  bills a non-ASCII character as two. A 107-beat Chinese lesson of 4,979 characters was about $0.47.

## Before handing over

Ensure the cold read and the source read were done and answered, `check` is clean, contact sheets are read (the pause
screens among them), and `numbers` is clean. The reply says what the cold read still reports (or that none was done),
what the source read left `stretched` and what the lesson leaves out that a viewer should know, which numbers are the
source's and which are yours, what was not verified, what the narration cost, and where the output files are.
