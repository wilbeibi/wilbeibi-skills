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
import yaml
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

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
    """Convert natural language to date range."""
    query_lower = query.lower()
    now = datetime.now()

    # Handle "last X days" pattern
    last_n_days = re.search(r'last (\d+) days?', query_lower)
    if last_n_days:
        days = int(last_n_days.group(1))
        start = now - timedelta(days=days)
        return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

    if any(x in query_lower for x in ["recent week", "last week", "past week"]):
        start = now - timedelta(days=7)
        return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

    if any(x in query_lower for x in ["recent month", "last month", "past month"]):
        start = now - timedelta(days=30)
        return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

    if "yesterday" in query_lower:
        date = now - timedelta(days=1)
        return date.strftime("%Y-%m-%d"), date.strftime("%Y-%m-%d")

    if "today" in query_lower:
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")

    # Extract specific dates
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', query)
    if date_match:
        date = date_match.group()
        return date, date

    return None, None

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
    except:
        pass
    return []

def search_notes_simple(query: str, vault_path: str = ".") -> List[str]:
    """Simple note search using ripgrep."""
    language = detect_language(query)
    terms = get_search_terms(query, language)

    # Parse dates if present
    start_date, end_date = parse_natural_date(query)

    results = []

    # Date-based search - only check most common pattern
    if start_date:
        if start_date == end_date:
            # Single day - check YYYY-MM-DD format only
            pattern = f"created: {start_date}"
        else:
            # Date range - match YYYY-MM pattern
            pattern = f"created: {start_date[:7]}"  # 2026-01

        date_results = rg(pattern, vault_path, ["-l"])

        # If no results, fallback to file system time
        if not date_results and start_date:
            # Get all .md files and filter by mtime
            import os
            from pathlib import Path

            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else start_dt

            for file_path in Path(vault_path).glob("**/*.md"):
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if start_dt <= mtime <= end_dt + timedelta(days=1):
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
    """Task search with simple filtering."""
    query_lower = query.lower()
    today = datetime.now().strftime("%Y-%m-%d")

    # Build pattern based on query type
    if "due today" in query_lower:
        pattern = f"^- \\[ \\].*📅 {today}"
    elif "overdue" in query_lower:
        # Get all tasks with dates, filter in Python
        pattern = "^- \\[ \\].*📅 \\d{4}-\\d{2}-\\d{2}"
    elif "high priority" in query_lower:
        pattern = "^- \\[ \\].*⏫"
    elif "priority" in query_lower:
        pattern = "^- \\[ \\].*[⏫🔼🔽]"
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

            # Filter overdue tasks
            if "overdue" in query_lower:
                date_match = re.search(r'📅 (\d{4}-\d{2}-\d{2})', parts[2])
                if date_match and date_match.group(1) < today:
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
    parser.add_argument("--vault", default=".", help="Vault path")
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
