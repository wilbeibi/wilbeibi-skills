---
name: show-me
description: Answer with a compact visual — call tree, component tree, file tree, pseudocode, type signature, diff, or Mermaid — instead of a wall of prose. Use when the user says "show me", "draw", "sketch", "diagram", "visualize", or asks how something is wired, what shape an API should take, or what a change would look like. Do NOT use for whole-repo briefings (use grok-repo) or for charts and dashboards (use dataviz).
---

# show-me

Pick the *smallest* view that makes the point, set it beside one or two lines of text, stop.
One view per question; two if a second genuinely adds an axis. Never all of them.

## Pick the view

| The question is about | Show |
|---|---|
| an algorithm, branching, an invariant | pseudocode |
| runtime order, who calls whom | call tree |
| UI structure, state ownership | component tree — JSX plus the hooks and module paths that matter |
| where code lives, refactor scope | shallow file tree, one-line responsibility per entry |
| interaction across processes or time | Mermaid `sequenceDiagram` / `stateDiagram` |
| the shape of an API before writing it | type signatures only, no bodies |
| a change to any of the above | that same view, as a `diff` |
| a layout, or a comparison too dense for the above | one self-contained HTML file |

## Render target decides the format

Terminals do not draw Mermaid — a ```mermaid block in a chat reply is source code the user
has to compile in their head. ASCII trees render everywhere.

- **Reply in the terminal** → indentation and box-drawing trees, pseudocode, diffs.
- **Output lands in a file that renders** — Obsidian note, GitHub PR or issue, markdown doc →
  Mermaid is worth it. Say where it will render.
- **HTML** is the last resort, for layout, spatial comparison, or an interactive explainer.
  Match the product's colors, type, and spacing; use real labels and real data. Write it
  outside the project tree (`$TMPDIR`) unless the user asks to keep it, then open it:
  `open $TMPDIR/show-me-<topic>.html`.

## Examples

Call tree — runtime order:

```text
submitForm
  createSession
    persistPrompt
    launchAgent
  navigateToSession
```

Component tree — structure, state, and the module a component comes from:

```tsx
<SessionPage> (apps/example/src/routes/session.tsx)
  useSessionEvents()
  <SessionToolbar>
    <RunSkillButton> (packages/ui)
```

File tree — responsibility, one line each:

```text
src/
├── commands/       # parses user actions
├── sessions/       # owns session state
└── transport/      # sends API requests
```

Diff — when the surrounding shape already exists. Diff whichever view fits the topic; any of
the above takes `diff` markers. Here, pseudocode:

```diff
 on(save)
-  write content
+  if content is unchanged
+    return cached result
+  write new content
+  invalidate cache
```

## Rules

- Include only the calls, files, props, states, and boundaries this question needs. Elide the
  rest with `…`. Do not pad a view toward completeness.
- Real paths, real names, real data. A tidy diagram with invented labels is worse than prose.
- Show the whole block instead of a diff when most of it is new, when the omitted context
  hides ownership or order, or when the user needs something copyable.
- Skip the preamble. The visual is the answer; the prose is a caption.
