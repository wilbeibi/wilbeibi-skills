---
name: youtube-transcript
description: Transform YouTube videos or transcripts into structured Obsidian notes with timestamps, metadata, callouts, and detailed section breakdowns. Use when the user provides a YouTube URL or asks to summarize, analyze, or convert a YouTube video into notes.
---

# youtube-transcript

Turn a YouTube URL or supplied transcript into a timestamped Obsidian note.

## Workflow

1. If neither URL nor transcript is provided, ask once for the missing source.
2. For a URL, run `scripts/extract_subtitle.py <url>` and read the selected `.vtt` or `.srt` path from its JSON output.
3. If extraction fails because `yt-dlp` is missing or subtitles are unavailable, say so and accept a manual transcript.
4. Transform the transcript using [TEMPLATE.md](TEMPLATE.md); load it before writing the note.
5. Ask for a save location only if the user did not provide one. Use `YYYY-MM-DD - [Video Title].md`.

## Content Rules

- Never invent facts; mark ambiguous claims as `[uncertain: reason]`.
- Preserve timestamps for every important section.
- Explain methods, frameworks, and processes as clear steps or paragraphs.
- Use Obsidian callouts for quotes, tips, warnings, notes, and caveats.

## Script

```bash
scripts/extract_subtitle.py "https://www.youtube.com/watch?v=..."
```

The script prints JSON with `subtitle_paths`, `best_subtitle`, and captured `yt-dlp` output. Prefer `best_subtitle`; inspect the raw files before summarizing.
