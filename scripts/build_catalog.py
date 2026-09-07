#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["PyYAML>=6.0.2"]
# ///
"""Generate metadata and file checksums without publishing skill bodies in the catalog."""
import argparse
import hashlib
import json
from pathlib import Path
import yaml


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
        rows.append({"name": data["name"], "description": data["description"], "compatibility": data.get("compatibility", ""), "path": f"skills/{skill.name}", "files": files})
        if data["name"] != skill.name:
            raise ValueError(f"name must match directory: {skill}")
    text = json.dumps({"schema": 1, "skills": rows}, indent=2, ensure_ascii=False) + "\n"
    destination = root / "catalog.json"
    if args.check:
        if not destination.is_file() or destination.read_text() != text:
            raise SystemExit("catalog is stale; run uv run scripts/build_catalog.py")
    else:
        destination.write_text(text)
    print(f"Catalog: {len(rows)} skills")


if __name__ == "__main__":
    main()
