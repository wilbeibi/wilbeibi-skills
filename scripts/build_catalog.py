#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["PyYAML>=6.0.2"]
# ///
"""Generate metadata and file checksums without publishing skill bodies in the catalog, and the skill table in README.md."""
import argparse
import hashlib
import json
from pathlib import Path
import yaml

# Keep in sync with AGENT_DIRS in skills/route-skill/scripts/route_skill.py.
AGENTS = {"claude", "codex", "pi", "hermes"}
README_START = "<!-- skills-table:start -->"
README_END = "<!-- skills-table:end -->"


def purpose(description: str) -> str:
    """First sentence of the description, before any trigger clause."""
    head = description.split(" Use when")[0].split(" Use for")[0].split(" Use it")[0]
    head = head.split(". ")[0].rstrip(".")
    return head + "."


def readme_text(root: Path, rows: list) -> str:
    readme = root / "README.md"
    text = readme.read_text()
    start, end = text.index(README_START), text.index(README_END)
    lines = ["| Skill | Use it for |", "|---|---|"]
    for row in rows:
        note = f" ({'/'.join(a.capitalize() for a in row['agents'])} only)" if row["agents"] else ""
        lines.append(f"| [{row['name']}]({row['path']}/SKILL.md) | {purpose(row['description'])}{note} |")
    table = "\n".join(lines)
    return text[: start + len(README_START)] + "\n" + table + "\n" + text[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    rows = []
    for skill in sorted((root / "skills").iterdir()):
        md = skill / "SKILL.md"
        if not md.is_file():
            continue
        data = yaml.safe_load(md.read_text().split("---", 2)[1])
        files = []
        for path in sorted(skill.rglob("*")):
            if any(p.startswith(".") or p == "__pycache__" for p in path.relative_to(skill).parts):
                continue
            if path.is_symlink():
                raise ValueError(f"catalog does not support symlinks: {path}")
            if path.is_file():
                files.append({"path": path.relative_to(skill).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "executable": bool(path.stat().st_mode & 0o111)})
        agents = data.get("agents") or []
        if isinstance(agents, str):
            agents = [agents]
        unknown = set(agents) - AGENTS
        if unknown:
            raise ValueError(f"unknown agents {sorted(unknown)} in {md}; known: {sorted(AGENTS)}")
        rows.append({"name": data["name"], "description": data["description"], "compatibility": data.get("compatibility", ""), "agents": sorted(agents), "path": f"skills/{skill.name}", "files": files})
        if data["name"] != skill.name:
            raise ValueError(f"name must match directory: {skill}")
    text = json.dumps({"schema": 1, "skills": rows}, indent=2, ensure_ascii=False) + "\n"
    destination = root / "catalog.json"
    readme = readme_text(root, rows)
    if args.check:
        if not destination.is_file() or destination.read_text() != text:
            raise SystemExit("catalog is stale; run uv run scripts/build_catalog.py")
        if (root / "README.md").read_text() != readme:
            raise SystemExit("README skill table is stale; run uv run scripts/build_catalog.py")
    else:
        destination.write_text(text)
        (root / "README.md").write_text(readme)
    print(f"Catalog: {len(rows)} skills")


if __name__ == "__main__":
    main()
