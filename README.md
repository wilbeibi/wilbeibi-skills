# wilbeibi-skills

Personal agent skills packaged for `npx skills`.

## Skills

| Skill | Description |
|-------|-------------|
| [obsidian-vault-search](skills/obsidian-vault-search/SKILL.md) | Search an Obsidian vault using natural language queries, dates, tags, and task filters. |
| [youtube-transcript](skills/youtube-transcript/SKILL.md) | Transform YouTube videos or transcripts into structured Obsidian notes with timestamps and callouts. |
| [dayflow-review](skills/dayflow-review/SKILL.md) | Query and analyze a local Dayflow time-tracking database. |
| [m-cli](skills/m-cli/SKILL.md) | Control macOS system settings with the `m` CLI when explicitly requested. |
| [test-writing](skills/test-writing/SKILL.md) | Guide effective, maintainable test writing. |
| [newcomer-lens-review](skills/newcomer-lens-review/SKILL.md) | Review code for missing context, onboarding gaps, and undocumented assumptions. |
| [code-review-russ-cox](skills/code-review-russ-cox/SKILL.md) | Review code through a simplicity, orthogonality, and anti-bloat lens. |
| [code-review-mitsuhiko](skills/code-review-mitsuhiko/SKILL.md) | Review code with pragmatic focus on APIs, dependencies, compatibility, and user value. |
| [code-review-burntsushi](skills/code-review-burntsushi/SKILL.md) | Review code for honest invariants, error boundaries, cost visibility, and API contracts. |
| [grill-me](skills/grill-me/SKILL.md) | Relentlessly interview the user one question at a time to stress-test a plan or design. |
| [write-skill](skills/write-skill/SKILL.md) | Scaffold a new skill in this repo following progressive-disclosure and trigger-rich-description principles. |
| [skill-curator](skills/skill-curator/SKILL.md) | Audit and de-duplicate an existing skill library — forked scripts, contradictory instructions, bloat, internal defects. |
| [write-readme](skills/write-readme/SKILL.md) | Write or critique a README for an open-source lib or CLI tool using the inverted-pyramid structure. |

## Install

Install all skills (auto-detects Claude Code or Codex):

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*'
```

Install a single skill:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill test-writing
```

<details>
<summary>More install options</summary>

Target a specific agent:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a claude-code
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a codex
npx skills add wilbeibi/wilbeibi-skills --skill '*' -a claude-code codex
```

Install globally (all projects) instead of the current project only:

```bash
npx skills add wilbeibi/wilbeibi-skills --skill '*' --global
```

List available skills before installing:

```bash
npx skills add wilbeibi/wilbeibi-skills --list
```

By default, `skills add` symlinks skill files so local edits propagate automatically. Use `--copy` for a detached snapshot.

</details>

## Update

```bash
npx skills update
```

<details>
<summary>More update options</summary>

```bash
npx skills update --global          # global installs only
npx skills update --project         # project installs only
npx skills update test-writing      # one skill
```

</details>

## Layout

Each skill lives in `skills/<name>/SKILL.md`. Supporting scripts and reference docs are colocated in the same directory.
