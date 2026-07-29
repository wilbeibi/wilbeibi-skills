#!/usr/bin/env python3
"""Append quick captures to Obsidian daily/weekly notes.

Stdlib only. Requires $OBSIDIAN_VAULT. See `capture.py --help`.
Prints the file and line it wrote so the caller can confirm.
"""
import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

WEEKDAYS = {name: i for i, names in enumerate(
    [("mon", "monday"), ("tue", "tues", "tuesday"), ("wed", "weds", "wednesday"),
     ("thu", "thur", "thurs", "thursday"), ("fri", "friday"),
     ("sat", "saturday"), ("sun", "sunday")]) for name in names}

PRIORITY = {"high": "⏫", "med": "🔼", "medium": "🔼", "low": "🔽"}


def die(msg):
    sys.exit(f"capture.py: {msg}")


def vault_root() -> Path:
    v = os.environ.get("OBSIDIAN_VAULT")
    if v:
        root = Path(v).expanduser()
    else:
        root = Path.cwd()
        if not ((root / "DailyPlan").is_dir() and (root / "Weekly").is_dir()):
            die("$OBSIDIAN_VAULT is not set and cwd is not a vault (no DailyPlan/ + Weekly/)")
    if not root.is_dir():
        die(f"vault not found: {root}")
    return root


def parse_when(s: str, base: dt.date):
    """today | tomorrow | +Nd | mon..sunday | this-week | next-week | YYYY-MM-DD | none"""
    t = s.strip().lower().replace(" ", "-")
    if t in ("none", "no", "-"):
        return None
    if t == "today":
        return base
    if t in ("tomorrow", "tmr"):
        return base + dt.timedelta(days=1)
    if t in ("this-week", "eow"):
        return base + dt.timedelta(days=6 - base.weekday())
    if t == "next-week":
        return base + dt.timedelta(days=7 - base.weekday())
    m = re.fullmatch(r"\+(\d+)d?", t)
    if m:
        return base + dt.timedelta(days=int(m.group(1)))
    if t in WEEKDAYS:
        return base + dt.timedelta(days=(WEEKDAYS[t] - base.weekday()) % 7)
    try:
        return dt.date.fromisoformat(t)
    except ValueError:
        die(f"can't parse due date {s!r} "
            "(use today, tomorrow, +Nd, mon..sunday, this-week, next-week, YYYY-MM-DD, none)")


def daily_path(root: Path, d: dt.date) -> Path:
    return root / "DailyPlan" / f"{d:%Y-%m-%d} {d:%a}.md"


def weekly_path(root: Path, d: dt.date) -> Path:
    iso = d.isocalendar()
    return root / "Weekly" / f"{iso[0]}-W{iso[1]:02d}.md"


# --- template rendering (the {{date:...}} moment-format subset the templates use) ---

def moment_format(d: dt.date, fmt: str) -> str:
    iso = d.isocalendar()
    out, i = [], 0
    while i < len(fmt):
        if fmt[i] == "[":
            j = fmt.index("]", i)
            out.append(fmt[i + 1:j])
            i = j + 1
        elif fmt.startswith("GGGG", i):
            out.append(str(iso[0])); i += 4
        elif fmt.startswith("YYYY", i):
            out.append(f"{d.year:04d}"); i += 4
        elif fmt.startswith("MM", i):
            out.append(f"{d.month:02d}"); i += 2
        elif fmt.startswith("DD", i):
            out.append(f"{d.day:02d}"); i += 2
        elif fmt.startswith("WW", i):
            out.append(f"{iso[1]:02d}"); i += 2
        elif fmt.startswith("dddd", i):
            out.append(d.strftime("%A")); i += 4
        elif fmt.startswith("ddd", i):
            out.append(d.strftime("%a")); i += 3
        else:
            out.append(fmt[i]); i += 1
    return "".join(out)


def render_template(text: str, base: dt.date) -> str:
    def repl(m):
        offset = int(m.group("off") or 0)
        return moment_format(base + dt.timedelta(days=offset), m.group("fmt"))
    return re.sub(r"\{\{date(?:(?P<off>[+-]\d+)d)?:(?P<fmt>[^}]+)\}\}", repl, text)


def ensure_note(root: Path, path: Path, template_name: str, base: dt.date) -> bool:
    # Non-empty, not merely existing: clicking a dangling [[2026-W30]] nav link
    # in Obsidian leaves a 0-byte note, and treating that as "already created"
    # means the template (and its ## Clips base block) never lands.
    if path.exists() and path.stat().st_size > 0:
        return False
    tpl = root / "Meta-Obsidian" / "Templates" / template_name
    if not tpl.exists():
        die(f"note {path.name} missing and template not found: {tpl}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_template(tpl.read_text(), base))
    return True


# --- section-aware editing (never touches fenced code blocks) ---

def fence_mask(lines):
    """True for lines inside (or opening/closing) ``` fences."""
    mask, inside = [], False
    for ln in lines:
        opens = ln.lstrip().startswith("```")
        if opens:
            mask.append(True)
            inside = not inside
        else:
            mask.append(inside)
    return mask


def find_section(lines, heading_substr):
    """Return (heading_idx, end_idx). End = next '## ' heading or '---' rule outside fences."""
    mask = fence_mask(lines)
    start = None
    for i, ln in enumerate(lines):
        if mask[i]:
            continue
        if start is None:
            if ln.startswith("## ") and heading_substr in ln:
                start = i
        elif ln.startswith("## ") or ln.strip() == "---":
            return start, i
    if start is None:
        return None, None
    return start, len(lines)


def insert_in_section(lines, heading_substr, new_lines, placeholder=None):
    """Fill a placeholder slot if present, else append after the section's last content line.

    `new_lines`: list of lines (first is the entry, rest are its sub-bullets).
    Returns a description of what happened; mutates `lines`.
    """
    h, end = find_section(lines, heading_substr)
    if h is None:
        die(f"section containing {heading_substr!r} not found")
    if placeholder:
        pat = re.compile(placeholder)
        for i in range(h + 1, end):
            if pat.fullmatch(lines[i].rstrip()):
                lines[i] = new_lines[0]
                lines[i + 1:i + 1] = new_lines[1:]
                return f"filled empty slot (line {i + 1})"
    last = h
    for i in range(h + 1, end):
        if lines[i].strip():
            last = i
    if last == h:  # empty section
        lines[h + 1:h + 1] = [""] + new_lines
        at = h + 3
    else:
        lines[last + 1:last + 1] = new_lines
        at = last + 2
    return f"appended (line {at})"


def load(path: Path):
    return path.read_text().splitlines()


def save(path: Path, lines):
    path.write_text("\n".join(lines) + "\n")


def report(path: Path, root: Path, created: bool, what: str, line: str):
    note = " (created from template)" if created else ""
    print(f"{path.relative_to(root)}{note}: {what}")
    print(f"  {line}")


# --- commands ---

def cmd_todo(args, root, today):
    if args.weekly:
        path = weekly_path(root, today)
        created = ensure_note(root, path, "Weekly Template.md", today)
        default_due = min(today + dt.timedelta(days=3),
                          today + dt.timedelta(days=6 - today.weekday()))
        section, placeholder = "Todos", None
    else:
        path = daily_path(root, today)
        created = ensure_note(root, path, "DailyTemplate.md", today)
        default_due = today
        section = "今天必须完成" if args.must else "其他"
        placeholder = r"- \[ \]\s*"
    if args.agent and not args.ctx:
        die("--agent requires context: add --ctx \"context: <paths/repos/URLs>\" "
            "and --ctx \"done-when: <acceptance criteria>\"")
    due = parse_when(args.due, today) if args.due else default_due
    line = f"- [ ] {args.text}"
    if args.agent:
        line += " #agent-todo"
    if due:
        line += f" 📅 {due}"
    if args.priority or (args.weekly and args.must):
        line += f" {PRIORITY[args.priority or 'high']}"
    new_lines = [line] + [f"\t- {c}" for c in (args.ctx or [])]

    lines = load(path)
    if args.weekly and find_section(lines, "Todos")[0] is None:
        fun, _ = find_section(lines, "Something Fun")
        anchor = fun if fun is not None else len(lines)
        lines[anchor:anchor] = ["## Todos", ""]
    what = insert_in_section(lines, section, new_lines, placeholder)
    save(path, lines)
    report(path, root, created, f"{section} — {what}", "\n  ".join(new_lines))


def cmd_log(args, root, today):
    path = daily_path(root, today)
    created = ensure_note(root, path, "DailyTemplate.md", today)
    time = args.time or dt.datetime.now().strftime("%H:%M")
    if not re.fullmatch(r"\d{1,2}:\d{2}", time):
        die(f"bad --time {args.time!r}, expected HH:MM")
    line = f"- {time} {args.text}"
    lines = load(path)
    what = insert_in_section(lines, "Log", [line], placeholder=r"- HH:mm\s*")
    save(path, lines)
    report(path, root, created, f"Log — {what}", line)


def _memo(args, root, today, label):
    path = daily_path(root, today)
    created = ensure_note(root, path, "DailyTemplate.md", today)
    line = f"- {label}: {args.text}"
    lines = load(path)
    what = insert_in_section(lines, "今日记", [line], placeholder=rf"- {label}[:：]\s*")
    save(path, lines)
    report(path, root, created, f"今日记 — {what}", line)


def cmd_learned(args, root, today):
    _memo(args, root, today, "新知")


def cmd_diary(args, root, today):
    _memo(args, root, today, "新事")


def cmd_fun(args, root, today):
    path = weekly_path(root, today)
    created = ensure_note(root, path, "Weekly Template.md", today)
    line = f"- {args.text}"
    lines = load(path)
    what = insert_in_section(lines, "Something Fun", [line])
    save(path, lines)
    report(path, root, created, f"Something Fun This Week — {what}", line)


def cmd_reflect(args, root, today):
    path = weekly_path(root, today)
    created = ensure_note(root, path, "Weekly Template.md", today)
    lines = load(path)
    h, end = find_section(lines, "Reflections")
    if h is None:
        die("Reflections section not found")
    for i in range(h + 1, end):
        if lines[i].startswith("Q:") and args.match in lines[i]:
            lines[i + 1:i + 1] = ["", args.text]
            save(path, lines)
            report(path, root, created, f"Reflections — under {lines[i][:40]!r}", args.text)
            return
    die(f"no reflection question matches {args.match!r}")


def note_date(path: Path):
    """Date encoded in a note's filename: daily YYYY-MM-DD or weekly GGGG-WNN (its Monday)."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", path.stem)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"(\d{4})-W(\d{1,2})$", path.stem)
    if m:
        try:
            return dt.date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)
        except ValueError:
            return None
    return None


def all_notes(root, today, days=0):
    """Today's daily + weekly first, then other notes newest-first.

    days > 0: skip notes whose filename date is older than `days` (no file reads needed).
    """
    first = [p for p in (daily_path(root, today), weekly_path(root, today)) if p.exists()]
    cutoff = today - dt.timedelta(days=days) if days else None
    rest = []
    for d in ("DailyPlan", "Weekly"):
        for p in (root / d).glob("*.md"):
            if p in first:
                continue
            nd = note_date(p)
            if nd is None or (cutoff and nd < cutoff):
                continue
            rest.append(p)
    return first + sorted(rest, key=lambda p: p.name, reverse=True)


def find_open_todo(root, today, match):
    """Yield (path, lines, index) of the first open '- [ ]' line containing `match`."""
    for path in all_notes(root, today):
        lines = load(path)
        mask = fence_mask(lines)
        for i, ln in enumerate(lines):
            if not mask[i] and ln.lstrip().startswith("- [ ]") and match in ln:
                return path, lines, i
    die(f"no open todo matches {match!r} in DailyPlan/ or Weekly/")


def cmd_done(args, root, today):
    path, lines, i = find_open_todo(root, today, args.match)
    lines[i] = lines[i].replace("- [ ]", "- [x]", 1).rstrip() + f" ✅ {today}"
    save(path, lines)
    report(path, root, False, f"done (line {i + 1})", lines[i].strip())


def cmd_annotate(args, root, today):
    path, lines, i = find_open_todo(root, today, args.match)
    j = i + 1
    while j < len(lines) and lines[j].strip() and lines[j][0] in " \t":
        j += 1
    lines.insert(j, f"\t- {args.text}")
    save(path, lines)
    report(path, root, False, f"annotated (line {j + 1})", lines[j].strip())


def cmd_agenda(args, root, today):
    found = []
    for path in all_notes(root, today, days=args.days):
        lines = load(path)
        mask = fence_mask(lines)
        for i, ln in enumerate(lines):
            if mask[i] or not ln.lstrip().startswith("- [ ]") or "#agent-todo" not in ln:
                continue
            m = re.search(r"📅 (\d{4}-\d{2}-\d{2})", ln)
            due = dt.date.fromisoformat(m.group(1)) if m else today  # undated counts as due
            if due > today:
                continue
            ctx = []
            j = i + 1
            while j < len(lines) and lines[j].strip() and lines[j][0] in " \t":
                ctx.append(lines[j])
                j += 1
            found.append((due, path.relative_to(root), i + 1, ln, ctx))
    for due, rel, lineno, ln, ctx in sorted(found, key=lambda f: f[0]):
        print(f"{rel}:{lineno}")
        print(ln)
        print("\n".join(ctx) + "\n" if ctx else "")
    scope = f"notes from the last {args.days} days (--days 0 for all)" if args.days else "all notes"
    print(f"{len(found)} #agent-todo due — scanned {scope}" if found
          else f"no #agent-todo due — nothing to do (scanned {scope})")


def cmd_paths(args, root, today):
    print(daily_path(root, today))
    print(weekly_path(root, today))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("todo", help="add a todo (daily by default, due today; "
                                    "--weekly: ## Todos, due today+3d capped at Sunday)")
    t.add_argument("text")
    t.add_argument("-w", "--weekly", action="store_true", help="weekly note instead of daily")
    t.add_argument("--must", action="store_true",
                   help="daily 🎯 must-do section (with --weekly: adds ⏫ instead)")
    t.add_argument("--due", help="today|tomorrow|+Nd|mon..sunday|this-week|next-week|YYYY-MM-DD|none")
    t.add_argument("-p", "--priority", choices=sorted(PRIORITY), help="⏫/🔼/🔽 marker")
    t.add_argument("--agent", action="store_true",
                   help="agent-owned todo: tags #agent-todo, requires --ctx")
    t.add_argument("--ctx", action="append", metavar="TEXT",
                   help="indented context sub-bullet under the todo (repeatable)")
    t.set_defaults(func=cmd_todo)

    lg = sub.add_parser("log", help="timestamped line in daily 🪵 Log")
    lg.add_argument("text")
    lg.add_argument("--time", help="HH:MM (default: now)")
    lg.set_defaults(func=cmd_log)

    for name, hlp, fn in [("learned", "daily 今日记 新知: line", cmd_learned),
                          ("diary", "daily 今日记 新事: line", cmd_diary),
                          ("fun", "weekly Something Fun This Week", cmd_fun)]:
        sp = sub.add_parser(name, help=hlp)
        sp.add_argument("text")
        sp.set_defaults(func=fn)

    r = sub.add_parser("reflect", help="answer a weekly reflection question")
    r.add_argument("match", help="substring of the Q: line")
    r.add_argument("text", help="the answer")
    r.set_defaults(func=cmd_reflect)

    d = sub.add_parser("done", help="tick the first open todo matching a substring "
                                    "(today's notes searched first, then all notes)")
    d.add_argument("match")
    d.set_defaults(func=cmd_done)

    a = sub.add_parser("annotate", help="append a sub-bullet under the first matching open todo "
                                        "(e.g. 'blocked: <question>')")
    a.add_argument("match")
    a.add_argument("text")
    a.set_defaults(func=cmd_annotate)

    ag = sub.add_parser("agenda", help="list open #agent-todo tasks due ≤ today, with their "
                                       "context sub-bullets and file:line")
    ag.add_argument("--days", type=int, default=90,
                    help="only scan notes from the last N days (default 90; 0 = all)")
    ag.set_defaults(func=cmd_agenda)

    sub.add_parser("paths", help="print today's daily and weekly note paths").set_defaults(func=cmd_paths)

    args = p.parse_args()
    args.func(args, vault_root(), dt.date.today())


if __name__ == "__main__":
    main()
