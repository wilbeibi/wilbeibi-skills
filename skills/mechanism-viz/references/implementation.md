# Implementation patterns

Stack-neutral unless marked. Source: bbtree's `vis/` and `vis/figures/` (see `bbtree-case.md`).

## Figures as self-contained SVG files

Generate each figure as a file at build time with a small program. Do not draw figures at runtime. One file then
embeds in any page, works as `<img>`, and diffs in review.

The file carries everything it needs:

- Palette with both themes: `@media (prefers-color-scheme: dark)`, plus `svg[data-theme=light|dark]` so a host page
  can force one.
- Alternate states selected by URL fragment through `:target`: `fig.svg#dark`, `#still`, `#light-still`.
- Pure CSS `@keyframes`, no script.
- Reduced motion sets `animation: none`, and each element's base style is its final-frame state, so a reader with
  reduced motion sees the finished picture, not a blank one.
- Web fonts do not load inside `<img>`. Pin monospace runs with `textLength` + `lengthAdjust="spacingAndGlyphs"` so
  they still line up with per-byte marks.

## Step-based motion model

A figure is `LEAD (0.6 s) + N steps + hold`, then it loops. Every element's keyframes span the whole cycle, so all
elements stay in sync without coordination. Authors write steps; the generator writes percentages.

| Primitive | Meaning |
|---|---|
| `appear(at)` | Fades in at step `at` and stays |
| `between(from, until)` | Visible only in that span |
| `lit_during(spans, rest)` | Highlighted in the spans, `rest` style otherwise |
| `vanish(at)` | Fades out at step `at` |

Fades take 0.15 of a step. Charts use a `once` mode: play once, then rest on the final frame.

Page side: inline the SVG into a shadow root with an HTML caption. Render it as the reader scrolls near, restart it
the first time it becomes visible, give looping figures a Pause that holds the current frame, and an Enlarge on
mobile.

## Interactive playback with one CSS variable

A `requestAnimationFrame` loop writes playback time into one CSS custom property, `--t`, on the container. Every
mark derives position, opacity, and highlight from `--t` with `calc()`. The framework re-renders only when the step
index changes. bbtree measured about 2.6 ms per frame at full speed.

- Run the loop only while playing and visible.
- About 700 ms per step; slow the first pass.
- Each step selects the matching element, so the inspector follows playback.
- Reduced motion: jump step to step, with no tweening.

## Explorer state

- The URL holds the full state (dataset, size, seed or build mode, selected instance, level, view). A deterministic
  build means the same URL gives the same picture. Push history so back and forward work.
- Curated scenarios spare the reader an empty input box.
- Keyboard: `/` search, `R` random, Space play, `,` and `.` single-step.
- The post and the explorer share components; a panel in the post is the explorer's panel.

## Chart motion that enacts the measurement

Bars grow at one speed, so the faster implementation's bar lands first:
`growth_ms = clamp(value / max * 800, 120, 800)`. The value fades in when its bar lands. Lines draw left to right
along the x axis (thread count). Changing a selector replays the chart. Bars are square at the baseline and rounded
at the data end (radius at most 4).

Chart rules from bbtree (general chart hygiene, such as zero baselines and shared scales, belongs to `dataviz`):

- The reader picks the card; nothing auto-rotates.
- A one-sentence conclusion above each card is computed from the data.
- Draw at the card's real width, one unit per pixel.
- A concurrency axis is proportional from zero, so linear scaling is a straight line through the origin.
- Memory is resident set after build, with the build-time peak as a lighter extension. Bytes requested hide
  allocator size classes: mimalloc gives a 192 B leaf a 224 B block, +21%.
- Annotation lines stay under 75 characters and link to the competitor's code.

## Post layout

- Body column about 72 characters; sidenotes in the right margin; a sticky outline in the left margin.
- Each part (`##`) opens with an overview. Its sections (`###`) are tabs, one open at a time, each ending with a
  "Next, 2 of 3" bar. Closed tabs use `hidden="until-found"` so browser find still reaches them.
- Number a list only when the post ranks its items.
- Mobile: sidenotes expand on tap (44 px target), the outline becomes a bottom sheet, figures can be enlarged.
- [stack-specific, idea portable] First paint: stylesheet in the static head, fonts loaded non-blocking with
  `media="print" onload="this.media='all'"`, theme read from storage before the first frame, and a skeleton built
  from the app's own classes so hydration does not jump.
