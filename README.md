# Claude Toolkit

My junk drawer of non-deterministic scripts:

- **[Obsidian](plugins/obsidian/skills/vault-search/skill.md)**: Search your [Obsidian](https://obsidian.md/) vault using natural language queries with date/tag/content filters (uses ripgrep on local files).
- **YouTube Transcript**: Transform YouTube video transcripts into comprehensive Obsidian notes with timestamps and structured analysis.
- **[Dayflow](plugins/dayflow/skills/dayflow-review.md)**: Query and analyze your local [Dayflow](https://github.com/JerryZLiu/Dayflow) time-tracking database.
- **[m-cli](plugins/m-cli/skills/m-cli.md)**: Control macOS system settings with [m-cli](https://github.com/rgcr/m-cli) (who doesn't want to switch to dark mode in Claude Code?).
- **[Code Review: Russ Cox](plugins/code-review/skills/code-review-russ-cox.md)**: Review code through the lens of simplicity, orthogonality, and anti-bloat philosophy.
- **[Code Review: Armin Ronacher](plugins/code-review/skills/code-review-mitsuhiko.md)**: Review code with pragmatic focus on context-appropriate design, minimal dependencies, and stability.
- **Testing**: Guidance on writing effective, maintainable tests.
- **[Newcomer Lens Review](plugins/newcomer-lens-review/skills/newcomer-lens-review.md)**: Review code like you just joined the team and ask "why did we do this?"


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

# Install Newcomer Lens Review
/plugin install newcomer-lens-review@wilbeibi-toolkit
```
