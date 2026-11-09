---
name: state-prototype
description: Builds a throwaway single-file HTML demo of a proposed state model, driven by an explicit transition table, with free-play buttons and scenario tabs a person can click through. Use when asked to prototype, sanity-check, or feel out a state machine, lifecycle, or status design before implementing it. Do NOT use to explain an existing mechanism (use mechanism-viz), to check every interleaving (use tla-model), to chart a checked model (use statechart), or for a static diagram (use show-me).
---

# state-prototype

A prototype is throwaway code that answers one question about a state model. The part worth keeping is its transition table.

## Steps

1. **State the question (REQUIRED).** Write one paragraph at the top of the page: the state model, and the one decision the demo must settle. Example: "Can a closed writer's journal reach the next writer with its old merge base?" If the question is not settled yet, run the grill-me skill first. Done when the question names one decision.
2. **Write the model as an explicit transition table** in one pure `<script>` block, with no DOM access:
   ```js
   const TRANSITIONS = [
     // from, event, to, owner: the one writer of this transition, guard
     { from: "open", event: "finish", to: "closed", owner: "runner receipt",
       guard: (s) => s.unsettled === 0 },
   ];
   function step(state, event) { /* matching row -> next state, else { refused: reason } */ }
   ```
   Every mutable field in the state belongs to a row, and every row names one owner. An event with no legal row is refused visibly, never ignored. Done when every state has an exit or is marked terminal.
3. **Build the page.** Use one self-contained HTML file with no framework, bundler, or server. From top to bottom:
   - The title and the question.
   - The current state as labelled fields, with the last change highlighted.
   - One button per event, always enabled, that shows a refusal when there is one.
   - Scenario tabs. Each resets to a known start and steps through its ordered buttons.
4. **Pick scenarios from the failure cases.** Cover the happy path, a failed awaited attempt, an ambiguous timeout, a crash between two steps, a late or duplicate executor, two writers at once, and a delete mid-flight. Drop a case the model cannot express, and say so on the page. Done when each scenario ends on a state the user can judge right or wrong.
5. **Hand over and capture the answer.** Write the file to the OS temp directory and give its path. Never write it into the repository. When the question is settled, record the verdict and the final transition table in the design doc, issue, or code. When the table lands in code, test it table-driven, one case per row and per refused event (test-writing). Keep the HTML only if the user asks.

## Rules

- Label buttons and fields in domain words. Use code identifiers only when the reader wrote the code.
- Keep state in memory unless persistence is the question.
- Write no tests and no generalisation: one prototype answers one question.
- A click-through shows one ordering. When the answer depends on timing between concurrent actors, take the question to tla-model.

## Notes

- Ported from the logic branch of [mattpocock/skills](https://github.com/mattpocock/skills) `prototype` (MIT). Adapted: the explicit transition table with owners, failure-case scenarios, and temp-directory output.
