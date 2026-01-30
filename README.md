# Claude Toolkit

My junk drawer of non-deterministic scripts:

- **[Obsidian](https://obsidian.md/)**: Search your vault using natural language queries with date/tag/content filters (uses ripgrep on local files).
- **YouTube Transcript**: Transform YouTube video transcripts into comprehensive Obsidian notes with timestamps and structured analysis.
- **[Dayflow](https://github.com/JerryZLiu/Dayflow)**: Query and analyze your local time-tracking database.
- **[m-cli](https://github.com/rgcr/m-cli)**: Control macOS system settings (who doesn't want to switch to dark mode in Claude Code?).
- **Code Review**: Russ Cox's philosophy for maintainable software.
- **Testing**: Guidance on writing effective, maintainable tests.


## Installation

### 1. Add the Marketplace
First, in Claude Code terminal:

```bash
/plugin marketplace add https://github.com/wilbeibi/claude-toolkit
```

### 2. Install Individual Tools
Once the marketplace is added, you can install specific tools using their names:

```bash
# Install Obsidian integration
/plugin install obsidian@wilbeibi-toolkit

# Install YouTube Transcript tool
/plugin install youtube-transcript@wilbeibi-toolkit

# Install Dayflow review tools
/plugin install dayflow@wilbeibi-toolkit

# Install macOS system tools
/plugin install m-cli@wilbeibi-toolkit

# Install Code Review philosophy
/plugin install code-review@wilbeibi-toolkit

# Install Testing guidance
/plugin install testing@wilbeibi-toolkit
```

