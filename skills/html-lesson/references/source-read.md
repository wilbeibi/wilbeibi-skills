# Source read

The cold read judges the order and the bridges and says so: it cannot check the facts. This read checks them. It is
done by a second reader, not the cold reader (who must stay cold) and not the author (who wrote the sentences and
believes them). Give the reader this file, `DIR/source.txt`, the scene map in `DIR/outline.md` (its `source` and
`leaves out` cells), and `DIR/thread/`. Run it on the finished script, straight after the thread gate and before any
scene is drawn: a sentence costs nothing to reword then and a clip later.

Why this gate exists: a lesson whose picture is right can still teach something the source never said. The picture is
rendered from code, so every digit on it is the digit that was typed; nothing in that makes the sentence true. The
`numbers` gate catches a figure the source does not contain and nothing else: a name, a research conclusion, a
mechanism stated more strongly than the paper states it, all pass it. This read covers the sentences and headings
the pages hold; text that is only on the drawn scene (a chart label, a card) is still checked by nobody but the
author at the eyes gate. And a lesson is a simplification, so what it drops is a claim too (the `leaves out` cell in
`authoring.md`).

## For the reader

You have the source and the pages. Each page after `00.txt` is one scene: its heading and its subtitles, in order.
For each page, take every sentence that states something about the world or about the source (a fact, a figure, a
mechanism, a result, what the authors found or recommend) and find it in `source.txt`. Use the scene map's `source`
cell as the place to start, not as proof.

Write one row per claim: `page | claim (first words) | verdict | where in source | note`.

- **supported**: the source says this, at this strength. Give the locator.
- **stretched**: the source says something weaker, narrower or conditional. Say what the source actually says.
- **invented**: not in the source. A worked example, an illustration or arithmetic of the author's own is fine if the
  page marks it as theirs; then write `own, marked`. If it is not marked, or it is presented as the source's finding,
  it is `invented`.
- **left out**: after the page's rows, one line: what the source says on this point that the page dropped, and whether
  a viewer who knows only the page would now believe something false. `—` if the omission is harmless.

Do not judge the order, the wording or the pictures. Do not be generous to a sentence because it sounds right: the
easiest claims to get past a reader are the ones that sound like the field.

Report the rows, then: every `invented` and `stretched` row in one list, and every `left out` line that would leave the
viewer believing something false.

## For the author

- **`invented`** is fixed by changing the sentence or the picture, never by adding a line to `source.txt` or a reason
  to `numbers.allow` that makes it pass. If the lesson needs the claim, find where it comes from and cite that source
  in the brief; if it cannot be found, cut it.
- **`stretched`** is reworded to the source's strength, or the gap is said aloud ("the paper shows this for one
  dataset").
- **`own, marked`** stays. **`own`** unmarked gets its `<span class="tag">`.
- **`left out`** that would mislead goes into the scene map's `leaves out` cell and into the scene as a clause, the
  closing scene or the handover, whichever the viewer needs to see. Harmless omissions are recorded in the cell only.

Rerun on the pages that changed. Stop when the report has no `invented` row, every `stretched` row is answered, and
every misleading `left out` is said somewhere the viewer will see it. The handover names what remains.

No lesson has been through this read when this was written: what a reader finds, how long it takes and how many rows
a lesson draws are not known. Measure the first ones and write the numbers here.
