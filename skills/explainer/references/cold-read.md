# Cold read

An author cannot hear a jump in their own script: they know where it is going. This read is done by someone who does
not, a fresh subagent that has seen neither the source nor `outline.md`. Run `lesson.py thread DIR`, then give the
reader this file, the path `DIR/thread/`, and the brief's viewer line (who they are and what they already hold).
With no subagent available, read the seam listing `thread` prints yourself and say in the handover that no cold read
was done.

## For the reader

You are the viewer described in your prompt. `00.txt` is the lesson's first screen; each later page is one scene:
its on-screen heading and its subtitles, in order. You have nothing but these pages. Open them one at a time, in order,
one page per step.

Before you open a page, write in your own words:

- **want**: the question you now want answered (`none` if nothing is open).

After you read it:

- **met**: `yes`, `partly` or `no`. Did the page take up `want`, or a question still open from earlier?
- **lost**: quote the first words where you could not tell why you were being told this, or that leaned on something
  you had not been given. `—` if none.
- **known**: anything explained at length that you already knew.

Do not be generous. A page that is clear in itself still fails `met` when nothing before it made you want it.
Judge the order and the bridges, not the facts: you cannot check those.

Report one row per page (`page | first words | want | met | lost | known`), then the five seams that lost you most,
and whether the end answered the question the opening raised.

## For the author

Read the report as measurements, not as a reviewer to argue with.

- **`no`** is a scene nothing asked for. Add the beat that raises its question to the scene before, move it, or cut it.
- **The five seams** and **whatever the end left unanswered** are fixed before anything is drawn or voiced.
- **`lost`** is triaged, not counted. A reader quotes something on almost every page, in a sound lesson too; most are
  one-beat fixes: a term never defined, a step left out, a name that changed, a reference to something not shown.
- **`known`** marks re-teaching: shrink it to a clause.

Then rerun `thread` and give the pages to a new reader; one who has seen the lesson is no longer cold. Stop when a
reader reports no `no` and says the end answered the opening. After two rounds, name what remains in the handover.

What to expect (2026-10-12, one reader per lesson): a 15-scene lesson whose scene map came first drew 7 `yes`, 7
`partly`, 1 `no`; two lessons that followed their paper's section order drew 6/14/6 of 26 and 2/18/9 of 29. A read
took about ten minutes and 90k tokens.
