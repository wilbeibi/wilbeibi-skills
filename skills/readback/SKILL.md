---
name: readback
description: Turn a plan, Markdown document, or conversation transcript into an HTML page the user reads, highlights, and comments on, returning their notes as a follow-up prompt through a waiting local command. Use when the user wants to mark up or annotate a document, react to a long session in the browser, or when you want line-level feedback on a plan before implementing it. Do NOT use to collect answers to specific open decisions (use questionnaire) or to interview the user one question at a time (use grill-me).
compatibility: Python 3.10+, stdlib only. Live delivery needs a browser on the same machine and a harness that can hold a foreground command open.
---

# readback

Hand the user the actual text; get back their words attached to the passages they picked. `review` blocks until they press **Confirm & send**, then writes exactly the prompt they confirmed to stdout and nothing else.

## Commands

```bash
# live: serve the review, wait, print the confirmed prompt on stdout
python3 scripts/readback.py review PLAN.md --out-dir /tmp/readback-plan

# standalone artifact: read, annotate, edit the prompt offline; cannot send
python3 scripts/readback.py build session.json -o review.html
```

Shared flags: `--format markdown|transcript` (inferred from `.md`/`.json`, required when `INPUT` is `-`) and `--title TEXT`. `review` also takes `--no-open` (print the URL, launch no browser); `build` takes `--force`. Without `--out-dir`, `review` creates a fresh private temporary directory and prints it.

## Choosing the input

- **Markdown** — a plan, design doc, or PR body. Pass the file as it stands; the exact source is preserved and offered for copy/download.
- **Transcript JSON** — the `catchup --json` shape: `{agent, session_id, metadata, warnings, entries:[{index, kind, role, time, text}]}`. Only `entries[].text` is required; unknown fields are ignored.
- Resolve which session you are exporting explicitly — never assume the newest one, and reflect any subset (`--since-compact` and friends) in the description you give the user. Carry the exporter's `warnings` through; they are shown on the page.
- Do not rewrite the material into a briefing, and never reconstruct "verbatim" exchanges from memory or a compaction summary. A recorded summary goes in as a labeled summary entry.

## Delivery

Run `review` in the foreground and wait using whatever your harness supports. Status checks may yield, but do not kill or restart a review because it is taking a while — a human is reading, and there is no timeout on that.

| Exit | Meaning |
|---|---|
| 0 | Confirmed. stdout is the prompt verbatim, with no wrapper and no added trailing newline. |
| 1 | Operational failure (port, unwritable directory). |
| 2 | Invalid CLI or input (malformed transcript, empty document, `--out-dir` already holding a review). |
| 3 | The user cancelled. No prompt, no feedback. |
| 130 | Interrupted. |

On exit 0, treat the quoted passages as references and the user's comments as the feedback to address, under the current conversation's mode and authority. **Confirm & send** delivers feedback; it is not approval of the document, permission to implement a plan, or authorization for restricted actions. No non-zero exit is a user response — never read cancellation or an interrupt as agreement.

## When it fails

- **Process died after the user confirmed:** the prompt is already on disk. Read `<review-dir>/followup.md` (the exact confirmed text) and `result.json` (outcome and submission id). Never ask the user to write the feedback again.
- **Harness cannot hold a running command:** `build` the artifact instead, give the user the path, and take the prompt back through copy/download. Say plainly that delivery is manual — do not claim the review was delivered.
- **Browser did not open:** the URL is already on stderr; ask the user to open it, or re-run with `--no-open`.
- **`--out-dir` refused:** it already contains a review. Choose an empty directory rather than replacing earlier feedback.

## Notes

- Review directory: `review.html` (standalone, carries no live credentials), `source.json` (immutable normalized input and SHA-256 fingerprint), `followup.md` (written atomically, only on confirm), `result.json`. Keep generated review directories out of this package.
- Annotations, prompt draft, and dirty state autosave in `localStorage` keyed by fingerprint. Editing the source starts a clean draft; an annotation whose quote no longer verifies at its stored offsets stays visible as unresolved instead of reattaching to another occurrence of the same text.
- The page is offline and CSP-locked: raw HTML in Markdown is inert, images do not load, links open with `noopener`. Only the live page reaches the loopback server, which checks a per-review token, Host, and same-origin `Origin`.
- Tests: `python3 scripts/test_readback.py`.
