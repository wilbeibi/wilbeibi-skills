# wilbeibi-skills

Personal agent skills packaged for `npx skills`.

## Install And Update

Use `npx skills` to install skills from this repo into Claude Code, Codex, or both.

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

Install all skills for both agents:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a claude-code codex
```

Install globally instead of only for the current project:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a claude-code codex --global
```

Update installed skills to the latest version from this repo:

```bash
npx skills update
```

Update only global installs:

```bash
npx skills update --global
```

Update only project installs:

```bash
npx skills update --project
```

Update one skill:

```bash
npx skills update test-writing
```

List installed skills:

```bash
npx skills list
npx skills list --global
npx skills list -a claude-code
npx skills list -a codex
```

By default, `skills add` links installed skill files into agent directories. Use `--copy` only when you want a detached copy that will not track local edits through the symlink.

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
- [skill-curator](skills/skill-curator/SKILL.md): Audit and de-duplicate an existing skill library — forked scripts, contradictory instructions, bloat, internal defects.
- [grill-me](skills/grill-me/SKILL.md): Relentlessly interview the user one question at a time to stress-test a plan or design.
- [code-review-burntsushi](skills/code-review-burntsushi/SKILL.md): Review code for honest invariants, error boundaries, cost visibility, and API contracts (BurntSushi lens, works across languages).
- [write-readme](skills/write-readme/SKILL.md): Write or critique a README for an open-source lib or CLI tool using the inverted-pyramid structure.

## Layout

Each skill lives in `skills/<skill-name>/SKILL.md`. Supporting scripts live inside the same skill directory so each skill is self-contained.
