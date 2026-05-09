# wilbeibi-skills

Personal agent skills packaged for `npx skills`.

## Install

List available skills:

```bash
npx skills add wilbeibi/wilbeibi-skills --list
```

Install one skill:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill youtube-transcript
```

Install all skills for the detected agent:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*'
```

Install all skills for a specific agent:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a claude-code
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a codex
```

## Skills

- [obsidian-vault-search](skills/obsidian-vault-search/SKILL.md): Search an Obsidian vault using natural language queries, dates, tags, and task filters.
- [youtube-transcript](skills/youtube-transcript/SKILL.md): Transform YouTube videos or transcripts into structured Obsidian notes with timestamps and callouts.
- [dayflow-review](skills/dayflow-review/SKILL.md): Query and analyze a local Dayflow time-tracking database.
- [m-cli](skills/m-cli/SKILL.md): Control macOS system settings with the `m` CLI when explicitly requested.
- [test-writing](skills/test-writing/SKILL.md): Guide effective, maintainable test writing.
- [newcomer-lens-review](skills/newcomer-lens-review/SKILL.md): Review code for missing context, onboarding gaps, and undocumented assumptions.
- [code-review-russ-cox](skills/code-review-russ-cox/SKILL.md): Review code through a simplicity, orthogonality, and anti-bloat lens.
- [code-review-mitsuhiko](skills/code-review-mitsuhiko/SKILL.md): Review code with pragmatic focus on APIs, dependencies, compatibility, and user value.
- [write-skill](skills/write-skill/SKILL.md): Scaffold a new skill in this repo following progressive-disclosure and trigger-rich-description principles.

## Layout

Each skill lives in `skills/<skill-name>/SKILL.md`. Supporting scripts live inside the same skill directory so each skill is self-contained.
