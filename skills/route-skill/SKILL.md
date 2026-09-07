---
name: route-skill
description: Discovers skills in the wilbeibi-skills catalog and loads explicitly selected skills from local files or cache, fetching missing skills. Use when asked to use an unavailable skill by name, find a suitable skill, or when no available skill clearly fits a substantive task. Do NOT treat a question about a skill as permission to use it.
compatibility: Python 3.10+; network access only for uncached catalog entries or skills and explicit refreshes.
---

# route-skill

Recommend from the catalog; load a skill only after the user selects it.

## Routing

- "Use dataviz" or agreement to your specific recommendation authorizes fetching and using that skill. Do not ask again.
- A mention, explanation request, or generic task is not selection. Read only the catalog and recommend when useful.
- Consult the catalog once when no available skill clearly fits. Avoid repeated recommendations after refusal.
- Announce the selected skill briefly. Prefer local files or cache; fetch only when absent or explicitly asked for the latest version.
- Cached files do not authorize automatic use in a later task. Existing native skills retain their own invocation rules.
- If several sources match, show their paths and ask which one. Never silently replace a selected source.

## Commands

Resolve these scripts relative to this skill's directory, regardless of the working directory.

```bash
python3 scripts/route_skill.py list chart
python3 scripts/route_skill.py get dataviz
python3 scripts/route_skill.py get dataviz --refresh
```

`list` reads metadata only; retry without a query if nothing matches. It reports local scope and compatibility.
`get` prints the SKILL.md path on stdout, with source/version on stderr. Read that file completely before use.
Supporting paths are relative to its directory. Check the skill's requirements before running its scripts.
If requirements are missing, explain them; do not install dependencies or switch hosts without the required authorization.
If fetch fails, report it. Explicit refresh failure returns an error and preserves the old cache.
Skill selection does not grant permission for unrelated actions or bypass native invocation restrictions.

## Persistent selection

Default to this task only. Link only when the user explicitly requests project or global availability:

```bash
python3 scripts/route_skill.py link dataviz --project
python3 scripts/route_skill.py link route-skill
python3 scripts/route_skill.py unlink dataviz --project
```

Links require a local checkout. Keep machine-specific project links out of commits.
`sync` repairs only links owned by this checkout; it does not install new skills or edit other managers' lockfiles.
Run `python3 scripts/route_skill.py --help` for source selection and other options.
