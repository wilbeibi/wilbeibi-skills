#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.28.0",
# ]
# ///

"""
Meilisearch vault search — search Obsidian notes via a Meilisearch index.

Usage:
  uv run meili_search.py "query"
  uv run meili_search.py "query" --limit 10
  uv run meili_search.py "query" --filter "tags=ai"
  uv run meili_search.py "query" --fields "title,path,tags"
  uv run meili_search.py "query" --full
  uv run meili_search.py "query" --json     # machine-readable for agents

Config (env):
  MEILI_URL         Meilisearch endpoint (default: http://127.0.0.1:7700)
  MEILI_SEARCH_KEY  search-only API key; falls back to ~/meilisearch/search-key.txt
  MEILI_INDEX       index uid (default: notes)

Hit paths are vault-relative; join with your vault root to open a note.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

MEILI_URL = os.environ.get("MEILI_URL", "http://127.0.0.1:7700").rstrip("/")
INDEX = os.environ.get("MEILI_INDEX", "notes")
TIMEOUT = 10
HL_PRE = "<<"
HL_POST = ">>"


def load_api_key() -> str:
    key = os.environ.get("MEILI_SEARCH_KEY")
    if key:
        return key.strip()
    key_file = Path.home() / "meilisearch" / "search-key.txt"
    if key_file.exists():
        return key_file.read_text().strip()
    print(
        "ERROR: no Meili search key. Set $MEILI_SEARCH_KEY or create "
        "~/meilisearch/search-key.txt",
        file=sys.stderr,
    )
    sys.exit(2)


def search_notes(
    query: str,
    limit: int = 5,
    filter_expr: str | None = None,
    fields: str | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    """Execute a search against the Meilisearch notes index."""
    url = f"{MEILI_URL}/indexes/{INDEX}/search"
    headers = {
        "Authorization": f"Bearer {load_api_key()}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "q": query,
        "limit": limit,
        "attributesToHighlight": ["title", "content"],
        "highlightPreTag": HL_PRE,
        "highlightPostTag": HL_POST,
    }

    if filter_expr:
        payload["filter"] = [filter_expr]

    if fields:
        wanted = [f.strip() for f in fields.split(",")]
        payload["attributesToRetrieve"] = wanted
        # Keep highlights (and their full-content copies) out of fields the
        # caller didn't ask for.
        payload["attributesToHighlight"] = [
            f for f in ("title", "content") if f in wanted
        ]

    if sort:
        payload["sort"] = [s.strip() for s in sort.split(",")]

    resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def format_date(raw: Any) -> str:
    """Format ISO date string or Unix timestamp to a short readable form."""
    if not raw:
        return "—"
    # Unix timestamp (integer seconds since epoch)
    if isinstance(raw, (int, float)) and raw > 1e8:
        try:
            return datetime.fromtimestamp(raw).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return str(raw)
    # ISO 8601 string
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(raw)


def format_tags(raw: Any) -> str:
    """Format tags field to a comma-separated string."""
    if not raw:
        return "—"
    if isinstance(raw, list):
        return ", ".join(str(t) for t in raw if t)
    return str(raw)


def snippet(content: Any, max_chars: int = 200) -> str:
    """Return a short plain-text snippet from content."""
    if not content:
        return "—"
    text = str(content).strip()
    if len(text) == 0:
        return "—"
    if len(text) > max_chars:
        return text[:max_chars].rsplit(" ", 1)[0] + " …"
    return text


def display_results(data: dict[str, Any], full: bool = False) -> None:
    """Print search results in a clean, readable format."""
    hits = data.get("hits", [])
    total = data.get("estimatedTotalHits", 0)

    if not hits:
        print("No results found.")
        return

    print(f"Found {total} result(s). Showing {len(hits)}:\n")

    for i, hit in enumerate(hits, 1):
        formatted = hit.get("_formatted", {})
        title = formatted.get("title") or hit.get("title") or hit.get("id", "Untitled")
        path = hit.get("path", "—")
        tags = format_tags(hit.get("tags"))
        created = format_date(hit.get("created"))
        desc = hit.get("description") or "—"
        content = formatted.get("content") or hit.get("content", "")

        print(f"{'═' * 60}")
        print(f"  [{i}] {title}")
        print(f"{'─' * 60}")
        print(f"  Path    : {path}")
        print(f"  Tags    : {tags}")
        print(f"  Created : {created}")
        print(f"  Desc    : {desc}")
        if full and content:
            print(f"  ── Content ──")
            print(f"  {content.strip()}")
        else:
            print(f"  ── Snippet ──")
            print(f"  {snippet(content)}")
        print()

    print(f"{'═' * 60}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search Obsidian vault notes via Meilisearch."
    )
    parser.add_argument("query", nargs="?", default="", help="Search query string")
    parser.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help='Filter expression, e.g. "tags=ai"',
    )
    parser.add_argument(
        "--fields",
        type=str,
        default=None,
        help='Comma-separated fields to return, e.g. "title,path,tags"',
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show full content instead of a cropped snippet",
    )
    parser.add_argument(
        "--sort",
        type=str,
        default=None,
        help='Sort expression(s), comma-separated. e.g. "updated:desc"',
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit raw Meilisearch JSON response (for agents).",
    )

    args = parser.parse_args()

    if not args.query and not args.filter:
        parser.print_help()
        sys.exit(1)

    try:
        data = search_notes(
            query=args.query,
            limit=args.limit,
            filter_expr=args.filter,
            fields=args.fields,
            sort=args.sort,
        )
        if args.json:
            json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        else:
            display_results(data, full=args.full)
    except requests.exceptions.ConnectionError:
        print(
            f"ERROR: Could not connect to Meilisearch at {MEILI_URL}. "
            "Is it running / reachable? Fall back to ripgrep search.",
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        detail = ""
        if e.response is not None:
            try:
                detail = e.response.json().get("message", "")
            except Exception:
                detail = e.response.text[:200]
        print(
            f"ERROR: Meilisearch returned HTTP {status}: {detail}",
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed — {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error — {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
