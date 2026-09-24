# wilbeibi-skills

> A trillion-parameter brain to wash my digital dishes.

These are the skills I keep around for Claude Code and Codex. Most began as a prompt I got tired of retyping: how I want a diff reviewed, when a test deserves to be committed, how to get my bearings in a repo I've never seen. Some are useful anywhere. Others only make sense on my machines, like the ones that assume a Mac running Hammerspoon or my Obsidian vault's layout.

Browse [`skills/`](skills/) and take what fits. Each skill is one folder with a `SKILL.md` at its root, so you can copy a single folder into your agent's skills directory and ignore the rest of the repo.

## Let the router pick

If you don't want to decide up front, link the router once (Python 3.10+):

```bash
git clone https://github.com/wilbeibi/wilbeibi-skills ~/src/wilbeibi-skills
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link route-skill
```

Then describe the job to your agent in plain words, such as "review this diff" or "why did this function change last spring?" The router suggests a skill and waits for you to choose before it loads anything. Asking what a skill does won't load it either.

To see what's available, run `route_skill.py list`, optionally with a word to filter on. `get <name>` loads a skill from your checkout or cache, and fetches it from GitHub only when it's missing. Downloads are checked against `catalog.json` and cached under `${XDG_CACHE_HOME:-~/.cache}/route-skill` until you pass `--refresh`.

## Keep a skill around

Loading a skill once leaves nothing behind. To keep one available, link it globally or for a single project:

```bash
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link code-review
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link test-writing --project
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py unlink test-writing --project
```

Global links go into `~/.agents/skills` and any Claude, Codex, Pi, or Hermes skill directories that already exist. Project links go into `.agents/skills` and `.claude/skills` in the current directory; keep them out of commits, for example with `.git/info/exclude`. The router never overwrites a real directory or a link it doesn't own.

To update, run `bin/skills-sync --pull`. It pulls with `--ff-only` and repairs the links this checkout owns. It never enables anything new. If you installed with `npx skills add … --all` or the old `load-skill`, follow [MIGRATION.md](MIGRATION.md) first.

## Limits

Persistent links need a checkout; a standalone copy of the router can only discover and fetch. The downloader is unauthenticated, so private GitHub repos won't work, and other sources must publish this repo's `catalog.json` format (select one with `--repo owner/repo --ref <branch-or-commit> --remote`). Skills report their requirements, but nothing gets installed for you.

## Changing a skill

Regenerate `catalog.json` whenever skill files change; CI rejects stale metadata and checksums. Run the same checks locally before pushing:

```bash
uv run scripts/check_skill_frontmatter.py
uv run scripts/build_catalog.py
python3 skills/route-skill/scripts/test_route_skill.py
```
