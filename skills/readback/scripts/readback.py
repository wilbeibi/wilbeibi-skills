#!/usr/bin/env python3
"""Readback: turn a plan or a conversation transcript into an HTML review surface.

    readback.py build INPUT -o review.html      standalone artifact, no server
    readback.py review INPUT --out-dir DIR      serve it and wait for the confirmed prompt

In `review`, stdout carries exactly the prompt the user confirmed and nothing else;
URLs, paths and diagnostics go to stderr. Exit 0 confirmed, 1 operational failure,
2 invalid input or usage, 3 the user cancelled.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import html
import http.server
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import threading
import time
import webbrowser

SCHEMA = 1
ANCHOR_VERSION = 1            # bump when rendering changes invalidate stored annotation offsets
MAX_BODY = 1 << 20            # 1 MiB submission ceiling
ACK_WINDOW = 5.0              # seconds kept alive after acceptance, for a lost acknowledgment
ASSETS = Path(__file__).resolve().parent.parent / "assets"

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_CANCELLED, EXIT_INTERRUPT = 0, 1, 2, 3, 130

FINGERPRINT_KEYS = ("kind", "role", "sourceIndex", "time", "tool", "input", "text")
CSP_BASE = ("default-src blob:; base-uri 'none'; form-action 'none'; object-src 'none'; "
            "img-src 'none'; media-src 'none'; font-src 'none'; "
            "style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src ")
CSP_OFFLINE = CSP_BASE + "'none'"
CSP_LIVE = CSP_BASE + "'self'"

TRANSCRIPT_SCOPE = ("Transcript entries exactly as the export produced them. Anything the export "
                    "leaves out - reasoning, tool calls, successful tool results - is absent here too.")
MARKDOWN_SCOPE = "Markdown document, rendered from the exact source stored with this review."


class InputError(Exception):
    """Bad CLI arguments or unusable input: exit 2."""


class OperationalError(Exception):
    """Everything worked as asked but the environment refused: exit 1."""


# --------------------------------------------------------------------------- input

def read_source(spec: str, fmt: str | None) -> tuple[str, str, str, Path | None]:
    """Return (raw text, format, display name, path)."""
    if spec == "-":
        if not fmt:
            raise InputError("--format markdown|transcript is required when reading stdin")
        data = sys.stdin.buffer.read()
        name, path = "stdin", None
    else:
        path = Path(spec)
        # read_bytes rather than is_file: named pipes and process substitution are legitimate inputs
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            raise InputError(f"no such file: {spec}") from None
        except IsADirectoryError:
            raise InputError(f"{spec} is a directory, not a file") from None
        except OSError as exc:
            raise InputError(f"cannot read {spec}: {exc.strerror or exc}") from None
        name = path.name
        if not fmt:
            fmt = {".md": "markdown", ".markdown": "markdown",
                   ".json": "transcript"}.get(path.suffix.lower(), "")
            if not fmt:
                raise InputError(f"cannot infer the format of {name}; "
                                 "pass --format markdown or --format transcript")
    try:
        raw = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"{name} is not valid UTF-8: {exc}") from None
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    if not raw.strip():
        raise InputError(f"{name} is empty; there is nothing to review")
    return raw, fmt, name, path


def first_heading(text: str) -> str | None:
    fence = None
    for line in text.splitlines():
        stripped = line.strip()
        opener = re.match(r"^(`{3,}|~{3,})", stripped)
        if opener:
            token = opener.group(1)[0]
            fence = None if fence == token else (fence or token)
            continue
        if fence:
            continue
        head = re.match(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if head and head.group(2).strip():
            return head.group(2).strip()
    return None


def normalize_markdown(raw: str, name: str, title: str | None) -> dict:
    return {
        "schema": SCHEMA,
        "anchorVersion": ANCHOR_VERSION,
        "kind": "markdown",
        "title": title or first_heading(raw) or name,
        "source": {"name": name, "format": "markdown"},
        "scope": MARKDOWN_SCOPE,
        "warnings": [],
        "entries": [{"id": "e1", "kind": "document", "sourceIndex": 1, "text": raw}],
    }


def normalize_transcript(raw: str, name: str, title: str | None) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"{name} is not valid JSON: {exc}") from None
    if not isinstance(data, dict):
        raise InputError('transcript JSON must be an object with an "entries" array')
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list):
        raise InputError(f'{name} has no "entries" array; '
                         "expected the shape written by `catchup --json`")

    entries = []
    for position, item in enumerate(raw_entries, start=1):
        where = f"entries[{position - 1}]"
        if not isinstance(item, dict):
            raise InputError(f"{where} must be an object, not {type(item).__name__}")
        text = item.get("text")
        if not isinstance(text, str):
            raise InputError(f'{where} needs a string "text", not {type(text).__name__}')
        entry = {"id": f"e{position}", "kind": "message", "text": text}
        kind = item.get("kind")
        if isinstance(kind, str) and kind.strip():
            entry["kind"] = kind.strip()
        index = item.get("index")
        entry["sourceIndex"] = (index if isinstance(index, (int, str))
                                and not isinstance(index, bool) else position)
        for key in ("role", "time", "tool"):
            value = item.get(key)
            if isinstance(value, str) and value:
                entry[key] = value
        if item.get("input") is not None:
            entry["input"] = item["input"]
        entries.append(entry)

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    warnings = [w for w in (data.get("warnings") or []) if isinstance(w, str)] \
        if isinstance(data.get("warnings"), list) else []

    source = {"name": name, "format": "transcript"}
    for key, field in (("agent", "agent"), ("sessionId", "session_id"), ("updatedAt", "updated_at")):
        value = data.get(field)
        if isinstance(value, str) and value:
            source[key] = value

    meta_title = metadata.get("title") if isinstance(metadata.get("title"), str) else None
    agent = source.get("agent")
    fallback = f"{agent} session" if agent else name
    return {
        "schema": SCHEMA,
        "anchorVersion": ANCHOR_VERSION,
        "kind": "transcript",
        "title": title or meta_title or fallback,
        "source": source,
        "scope": TRANSCRIPT_SCOPE,
        "warnings": warnings,
        "entries": entries,
    }


def fingerprint(document: dict) -> str:
    """Content identity: presentation overrides and build time must not change it."""
    identity = {
        "schema": document["schema"],
        "anchorVersion": document["anchorVersion"],
        "kind": document["kind"],
        "source": {key: document["source"].get(key) for key in ("name", "agent", "sessionId")},
        "entries": [{key: entry.get(key) for key in FINGERPRINT_KEYS}
                    for entry in document["entries"]],
    }
    blob = json.dumps(identity, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_document(args: argparse.Namespace) -> tuple[dict, str, Path | None]:
    raw, fmt, name, path = read_source(args.input, args.format)
    if args.title is not None and not args.title.strip():
        raise InputError("--title cannot be empty")
    title = args.title.strip() if args.title else None
    document = (normalize_markdown if fmt == "markdown" else normalize_transcript)(raw, name, title)
    if not document["entries"]:
        raise InputError(f"{name} has no readable content; there is nothing to review")
    document["fingerprint"] = fingerprint(document)
    return document, raw, path


# --------------------------------------------------------------------------- page

def embed_json(value) -> str:
    """JSON safe to paste inside <script>: no source string can close the element."""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    for bad, good in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"),
                      ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        text = text.replace(bad, good)
    return text


def check_inline(label: str, code: str) -> None:
    """Refuse code that could close or swallow its own <script> element.

    `</script` ends the element wherever it appears. `<script` matters because a preceding
    `<!--` would put the tokenizer in the double-escaped state and eat the rest of the page.
    A bare `<!--` (markdown-it has one, in a regex) is harmless on its own.
    """
    for token in ("</script", "<script"):
        if token in code.lower():
            raise OperationalError(f"{label} contains {token!r} and cannot be inlined safely")


def raw_name(document: dict) -> str:
    name = document["source"].get("name") or "source"
    want = ".md" if document["kind"] == "markdown" else ".json"
    return name if name.lower().endswith(want) else f"source{want}"


def render_page(document: dict, raw: str, live: dict | None = None) -> str:
    css = (ASSETS / "review.css").read_text(encoding="utf-8")
    script = (ASSETS / "review.js").read_text(encoding="utf-8")
    vendor = (ASSETS / "vendor" / "markdown-it.min.js").read_text(encoding="utf-8")
    template = (ASSETS / "review.html").read_text(encoding="utf-8")
    check_inline("review.js", script)
    check_inline("markdown-it.min.js", vendor)
    if "</style" in css.lower():
        raise OperationalError("review.css cannot be inlined safely")
    payload = {"schema": SCHEMA, "anchorVersion": ANCHOR_VERSION, "document": document,
               "raw": raw, "rawName": raw_name(document)}
    values = {
        "TITLE": html.escape(document["title"]),
        "CSP": CSP_LIVE if live else CSP_OFFLINE,
        "CSS": css,
        "VENDOR": vendor,
        "JS": script,
        "PAYLOAD": embed_json(payload),
        "LIVE": embed_json(live),
    }
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], template)


def write_atomic(path: Path, text: str, mode: int = 0o600) -> None:
    handle, temp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".readback-")
    temp = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    try:
        fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


# --------------------------------------------------------------------------- build

def cmd_build(args: argparse.Namespace) -> int:
    document, raw, _ = build_document(args)
    out = Path(args.output)
    if out.exists() and not args.force:
        raise InputError(f"{out} already exists; pass --force to overwrite it")
    if out.parent and not out.parent.exists():
        raise InputError(f"no such directory: {out.parent}")
    out.write_text(render_page(document, raw), encoding="utf-8")
    count = len(document["entries"])
    unit = "entry" if count == 1 else "entries"
    print(f"{out} · {count} {unit} · sha256 {document['fingerprint'][:16]}")
    return EXIT_OK


# --------------------------------------------------------------------------- review

class ReviewState:
    """One review's outcome. Every transition happens under `lock`."""

    def __init__(self, review_dir: Path, document: dict, review_id: str):
        self.dir = review_dir
        self.document = document
        self.review_id = review_id
        self.lock = threading.Lock()
        self.done = threading.Event()
        self.status = "open"
        self.prompt: str | None = None
        self.ack: dict | None = None

    def accept(self, submission_id: str, prompt: str, count: int | None) -> dict:
        """Save durably first; only a saved prompt is ever acknowledged."""
        encoded = prompt.encode("utf-8")
        write_atomic(self.dir / "followup.md", prompt)
        result = {
            "schema": SCHEMA,
            "status": "submitted",
            "reviewId": self.review_id,
            "submissionId": submission_id,
            "fingerprint": self.document["fingerprint"],
            "title": self.document["title"],
            "source": self.document["source"],
            "promptFile": "followup.md",
            "promptBytes": len(encoded),
            "promptSha256": hashlib.sha256(encoded).hexdigest(),
            "annotationCount": count,
            "submittedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        write_atomic(self.dir / "result.json", json.dumps(result, indent=2) + "\n")
        self.prompt = prompt
        self.status = "accepted"
        self.ack = {"status": "accepted", "submissionId": submission_id,
                    "savedTo": str(self.dir / "followup.md")}
        self.done.set()
        return dict(self.ack)

    def cancel(self) -> dict:
        result = {"schema": SCHEMA, "status": "cancelled", "reviewId": self.review_id,
                  "fingerprint": self.document["fingerprint"],
                  "cancelledAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        write_atomic(self.dir / "result.json", json.dumps(result, indent=2) + "\n")
        self.status = "cancelled"
        self.done.set()
        return {"status": "cancelled"}


class ReviewServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, handler, *, state: ReviewState, token: str, page: bytes):
        super().__init__(address, handler)
        self.state = state
        self.token = token
        self.page = page
        self.expected_host = f"127.0.0.1:{self.server_address[1]}"
        self.origin = f"http://{self.expected_host}"

    def handle_error(self, request, client_address):   # a dropped browser tab is not news
        pass


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "readback"
    sys_version = ""

    def log_message(self, fmt, *args):     # keep stderr for the agent's diagnostics
        pass

    # -- plumbing
    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP_LIVE + "; frame-ancestors 'none'")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, (json.dumps(obj) + "\n").encode("utf-8"), "application/json; charset=utf-8")

    def _route(self, mutating: bool) -> str | None:
        """Return the path after /r/<token>, or None once an error has been sent."""
        if self.headers.get("Host", "") != self.server.expected_host:
            self._json(421, {"error": "unexpected Host header; open the review URL that was printed"})
            return None
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        parts = path.split("/")
        if len(parts) < 3 or parts[1] != "r" or not hmac.compare_digest(parts[2], self.server.token):
            self._json(404, {"error": "not found"})
            return None
        if mutating and self.headers.get("Origin") != self.server.origin:
            self._json(403, {"error": "cross-origin or file:// request refused"})
            return None
        return "/".join(parts[3:])

    def _body(self) -> dict | None:
        ctype = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if ctype != "application/json":
            self._json(415, {"error": "expected Content-Type: application/json"})
            return None
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._json(411, {"error": "Content-Length required"})
            return None
        if length < 0 or length > MAX_BODY:
            self._json(413, {"error": f"body larger than {MAX_BODY} bytes"})
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": f"invalid JSON body: {exc}"})
            return None
        if not isinstance(payload, dict):
            self._json(400, {"error": "body must be a JSON object"})
            return None
        return payload

    # -- routes
    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == f"/r/{self.server.token}":
            self._send(301, b"", "text/plain; charset=utf-8",
                       {"Location": f"/r/{self.server.token}/"})
            return
        route = self._route(mutating=False)
        if route is None:
            return
        if route == "":
            self._send(200, self.server.page, "text/html; charset=utf-8")
        elif route == "status":
            state = self.server.state
            with state.lock:
                body = {"status": state.status, "reviewId": state.review_id}
                if state.ack:
                    body["submissionId"] = state.ack["submissionId"]
            self._json(200, body)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        route = self._route(mutating=True)
        if route is None:
            return
        if route == "submit":
            self._submit()
        elif route == "cancel":
            self._cancel()
        else:
            self._json(404, {"error": "not found"})

    def _submit(self) -> None:
        payload = self._body()
        if payload is None:
            return
        submission_id = payload.get("submission_id")
        prompt = payload.get("prompt")
        if not isinstance(submission_id, str) or not 1 <= len(submission_id) <= 200:
            self._json(400, {"error": "submission_id must be a short non-empty string"})
            return
        if not isinstance(prompt, str):
            self._json(400, {"error": "prompt must be a string"})
            return
        if not prompt.strip():
            self._json(400, {"error": "an empty prompt is not a response"})
            return
        count = payload.get("annotation_count")
        count = count if isinstance(count, int) and not isinstance(count, bool) else None

        state = self.server.state
        with state.lock:
            if state.status == "cancelled":
                self._json(409, {"error": "this review was cancelled; nothing was sent"})
                return
            if state.status == "accepted":
                if hmac.compare_digest(state.ack["submissionId"], submission_id) \
                        and state.prompt == prompt:
                    self._json(200, dict(state.ack, duplicate=True))
                else:
                    self._json(409, {"error": "this review already delivered a prompt and cannot "
                                              "be overwritten",
                                     "submissionId": state.ack["submissionId"]})
                return
            try:
                ack = state.accept(submission_id, prompt, count)
            except OSError as exc:
                self._json(500, {"error": f"could not save the prompt, nothing was sent: {exc}"})
                return
        self._json(200, ack)

    def _cancel(self) -> None:
        if self._body() is None:
            return
        state = self.server.state
        with state.lock:
            if state.status == "accepted":
                self._json(409, {"error": "the prompt was already delivered; too late to cancel"})
                return
            if state.status == "cancelled":
                self._json(200, {"status": "cancelled"})
                return
            try:
                body = state.cancel()
            except OSError as exc:
                self._json(500, {"error": f"could not record the cancellation: {exc}"})
                return
        self._json(200, body)


def prepare_review_dir(raw_dir: str | None) -> Path:
    if raw_dir is None:
        return Path(tempfile.mkdtemp(prefix="readback-"))
    review_dir = Path(raw_dir)
    if review_dir.exists():
        if not review_dir.is_dir():
            raise InputError(f"{review_dir} is not a directory")
        for marker in ("review.html", "source.json", "followup.md", "result.json"):
            if (review_dir / marker).exists():
                raise InputError(f"{review_dir} already holds a review ({marker}); "
                                 "choose an empty --out-dir so earlier feedback is not replaced")
    else:
        try:
            review_dir.mkdir(parents=True, mode=0o700)
        except OSError as exc:
            raise InputError(f"cannot create {review_dir}: {exc}") from None
    return review_dir


def cmd_review(args: argparse.Namespace) -> int:
    document, raw, path = build_document(args)
    review_dir = prepare_review_dir(args.out_dir)
    review_id = secrets.token_urlsafe(9)
    token = secrets.token_urlsafe(24)

    source_record = {"schema": SCHEMA, "anchorVersion": ANCHOR_VERSION,
                     "fingerprint": document["fingerprint"], "reviewId": review_id,
                     "inputPath": str(path.resolve()) if path else None,
                     "document": document, "raw": raw}
    try:
        write_atomic(review_dir / "review.html", render_page(document, raw))
        write_atomic(review_dir / "source.json",
                     json.dumps(source_record, ensure_ascii=False, indent=2) + "\n")
    except OSError as exc:
        raise OperationalError(f"cannot write into {review_dir}: {exc}") from None

    state = ReviewState(review_dir, document, review_id)
    live = {"reviewId": review_id, "dir": str(review_dir),
            "promptFile": str(review_dir / "followup.md"),
            "resultFile": str(review_dir / "result.json")}
    page = render_page(document, raw, live=live).encode("utf-8")
    try:
        server = ReviewServer(("127.0.0.1", 0), Handler, state=state, token=token, page=page)
    except OSError as exc:
        raise OperationalError(f"cannot bind a loopback port: {exc}") from None
    url = f"http://{server.expected_host}/r/{token}/"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    count = len(document["entries"])
    log(f"readback: {document['title']!r} · {count} {'entry' if count == 1 else 'entries'} "
        f"· sha256 {document['fingerprint'][:16]}")
    log(f"readback: review at {url}")
    log(f"readback: artifact {review_dir / 'review.html'} (opens offline, cannot send)")
    log("readback: waiting for Confirm & send in the browser; nothing arrives until then")
    if not args.no_open:
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    try:
        while not state.done.wait(0.5):
            pass
    except KeyboardInterrupt:
        with state.lock:
            interrupted_status = state.status
        if interrupted_status != "accepted":
            server.shutdown()
            log(f"readback: interrupted; no feedback was sent. Artifact: {review_dir / 'review.html'}")
            return EXIT_INTERRUPT

    if state.status == "accepted":
        deadline = time.monotonic() + ACK_WINDOW
        while time.monotonic() < deadline:      # bounded window for a lost ack and its retry
            time.sleep(0.1)
        server.shutdown()
        log(f"readback: confirmed · saved {review_dir / 'followup.md'}")
        sys.stdout.write(state.prompt)
        sys.stdout.flush()
        return EXIT_OK

    server.shutdown()
    log(f"readback: cancelled by the user; no feedback was sent. "
        f"Notes remain in {review_dir / 'review.html'}")
    return EXIT_CANCELLED


def open_browser(url: str) -> None:
    time.sleep(0.2)
    try:
        opened = webbrowser.open(url, new=2)
    except Exception:                                  # noqa: BLE001 - any backend may fail
        opened = False
    if not opened:
        log("readback: could not launch a browser; open the URL above yourself")


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- cli

def parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("input", metavar="INPUT", help="markdown or transcript file, or - for stdin")
    common.add_argument("--format", choices=("markdown", "transcript"),
                        help="override the format inferred from the file extension")
    common.add_argument("--title", help="override the title (does not change the fingerprint)")

    top = argparse.ArgumentParser(prog="readback.py", description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = top.add_subparsers(dest="command", required=True)

    build = subs.add_parser("build", parents=[common], help="write a self-contained review page")
    build.add_argument("-o", "--output", default="review.html", help="output HTML (default review.html)")
    build.add_argument("--force", action="store_true", help="overwrite an existing output file")
    build.set_defaults(run=cmd_build)

    review = subs.add_parser("review", parents=[common],
                             help="serve the review and wait for the confirmed prompt")
    review.add_argument("--out-dir", help="review directory (default: a fresh temporary directory)")
    review.add_argument("--no-open", action="store_true", help="print the URL, launch no browser")
    review.set_defaults(run=cmd_review)
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.run(args)
    except InputError as exc:
        log(f"readback: {exc}")
        return EXIT_USAGE
    except OperationalError as exc:
        log(f"readback: {exc}")
        return EXIT_FAIL
    except KeyboardInterrupt:
        log("readback: interrupted")
        return EXIT_INTERRUPT
    except BrokenPipeError:
        return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
