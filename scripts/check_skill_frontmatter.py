#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["PyYAML>=6.0.2"]
# ///

from pathlib import Path
import re
import sys

import yaml

# Cross-pointers in descriptions: "(use show-me)" anywhere, or a bare "(grill-me)" after "Do NOT".
USE_POINTER = re.compile(r"\(use `?([a-z0-9-]+)`?\)")
BARE_POINTER = re.compile(r"\(([a-z0-9]+(?:-[a-z0-9]+)+)\)")


def main() -> int:
    skill_files = sorted(Path("skills").glob("*/SKILL.md"))
    if not skill_files:
        print("No skill files found under skills/*/SKILL.md", file=sys.stderr)
        return 1

    names = {path.parent.name for path in skill_files}
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
            raw = next((line for line in frontmatter.splitlines() if line.startswith(f"{key}:")), "")
            if " #" in raw and not raw[len(key) + 1 :].lstrip().startswith(('"', "'")):
                errors.append(f"{path}: {key} contains ' #', which YAML reads as a comment; quote the value or drop the '#'")

        description = data.get("description") if isinstance(data.get("description"), str) else ""
        targets = set(USE_POINTER.findall(description)) | set(BARE_POINTER.findall(description.partition("Do NOT")[2]))
        for target in sorted(targets - names):
            errors.append(f"{path}: description points to '{target}', which is not a skill under skills/")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Validated {len(skill_files)} skill frontmatter blocks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
