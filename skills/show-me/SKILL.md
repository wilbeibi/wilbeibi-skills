---
name: show-me
description: Explain code structure, dataflow, or proposed changes with a compact tree, pseudocode, type signature, diff, or diagram. Use when a visual clarifies those relationships; whole-repo briefings belong to grok-repo.
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

- Use trees, pseudocode, or diffs in plain terminals. Use Mermaid when the actual destination renders it.
- Use an interactive visualization or self-contained HTML when interaction or spatial layout adds value.
  Follow the host's output-directory convention and return a link. Open the file only when requested,
  using the available platform mechanism; do not assume macOS or a graphical session.

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
