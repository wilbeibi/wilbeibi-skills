#!/usr/bin/env python3
"""Build a self-contained offline HTML questionnaire from a questions JSON.

Usage: build.py questions.json [-o out.html]

The output is a single dependency-free HTML file (strict CSP, no network).
The user answers in a browser; drafts autosave to localStorage; "Generate
answers" emits markdown keyed by stable question ids, available as
copy-to-clipboard and as a .md download. See SKILL.md for the JSON schema
and the answers-markdown contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self' blob:; img-src 'none'; connect-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<title>Questionnaire</title>
<style>
:root{
  --bg:#f6f4ef; --card:#fffdf8; --ink:#1c2433; --muted:#67707f; --line:#ddd6c9;
  --accent:#8a5a2a; --accent-soft:#f4e8d8; --good:#2f6b4f;
}
@media (prefers-color-scheme: dark){
  :root{ --bg:#12151c; --card:#1a1e27; --ink:#e8e6e1; --muted:#98a0ad; --line:#2c3240;
         --accent:#d0a26a; --accent-soft:#2b2418; --good:#7fc6a4; }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 ui-sans-serif,-apple-system,"Segoe UI","PingFang SC","Hiragino Sans GB",sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:0 20px 90px}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);
  padding:14px 0 10px;margin-bottom:16px}
h1{font-size:1.35rem;margin:0 0 8px;line-height:1.25}
.progress{display:flex;align-items:center;gap:10px;font-size:.82rem;color:var(--muted)}
.track{flex:1;height:6px;border-radius:3px;background:var(--line);overflow:hidden}
#fill{height:100%;width:0;background:var(--good);transition:width 160ms ease}
.intro{white-space:pre-wrap;color:var(--muted);font-size:.95rem;border-left:3px solid var(--line);
  padding:2px 0 2px 14px;margin:0 0 8px}
h2.sec{font-size:1.05rem;margin:28px 0 4px;color:var(--accent)}
section.q{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:16px 18px;margin:14px 0}
section.q.answered{border-left:3px solid var(--good)}
.head{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.num{color:var(--accent);font-weight:700;font-size:.78rem;letter-spacing:.06em}
.qlabel{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.05em}
.tag-opt{font-size:.72rem;color:var(--muted);border:1px solid var(--line);border-radius:99px;padding:1px 8px}
.stem{font-weight:700;margin:8px 0 6px}
.why{color:var(--muted);font-size:.92rem;margin:0 0 6px;white-space:pre-wrap}
.ref{font-size:.78rem;color:var(--muted);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;margin:0 0 6px}
.opts{margin-top:10px}
.opt{display:flex;gap:10px;align-items:flex-start;padding:9px 12px;border:1px solid var(--line);
  border-radius:10px;margin:6px 0;cursor:pointer}
.opt.on{border-color:var(--accent);background:var(--accent-soft)}
.opt input{margin-top:5px;accent-color:var(--accent)}
.val{font-weight:600}
.rec{font-size:.68rem;font-weight:700;color:var(--accent);border:1px solid var(--accent);
  border-radius:99px;padding:0 7px;margin-left:8px;vertical-align:2px;text-transform:uppercase;letter-spacing:.04em}
.detail{display:block;color:var(--muted);font-size:.85rem;font-weight:400}
textarea{width:100%;border:1px solid var(--line);border-radius:10px;background:var(--card);
  color:var(--ink);padding:9px 11px;font:inherit;font-size:.92rem;resize:vertical;margin-top:10px}
textarea:focus,.opt:focus-within{outline:2px solid var(--accent);outline-offset:1px}
.skipline{color:var(--muted);font-style:italic;font-size:.85rem;margin:14px 0}
.actions{display:flex;gap:10px;align-items:center;margin-top:26px;flex-wrap:wrap}
button{min-height:38px;border:1px solid var(--line);border-radius:10px;padding:7px 14px;
  background:var(--card);color:var(--ink);font:inherit;font-weight:600;cursor:pointer}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.hint{color:var(--muted);font-size:.85rem;flex-basis:100%}
#out h2{font-size:1rem;margin:26px 0 8px}
#outText{min-height:280px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem;margin-top:0}
</style>
</head>
<body>
<div class="wrap">
<header class="bar">
  <h1 id="title"></h1>
  <div class="progress"><span id="count"></span><div class="track"><div id="fill"></div></div></div>
</header>
<div class="intro" id="intro" hidden></div>
<main id="qs"></main>
<div class="actions">
  <button id="build" class="primary">Generate answers</button>
  <button id="copy" hidden>Copy</button>
  <button id="dl" hidden>Download .md</button>
  <span class="hint" id="hint">Unanswered questions are recorded as open, not skipped. Drafts autosave in this browser.</span>
</div>
<div id="out" hidden>
  <h2>Give this back to the agent — paste it into the session or save the .md next to the project</h2>
  <textarea id="outText" readonly spellcheck="false"></textarea>
</div>
</div>
<script>
"use strict";
const CONFIG = __CONFIG_JSON__;
const QS = CONFIG.questions.map((q, i) => ({
  ...q, n: i + 1, type: q.type || "single",
  options: (q.options || []).map(o => typeof o === "string" ? { value: o } : o),
}));
const byId = new Map(QS.map(q => [q.id, q]));
const KEY = "questionnaire::" + CONFIG.title + "::" + QS.map(q => q.id).join("|");
const $ = id => document.getElementById(id);

function h(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

document.title = CONFIG.title;
$("title").textContent = CONFIG.title;
if (CONFIG.intro) { $("intro").hidden = false; $("intro").textContent = CONFIG.intro; }

const main = $("qs");
let lastSection = null;
for (const q of QS) {
  if (q.section && q.section !== lastSection) {
    main.appendChild(h("h2", "sec", q.section));
    lastSection = q.section;
  }
  const skip = h("div", "skipline");
  skip.hidden = true; skip.id = "skip-" + q.id;
  main.appendChild(skip);

  const card = h("section", "q");
  card.id = "card-" + q.id;
  const head = h("div", "head");
  head.appendChild(h("span", "num", "Q" + q.n));
  if (q.label) head.appendChild(h("span", "qlabel", q.label));
  if (q.optional) head.appendChild(h("span", "tag-opt", "optional"));
  card.appendChild(head);
  card.appendChild(h("p", "stem", q.question));
  if (q.why) card.appendChild(h("p", "why", q.why));
  if (q.ref) card.appendChild(h("p", "ref", q.ref));
  if (q.type !== "text") {
    const opts = h("div", "opts");
    for (const o of q.options) {
      const lab = h("label", "opt");
      const inp = document.createElement("input");
      inp.type = q.type === "multi" ? "checkbox" : "radio";
      inp.name = "q-" + q.id;
      inp.value = o.value;
      lab.appendChild(inp);
      const span = h("span", "lab");
      const val = h("span", "val", o.value);
      if (o.recommended) val.appendChild(h("span", "rec", "suggested"));
      span.appendChild(val);
      if (o.detail) span.appendChild(h("span", "detail", o.detail));
      lab.appendChild(span);
      opts.appendChild(lab);
    }
    card.appendChild(opts);
  }
  if (q.type === "text" || q.note) {
    const ta = document.createElement("textarea");
    ta.rows = q.type === "text" ? 4 : 2;
    ta.placeholder = q.type === "text" ? "your answer" : "optional note";
    ta.dataset.note = q.id;
    card.appendChild(ta);
  }
  main.appendChild(card);
}

function chosen(q) {
  return Array.from(document.querySelectorAll('input[name="q-' + q.id + '"]:checked')).map(i => i.value);
}
function noteOf(q) {
  const ta = document.querySelector('textarea[data-note="' + q.id + '"]');
  return ta ? ta.value : "";
}
function visible(q) {
  const c = q.showIf;
  if (!c) return true;
  const target = byId.get(c.q);
  if (!target || !visible(target)) return !target;
  const got = chosen(target)[0] || null;
  if ("is" in c) return got === c.is;
  if ("not" in c) return got === null ? true : got !== c.not;
  return true;
}
function answered(q) {
  return q.type === "text" ? noteOf(q).trim().length > 0 : chosen(q).length > 0;
}

function refresh() {
  let total = 0, done = 0;
  for (const q of QS) {
    const card = $("card-" + q.id), skip = $("skip-" + q.id);
    const on = visible(q);
    card.hidden = !on;
    if (!on) {
      const ctrl = byId.get(q.showIf.q);
      const got = ctrl ? (chosen(ctrl)[0] || null) : null;
      skip.hidden = !got;
      if (got) skip.textContent = "Q" + q.n + (q.label ? " · " + q.label : "") +
        " — skipped (you answered “" + got + "”)";
      continue;
    }
    skip.hidden = true;
    const ok = answered(q);
    card.classList.toggle("answered", ok);
    if (!q.optional) { total++; if (ok) done++; }
  }
  $("count").textContent = done + " / " + total + " answered";
  $("fill").style.width = total ? (100 * done / total) + "%" : "0";
}

function save() {
  const state = {};
  for (const q of QS) state[q.id] = { v: chosen(q), t: noteOf(q) };
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode */ }
}
function restore() {
  let state = null;
  try { state = JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return; }
  if (!state) return;
  for (const q of QS) {
    const s = state[q.id];
    if (!s) continue;
    for (const v of s.v || []) {
      for (const inp of document.querySelectorAll('input[name="q-' + q.id + '"]')) {
        if (inp.value === v) inp.checked = true;
      }
    }
    if (s.t) {
      const ta = document.querySelector('textarea[data-note="' + q.id + '"]');
      if (ta) ta.value = s.t;
    }
  }
  for (const inp of document.querySelectorAll(".opts input")) {
    inp.closest(".opt").classList.toggle("on", inp.checked);
  }
}

document.addEventListener("change", e => {
  const t = e.target;
  if (t.matches("input")) {
    for (const inp of document.querySelectorAll('input[name="' + t.name + '"]')) {
      inp.closest(".opt").classList.toggle("on", inp.checked);
    }
  }
  save(); refresh();
});
document.addEventListener("input", e => {
  if (e.target.matches("textarea")) { save(); refresh(); }
});

function markdown() {
  const date = new Date().toISOString().slice(0, 10);
  let total = 0, done = 0;
  for (const q of QS) if (visible(q) && !q.optional) { total++; if (answered(q)) done++; }
  const L = ["# " + CONFIG.title + " — answers", "", "Answered " + done + " / " + total + " · " + date, ""];
  for (const q of QS) {
    let head = "**Q" + q.n + (q.label ? " · " + q.label : "") + "** (`" + q.id + "`)";
    if (!visible(q)) {
      const ctrl = byId.get(q.showIf.q);
      const got = ctrl ? (chosen(ctrl)[0] || null) : null;
      L.push(head + " — skipped by branching" + (got ? " (" + ctrl.id + " = “" + got + "”)" : ""), "");
      continue;
    }
    const vs = chosen(q), note = noteOf(q).trim();
    const lines = [];
    if (q.type === "text") {
      if (note) lines.push("> " + note.replace(/\n/g, "\n> "));
      else head += q.optional ? " — no answer (optional)" : " — open, no answer given";
    } else {
      if (!vs.length) head += q.optional ? " — no answer (optional)" : " — open, no answer given";
      else if (q.type === "multi") for (const v of vs) lines.push("- " + v);
      else lines.push("→ " + vs[0]);
      if (note) lines.push("> note: " + note.replace(/\n/g, "\n> "));
    }
    L.push(head, ...lines, "");
  }
  if (CONFIG.outro) L.push("---", "", CONFIG.outro, "");
  return L.join("\n");
}

$("build").addEventListener("click", () => {
  $("outText").value = markdown();
  $("out").hidden = false;
  $("copy").hidden = false;
  $("dl").hidden = false;
  $("hint").textContent = "Generated — copy it back to the agent, or download the .md.";
  $("out").scrollIntoView({ behavior: "smooth", block: "start" });
});

$("copy").addEventListener("click", function () {
  const ta = $("outText"), btn = this;
  const flash = () => { btn.textContent = "Copied"; setTimeout(() => { btn.textContent = "Copy"; }, 1500); };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(ta.value).then(flash, () => ta.select());
  } else {
    ta.select();
    try { document.execCommand("copy"); flash(); } catch (e) { /* selection is the fallback */ }
  }
});

$("dl").addEventListener("click", () => {
  const slug = (CONFIG.title.toLowerCase().replace(/[^a-z0-9一-鿿]+/g, "-").replace(/^-+|-+$/g, "")
    || "questionnaire");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([$("outText").value], { type: "text/markdown;charset=utf-8" }));
  a.download = slug + "-answers-" + new Date().toISOString().slice(0, 10) + ".md";
  document.body.appendChild(a);
  a.click();
  a.remove();
});

restore();
refresh();
</script>
</body>
</html>
"""


def validate(cfg: dict) -> list[str]:
    errors = []
    if not isinstance(cfg.get("title"), str) or not cfg["title"].strip():
        errors.append("top-level 'title' (non-empty string) is required")
    questions = cfg.get("questions")
    if not isinstance(questions, list) or not questions:
        return errors + ["top-level 'questions' (non-empty array) is required"]
    seen: set[str] = set()
    for i, q in enumerate(questions):
        where = f"questions[{i}]"
        if not isinstance(q, dict):
            errors.append(f"{where}: must be an object")
            continue
        qid = q.get("id")
        if not isinstance(qid, str) or not qid.strip():
            errors.append(f"{where}: 'id' (non-empty string) is required")
            qid = None
        elif qid in seen:
            errors.append(f"{where}: duplicate id '{qid}'")
        else:
            seen.add(qid)
        if not isinstance(q.get("question"), str) or not q["question"].strip():
            errors.append(f"{where}: 'question' (non-empty string) is required")
        qtype = q.get("type", "single")
        if qtype not in ("single", "multi", "text"):
            errors.append(f"{where}: type must be single, multi, or text (got '{qtype}')")
        if qtype in ("single", "multi"):
            opts = q.get("options")
            if not isinstance(opts, list) or len(opts) < 2:
                errors.append(f"{where}: choice questions need at least 2 options")
            else:
                for j, o in enumerate(opts):
                    if isinstance(o, str):
                        continue
                    if not isinstance(o, dict) or not isinstance(o.get("value"), str):
                        errors.append(f"{where}.options[{j}]: must be a string or an object with 'value'")
        cond = q.get("showIf")
        if cond is not None:
            if not isinstance(cond, dict) or "q" not in cond or not ("is" in cond or "not" in cond):
                errors.append(f"{where}: showIf must be {{\"q\": <id>, \"is\"|\"not\": <option value>}}")
            elif cond["q"] not in seen or cond["q"] == qid:
                errors.append(f"{where}: showIf.q '{cond['q']}' must name an earlier question id")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("config", type=Path, help="questions JSON file")
    parser.add_argument("-o", "--output", type=Path, help="output HTML path (default: <config stem>.html)")
    args = parser.parse_args()

    try:
        cfg = json.loads(args.config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: cannot read {args.config}: {e}")

    errors = validate(cfg)
    if errors:
        sys.exit("invalid questionnaire config:\n  " + "\n  ".join(errors))

    payload = json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/")
    out = args.output or args.config.with_suffix(".html")
    out.write_text(TEMPLATE.replace("__CONFIG_JSON__", payload), encoding="utf-8")
    n = len(cfg["questions"])
    print(f"{out}: {n} question{'s' if n != 1 else ''}, "
          f"{sum(1 for q in cfg['questions'] if q.get('showIf'))} conditional")


if __name__ == "__main__":
    main()
