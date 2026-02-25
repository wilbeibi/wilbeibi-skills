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

First, add the marketplace:

```bash
/plugin marketplace add wilbeibi/claude-toolkit
```

Then install any plugin:

```bash
/plugin install obsidian@claude-toolkit
/plugin install youtube-transcript@claude-toolkit
/plugin install dayflow@claude-toolkit
/plugin install m-cli@claude-toolkit
/plugin install code-review@claude-toolkit
/plugin install testing@claude-toolkit
/plugin install newcomer-lens-review@claude-toolkit
```
