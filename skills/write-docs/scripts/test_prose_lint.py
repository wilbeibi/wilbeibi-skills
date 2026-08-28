#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("prose_lint.py")


def run_lint(text: str, mode: str = "strict", *, json_output: bool = True):
    command = [sys.executable, str(SCRIPT), "--mode", mode]
    if json_output:
        command.append("--json")
    command.append("-")
    return subprocess.run(command, input=text, text=True, capture_output=True)


class ProseLintBehaviorTests(unittest.TestCase):
    def test_clean_strict_procedure_has_no_findings(self):
        result = run_lint("Open the valve.\n\nClose the access panel.")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["files"][0]["findings"], [])

    def test_strict_mode_reports_mechanical_rules_with_locations(self):
        text = (
            "Before you continue, verify that the local service has stopped and that no "
            "other process can write to the database during this operation.\n"
            "Don't restart it; inspect the log first.\n"
        )

        result = run_lint(text)
        findings = json.loads(result.stdout)["files"][0]["findings"]

        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            {(item["line"], item["rule"], item["severity"]) for item in findings},
            {
                (1, "sentence-length", "error"),
                (2, "contraction", "error"),
                (2, "semicolon", "error"),
            },
        )

    def test_natural_mode_allows_contractions_but_reviews_passive_voice(self):
        result = run_lint(
            "It's ready; the old cache was removed because its actor is irrelevant.",
            mode="natural",
        )
        findings = json.loads(result.stdout)["files"][0]["findings"]

        self.assertEqual(result.returncode, 0)
        self.assertEqual([item["rule"] for item in findings], ["possible-passive"])
        self.assertEqual(findings[0]["severity"], "review")

    def test_natural_sentence_length_is_a_review_prompt(self):
        text = (
            "This paragraph explains the design choice with enough surrounding context to "
            "help a future maintainer understand the tradeoff without opening the original issue or reading the implementation history."
        )

        result = run_lint(text, mode="natural")
        findings = json.loads(result.stdout)["files"][0]["findings"]

        self.assertEqual(result.returncode, 0)
        self.assertEqual(findings[0]["rule"], "sentence-length")
        self.assertEqual(findings[0]["severity"], "review")

    def test_markdown_metadata_code_and_urls_are_ignored(self):
        text = """---
title: Don't perform an analysis; use the tool
---

Run `don't; perform an analysis` and open https://example.com/seamless.

```text
Don't perform an analysis; this seamless line is intentionally long enough to fail every strict check in the checker.
```
"""

        result = run_lint(text)

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_high_confidence_phrases_are_review_findings(self):
        text = (
            "It is important to note that this seamless tool may potentially be able to "
            "perform an analysis of the report."
        )

        result = run_lint(text, mode="natural")
        rules = {item["rule"] for item in json.loads(result.stdout)["files"][0]["findings"]}

        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            rules,
            {"empty-intro", "marketing-claim", "nominalized-action", "stacked-hedge"},
        )

    def test_readme_marketing_claims_are_review_findings(self):
        result = run_lint(
            "This robust and powerful tool gives instant results with no re-explaining.",
            mode="natural",
        )
        findings = json.loads(result.stdout)["files"][0]["findings"]

        self.assertEqual(result.returncode, 0)
        self.assertEqual({item["rule"] for item in findings}, {"marketing-claim"})

    def test_initialism_does_not_hide_a_long_strict_sentence(self):
        text = (
            "Use the U.S. region when the account needs residency controls and the "
            "administrator must retain every audit record for seven years."
        )

        result = run_lint(text)
        findings = json.loads(result.stdout)["files"][0]["findings"]

        self.assertEqual(result.returncode, 1)
        self.assertEqual([item["rule"] for item in findings], ["sentence-length"])

    def test_table_cells_are_checked_but_delimiter_rows_are_not(self):
        text = """| Claim | Value |
|---|---|
| Quality | This seamless product changes everything. |
"""

        result = run_lint(text, mode="natural")
        findings = json.loads(result.stdout)["files"][0]["findings"]

        self.assertEqual(result.returncode, 0)
        self.assertEqual([item["rule"] for item in findings], ["marketing-claim"])
        self.assertEqual(findings[0]["line"], 3)

    def test_one_line_ignore_marker_skips_teaching_examples(self):
        text = 'Do not write “perform an analysis.” <!-- prose-lint-ignore -->\n'

        result = run_lint(text, mode="natural")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["files"][0]["findings"], [])

    def test_text_output_supports_multiple_files_and_preserves_line_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.md"
            second = Path(directory) / "second.md"
            first.write_text("Safe sentence.\nDon't continue.\n", encoding="utf-8")
            second.write_text("Stop the service.\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mode",
                    "strict",
                    str(first),
                    str(second),
                ],
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{first}:2: error contraction", result.stdout)
        self.assertIn(f"{second}: no findings", result.stdout)

    def test_unreadable_input_returns_usage_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--mode", "strict", "/missing/prose.md"],
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)


if __name__ == "__main__":
    unittest.main()
