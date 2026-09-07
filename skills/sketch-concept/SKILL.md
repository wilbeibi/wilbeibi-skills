---
name: sketch-concept
description: Generate a playful hand-drawn illustration that explains one technical mechanism or data insight — architecture, concurrency, storage, caching, queues, retries — for a blog post, doc, or slide. Use when asked for an illustration, a hand-drawn or Excalidraw-style visual, or a picture that makes one engineering idea click. Do NOT use for answering in-chat with a text diagram (use show-me) or for charts of real data (use dataviz).
---

# sketch-concept

Make an abstract technical mechanism feel like a small physical world. The illustration should communicate one insight at a glance, not attempt to be a complete architecture diagram.

## Visual language

- Use thick, slightly wobbly black outlines, flat colors, generous whitespace, and a handwritten font resembling Virgil or Patrick Hand.
- Use a soft paper-colored or saturated single-color background. Keep the palette to 4–5 colors: sky blue, pale lemon, ochre, coral, lavender, plus black.
- Reuse one visual identity for like things: people for requests/tenants, small packages for chunks/messages, a warehouse for remote storage, a cabinet for cache, a ticket booth or tent for admission control.
- Turn each important system component into a friendly physical metaphor. Make the metaphor support the actual behavior rather than decorate it.
- Use direct arrows for the happy path. Reserve a large curved arrow for retry, queueing, timeout, or feedback loops.
- Put the conclusion in the composition itself (color, position, missing item) and reinforce it with one short caption.

Avoid dashboards, gradients, glossy vector UI, generic cloud-service logos, dense boxes, and more than one central claim.

## Choose the story

Before generating, express the picture as:

`actor → decision or absence → visible consequence`

Examples:

- A file read → one chunk is missing → fetch only that chunk.
- Requests arrive → capacity runs out → the newest request is served first.
- Writes accumulate → small files are merged → reads become cheaper.
- A retrying client → a budget is exhausted → retries stop before overload spreads.

Prefer a before/after pair when contrast is the lesson. Prefer a three-object left-to-right scene for a single data path. Use a hand-drawn chart only when the trend itself is the lesson.

## Generate a draft

Use the image-generation tool for the illustration. State the use case as `infographic-diagram`, and include:

1. A precise scene and the metaphor for each component.
2. Layout direction and the one flow or transition being shown.
3. A fixed palette and the visual-language constraints above.
4. Every required label as verbatim quoted text.
5. A reminder: flat colors, legible labels, no logos, no gradients, no watermark.

For reference images, treat them as style references only; do not reproduce their specific composition or characters.

## Verify and refine

Inspect the result for three things:

- **Meaning:** the arrow direction, state transition, and physical metaphor agree with the system behavior.
- **Legibility:** every important label is readable; remove secondary text rather than shrinking it.
- **Coherence:** line weight, handwriting, and the asset language remain consistent.

If the draft misses one of these, make one targeted regeneration request. When exact data values or dense labels must be guaranteed, use the generated image as an art-direction reference and create the final diagram in SVG, Figma, or Excalidraw instead.

## Prompt skeleton

```text
Use case: infographic-diagram
Asset type: technical blog illustration
Primary request: Explain [one mechanism] as [one visual story].
Scene/backdrop: [single background color].
Subject: [left / center / right objects and the physical metaphor for each].
Composition/framing: [before/after, left-to-right path, or chart].
Style/medium: whimsical hand-drawn systems illustration; thick wobbly black ink
outlines; handwritten Virgil-like lettering; flat colors; generous whitespace.
Color palette: [up to five colors].
Text (verbatim): "[label 1]"; "[label 2]".
Constraints: exactly one main takeaway; all text legible; no gradients, logos,
watermark, generic dashboard panels, or photorealism.
```
