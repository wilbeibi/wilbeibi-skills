---
name: dataviz
description: Design and implement evidence-first charts from real data for technical blogs, reports, READMEs, and product explainers. Use when asked for a benchmark graph, data illustration, performance chart, tradeoff plot, small multiple, or an editorial chart in React/Recharts or a static plotting stack. Do NOT use for text-only diagrams (use show-me), hand-drawn conceptual art (use sketch-concept), or dashboard UI design.
---

# dataviz

Turn a concrete claim and its source data into a publication-quality chart that reads like an editorial illustration, not a generic dashboard widget.

## Start with the claim

Inspect the real data before choosing a chart. State the sentence the figure must prove, the comparison that matters, and any uncertainty or missing measurements. Never invent values, smooth away inconvenient results, or imply causality the experiment does not establish.

Choose the smallest form that carries the claim:

| Question | Form |
|---|---|
| How does a metric change over time or training? | Line chart; add uncertainty bands or error bars when available |
| Where is the quality/cost/latency frontier? | Scatter plot; label points directly and explain the favorable corner |
| What contributes to a total? | Stacked bars; use a shared scale for comparisons |
| How does behavior differ by mode or corpus size? | Small multiples with identical axes |
| Is only one comparison important? | Annotated slope, dot, or bar chart instead of a full dashboard |

## Editorial visual language

- Put a conclusion-oriented title inside the figure. Add a short orientation such as `top left is best` when direction is not obvious.
- Prefer a single dark canvas (`#0f172b`) with slate grid lines and labels. Reserve saturated colors for data.
- Use a compact technical or monospace face when it matches the publication; keep numerals tabular.
- Use thin grid lines, clear axes, restrained legends, and generous internal spacing. Avoid cards, gradients, shadows, KPI chrome, and decorative controls.
- Encode important categories with color plus shape, dash, or position. Give the focal series the strongest contrast and mute baselines.
- Label a small number of scatter points directly. Store optional `label_dx` and `label_dy` offsets with the data and add subtle leader lines when labels move far from points.
- Use one palette consistently. A practical dark-chart palette is cyan `#06b6d4`, blue `#3b82f6`, emerald `#10b981`, amber `#f59e0b`, violet `#8b5cf6`, pink `#ec4899`, lime `#84cc16`, and gray `#94a3b8`.

## Data contract

Keep measurements separate from presentation. Prefer a small CSV or JSON file checked in beside the article data rather than embedding rows in component code.

- Line data: first column is the x value; each series is a column; use `<series>_stderr` for uncertainty when present.
- Scatter data: `name,x,y,shape,color,label_dx,label_dy`.
- Stacked bars: first column is the category; remaining columns are stack segments.
- Preserve a download link to the underlying data when the figure is published on the web.

## Implementation

Use the project's existing plotting stack. In a React site, prefer responsive SVG with Recharts: `ResponsiveContainer`, the appropriate chart primitive, subdued `CartesianGrid`, explicit axes, a custom dark tooltip, and custom labels only where they improve comprehension.

Keep reusable wrappers narrow: `EditorialLineChart`, `EditorialScatterChart`, and `EditorialBarChart` may own data loading, responsive margins, palette, tooltips, legends, and downloads. Article code should supply the data path, title, axis labels, ticks/domains, and series emphasis.

For alternate views such as `Narrow` and `Open-ended`, use a small accessible segmented control and keep axes stable where comparison matters. Do not hide a materially different scale behind a tab without making the change obvious.

On narrow screens, reduce chart height and tick density, move long axis descriptions below the plot, and fall back from direct labels to a legend when collisions cannot be resolved cleanly.

## Honesty checks

- Bars start at zero unless a broken baseline is explicit and justified.
- Log axes are labeled and never receive zero or negative values.
- Units appear in axis titles or tick labels, not only in prose.
- Error bars and sample aggregation match the stated methodology.
- Color is not the only carrier of meaning.
- Related panels share domains, ticks, ordering, and category colors.

## Verify

Render the final chart with representative and edge-case data. Check the claim against the plotted values, hover/focus behavior, label collisions, clipped axes, downloadable data, and layouts around 320, 768, and 1440 pixels. Remove any element that does not help read the comparison.
