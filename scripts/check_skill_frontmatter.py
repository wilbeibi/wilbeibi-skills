#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["PyYAML>=6.0.2"]
# ///

from pathlib import Path
import sys

import yaml


def main() -> int:
    skill_files = sorted(Path("skills").glob("*/SKILL.md"))
    if not skill_files:
        print("No skill files found under skills/*/SKILL.md", file=sys.stderr)
        return 1

    errors: list[str] = []

    for path in skill_files:
        text = path.read_text()
        if not text.startswith("---\n"):
            errors.append(f"{path}: missing YAML frontmatter")
            continue

        try:
            _, frontmatter, _ = text.split("---\n", 2)
        except ValueError:
            errors.append(f"{path}: missing closing YAML frontmatter delimiter")
            continue

        try:
            data = yaml.safe_load(frontmatter)
        except yaml.YAMLError as exc:
            errors.append(f"{path}: invalid YAML frontmatter: {exc}")
            continue

        if not isinstance(data, dict):
            errors.append(f"{path}: frontmatter must be a YAML mapping")
            continue

        for key in ("name", "description"):
            value = data.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{path}: {key} must be a non-empty string")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Validated {len(skill_files)} skill frontmatter blocks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
