# Migrating to route-skill

For hosts that already installed this repo with `npx skills add … --all` or the old `load-skill` linker.
New machines can ignore this file and follow the README quickstart.

## Target state

- One checkout of this repo on the host.
- `route-skill` linked globally. Link other skills only when you want them always available.
- Occasional skills loaded with `route_skill.py get` after you explicitly select them (cache under `~/.cache/route-skill`).
- Host `skills-sync` only repairs checkout-owned links. It must not run `npx skills add … --all`.

## Steps

Commands below use `~/src/wilbeibi-skills`. Adjust the path if your checkout differs.

1. Update the checkout to a revision that contains `skills/route-skill/` and `catalog.json`.

```bash
cd ~/src/wilbeibi-skills
git pull --ff-only
```

2. Replace the host sync wrapper so housekeeping cannot reinstall every skill.

```bash
cat > ~/.config/bin/skills-sync <<'EOF'
#!/bin/sh
set -e
exec "$HOME/src/wilbeibi-skills/bin/skills-sync" "$@"
EOF
chmod +x ~/.config/bin/skills-sync
```

If this host protects local edits with `~/.agents/skills/.local-changes`, keep that check in the wrapper and exit before calling the repo script.

3. Enable the router.

```bash
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py link route-skill
```

4. Convert installed **repo** skills from copied directories into checkout-owned symlinks.
   Leave third-party or machine-local skills alone (for example `impeccable`, `web-search`, `zhihu`).

```bash
root=$HOME/src/wilbeibi-skills
router=$root/skills/route-skill/scripts/route_skill.py
for skill in "$root"/skills/*; do
  [ -f "$skill/SKILL.md" ] || continue
  name=$(basename "$skill")
  target=$HOME/.agents/skills/$name
  [ -e "$target" ] || [ -L "$target" ] || continue
  if [ -L "$target" ] && [ "$(realpath "$target")" = "$(realpath "$skill")" ]; then
    continue
  fi
  rm -rf "$HOME/.agents/skills/$name"
  for agent in .claude/skills .codex/skills .pi/agent/skills .hermes/skills; do
    path=$HOME/$agent/$name
    [ -e "$path" ] || [ -L "$path" ] || continue
    rm -rf "$path"
  done
  python3 "$router" link "$name"
done
python3 "$router" sync
```

`link` refuses to overwrite unmanaged targets. Remove the old copy first.

5. Smoke-test.

```bash
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py list chart
python3 ~/src/wilbeibi-skills/skills/route-skill/scripts/route_skill.py get write-docs
```

`get` prints a `SKILL.md` path on stdout. Skills that were never installed stay on-demand until you select them.

## Do not

- Run `npx skills add wilbeibi/wilbeibi-skills --all` on a migrated host.
- Delete machine-local skills that are not in this repo.
- Commit project-level `.agents/skills` or `.claude/skills` links. Keep those links host-specific.

## After migration

- Update content with `bin/skills-sync --pull` (or `git pull` in the checkout). Owned links follow the checkout.
- Refresh remote catalog/cache only when you ask: `route_skill.py list --refresh` or `get NAME --refresh`.
- Point host agent docs (AGENTS.md / housekeeping runbooks) at this model so future agents do not revive `--all`.
