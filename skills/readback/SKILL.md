---
name: readback
description: Put a long reply of your own - or a plan, document, or session transcript - on an HTML page the user reads, highlights, and comments on, returning their notes as a follow-up prompt through a waiting local command. Use when your answer is too long to review in a terminal, when the user wants to mark up or annotate a document, or when you want line-level feedback on a plan before implementing it. Do NOT use to collect answers to specific open decisions (use questionnaire) or to interview the user one question at a time (use grill-me).
compatibility: Python 3.10+, stdlib only. Live delivery needs a browser on the same machine and a harness that can hold a foreground command open.
---

# readback

A terminal is a bad place to read two thousand words and a hopeless place to argue with a specific sentence in them. Hand the reader the actual text on a page; get back their words attached to the passages they picked. `review` blocks until they press **Confirm & send**, then writes exactly the prompt they confirmed to stdout and nothing else.

The usual case is one long reply of your own — a draft, a design, an analysis you just wrote — and the reader wants to mark it up rather than answer it in prose.

## Commands

```bash
# the reply you just wrote, piped in as its own text (the common case)
python3 scripts/readback.py review - --format markdown --title "v4 volume commit design" <<'RB'
<the reply, exactly as you sent it>
RB

# a file that already exists: a plan, a design doc, a PR body
python3 scripts/readback.py review PLAN.md --out-dir /tmp/readback-plan

# standalone artifact: read, annotate, edit the prompt; cannot send it back
python3 scripts/readback.py build session.json -o review.html
```

Shared flags: `--format markdown|transcript` (inferred from `.md`/`.json`, required when `INPUT` is `-`), `--title TEXT`, and `--no-diagrams`. `review` also takes `--no-open` (print the URL, launch no browser); `build` takes `--force`. Without `--out-dir`, `review` creates a fresh private temporary directory and prints it.

## Choosing the input

- **One long reply** — the common case, and the reason to reach for this at all. Pipe the reply's text in as Markdown with `--title` naming what it is. Send the same words you sent the user: this page is their copy of your reply, the marks come back as offsets into it, and a rewrite would anchor their comments to sentences they never read. Say plainly that the page is that reply, not a new document.
- **Markdown file** — a plan, design doc, or PR body that already exists on disk. Pass the file as it stands; the exact source is preserved and offered for copy/download.
- **Transcript JSON** — a whole session, when the reader is reacting to the arc of the work rather than to one answer. Reach for this only when they ask for the session; one reply is the smaller, sharper unit. The `catchup --json` shape: `{agent, session_id, metadata, warnings, entries:[{index, kind, role, time, text}]}`. Only `entries[].text` is required; unknown fields are ignored.
- Tool calls, results and failures are held back: the page opens on the conversation, with a `N tool steps` button and a seam at each run to bring them back. Export the session whole — the page decides what to put in front of the reader, and a 233-entry Codex export that is 188 tool steps still reads as its 45 turns. Do not pre-filter the entries yourself.
- An exporter's own title is often the working directory (`catchup --json` on a repo session gives `rlp`), which names nothing the reader can recognise. Pass `--title` with what the session was about whenever the source title is a path component or otherwise says nothing.
- Resolve which session you are exporting explicitly — never assume the newest one, and reflect any subset (`--since-compact` and friends) in the description you give the user. Carry the exporter's `warnings` through; they are shown on the page.
- Do not rewrite the material into a briefing, and never reconstruct "verbatim" exchanges from memory or a compaction summary. A recorded summary goes in as a labeled summary entry.

## Delivery

Run `review` in the foreground and wait using whatever your harness supports. Status checks may yield, but do not kill or restart a review because it is taking a while — a human is reading, and there is no timeout on that.

| Exit | Meaning |
|---|---|
| 0 | Confirmed. stdout is the prompt verbatim, with no wrapper and no added trailing newline. A confirmed review with no annotations is a real outcome — the prompt says so, in an `Outcome:` line. |
| 1 | Operational failure (port, unwritable directory). |
| 2 | Invalid CLI or input (malformed transcript, empty document, `--out-dir` already holding a review). |
| 3 | The user cancelled. No prompt, no feedback. |
| 130 | Interrupted. |

The prompt is the reader's draft, not a read-out: they can edit it before confirming, and `result.json` records `promptEdited` when they did. So take the text on stdout as what they meant to send, even where a sentence answers to no annotation — do not reconcile it against a count.

On exit 0, treat the quoted passages as references and the user's comments as the feedback to address, under the current conversation's mode and authority. Each item is labelled with what the reader wanted from it, and the labels are not interchangeable: answer a **Question** in your reply rather than editing for it, apply a **Change**, and treat a **Note** as context rather than an instruction. When the page was one of your own replies, a **Change** means revise that passage of the reply or the draft it carried — not the codebase, unless the passage was about code you had already been asked to change. Reading a page of questions as a page of edit requests is the failure this labelling exists to prevent.

**Confirm & send** delivers feedback; it is not approval of the document, permission to implement a plan, or authorization for restricted actions. That holds for the empty review too: `Outcome: Read in full` means the reader wanted nothing changed, not that they authorized anything. No non-zero exit is a user response — never read cancellation or an interrupt as agreement.

## When it fails

- **Process died after the user confirmed:** the prompt is already on disk. Read `<review-dir>/followup.md` (the exact confirmed text) and `result.json` (outcome and submission id). Never ask the user to write the feedback again.
- **Harness cannot hold a running command:** `build` the artifact instead, give the user the path, and take the prompt back through copy/download. Say plainly that delivery is manual — do not claim the review was delivered.
- **Browser did not open:** the URL is already on stderr; ask the user to open it, or re-run with `--no-open`.
- **`--out-dir` refused:** it already contains a review. Choose an empty directory rather than replacing earlier feedback.

## Notes

- Review directory: `review.html` (standalone, carries no live credentials), `source.json` (immutable normalized input and SHA-256 fingerprint), `followup.md` (written atomically, only on confirm), `result.json`. Keep generated review directories out of this package.
- Annotations and any hand-edited prompt autosave in `localStorage` keyed by fingerprint. Editing the source starts a clean draft; an annotation whose quote no longer verifies at its stored offsets stays visible as unresolved instead of reattaching to another occurrence of the same text.
- Fenced `mermaid` blocks are drawn on the page, from a vendored renderer, with the source kept one click below the drawing. Nothing is fetched: the 3.4 MB renderer is inlined only when the source actually has a diagram, and `--no-diagrams` keeps it out. Comments anchor to the diagram source, not to the picture.
- Raw HTML in Markdown stays inert, but the structural tags a draft carries (`<details>`, `<summary>`, `<b>`, `<br>`) are unwrapped to their own words before rendering, with a summary kept as a bold lead-in and its block shown open — a reader marking up a draft should see all of it, not `<details><summary><b>Migration</b> (expand)</summary>` mid-sentence. Code, fenced or inline, keeps its angle brackets; a tag not on the list stays visible rather than guessed at.
- The page is offline and CSP-locked: raw HTML in Markdown is inert, images do not load, links open with `noopener`. Only the live page reaches the loopback server, which checks a per-review token, Host, and same-origin `Origin`.
- Tests: `python3 scripts/test_readback.py`.
