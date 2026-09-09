#!/usr/bin/env python3
"""Offline checks: normalization, fingerprints, page inlining, and the loopback protocol."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("readback", Path(__file__).with_name("readback.py"))
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)

ASSETS = Path(__file__).resolve().parent.parent / "assets"
FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

# Recorded when the file was vendored; see assets/vendor/README.md.
MARKDOWN_IT_SHA256 = "38c70a1e7ca91ab40e2d9e6e60129851a717ed1c7d4acbbdd41bf9503791cf68"
MERMAID_SHA256 = "581ed7d74bd9048d0e3a91363927d72ef22942d7722546b27f7cc29e35390eb8"


def doc_from(text, name="plan.md", title=None):
    document = rb.normalize_markdown(text, name, title)
    document["fingerprint"] = rb.fingerprint(document)
    return document


class Sources(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing_directory_and_empty_inputs_are_input_errors(self):
        with self.assertRaisesRegex(rb.InputError, "no such file"):
            rb.read_source(str(self.dir / "absent.md"), None)
        with self.assertRaisesRegex(rb.InputError, "is a directory"):
            rb.read_source(str(self.dir), "markdown")
        self.write("empty.md", "")
        with self.assertRaisesRegex(rb.InputError, "is empty"):
            rb.read_source(str(self.dir / "empty.md"), None)
        self.write("blank.md", "   \n\n\t\n")
        with self.assertRaisesRegex(rb.InputError, "is empty"):
            rb.read_source(str(self.dir / "blank.md"), None)

    def test_unreadable_file_reports_the_reason_not_absence(self):
        path = self.write("locked.md", "# Locked\n")
        path.chmod(0o000)
        self.addCleanup(path.chmod, 0o600)
        if os.access(path, os.R_OK):
            self.skipTest("running with privileges that ignore file permissions")
        with self.assertRaisesRegex(rb.InputError, "cannot read"):
            rb.read_source(str(path), None)

    def test_format_comes_from_the_extension_and_can_be_overridden(self):
        self.write("a.md", "# A\n")
        self.write("b.json", '{"entries": [{"text": "hi"}]}')
        self.write("c.txt", "plain\n")
        self.assertEqual(rb.read_source(str(self.dir / "a.md"), None)[1], "markdown")
        self.assertEqual(rb.read_source(str(self.dir / "b.json"), None)[1], "transcript")
        self.assertEqual(rb.read_source(str(self.dir / "c.txt"), "markdown")[1], "markdown")
        with self.assertRaisesRegex(rb.InputError, "cannot infer the format"):
            rb.read_source(str(self.dir / "c.txt"), None)

    def test_bom_is_dropped_and_invalid_utf8_is_rejected(self):
        (self.dir / "bom.md").write_bytes("\ufeff# Title\n".encode("utf-8"))
        raw, _, _, _ = rb.read_source(str(self.dir / "bom.md"), None)
        self.assertTrue(raw.startswith("# Title"))
        (self.dir / "bad.md").write_bytes(b"# T\n\xff\xfe not utf-8\n")
        with self.assertRaisesRegex(rb.InputError, "not valid UTF-8"):
            rb.read_source(str(self.dir / "bad.md"), None)

    def test_stdin_requires_an_explicit_format(self):
        with self.assertRaisesRegex(rb.InputError, "--format"):
            rb.read_source("-", None)


class Titles(unittest.TestCase):
    def test_first_heading_ignores_headings_inside_fences(self):
        self.assertEqual(rb.first_heading("```\n# Not a title\n```\n\n# Real\n"), "Real")
        self.assertEqual(rb.first_heading("~~~\n# No\n~~~\n## Yes\n"), "Yes")
        self.assertEqual(rb.first_heading("   ### Indented three ###\n"), "Indented three")
        self.assertIsNone(rb.first_heading("     # Four spaces is code\n"))
        self.assertIsNone(rb.first_heading("#\n#hashtag\nplain text\n"))

    def test_title_precedence_is_override_then_heading_then_filename(self):
        self.assertEqual(rb.normalize_markdown("# Head\n", "plan.md", None)["title"], "Head")
        self.assertEqual(rb.normalize_markdown("# Head\n", "plan.md", "Given")["title"], "Given")
        self.assertEqual(rb.normalize_markdown("no heading\n", "plan.md", None)["title"], "plan.md")


class Transcripts(unittest.TestCase):
    def load(self, obj, name="conversation.json", title=None):
        return rb.normalize_transcript(json.dumps(obj), name, title)

    def test_real_fixture_keeps_every_entry_and_its_kind(self):
        raw = (FIXTURES / "conversation.json").read_text(encoding="utf-8")
        document = rb.normalize_transcript(raw, "conversation.json", None)
        self.assertEqual(len(document["entries"]), 9)
        self.assertEqual([e["id"] for e in document["entries"][:3]], ["e1", "e2", "e3"])
        kinds = {e["kind"] for e in document["entries"]}
        self.assertLessEqual({"message", "compaction", "branch", "failure"}, kinds)
        self.assertEqual(document["source"]["agent"], "codex")
        self.assertTrue(document["warnings"])

    def test_ids_stay_unique_when_the_export_repeats_an_index(self):
        document = self.load({"entries": [{"text": "a", "index": 2}, {"text": "b", "index": 2}]})
        self.assertEqual([e["id"] for e in document["entries"]], ["e1", "e2"])
        self.assertEqual([e["sourceIndex"] for e in document["entries"]], [2, 2])

    def test_missing_index_falls_back_to_position(self):
        document = self.load({"entries": [{"text": "a"}, {"text": "b", "index": 7}]})
        self.assertEqual([e["sourceIndex"] for e in document["entries"]], [1, 7])

    def test_malformed_shapes_are_input_errors(self):
        for payload, pattern in (
            ("[]", "must be an object"),
            ("null", "must be an object"),
            ('{"entries": "nope"}', 'no "entries" array'),
            ('{"entries": [3]}', "must be an object"),
            ('{"entries": [{"text": 3}]}', 'needs a string "text"'),
            ("{oops", "not valid JSON"),
        ):
            with self.assertRaisesRegex(rb.InputError, pattern):
                rb.normalize_transcript(payload, "c.json", None)

    def test_unknown_fields_are_ignored_and_warnings_must_be_strings(self):
        document = self.load({"entries": [{"text": "a", "surprise": {"deep": 1}}],
                              "warnings": ["real", 5, None], "unknown_top": True})
        self.assertNotIn("surprise", document["entries"][0])
        self.assertEqual(document["warnings"], ["real"])

    def test_title_falls_back_to_the_agent_then_the_filename(self):
        self.assertEqual(self.load({"entries": [{"text": "a"}], "agent": "codex"})["title"],
                         "codex session")
        self.assertEqual(self.load({"entries": [{"text": "a"}]})["title"], "conversation.json")
        self.assertEqual(self.load({"entries": [{"text": "a"}],
                                    "metadata": {"title": "Meta"}})["title"], "Meta")


class Fingerprints(unittest.TestCase):
    def test_presentation_overrides_do_not_change_identity(self):
        plain = rb.normalize_markdown("# A\nbody\n", "plan.md", None)
        titled = rb.normalize_markdown("# A\nbody\n", "plan.md", "Different title")
        self.assertNotEqual(plain["title"], titled["title"])
        self.assertEqual(rb.fingerprint(plain), rb.fingerprint(titled))

    def test_content_changes_change_the_fingerprint(self):
        base = rb.normalize_markdown("# A\nbody\n", "plan.md", None)
        for other in (rb.normalize_markdown("# A\nbody!\n", "plan.md", None),
                      rb.normalize_markdown("# A\nbody\n", "other.md", None)):
            self.assertNotEqual(rb.fingerprint(base), rb.fingerprint(other))

    def test_fingerprint_is_stable_across_runs(self):
        document = rb.normalize_markdown("# A\nbody\n", "plan.md", None)
        self.assertEqual(rb.fingerprint(document), rb.fingerprint(dict(document)))
        self.assertEqual(len(rb.fingerprint(document)), 64)


class Embedding(unittest.TestCase):
    def test_no_embedded_string_can_close_the_script_element(self):
        hostile = {"text": "</script><script>window.__pwned=1</script>",
                   "also": "<!-- <script> -->", "amp": "&", "sep": "a b c"}
        embedded = rb.embed_json(hostile)
        for token in ("<", ">", "&", "\u2028", "\u2029"):
            self.assertNotIn(token, embedded)
        self.assertEqual(json.loads(embedded), hostile)

    def test_check_inline_rejects_script_tokens_but_allows_comment_openers(self):
        with self.assertRaises(rb.OperationalError):
            rb.check_inline("x", "var a = '</SCRIPT>';")
        with self.assertRaises(rb.OperationalError):
            rb.check_inline("x", "var a = '<script>';")
        rb.check_inline("x", "var re = /<!--/;")

    def test_vendored_markdown_it_matches_the_recorded_checksum(self):
        data = (ASSETS / "vendor" / "markdown-it.min.js").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), MARKDOWN_IT_SHA256)
        self.assertTrue((ASSETS / "vendor" / "markdown-it.LICENSE").is_file())
        drawn = (ASSETS / "vendor" / "mermaid.min.js").read_bytes()
        self.assertEqual(hashlib.sha256(drawn).hexdigest(), MERMAID_SHA256)
        self.assertTrue((ASSETS / "vendor" / "mermaid.LICENSE").is_file())
        readme = (ASSETS / "vendor" / "README.md").read_text(encoding="utf-8")
        self.assertIn(MARKDOWN_IT_SHA256, readme)


class Pages(unittest.TestCase):
    def test_every_template_placeholder_is_filled(self):
        page = rb.render_page(doc_from("# Title\n\nplain body\n"), "# Title\n\nplain body\n")
        self.assertNotRegex(page, r"\{\{[A-Z_]+\}\}")

    def test_placeholders_in_the_document_are_not_rescanned(self):
        raw = "# Title\n\nA {{CSS}} literal and {{PAYLOAD}} too.\n"
        page = rb.render_page(doc_from(raw), raw)
        payload = json.loads(page.split("window.RB_PAYLOAD=", 1)[1]
                             .split(";window.RB_LIVE=", 1)[0])
        self.assertEqual(payload["raw"], raw)     # one pass: the payload is never substituted into
        self.assertNotIn("--accent", payload["raw"])

    def test_offline_pages_carry_no_live_credentials(self):
        page = rb.render_page(doc_from("# T\n"), "# T\n")
        self.assertIn("window.RB_LIVE=null", page)
        self.assertIn(rb.CSP_OFFLINE, page)
        self.assertNotIn(rb.CSP_LIVE, page)

    def test_live_pages_declare_the_self_connect_policy(self):
        page = rb.render_page(doc_from("# T\n"), "# T\n", live={"reviewId": "r1"})
        self.assertIn(rb.CSP_LIVE, page)
        self.assertIn('"reviewId"', page)

    def test_titles_are_escaped_into_the_head(self):
        page = rb.render_page(doc_from("# <img src=x onerror=alert(1)>\n"), "x")
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;img", page)

    def test_source_download_name_matches_the_format(self):
        self.assertEqual(rb.raw_name(doc_from("# T\n", name="plan.md")), "plan.md")
        self.assertEqual(rb.raw_name(doc_from("# T\n", name="plan.txt")), "source.md")
        transcript = rb.normalize_transcript('{"entries": [{"text": "a"}]}', "c.json", None)
        self.assertEqual(rb.raw_name(transcript), "c.json")

    def test_the_page_only_references_element_ids_that_exist(self):
        markup = (ASSETS / "review.html").read_text(encoding="utf-8")
        script = (ASSETS / "review.js").read_text(encoding="utf-8")
        present = set(re.findall(r'id="([A-Za-z0-9_-]+)"', markup))
        wanted = set(re.findall(r'\$\("([A-Za-z0-9_-]+)"\)', script))
        wanted |= set(re.findall(r'getElementById\("([A-Za-z0-9_-]+)"\)', script))
        self.assertEqual(wanted - present, set())

    def test_assets_stay_inlineable(self):
        rb.check_inline("review.js", (ASSETS / "review.js").read_text(encoding="utf-8"))
        rb.check_inline("markdown-it.min.js",
                        (ASSETS / "vendor" / "markdown-it.min.js").read_text(encoding="utf-8"))
        rb.check_inline("mermaid.min.js",
                        (ASSETS / "vendor" / "mermaid.min.js").read_text(encoding="utf-8"))
        self.assertNotIn("</style", (ASSETS / "review.css").read_text(encoding="utf-8").lower())


class AtomicWrites(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def test_files_land_private_and_complete(self):
        target = self.dir / "followup.md"
        rb.write_atomic(target, "prompt text")
        self.assertEqual(target.read_text(encoding="utf-8"), "prompt text")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertEqual([p.name for p in self.dir.iterdir()], ["followup.md"])

    def test_a_failed_write_leaves_no_partial_file_behind(self):
        target = self.dir / "followup.md"
        rb.write_atomic(target, "first")

        with patch.object(rb.os, "replace", side_effect=OSError("no space left")):
            with self.assertRaises(OSError):
                rb.write_atomic(target, "second")
        self.assertEqual(target.read_text(encoding="utf-8"), "first")
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["followup.md"])


class ReviewDirectories(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def test_a_fresh_directory_is_created_private(self):
        made = rb.prepare_review_dir(str(self.dir / "new"))
        self.assertTrue(made.is_dir())
        self.assertEqual(stat.S_IMODE(made.stat().st_mode), 0o700)

    def test_an_existing_review_is_never_overwritten(self):
        used = self.dir / "used"
        used.mkdir()
        (used / "followup.md").write_text("earlier feedback", encoding="utf-8")
        with self.assertRaisesRegex(rb.InputError, "already holds a review"):
            rb.prepare_review_dir(str(used))

    def test_a_file_is_not_a_review_directory(self):
        path = self.dir / "file"
        path.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(rb.InputError, "not a directory"):
            rb.prepare_review_dir(str(path))

    def test_an_empty_existing_directory_is_reused(self):
        empty = self.dir / "empty"
        empty.mkdir()
        self.assertEqual(rb.prepare_review_dir(str(empty)), empty)


class BuildCommand(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = rb.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_building_the_fixtures_produces_standalone_pages(self):
        for fixture in ("plan.md", "conversation.json", "hostile.md"):
            out = self.dir / (fixture + ".html")
            code, stdout, _ = self.run_main(["build", str(FIXTURES / fixture), "-o", str(out)])
            self.assertEqual(code, rb.EXIT_OK, fixture)
            self.assertIn("sha256", stdout)
            page = out.read_text(encoding="utf-8")
            self.assertIn("window.RB_LIVE=null", page)
            self.assertNotIn("http://127.0.0.1", page)

    def test_an_existing_file_needs_force(self):
        out = self.dir / "review.html"
        out.write_text("earlier", encoding="utf-8")
        code, _, err = self.run_main(["build", str(FIXTURES / "plan.md"), "-o", str(out)])
        self.assertEqual(code, rb.EXIT_USAGE)
        self.assertIn("--force", err)
        self.assertEqual(out.read_text(encoding="utf-8"), "earlier")
        code, _, _ = self.run_main(["build", str(FIXTURES / "plan.md"), "-o", str(out), "--force"])
        self.assertEqual(code, rb.EXIT_OK)

    def test_a_missing_output_directory_is_reported_before_rendering(self):
        code, _, err = self.run_main(
            ["build", str(FIXTURES / "plan.md"), "-o", str(self.dir / "absent" / "r.html")])
        self.assertEqual(code, rb.EXIT_USAGE)
        self.assertIn("no such directory", err)

    def test_bad_input_exits_two_and_says_why(self):
        code, _, err = self.run_main(["build", str(self.dir / "nope.md"), "-o", str(self.dir / "o.html")])
        self.assertEqual(code, rb.EXIT_USAGE)
        self.assertIn("no such file", err)

    def test_a_transcript_with_no_entries_is_refused(self):
        empty = self.dir / "empty.json"
        empty.write_text('{"entries": []}', encoding="utf-8")
        code, _, err = self.run_main(["build", str(empty), "-o", str(self.dir / "o.html")])
        self.assertEqual(code, rb.EXIT_USAGE)
        self.assertIn("nothing to review", err)


class Protocol(unittest.TestCase):
    """The loopback contract, exercised against a real server on a real port."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        document = doc_from("# Plan\n\nbody\n")
        self.state = rb.ReviewState(self.dir, document, "rev-1")
        self.token = "t" * 32
        self.server = rb.ReviewServer(("127.0.0.1", 0), rb.Handler,
                                      state=self.state, token=self.token, page=b"<html>page</html>")
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(self.server.shutdown)
        self.host = self.server.expected_host
        self.base = f"/r/{self.token}"

    def request(self, method, path, body=None, headers=None, host=None):
        conn = http.client.HTTPConnection(self.host, timeout=5)
        try:
            sent = dict(headers or {})
            if body is not None:
                sent.setdefault("Content-Type", "application/json")
                sent.setdefault("Origin", self.server.origin)
            conn.request(method, path, body=body, headers={**sent, "Host": host or self.host})
            response = conn.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            conn.close()

    def declared_length(self, length):
        """Announce an oversized body without sending it: the cap is checked before any read."""
        conn = http.client.HTTPConnection(self.host, timeout=5)
        try:
            conn.putrequest("POST", f"{self.base}/submit", skip_host=True)
            for key, value in (("Host", self.host), ("Content-Type", "application/json"),
                               ("Origin", self.server.origin), ("Content-Length", str(length))):
                conn.putheader(key, value)
            conn.endheaders()
            return conn.getresponse().status
        finally:
            conn.close()

    def submit(self, **payload):
        return self.request("POST", f"{self.base}/submit", json.dumps(payload))

    def test_the_page_is_served_only_under_the_exact_token(self):
        status, body = self.request("GET", f"{self.base}/")
        self.assertEqual((status, body), (200, "<html>page</html>"))
        self.assertEqual(self.request("GET", "/r/" + "x" * 32 + "/")[0], 404)
        self.assertEqual(self.request("GET", "/")[0], 404)
        self.assertEqual(self.request("GET", f"{self.base}/../../etc/passwd")[0], 404)
        self.assertEqual(self.request("GET", f"{self.base}/unknown")[0], 404)
        self.assertEqual(self.request("GET", self.base)[0], 301)

    def test_a_foreign_host_header_is_refused(self):
        self.assertEqual(self.request("GET", f"{self.base}/", host="evil.example")[0], 421)

    def test_mutations_require_a_same_origin_request(self):
        status, _ = self.request("POST", f"{self.base}/submit", json.dumps({"prompt": "x"}),
                                 headers={"Origin": "http://evil.example"})
        self.assertEqual(status, 403)
        status, _ = self.request("POST", f"{self.base}/submit", json.dumps({"prompt": "x"}),
                                 headers={"Origin": "null"})
        self.assertEqual(status, 403)

    def test_bodies_must_be_json_and_bounded(self):
        status, _ = self.request("POST", f"{self.base}/submit", "{}",
                                 headers={"Content-Type": "text/plain",
                                          "Origin": self.server.origin})
        self.assertEqual(status, 415)
        self.assertEqual(self.declared_length(rb.MAX_BODY + 10), 413)
        self.assertEqual(self.request("POST", f"{self.base}/submit", "{oops")[0], 400)
        self.assertEqual(self.request("POST", f"{self.base}/submit", "[]")[0], 400)

    def test_an_empty_prompt_is_not_a_response(self):
        self.assertEqual(self.submit(submission_id="s1", prompt="   ")[0], 400)
        self.assertEqual(self.submit(submission_id="s1", prompt=None)[0], 400)
        self.assertEqual(self.submit(prompt="text")[0], 400)
        self.assertFalse((self.dir / "followup.md").exists())
        self.assertEqual(self.state.status, "open")

    def test_a_confirmed_prompt_is_saved_before_it_is_acknowledged(self):
        status, body = self.submit(submission_id="s1", prompt="do the thing", annotation_count=2)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["submissionId"], "s1")
        self.assertEqual((self.dir / "followup.md").read_text(encoding="utf-8"), "do the thing")
        result = json.loads((self.dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["annotationCount"], 2)
        self.assertEqual(result["promptSha256"],
                         hashlib.sha256(b"do the thing").hexdigest())
        self.assertNotIn("do the thing", json.dumps(result))     # no second copy of the prompt
        self.assertTrue(self.state.done.is_set())

    def test_the_diagram_renderer_rides_along_only_when_there_is_a_diagram(self):
        """3.4 MB is worth carrying for a drawing, and not worth carrying otherwise."""
        plain = rb.normalize_markdown("# Plan\n\nNo pictures here.\n", "p.md", None)
        self.assertFalse(rb.wants_diagrams(plain))
        page = rb.render_page(plain, "# Plan\n")
        self.assertNotIn("__esbuild_esm_mermaid_nm", page)

        raw = "# Plan\n\n```mermaid\nflowchart TD\n  A --> B\n```\n"
        drawn = rb.normalize_markdown(raw, "p.md", None)
        self.assertTrue(rb.wants_diagrams(drawn))
        self.assertIn("__esbuild_esm_mermaid_nm", rb.render_page(drawn, raw))
        # ...and not when the caller says no
        self.assertNotIn("__esbuild_esm_mermaid_nm",
                         rb.render_page(drawn, raw, diagrams=False))

    def test_only_a_real_mermaid_fence_counts_as_a_diagram(self):
        def has(text):
            return rb.wants_diagrams(rb.normalize_markdown(text, "p.md", None))
        self.assertTrue(has("```mermaid\nflowchart TD\n```\n"))
        self.assertTrue(has("~~~mermaid\nflowchart TD\n~~~\n"))
        self.assertTrue(has("   ```mermaid\nflowchart TD\n```\n"))
        self.assertFalse(has("Ask me about mermaid diagrams sometime.\n"))
        self.assertFalse(has("```mermaidish\nnot a diagram\n```\n"))
        self.assertFalse(has("```python\nprint('mermaid')\n```\n"))

    def test_the_result_records_whether_the_reader_edited_the_prompt(self):
        """A hand-edited prompt carries sentences no annotation accounts for."""
        status, _ = self.submit(submission_id="s1", prompt="mine, typed by hand",
                                annotation_count=1, prompt_edited=True)
        self.assertEqual(status, 200)
        result = json.loads((self.dir / "result.json").read_text(encoding="utf-8"))
        self.assertIs(result["promptEdited"], True)
        self.assertEqual(result["annotationCount"], 1)

    def test_an_unflagged_or_bogus_edited_flag_records_nothing(self):
        self.assertEqual(self.submit(submission_id="s1", prompt="generated",
                                     prompt_edited="yes please")[0], 200)
        result = json.loads((self.dir / "result.json").read_text(encoding="utf-8"))
        self.assertIsNone(result["promptEdited"])

    def test_a_retried_submission_is_idempotent_but_a_different_one_conflicts(self):
        self.submit(submission_id="s1", prompt="first")
        status, body = self.submit(submission_id="s1", prompt="first")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["duplicate"])
        status, body = self.submit(submission_id="s2", prompt="second")
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["submissionId"], "s1")
        status, _ = self.submit(submission_id="s1", prompt="edited after the fact")
        self.assertEqual(status, 409)
        self.assertEqual((self.dir / "followup.md").read_text(encoding="utf-8"), "first")

    def test_cancelling_records_the_outcome_and_sends_nothing(self):
        status, body = self.request("POST", f"{self.base}/cancel", "{}")
        self.assertEqual((status, json.loads(body)["status"]), (200, "cancelled"))
        self.assertFalse((self.dir / "followup.md").exists())
        result = json.loads((self.dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(self.request("POST", f"{self.base}/cancel", "{}")[0], 200)
        self.assertEqual(self.submit(submission_id="s1", prompt="too late")[0], 409)

    def test_cancelling_after_delivery_is_refused(self):
        self.submit(submission_id="s1", prompt="delivered")
        self.assertEqual(self.request("POST", f"{self.base}/cancel", "{}")[0], 409)
        result = json.loads((self.dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "submitted")

    def test_status_lets_a_browser_resolve_an_uncertain_send(self):
        status, body = self.request("GET", f"{self.base}/status")
        self.assertEqual((status, json.loads(body)["status"]), (200, "open"))
        self.submit(submission_id="s1", prompt="delivered")
        _, body = self.request("GET", f"{self.base}/status")
        self.assertEqual(json.loads(body)["submissionId"], "s1")

    def test_only_one_of_many_concurrent_submissions_wins(self):
        start = threading.Barrier(6)
        codes = []
        lock = threading.Lock()

        def race(n):
            start.wait()
            code, _ = self.submit(submission_id=f"s{n}", prompt=f"prompt {n}")
            with lock:
                codes.append(code)

        threads = [threading.Thread(target=race, args=(n,)) for n in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        self.assertEqual(sorted(codes), [200] + [409] * 5)
        saved = (self.dir / "followup.md").read_text(encoding="utf-8")
        self.assertEqual(saved, self.state.prompt)


class EndToEnd(unittest.TestCase):
    """`review` from the caller's side: stdout is the prompt and nothing else."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.ack = rb.ACK_WINDOW
        rb.ACK_WINDOW = 0.05
        self.addCleanup(setattr, rb, "ACK_WINDOW", self.ack)

    def start(self, out_dir):
        """Run the CLI on a thread; return (result holder, captured stdout, review URL)."""
        out, err = io.StringIO(), io.StringIO()
        holder = {}

        def run():
            with redirect_stdout(out), redirect_stderr(err):
                holder["code"] = rb.main(["review", str(FIXTURES / "plan.md"),
                                          "--out-dir", str(out_dir), "--no-open"])

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            found = re.search(r"http://127\.0\.0\.1:\d+/r/[\w-]+/", err.getvalue())
            if found:
                return holder, out, found.group(0), thread, err
            time.sleep(0.02)
        raise AssertionError(f"no review URL on stderr: {err.getvalue()!r}")

    def post(self, url, path, payload):
        host = url.split("//", 1)[1].split("/", 1)[0]
        conn = http.client.HTTPConnection(host, timeout=5)
        try:
            conn.request("POST", url.split(host, 1)[1] + path, body=json.dumps(payload),
                         headers={"Content-Type": "application/json", "Host": host,
                                  "Origin": f"http://{host}"})
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()

    def test_a_confirmed_prompt_reaches_stdout_verbatim(self):
        review_dir = self.dir / "review"
        holder, out, url, thread, err = self.start(review_dir)
        prompt = "Please address the following feedback.\n\n1. Policy\n> quote\n\nMy comment:\nfix it"
        status, _ = self.post(url, "submit", {"submission_id": "s1", "prompt": prompt,
                                              "annotation_count": 1})
        self.assertEqual(status, 200)
        thread.join(10)
        self.assertEqual(holder["code"], rb.EXIT_OK)
        self.assertEqual(out.getvalue(), prompt)              # no wrapper, no trailing newline
        self.assertEqual((review_dir / "followup.md").read_text(encoding="utf-8"), prompt)
        self.assertIn("confirmed", err.getvalue())
        self.assertEqual(sorted(p.name for p in review_dir.iterdir()),
                         ["followup.md", "result.json", "review.html", "source.json"])

    def test_the_saved_artifact_is_offline_and_the_source_is_kept_verbatim(self):
        review_dir = self.dir / "review"
        holder, out, url, thread, _ = self.start(review_dir)
        try:
            artifact = (review_dir / "review.html").read_text(encoding="utf-8")
            token = url.rstrip("/").rsplit("/", 1)[1]
            self.assertNotIn(token, artifact)
            self.assertIn("window.RB_LIVE=null", artifact)
            source = json.loads((review_dir / "source.json").read_text(encoding="utf-8"))
            self.assertEqual(source["raw"], (FIXTURES / "plan.md").read_text(encoding="utf-8"))
            self.assertEqual(source["fingerprint"], source["document"]["fingerprint"])
        finally:
            self.post(url, "cancel", {})
            thread.join(10)

    def test_cancelling_exits_three_with_empty_stdout(self):
        review_dir = self.dir / "review"
        holder, out, url, thread, err = self.start(review_dir)
        status, _ = self.post(url, "cancel", {})
        self.assertEqual(status, 200)
        thread.join(10)
        self.assertEqual(holder["code"], rb.EXIT_CANCELLED)
        self.assertEqual(out.getvalue(), "")
        self.assertFalse((review_dir / "followup.md").exists())
        self.assertIn("no feedback was sent", err.getvalue())


if __name__ == "__main__":
    unittest.main()
