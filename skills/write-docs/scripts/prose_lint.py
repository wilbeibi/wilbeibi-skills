#!/usr/bin/env python3
"""Advisory checks for avoidable ambiguity and generic technical prose."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Iterable


WORD_RE = re.compile(r"\b[\w]+(?:[-'’][\w]+)*\b", re.UNICODE)
LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
TABLE_RE = re.compile(r"^\s*\|.*\|\s*$")
TABLE_DELIMITER_RE = re.compile(r":?-{3,}:?")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
URL_RE = re.compile(r"(?:https?://|mailto:)[^\s)>]+")
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^]]+)]\([^)]+\)")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^]]*]\([^)]+\)")
AUTOLINK_RE = re.compile(r"<(?:https?://|mailto:)[^>]+>")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->")
IGNORE_MARKER = "<!-- prose-lint-ignore -->"

CONTRACTION_RE = re.compile(
    r"\b(?:can['’]t|won['’]t|don['’]t|doesn['’]t|didn['’]t|isn['’]t|"
    r"aren['’]t|wasn['’]t|weren['’]t|haven['’]t|hasn['’]t|hadn['’]t|"
    r"shouldn['’]t|wouldn['’]t|couldn['’]t|mustn['’]t|I['’]m|you['’]re|"
    r"we['’]re|they['’]re|it['’]s|that['’]s|there['’]s|I['’]ve|you['’]ve|"
    r"we['’]ve|they['’]ve|I['’]ll|you['’]ll|we['’]ll|they['’]ll|I['’]d|"
    r"you['’]d|we['’]d|they['’]d)\b",
    re.IGNORECASE,
)

PHRASE_RULES = (
    (
        "empty-intro",
        re.compile(
            r"\b(?:it is important to note that|it should be noted that|"
            r"it is worth noting that|please note that|as mentioned above|"
            r"as noted above)\b",
            re.IGNORECASE,
        ),
        "remove the empty introduction and state the fact directly",
    ),
    (
        "stacked-hedge",
        re.compile(
            r"\b(?:may|might|could|should|would)\s+(?:potentially\s+)?"
            r"(?:be able to|help to|serve to|possibly)\b",
            re.IGNORECASE,
        ),
        "name the condition or confidence instead of stacking helper words",
    ),
    (
        "marketing-claim",
        re.compile(
            r"\b(?:seamless(?:ly)?|world-class|next-generation|revolutionary|"
            r"game-changing|best-in-class|cutting-edge|effortless(?:ly)?|"
            r"battle-tested|enterprise-grade|robust|powerful|instant|"
            r"no[- ]re-explaining)\b",
            re.IGNORECASE,
        ),
        "replace the quality claim with evidence or a bounded capability",
    ),
    (
        "nominalized-action",
        re.compile(
            r"\b(?:perform an analysis|conduct a review|make a decision|"
            r"provide an explanation|carry out an assessment)\b",
            re.IGNORECASE,
        ),
        "prefer a direct verb when it preserves the meaning",
    ),
)

PERFECT_TENSE_RE = re.compile(
    r"\b(?:has|have|had)\s+(?:already\s+|just\s+|not\s+|never\s+)?"
    r"(?:been|\w+ed|built|done|found|given|gone|held|kept|known|made|"
    r"put|run|seen|sent|set|shown|taken|thrown|written)\b",
    re.IGNORECASE,
)

MAX_PARAGRAPH_SENTENCES = 6

PASSIVE_RE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being)\s+"
    r"(?:\w+ly\s+)?(?:\w+ed|built|done|found|given|held|kept|known|made|"
    r"put|read|run|seen|sent|set|shown|taken|thrown|written)\b",
    re.IGNORECASE,
)

ABBREVIATIONS = (
    "e.g.",
    "i.e.",
    "etc.",
    "vs.",
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
)


@dataclass(frozen=True)
class Finding:
    line: int
    rule: str
    severity: str
    message: str


@dataclass
class Block:
    text: list[str]
    lines: list[int]

    @classmethod
    def empty(cls) -> "Block":
        return cls([], [])

    def add(self, fragment: str, line: int) -> None:
        if self.text:
            self.text.append(" ")
            self.lines.append(line)
        self.text.extend(fragment)
        self.lines.extend([line] * len(fragment))

    def finish(self) -> tuple[str, list[int]] | None:
        raw = "".join(self.text)
        value = raw.strip()
        if not value:
            return None
        left_trim = len(raw) - len(raw.lstrip())
        return value, self.lines[left_trim : left_trim + len(value)]


def _spaces(match: re.Match[str]) -> str:
    return " " * len(match.group(0))


def mask_inline_markdown(line: str) -> str:
    line = HTML_COMMENT_RE.sub(_spaces, line)
    line = MARKDOWN_IMAGE_RE.sub(_spaces, line)
    line = AUTOLINK_RE.sub(_spaces, line)
    line = URL_RE.sub(_spaces, line)
    line = INLINE_CODE_RE.sub(_spaces, line)

    def keep_link_text(match: re.Match[str]) -> str:
        text = match.group(1)
        return text + (" " * (len(match.group(0)) - len(text)))

    return MARKDOWN_LINK_RE.sub(keep_link_text, line)


def prose_blocks(text: str) -> list[tuple[str, list[int]]]:
    lines = text.splitlines()
    blocks: list[tuple[str, list[int]]] = []
    current = Block.empty()
    in_fence: str | None = None
    in_frontmatter = bool(lines and lines[0].strip() == "---")
    in_comment = False

    def flush() -> None:
        nonlocal current
        finished = current.finish()
        if finished:
            blocks.append(finished)
        current = Block.empty()

    for number, raw in enumerate(lines, 1):
        if in_frontmatter:
            if number > 1 and raw.strip() == "---":
                in_frontmatter = False
            continue

        fence = FENCE_RE.match(raw)
        if fence:
            marker = fence.group(1)[0]
            if in_fence is None:
                flush()
                in_fence = marker
            elif marker == in_fence:
                in_fence = None
            continue
        if in_fence is not None:
            continue

        if in_comment:
            if "-->" in raw:
                in_comment = False
            continue
        if "<!--" in raw and "-->" not in raw:
            flush()
            in_comment = True
            continue

        if IGNORE_MARKER in raw:
            flush()
            continue

        if not raw.strip():
            flush()
            continue
        if HEADING_RE.match(raw):
            flush()
            continue
        if TABLE_RE.match(raw):
            flush()
            cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
            if cells and all(TABLE_DELIMITER_RE.fullmatch(cell.replace(" ", "")) for cell in cells):
                continue
            for cell in cells:
                fragment = mask_inline_markdown(cell).strip()
                if not fragment:
                    continue
                table_block = Block.empty()
                table_block.add(fragment, number)
                finished = table_block.finish()
                if finished:
                    blocks.append(finished)
            continue

        fragment = re.sub(r"^\s*>\s?", "", raw)
        if fragment.startswith("[!"):
            flush()
            continue
        if LIST_RE.match(fragment):
            flush()
            fragment = LIST_RE.sub("", fragment)

        fragment = mask_inline_markdown(fragment).strip()
        if fragment:
            current.add(fragment, number)

    flush()
    return blocks


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for match in re.finditer(r"[.!?](?:[\"')\]]+)?(?=\s|$)", text):
        end = match.end()
        candidate = text[start:end].rstrip().lower()
        if any(candidate.endswith(abbreviation) for abbreviation in ABBREVIATIONS):
            continue
        if re.search(r"(?:[a-z]\.){2,}$", candidate):
            continue
        left = start
        while left < end and text[left].isspace():
            left += 1
        if left < end:
            spans.append((left, end))
        start = end

    while start < len(text) and text[start].isspace():
        start += 1
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def line_for_offset(line_map: list[int], offset: int) -> int:
    if not line_map:
        return 1
    return line_map[min(offset, len(line_map) - 1)]


def lint_text(text: str, mode: str) -> list[Finding]:
    findings: list[Finding] = []
    max_words = 20 if mode == "strict" else 25
    length_severity = "error" if mode == "strict" else "review"

    for block_text, line_map in prose_blocks(text):
        spans = sentence_spans(block_text)
        if len(spans) > MAX_PARAGRAPH_SENTENCES:
            findings.append(
                Finding(
                    line_for_offset(line_map, spans[0][0]),
                    "paragraph-length",
                    "review",
                    f"{len(spans)} sentences in one paragraph; split by topic "
                    f"(aim for at most {MAX_PARAGRAPH_SENTENCES})",
                )
            )
        for start, end in spans:
            sentence = block_text[start:end]
            count = len(WORD_RE.findall(sentence))
            if count > max_words:
                findings.append(
                    Finding(
                        line_for_offset(line_map, start),
                        "sentence-length",
                        length_severity,
                        f"{count} words; {mode} mode uses a {max_words}-word review threshold",
                    )
                )

        if mode == "strict":
            for match in re.finditer(";", block_text):
                findings.append(
                    Finding(
                        line_for_offset(line_map, match.start()),
                        "semicolon",
                        "error",
                        "split procedural clauses into separate sentences or steps",
                    )
                )
            for match in CONTRACTION_RE.finditer(block_text):
                findings.append(
                    Finding(
                        line_for_offset(line_map, match.start()),
                        "contraction",
                        "error",
                        "expand contractions in strict procedural text",
                    )
                )
            for match in PERFECT_TENSE_RE.finditer(block_text):
                findings.append(
                    Finding(
                        line_for_offset(line_map, match.start()),
                        "perfect-tense",
                        "review",
                        "prefer a simple tense: “the service stopped”, "
                        "not “the service has stopped”",
                    )
                )

        for rule, pattern, message in PHRASE_RULES:
            for match in pattern.finditer(block_text):
                findings.append(
                    Finding(
                        line_for_offset(line_map, match.start()),
                        rule,
                        "review",
                        message,
                    )
                )

        for match in PASSIVE_RE.finditer(block_text):
            findings.append(
                Finding(
                    line_for_offset(line_map, match.start()),
                    "possible-passive",
                    "review",
                    "name the actor if responsibility matters; keep passive voice when it does not",
                )
            )

    return sorted(findings, key=lambda item: (item.line, item.rule, item.message))


def read_inputs(paths: Iterable[str]) -> list[tuple[str, str]]:
    inputs: list[tuple[str, str]] = []
    stdin_seen = False
    for value in paths:
        if value == "-":
            if stdin_seen:
                raise ValueError("stdin may be specified only once")
            stdin_seen = True
            inputs.append(("<stdin>", sys.stdin.read()))
            continue
        path = Path(value)
        try:
            inputs.append((value, path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"cannot read {value}: {exc}") from exc
    return inputs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report advisory clarity findings without rewriting prose."
    )
    parser.add_argument("--mode", choices=("strict", "natural"), required=True)
    parser.add_argument("--json", action="store_true", help="emit structured output")
    parser.add_argument("paths", nargs="+", metavar="PATH", help="Markdown file or - for stdin")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        inputs = read_inputs(args.paths)
    except ValueError as exc:
        print(f"prose_lint: {exc}", file=sys.stderr)
        return 2

    results = []
    error_count = 0
    for path, text in inputs:
        findings = lint_text(text, args.mode)
        error_count += sum(finding.severity == "error" for finding in findings)
        results.append(
            {
                "path": path,
                "findings": [asdict(finding) for finding in findings],
            }
        )

    if args.json:
        print(json.dumps({"mode": args.mode, "files": results}, indent=2))
    else:
        for result in results:
            if not result["findings"]:
                print(f"{result['path']}: no findings")
                continue
            for finding in result["findings"]:
                print(
                    f"{result['path']}:{finding['line']}: {finding['severity']} "
                    f"{finding['rule']}: {finding['message']}"
                )

    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
