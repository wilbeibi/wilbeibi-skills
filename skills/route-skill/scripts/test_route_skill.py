#!/usr/bin/env python3
"""Three offline CLI scenarios: discover/fetch, cache/refresh, link ownership."""
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("router", Path(__file__).with_name("route_skill.py"))
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)


class Scenarios(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.project = self.home / "project"
        self.project.mkdir()
        (self.project / ".git").mkdir()
        old_cwd = Path.cwd()
        os.chdir(self.project)
        self.addCleanup(os.chdir, old_cwd)
        self.env = patch.dict(os.environ, {
            "HOME": str(self.home),
            "XDG_CACHE_HOME": str(self.home / "cache"),
            "LOAD_SKILL_REPO": "wilbeibi/wilbeibi-skills",
            "LOAD_SKILL_REF": "main",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.checkout_mock = patch.object(router, "checkout", return_value=None).start()
        self.addCleanup(patch.stopall)
        self.revision = "a" * 40
        self.bodies = {
            "SKILL.md": b"---\nname: chart\ndescription: Draw charts\n---\nRead scripts/draw.py.\n",
            "scripts/draw.py": b"print('chart')\n",
            "assets/theme.txt": b"blue\n",
        }
        self.files = [
            {"path": p, "sha256": hashlib.sha256(b).hexdigest(), "executable": p.endswith(".py")}
            for p, b in self.bodies.items()
        ]
        self.catalog = {
            "schema": 1,
            "skills": [
                {"name": "chart", "description": "Draw charts", "compatibility": "Python", "files": self.files},
                {"name": "other", "description": "Unrelated", "files": []},
            ],
        }
        self.requests = []
        patch.object(router, "download", side_effect=self.download).start()

    def download(self, url):
        self.requests.append(url)
        if "/commits/" in url:
            return json.dumps({"sha": self.revision}).encode()
        if url.endswith("/catalog.json"):
            return json.dumps(self.catalog).encode()
        prefix = f"https://raw.githubusercontent.com/wilbeibi/wilbeibi-skills/{self.revision}/skills/chart/"
        if url.startswith(prefix):
            return self.bodies[url[len(prefix):]]
        raise AssertionError(f"unexpected download: {url}")

    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["route_skill.py", *args]), redirect_stdout(stdout), redirect_stderr(stderr):
            router.main()
        return stdout.getvalue(), stderr.getvalue()

    def get(self, *extra):
        output, _ = self.run_cli("get", "chart", *extra)
        return Path(output.strip())

    def test_discovery_and_first_use_fetch_only_selected_skill(self):
        output, _ = self.run_cli("list", "chart")
        self.assertIn("requires: Python", output)
        self.assertEqual(len(self.requests), 2)
        self.assertFalse(any("/skills/" in url for url in self.requests))
        self.requests.clear()
        self.run_cli("list")
        self.assertEqual(self.requests, [])

        md = self.get()
        self.assertEqual(md.read_bytes(), self.bodies["SKILL.md"])
        self.assertEqual((md.parent / "assets/theme.txt").read_bytes(), b"blue\n")
        self.assertTrue((md.parent / "scripts/draw.py").stat().st_mode & 0o111)
        self.assertEqual(len(self.requests), 3)
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse((self.project / ".agents").exists())

    def test_cache_reused_offline_and_failed_refresh_preserves_it(self):
        old = self.get()
        for path in (self.home / "cache").rglob("*"):
            os.utime(path, (1, 1))
        with patch.object(router, "download", side_effect=AssertionError("network forbidden")):
            self.assertEqual(self.get(), old)

        self.revision = "b" * 40
        self.bodies["assets/theme.txt"] = b"corrupt\n"
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            self.get("--refresh")
        self.assertEqual(self.get(), old)
        self.assertEqual((old.parent / "assets/theme.txt").read_bytes(), b"blue\n")

        self.bodies["assets/theme.txt"] = b"red\n"
        self.files[2]["sha256"] = hashlib.sha256(b"red\n").hexdigest()
        new = self.get("--refresh")
        self.assertNotEqual(old, new)
        self.assertEqual((old.parent / "assets/theme.txt").read_bytes(), b"blue\n")
        self.assertEqual((new.parent / "assets/theme.txt").read_bytes(), b"red\n")

    def test_links_respect_ownership_scope_and_conflicts(self):
        root = self.home / "checkout"
        skill = root / "skills/chart"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_bytes(self.bodies["SKILL.md"])
        self.checkout_mock.return_value = root
        for d in (".claude/skills", ".codex/skills", ".pi/agent/skills"):
            (self.home / d).mkdir(parents=True)

        conflict = self.home / ".codex/skills/chart"
        conflict.mkdir()
        with self.assertRaisesRegex(ValueError, "unmanaged target"):
            self.run_cli("link", "chart")
        self.assertFalse((self.home / ".agents/skills/chart").exists())
        conflict.rmdir()

        canon = self.home / ".agents/skills"
        (canon / "unrelated").mkdir(parents=True)
        lock = canon.parent / ".skill-lock.json"
        lock.write_text('{"skills":{"chart":{"source":"wilbeibi/wilbeibi-skills"}}}')
        before = lock.read_bytes()
        broken = self.home / ".claude/skills/broken"
        broken.symlink_to("/nonexistent/unrelated")

        self.run_cli("link", "chart")
        self.assertEqual((canon / "chart").resolve(), root / "skills/chart")
        mirror = self.home / ".codex/skills/chart"
        mirror.unlink()
        self.run_cli("sync")
        self.assertTrue(mirror.is_symlink())
        self.run_cli("unlink", "chart")
        self.assertFalse((canon / "chart").is_symlink())
        self.assertFalse(mirror.is_symlink())
        self.assertTrue(broken.is_symlink())
        self.assertFalse((self.home / ".claude/skills/unrelated").exists())
        self.assertEqual(lock.read_bytes(), before)

        self.run_cli("link", "chart", "-p")
        self.assertEqual((self.project / ".agents/skills/chart").resolve(), root / "skills/chart")
        self.assertFalse((self.home / ".agents/skills/chart").exists())


if __name__ == "__main__":
    unittest.main()
