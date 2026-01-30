# YouTube Transcript to Obsidian Note

Transform YouTube video transcripts into comprehensive, article-style Obsidian notes with proper formatting, timestamps, and structured analysis.

## Features

- **Automatic transcript extraction** using `yt-dlp`
- **Obsidian-optimized formatting** with callouts, bold/italic styling, and inline code
- **Structured output** with YAML frontmatter, metadata, overview, and section breakdowns
- **Timestamp preservation** for easy reference back to the video
- **Content analysis** that walks through videos step-by-step without over-condensing
- **Smart callouts** for quotes, tips, warnings, and important notes

## Prerequisites

Install `yt-dlp` to enable automatic transcript extraction:

```bash
pip install yt-dlp
```

## Usage

Simply provide a YouTube URL or ask to analyze/transform a YouTube video:

```
Analyze this YouTube video: https://www.youtube.com/watch?v=...
```

```
Create an Obsidian note from this YouTube transcript
```

The skill will:
1. Extract the transcript using `yt-dlp`
2. Analyze and structure the content
3. Apply Obsidian formatting (callouts, bold, italic, inline code)
4. Save as a formatted Markdown file with YAML frontmatter

## Output Format

Generated notes include:
- **YAML frontmatter** with title, date, tags, source, and author
- **Metadata section** with channel/author and source URL
- **Overview** summarizing the video's core argument
- **Section breakdown** with timestamps and detailed analysis
- **Key takeaways** (optional)

Files are saved with the format: `YYYY-MM-DD - [Video Title].md`

## Installation

```bash
/plugin install youtube-transcript@wilbeibi-toolkit
```
