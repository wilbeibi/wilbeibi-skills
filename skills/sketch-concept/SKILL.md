---
name: sketch-concept
description: Draw a hand-drawn SVG illustration that explains one technical mechanism or data insight — architecture, concurrency, storage, caching, queues, retries — for a blog post, doc, or slide. Use when asked for an illustration, a hand-drawn or Excalidraw-style visual, or a picture that makes one engineering idea click. Do NOT use for answering in-chat with a text diagram (use show-me), for charts of real data (use dataviz), or for an animated or interactive step-by-step walkthrough of your own system (use mechanism-viz).
compatibility: Python 3.10+, stdlib only; Chromium or Chrome for `sketch.py check`.
---

# sketch-concept

One figure, one idea, in the notation the reader already knows, drawn with a wobbly pen. `scripts/sketch.py`
(paths are relative to this skill's directory) draws it as static SVG and checks it in a real browser at phone
and desktop width, light and dark.

## Steps

1. **Choose the story.** Write the picture as `actor → decision or absence → visible consequence`, e.g. a file
   read → one chunk is missing → only that chunk is fetched. Contrast is the lesson → a before/after pair, or
   columns that differ in one place. One data path → three objects, left to right. Layers are the lesson → a
   stack, top to bottom. A trend is the lesson → its shape, hand-drawn, without real values. Done when the line
   names one consequence a reader can point at.
2. **Pick the glyphs.** The field has a standard notation → draw it: the reader's mental map is already built
   from it, and a metaphor makes them translate. It has none → one physical metaphor per kind of thing, reused
   for every instance. Done when each glyph is the usual one or a consistent metaphor, and the claim shows in
   the composition (a colour, a position, a missing item), not only in the caption.

   | Thing | Glyph | Pen |
   |---|---|---|
   | container | box standing on a shared host-kernel bar | `box` |
   | VM, microVM | dashed boundary around the app and its own guest-kernel strip | `box(dash="7 6")` |
   | disk, object storage | cylinder | `cylinder` |
   | memory, page cache | module with pins | `memory` |
   | queue | row of slots | one `box` per slot |
   | request or data flow | straight arrow; one big curved arrow for retry, timeout or feedback | `arrow(bend=...)` |
   | more of the same | three dots | `dots` |

3. **Draw.** Write a script against `Pen`; this one passes `check`:

   ```python
   import sys; sys.path.insert(0, "<skill dir>/scripts")
   from pathlib import Path
   from sketch import Pen, page

   p = Pen(seed=3)
   for x, name in ((24, "app A"), (100, "app B")):           # containers stand on the host kernel
       p.box(x, 44, 64, 70, fill="sky")
       p.text(x + 32, 84, name, maxw=56)
   p.box(188, 16, 156, 108, fill="wash", dash="7 6")         # the VM boundary
   p.text(266, 36, "microVM", size=13, color="ink-2", maxw=140)
   p.box(204, 46, 124, 34, fill="sky")
   p.text(266, 68, "app C", maxw=110)
   p.box(204, 86, 124, 28, fill="ochre")                     # its own kernel
   p.text(266, 105, "guest kernel", maxw=110)
   p.box(16, 134, 328, 36, fill="lavender")
   p.text(180, 157, "host kernel", maxw=300)
   fig = p.svg(360, 186, label="Two containers share the host kernel; a microVM runs its own guest kernel")
   Path("kernels.html").write_text(page(fig, "Kernels", caption="Containers share the host kernel; a microVM brings its own."))
   ```

   - Units are CSS px at full size, and later calls paint on top. `text` takes the baseline: centre a label in
     a box at its middle + size × 0.35. Give every label `maxw`, the room it has.
   - Start the viewBox near 360 wide: a 375 px phone gives the figure about 343 px, and 14-unit labels must
     still render at 11 px or more.
   - Colours are palette names: `paper ink ink-2 wash card lid sky sky-2 lemon ochre coral lavender`. Ink reads
     on every fill in both modes; muted `ink-2` only on paper, wash and card. Use four or five fills, give each
     one meaning (lemon = shared), and name that meaning in the caption.
   - Labels are a word or three; sentences go in the caption. No gradients, logos, glossy UI or second claim.
   - Patrick Hand and Virgil draw Latin script only. For CJK or another script, add a hand font that covers it,
     e.g. `svg(font="'Patrick Hand', 'ZCOOL KuaiLe', sans-serif")`, and its stylesheet link to `page(head=...)`.
   - `svg()` returns one self-contained `<svg>` (no `<style>` or script) that pastes into any page and falls
     back to the light palette. A host page gets dark mode by adding `sketch.TOKENS_CSS` to its stylesheet;
     `page()` already includes it.

   Done when every label has `maxw`, the `label` alt text states the claim, and the seed is fixed: the same
   calls give the same bytes.
4. **Check.** Run it on the figure page, then on the page that embeds the figure, whose column, fonts and
   theme are what readers see. `check` opens a local file: if that page links root paths like `/style.css`,
   check a copy whose links are relative.

   ```bash
   python3 scripts/sketch.py check kernels.html --shots shots/
   ```

   Each `FAIL` line names one fault and, when it is not everywhere, the widths and modes it shows in; the last
   line is `CHECK OK` or `CHECK FAILED` (exit 1). On the embedding page it reads every `<svg>`, diagrams you
   did not draw included; act on the lines about yours. Change the drawing, not the check:

   - label too wide, overlapping or past the edge → shorter words first, then move or widen the box;
   - text below 11 px → fewer, larger labels or a narrower viewBox, never smaller text;
   - contrast → `ink`, or muted text only on paper, wash or card;
   - a font missing, or characters no listed font has → load a font that covers them;
   - drawing past the viewBox → widen the viewBox;
   - `warn … same in dark mode` → add `TOKENS_CSS` to the page.

   Then open the four screenshots: arrows point the way the system moves, and the claim reads at 375 px. Done
   when the figure page prints `CHECK OK`, no line from the embedding page is about your figure, and the
   screenshots show the story line from step 1.

## Optional: an image-model draft

When an image-generation tool is available and the composition is still open, a draft can settle it. The final
figure stays SVG drawn with `Pen`: generated text and notation drift. Treat any reference image as style only.

```text
Use case: infographic-diagram
Primary request: Explain [one mechanism] as [the story line from step 1].
Subject: [left / centre / right objects, each in its field's standard notation].
Style: hand-drawn systems sketch; thick wobbly ink outlines; handwritten lettering; flat colours on paper;
generous whitespace; palette [up to five colours].
Text (verbatim): "[label 1]"; "[label 2]".
Constraints: one takeaway; every label legible; no gradients, logos, watermark, dashboards or photorealism.
```
