# YouTube Transcript to Obsidian Note

Use this skill when the user asks to "analyze YouTube video", "transform YouTube transcript", "create Obsidian note from YouTube", "summarize YouTube video", or provides a YouTube URL for detailed note-taking.

## Workflow

1. **Get YouTube URL**: If not provided, ask the user for the YouTube URL
2. **Extract transcript**: Use the Bash tool to run `yt-dlp --write-subs --write-auto-subs --skip-download <youtube_url>` to download subtitle files
3. **Read transcript**: Use the Read tool to read the downloaded subtitle file (.vtt or .srt format)
4. **Transform content**: Apply the content analysis and formatting rules below
5. **Ask for save location**: Ask the user where to save the note (suggest `~/Documents/` or their Obsidian vault path)
6. **Write note**: Use the Write tool to save the formatted Markdown file with a descriptive filename based on the video title

---

## Content Analysis Rules

* **Depth & Precision:** Never over-condense. Walk through the video step-by-step in simple language.
* **Frameworks:** If a method, process, or framework appears, rewrite it as clear, well-structured steps or paragraphs.
* **Ambiguity:** Do not add new facts. If the source is ambiguous, preserve the original meaning and explicitly note the uncertainty.
* **Timestamps:** Extract and include timestamps for every important section.

## Obsidian Formatting Rules

You must apply the following specific formatting syntax to the content:

* **Callouts:** Use Obsidian callouts for specific content types:
    * `> [!quote]` for noteworthy lines or quotes worth pondering.
    * `> [!tip]` for actionable advice, methods, or best practices.
    * `> [!warning]` for common pitfalls or things to avoid.
    * `> [!note]` for important clarifications, uncertainties, or caveats.
* **Styling:**
    * Use **bold** for key concepts (first mention only).
    * Use *italic* for subtle emphasis.
    * Use `inline code` for technical terms, specific commands, or tools.
* **Structure:** Use `##` for main sections and `###` for subsections.

## Output Structure

Your **ENTIRE** response should be written to a single Markdown file using the Write tool.

### A. YAML Frontmatter
Add this at the very top (no code fences, just raw YAML):

---
title: (Create a descriptive title based on the content)
date: (Today's date YYYY-MM-DD)
tags: [youtube, video-notes, tag1, tag2]
source: (Video URL)
author: (Video Creator Name)
---

### B. Metadata Section
* **Channel/Author:** [Name]
* **Source URL:** [Link]
* **Duration:** [If available from video metadata]

### C. Overview
* A single, high-level paragraph stating the video's core argument and conclusion.

### D. Section Breakdown
* For each major topic/segment:
    * **Heading:** (Topic Name)
    * **Timestamp:** (e.g., 04:20)
    * **Content:** The detailed explanation, steps, or analysis using the formatting rules defined above.
        * If any claim is uncertain, mark it [uncertain] with a brief note.
        * If there are good lines/quotes worth readers pondering, keep the quote (use quote callout).

### E. Key Takeaways (Optional)
* Bullet points of main insights or action items

---

## File Naming Convention

Use this format: `YYYY-MM-DD - [Video Title].md`

Example: `2026-01-29 - How to Build Better AI Agents.md`

## Error Handling

* If `yt-dlp` is not installed, inform the user and ask them to install it: `pip install yt-dlp`
* If no subtitles are available, inform the user that automatic transcription might not be available
* If the user prefers to provide the transcript manually, accept it and proceed with the transformation
