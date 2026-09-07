#!/usr/bin/env python3
"""Discover metadata, get explicitly selected skills, and manage checkout-owned links."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote
from urllib.request import urlopen


def read_json(path):
    return json.loads(path.read_text())


def download(url):
    with urlopen(url, timeout=30) as response:
        return response.read()


def valid_name(name):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(f"invalid skill name: {name!r}")
    return name


def checkout():
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists() and (parent / "skills").is_dir():
            return parent
    return None


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as out:
        temporary = Path(out.name)
        json.dump(value, out, indent=2)
        out.write("\n")
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class Store:
    def __init__(self, repo, ref, remote=False):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("source must be owner/repo")
        self.repo, self.ref = repo, ref
        self.root = None if remote or repo != "wilbeibi/wilbeibi-skills" else checkout()
        identity = hashlib.sha256(f"{repo}@{ref}".encode()).hexdigest()[:20]
        self.cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "route-skill" / identity

    def catalog(self, refresh=False):
        if self.root and not refresh:
            return read_json(self.root / "catalog.json"), "checkout"
        cached = self.cache / "catalog.json"
        if cached.is_file() and not refresh:
            entry = read_json(cached)
            return entry["catalog"], entry["revision"]
        commit = json.loads(download(f"https://api.github.com/repos/{self.repo}/commits/{quote(self.ref, safe='')}"))
        revision = commit["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("invalid source revision")
        data = json.loads(download(f"https://raw.githubusercontent.com/{self.repo}/{revision}/catalog.json"))
        if data.get("schema") != 1 or not isinstance(data.get("skills"), list):
            raise ValueError("unsupported catalog; expected schema 1")
        atomic_json(cached, {"revision": revision, "catalog": data})
        return data, revision

    def get(self, name, refresh=False):
        valid_name(name)
        if self.root and not refresh and (self.root / "skills" / name / "SKILL.md").is_file():
            revision = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "--short", "HEAD"], text=True).strip()
            dirty = subprocess.check_output(["git", "-C", str(self.root), "status", "--porcelain", "--", f"skills/{name}"], text=True)
            return self.root / "skills" / name, f"checkout {revision}{' + local edits' if dirty else ''}"
        if self.root and not refresh:
            raise ValueError(f"no skill {name!r} in this checkout; use --remote to fetch from {self.repo}")
        pointer = self.cache / f"{name}.json"
        if pointer.is_file() and not refresh:
            entry = read_json(pointer)
            directory = self.cache / "snapshots" / entry["snapshot"] / name
            self.verify(directory, entry["files"])
            return directory, f"cache {entry['revision']}"
        catalog, revision = self.catalog(refresh)
        rows = [r for r in catalog["skills"] if r["name"] == name]
        if len(rows) != 1:
            raise ValueError(f"unknown or ambiguous skill {name!r}; run list --refresh to update the catalog")
        files = rows[0]["files"]
        if not any(f["path"] == "SKILL.md" for f in files):
            raise ValueError("catalog entry lacks SKILL.md")
        snapshots = self.cache / "snapshots"
        snapshots.mkdir(parents=True, exist_ok=True)
        # mkdtemp + rename keeps existing snapshot paths usable by running tasks.
        stage_root = Path(tempfile.mkdtemp(prefix="fetch-", dir=snapshots))
        try:
            stage = stage_root / name
            for item in files:
                relative = self.safe_path(item["path"])
                target = stage / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                content = download(f"https://raw.githubusercontent.com/{self.repo}/{revision}/skills/{name}/{quote(relative.as_posix())}")
                if hashlib.sha256(content).hexdigest() != item["sha256"]:
                    raise ValueError(f"checksum mismatch: {name}/{relative}")
                target.write_bytes(content)
                target.chmod(0o755 if item.get("executable") else 0o644)
            self.verify(stage, files)
            destination = snapshots / (stage_root.name + "-ready")
            stage_root.rename(destination)
        except Exception:
            shutil.rmtree(stage_root, ignore_errors=True)
            raise
        atomic_json(pointer, {"snapshot": destination.name, "revision": revision, "files": files})
        return destination / name, f"fetched {revision}"

    @staticmethod
    def safe_path(value):
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or not path.parts or "\\" in value:
            raise ValueError(f"unsafe catalog path: {value!r}")
        return path

    @classmethod
    def verify(cls, directory, files):
        for item in files:
            path = directory / cls.safe_path(item["path"])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError(f"incomplete or changed cache: {path}; use get NAME --refresh")


def project_dirs():
    here = Path.cwd()
    for parent in (here, *here.parents):
        yield parent / ".agents" / "skills"
        yield parent / ".claude" / "skills"
        if (parent / ".git").exists() or parent == Path.home():
            break


def local_candidates(name):
    paths = [d / name for d in project_dirs()]
    paths += [Path.home() / ".agents" / "skills" / name,
              Path.home() / ".claude" / "skills" / name,
              Path.home() / ".codex" / "skills" / name]
    return sorted({p.resolve() for p in paths if (p / "SKILL.md").is_file()})


def agent_dirs():
    home = Path.home()
    return [home / ".claude/skills", home / ".codex/skills",
            home / ".pi/agent/skills", home / ".hermes/skills"]


def owned(path, root):
    return path.is_symlink() and path.resolve().parent == root / "skills"


def link_paths(name, project):
    if project:
        return [Path.cwd() / d / "skills" / name for d in (".agents", ".claude")]
    return [Path.home() / ".agents/skills" / name] + [d / name for d in agent_dirs() if d.parent.is_dir()]


def change_links(root, names, project, remove=False):
    if root is None:
        raise ValueError("persistent links require a local checkout")
    operations = []
    for name in names:
        valid_name(name)
        target = root / "skills" / name
        if not remove and not (target / "SKILL.md").is_file():
            raise ValueError(f"no local skill {name!r}")
        for path in link_paths(name, project):
            if path.exists() or path.is_symlink():
                if not owned(path, root) or path.resolve() != target:
                    raise ValueError(f"unmanaged target; leaving unchanged: {path}")
                if remove:
                    operations.append((path, None))
            elif not remove:
                operations.append((path, target))
    for path, target in operations:
        if target is None:
            path.unlink()
            print(f"removed {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(os.path.relpath(target, path.parent))
            print(f"linked {path}")
    if not operations:
        print("no changes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("list", "get", "link", "unlink", "sync"):
        p = sub.add_parser(command)
        p.add_argument("--repo", default=os.environ.get("LOAD_SKILL_REPO", "wilbeibi/wilbeibi-skills"))
        p.add_argument("--ref", default=os.environ.get("LOAD_SKILL_REF", "main"))
        p.add_argument("--remote", action="store_true", help="select repository source instead of installed/local skills")
        if command in ("list", "get"):
            p.add_argument("--refresh", action="store_true", help="fetch current remote metadata/content; preserve old cache on failure")
        if command == "list":
            p.add_argument("query", nargs="?", default="")
        if command == "get":
            p.add_argument("name")
        if command in ("link", "unlink"):
            p.add_argument("names", nargs="+")
            p.add_argument("-p", "--project", action="store_true")
    args = parser.parse_args()
    store = Store(args.repo, args.ref, args.remote or args.ref != "main")
    if args.command == "get":
        valid_name(args.name)
        candidates = [] if args.remote or args.refresh or args.repo != "wilbeibi/wilbeibi-skills" or args.ref != "main" else local_candidates(args.name)
        if len(candidates) > 1:
            raise ValueError("multiple local sources; choose and read one directly, or use --remote:\n" + "\n".join(map(str, candidates)))
        if candidates:
            directory, source = candidates[0], f"installed local {candidates[0]}"
        else:
            directory, source = store.get(args.name, args.refresh)
        print(directory / "SKILL.md")
        print(f"route-skill: {source}", file=sys.stderr)
    elif args.command == "list":
        catalog, revision = store.catalog(args.refresh)
        rows = [r for r in catalog["skills"] if args.query.lower() in (r["name"] + " " + r["description"]).lower()]
        if not rows:
            raise ValueError("no matching skill; run list without a query")
        for row in rows:
            name = valid_name(row["name"])
            local = local_candidates(name)
            status = "local: " + ", ".join(map(str, local)) if local else "catalog"
            print(f"{name}: {row['description']}\n  [{status}] requires: {row.get('compatibility') or 'see skill instructions'}")
        print(f"route-skill: {args.repo}@{revision}", file=sys.stderr)
    elif args.command in ("link", "unlink"):
        change_links(store.root, args.names, args.project, args.command == "unlink")
    else:
        if store.root is None:
            raise ValueError("sync requires a local checkout")
        canonical = Path.home() / ".agents/skills"
        for path in sorted(canonical.iterdir()) if canonical.is_dir() else []:
            if owned(path, store.root):
                change_links(store.root, [path.name], False, not (path / "SKILL.md").is_file())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"route-skill: {error}", file=sys.stderr)
        raise SystemExit(1)
