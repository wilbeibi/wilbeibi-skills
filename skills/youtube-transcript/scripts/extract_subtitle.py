#!/usr/bin/env python3
"""Download YouTube subtitles with yt-dlp and print selected subtitle paths."""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract YouTube subtitle files with yt-dlp.")
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument(
        "--out-dir",
        default="/tmp/youtube-transcript",
        help="Directory for downloaded subtitle files",
    )
    parser.add_argument(
        "--langs",
        default="en.*,en",
        help="yt-dlp subtitle language selector",
    )
    args = parser.parse_args()

    if not shutil.which("yt-dlp"):
        print(
            json.dumps(
                {
                    "returncode": 127,
                    "subtitle_paths": [],
                    "best_subtitle": None,
                    "stdout": "",
                    "stderr": "yt-dlp is not installed or not on PATH.",
                },
                indent=2,
            )
        )
        print("yt-dlp is not installed or not on PATH.", file=sys.stderr)
        return 127

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time() - 1

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        args.langs,
        "--sub-format",
        "vtt/srt/best",
        "--skip-download",
        "--output",
        str(out_dir / "%(title).200B [%(id)s].%(ext)s"),
        args.url,
    ]

    proc = subprocess.run(cmd, text=True, capture_output=True)
    subtitle_paths = sorted(
        [
            str(path)
            for pattern in ("*.vtt", "*.srt")
            for path in out_dir.glob(pattern)
            if path.stat().st_mtime >= started
        ]
    )

    result = {
        "returncode": proc.returncode,
        "subtitle_paths": subtitle_paths,
        "best_subtitle": subtitle_paths[0] if subtitle_paths else None,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if proc.returncode != 0:
        return proc.returncode
    if not subtitle_paths:
        print("No subtitle files were downloaded.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
