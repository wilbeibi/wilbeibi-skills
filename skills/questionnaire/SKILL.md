---
name: questionnaire
description: Turn the open decisions from a long discussion into a self-contained offline HTML questionnaire the user fills at their own pace, whose answers come back as markdown keyed by stable question ids. Use when the user wants to finalize or confirm a design, align on accumulated decisions, review assumptions from notes/memory, or asks for a survey or questionnaire. Do NOT use for live one-question-at-a-time interviews (use grill-me).
---

# questionnaire

Batch the conversation's unresolved decisions into one HTML form; consume the markdown answers it emits. The answers file is the alignment contract — every question comes back as answered, open, or skipped-by-branching; nothing is silently dropped.

## Workflow

1. Mine the discussion, notes, and memory for *decisions still open*, not topics. Points already settled go into `intro` as a "current understanding" summary — add one leading `text` question asking what in it is wrong, instead of re-asking each settled point.
2. Write `questions.json` (schema below), then build:

   ```bash
   python3 scripts/build.py questions.json -o alignment.html
   ```

3. Deliver: write the HTML somewhere the user can open it (project dir or scratchpad) and give them the path; in a remote/claude.ai session, publish it as an Artifact instead.
4. Consume: the page's **Generate answers** button emits markdown the user pastes back or downloads as `.md`. Parse by the `` (`id`) `` keys, not question numbers or wording. Treat `open — no answer given` as still-undecided — never fill those in yourself. Record ruled decisions wherever the project keeps them (design doc, ADR, memory), quoting the answer.

## questions.json

```json
{
  "title": "Mitate — design alignment",
  "intro": "Current understanding (flag anything wrong in Q1):\n- ...",
  "outro": "Closing instruction echoed to the agent under the answers.",
  "questions": [
    {
      "id": "storage",
      "label": "Storage layout",
      "section": "Architecture",
      "question": "One JSONB table, or normalized?",
      "why": "What hangs on this decision, in the user's terms.",
      "ref": "SPEC.md §3",
      "type": "single",
      "options": [
        {"value": "Single JSONB table", "detail": "Consequence of picking this.", "recommended": true},
        "Normalized from day one",
        "Other — see note"
      ],
      "note": true,
      "optional": false,
      "showIf": {"q": "earlier-id", "is": "that question's option value"}
    }
  ]
}
```

- `type`: `single` (default) | `multi` | `text`. Choice types need ≥2 `options` (plain strings allowed); `text` renders a textarea.
- `note: true` adds an optional free-text field under the choices; `optional: true` excludes the question from the answered count; `section` renders a heading when it changes; `showIf` supports `is` or `not` against an **earlier** question's option value.

## Composing questions

- One decision per question. If a stem contains "and", split it.
- Options must be mutually exclusive and each `detail` states the consequence of picking it, not a restatement. Mark your `recommended` pick — you have an opinion and hiding it wastes the user's time — and include an "Other / needs discussion" escape so no one is forced into a false choice.
- `why` says what downstream work changes with the answer; `ref` points at the file/line or note that proves the framing, so the user can check you.
- `showIf` only for real dependencies (e.g. "what replaces the gate?" only if they skip the gate). Skipped questions still appear in the answers, marked skipped.
- Keep decision alignment to ~15 questions or fewer. For large elicitation (requirements, preferences for a doc you'll draft), group with `section`, mark nice-to-haves `optional`, and tell the user they can answer in sittings — drafts autosave.

## Notes

- The HTML is dependency-free and offline: strict CSP, no network, drafts in localStorage. When content is personal (finances, health), say so — answers never leave their machine until they hand them back.
- Storage key includes the question-id list, so regenerating with changed questions starts a clean draft rather than restoring stale answers.
- Build output like `alignment.html: 12 questions, 2 conditional` confirms parse + validation; errors list the failing `questions[i]` and exit non-zero.
