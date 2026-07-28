#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Vault Search - Minimal processing layer for what ripgrep can't handle

PHILOSOPHY:
- 80% queries → direct ripgrep (fast)
- 20% queries → this script (date math, ranking, language detection)
- AI agent orchestrates and understands intent

WHAT THIS SCRIPT DOES:
1. Natural language dates → date ranges ("recent week" → last 7 days)
2. Multi-dimensional ranking (combine date + tag + content matches)
3. Language-specific search patterns (Chinese vs English)
4. Date comparisons for tasks (overdue filtering)

WHAT IT DOESN'T DO:
- Simple grep patterns → use ripgrep directly
- Complex intent parsing → AI agent handles that
"""

import os
import re
import sys
import yaml
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

# Best-effort signal that a task query wanted a date filter, for the
# "did we silently drop your filter" warning in search_tasks — not
# exhaustive, just enough to catch phrasing near what's already supported.
TEMPORAL_HINT = re.compile(r'\b(today|yesterday|overdue|week|month|days?)\b|\d{4}-\d{2}-\d{2}')

def detect_language(query: str) -> str:
    """Simple language detection based on character presence."""
    if any('\u4e00' <= ch <= '\u9fff' for ch in query):
        return "chinese"
    return "english"

def get_search_terms(query: str, language: str) -> List[str]:
    """Extract search terms from the query without hardcoded synonym lists."""
    if language == "chinese":
        # Prefer contiguous CJK sequences; fall back to alnum tokens.
        cjk_terms = re.findall(r'[\u4e00-\u9fff]{2,}', query)
        if cjk_terms:
            return cjk_terms
        return re.findall(r'[A-Za-z0-9]{3,}', query)

    # English/default: basic tokenization, keep 3+ length to reduce noise.
    return re.findall(r'[A-Za-z0-9]{3,}', query.lower())




def parse_natural_date(query: str) -> Tuple[Optional[str], Optional[str]]:
    """Convert natural language to a (start, end) date range, inclusive.

    None on either side means open-ended (unbounded past / unbounded future).
    This is the single place new date phrases get taught — callers (note
    search, task search) just consume the resulting range, so adding a
    phrase here benefits every caller instead of needing a per-caller branch.

    Uses the host machine's local clock (datetime.now()), not a configured
    timezone — correct as long as this runs where the user is (the Mac).
    Don't call this from a differently-timezoned host (e.g. a cron job on
    the joi mirror) and expect "today"/"overdue" to line up with PDT.
    """
    query_lower = query.lower()
    now = datetime.now()
    fmt = "%Y-%m-%d"

    # Handle "last X days" pattern
    last_n_days = re.search(r'last (\d+) days?', query_lower)
    if last_n_days:
        days = int(last_n_days.group(1))
        start = now - timedelta(days=days)
        return start.strftime(fmt), now.strftime(fmt)

    if any(x in query_lower for x in ["recent week", "last week", "past week"]):
        start = now - timedelta(days=7)
        return start.strftime(fmt), now.strftime(fmt)

    if any(x in query_lower for x in ["recent month", "last month", "past month"]):
        start = now - timedelta(days=30)
        return start.strftime(fmt), now.strftime(fmt)

    # ISO week (Monday-Sunday) containing "now", shifted by `offset` weeks.
    def iso_week_range(offset: int) -> Tuple[str, str]:
        monday = now - timedelta(days=now.weekday()) + timedelta(weeks=offset)
        sunday = monday + timedelta(days=6)
        return monday.strftime(fmt), sunday.strftime(fmt)

    if "this week" in query_lower:
        return iso_week_range(0)

    if "next week" in query_lower:
        return iso_week_range(1)

    if "overdue" in query_lower:
        # Open start, end = yesterday: anything with a date strictly before today.
        yesterday = now - timedelta(days=1)
        return None, yesterday.strftime(fmt)

    if "yesterday" in query_lower:
        date = now - timedelta(days=1)
        return date.strftime(fmt), date.strftime(fmt)

    if "today" in query_lower:
        return now.strftime(fmt), now.strftime(fmt)

    # Extract specific dates
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', query)
    if date_match:
        date = date_match.group()
        return date, date

    return None, None

def in_range(date_str: str, start: Optional[str], end: Optional[str]) -> bool:
    """ISO date-string membership in an inclusive [start, end] range.

    None on either side is an open bound. The one place every date filter
    (task due-dates, note created-dates, the mtime fallback) checks
    membership, so all three agree on inclusivity instead of each inventing
    its own comparison.
    """
    if start and date_str < start:
        return False
    if end and date_str > end:
        return False
    return True

def rg(pattern: str, path: str = ".", extra_args: List[str] = None) -> List[str]:
    """Simple ripgrep wrapper."""
    cmd = ["rg", pattern, "--glob", "*.md"]
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        if result.returncode > 1:
            # 1 = no matches (normal, silent). >1 = rg itself failed
            # (bad pattern, missing binary, etc.) — an agent caller can't
            # tell that apart from "genuinely zero results" unless we say so.
            print(f"rg failed (exit {result.returncode}): {result.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"rg failed to run: {e}", file=sys.stderr)
    return []

def search_notes_simple(query: str, vault_path: str = ".") -> List[str]:
    """Simple note search using ripgrep."""
    language = detect_language(query)
    terms = get_search_terms(query, language)

    # Parse dates if present
    start_date, end_date = parse_natural_date(query)

    results = []

    # Date-based search: grep a superset of dated frontmatter, then filter
    # precisely with in_range — same shape and same inclusivity rule that
    # search_tasks uses for 📅 due-dates, instead of a month-prefix
    # approximation that overmatches (a week can span two months).
    if start_date or end_date:
        candidates = rg(r"created: \d{4}-\d{2}-\d{2}", vault_path, ["-n"])
        date_results = []
        for line in candidates:
            if not line:
                continue
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', parts[2])
            if date_match and in_range(date_match.group(), start_date, end_date):
                date_results.append(parts[0])

        # No frontmatter matches at all → fall back to file system mtime,
        # same range check.
        if not date_results:
            for file_path in Path(vault_path).glob("**/*.md"):
                mtime_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")
                if in_range(mtime_date, start_date, end_date):
                    date_results.append(str(file_path.relative_to(vault_path)))

        results.extend(date_results)

    # Content search based on query terms only; synonyms handled by the agent.
    for term in terms:
        pattern = re.escape(term)
        if language != "chinese":
            pattern = rf"\b{pattern}\b"
        term_results = rg(pattern, vault_path, ["-l", "-i"])
        if term_results:
            results.extend(term_results)

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for r in results:
        if r and r not in seen:
            seen.add(r)
            unique.append(r)

    return unique

def search_tasks(query: str, vault_path: str = ".") -> List[Dict]:
    """Task search with simple filtering.

    Priority is its own concept (not date-based) and stays a direct glyph
    match. Everything date-related — today, overdue, this week, a specific
    date — goes through parse_natural_date's (start, end) range so new date
    phrases only need to be taught once, in that one function.
    """
    query_lower = query.lower()
    start_date, end_date = parse_natural_date(query)

    if not (start_date or end_date) and TEMPORAL_HINT.search(query_lower):
        # Query looks like it wanted a date filter but no phrase matched —
        # say so, rather than silently falling through to an unfiltered
        # task dump that looks identical to a real (empty) date match.
        print(f"# date phrase not recognized in {query!r} — showing unfiltered results", file=sys.stderr)

    if "high priority" in query_lower:
        pattern = "^- \\[ \\].*⏫"
    elif "priority" in query_lower:
        pattern = "^- \\[ \\].*[⏫🔼🔽]"
    elif start_date or end_date:
        # Get all tasks with dates, filter by range in Python
        pattern = "^- \\[ \\].*📅 \\d{4}-\\d{2}-\\d{2}"
    else:
        # General task search
        pattern = "^- \\[ \\]"

    # Get matches
    lines = rg(pattern, vault_path, ["-n"])

    # Parse and filter
    tasks = []
    for line in lines:
        if not line:
            continue
        parts = line.split(':', 2)
        if len(parts) >= 3:
            task = {
                "file": parts[0],
                "line": parts[1],
                "text": parts[2]
            }

            if start_date or end_date:
                date_match = re.search(r'📅 (\d{4}-\d{2}-\d{2})', parts[2])
                if date_match and in_range(date_match.group(1), start_date, end_date):
                    tasks.append(task)
            else:
                tasks.append(task)

    return tasks

def main():
    parser = argparse.ArgumentParser(
        description="Vault search with natural language support",
        epilog="Examples:\n"
               "  %(prog)s 'recent week psychology'\n"
               "  %(prog)s 'tasks due today'\n"
               "  %(prog)s '找3-2-1技巧'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--vault",
        default=os.environ.get("OBSIDIAN_VAULT", "."),
        help="Vault path (default: $OBSIDIAN_VAULT or .)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--raw", action="store_true", help="Raw output for piping")

    args = parser.parse_args()

    # Detect task vs note search
    is_task = any(x in args.query.lower() for x in ["task", "todo", "due", "overdue", "priority"])

    if is_task:
        tasks = search_tasks(args.query, args.vault)

        if args.raw:
            for task in tasks[:args.limit]:
                print(f"{task['file']}:{task['line']}:{task['text']}")
        else:
            print(f"🔍 Tasks: '{args.query}'")
            print("=" * 60)
            if tasks:
                for i, task in enumerate(tasks[:args.limit], 1):
                    print(f"\n{i}. {task['file']}:{task['line']}")
                    print(f"   {task['text'].strip()}")
                if len(tasks) > args.limit:
                    print(f"\n💡 Showing {args.limit} of {len(tasks)} tasks")
            else:
                print("❌ No tasks found")
    else:
        notes = search_notes_simple(args.query, args.vault)

        if args.raw:
            for note in notes[:args.limit]:
                print(note)
        else:
            language = detect_language(args.query)
            print(f"🔍 Notes: '{args.query}' [{language}]")
            print("=" * 60)
            if notes:
                for i, note in enumerate(notes[:args.limit], 1):
                    print(f"{i}. {note}")
                if len(notes) > args.limit:
                    print(f"\n💡 Showing {args.limit} of {len(notes)} notes")
            else:
                print("❌ No notes found")

if __name__ == "__main__":
    main()
