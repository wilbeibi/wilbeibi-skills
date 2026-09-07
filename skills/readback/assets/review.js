/* Readback review page: render, annotate, compose a follow-up, send it back.
   Loaded after window.RB_PAYLOAD / window.RB_LIVE and the vendored markdown-it. */
"use strict";
(function () {
const PAYLOAD = window.RB_PAYLOAD;
const LIVE = window.RB_LIVE;
const DOC = PAYLOAD.document;
const ANCHOR = PAYLOAD.anchorVersion;
const ENTRIES = DOC.entries || [];
const KEY = "readback::v" + ANCHOR + "::" + DOC.fingerprint;
const CONTEXT = 48;
const SEARCH_LIMIT = 2000;

const $ = function (id) { return document.getElementById(id); };
const HL_OK = typeof window.Highlight === "function" && !!(window.CSS && CSS.highlights);

/* ---- state ------------------------------------------------------------ */
let anns = [];                       // serializable annotation records
const RANGES = new Map();            // annotation id -> live Range
const UNRESOLVED = new Set();        // annotation ids whose anchor failed verification
const indexes = new Map();           // entry id -> canonical text index
const entryEls = new Map();          // entry id -> [data-entry] element
let activeId = null;
let editing = null;                  // {id} | {sel} | {scope:"document"}
let pendingSel = null;               // selection captured for the menu
let promptBuilt = null;              // last mechanically built text
let promptStale = false;
let sent = false;
let cancelled = false;
let submissionId = null;
let storageOK = true;
let matches = [];
let matchAt = -1;

/* ---- markdown --------------------------------------------------------- */
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
const md = window.markdownit({
  html: false, xhtmlOut: false, breaks: false, linkify: false, typographer: false,
});
md.validateLink = function (url) { return /^(https?:|mailto:)/i.test(String(url).trim()); };
md.renderer.rules.image = function (tokens, idx) {
  const t = tokens[idx];
  const label = t.content || t.attrGet("src") || "";
  return '<span class="imgnote">[image not shown: ' + esc(label) + "]</span>";
};
const renderToken = function (tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options, env, self);
};
const defLinkOpen = md.renderer.rules.link_open || renderToken;
md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const t = tokens[idx];
  if (t.attrGet("href")) {
    t.attrSet("target", "_blank");
    t.attrSet("rel", "noopener noreferrer nofollow ugc");
  } else {
    t.attrJoin("class", "dead");
    t.attrSet("title", "Link not followed: unsupported URL scheme");
  }
  return defLinkOpen(tokens, idx, options, env, self);
};

/* ---- rendering -------------------------------------------------------- */
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}
function caret() {
  const c = el("span", "caret", "▸");
  c.setAttribute("aria-hidden", "true");
  c.setAttribute("data-rb-ui", "");   // decoration: never part of quotable text
  return c;
}
function firstLine(text) {
  const lines = String(text).split("\n");
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    if (t) return t.length > 100 ? t.slice(0, 99) + "…" : t;
  }
  return "(empty)";
}
function clockOf(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return String(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function foldCode(root) {
  const pres = root.querySelectorAll("pre");
  for (let i = 0; i < pres.length; i++) {
    const pre = pres[i];
    if (pre.parentElement && pre.parentElement.classList.contains("code")) continue;
    const n = (pre.textContent.match(/\n/g) || []).length + 1;
    const d = el("details", "code");
    d.open = true;
    const s = el("summary", null, "Code · " + n + (n === 1 ? " line" : " lines"));
    s.setAttribute("data-rb-ui", "");
    pre.replaceWith(d);
    d.appendChild(s);
    d.appendChild(pre);
  }
}
/* Split rendered markdown into foldable sections at h1-h3 boundaries. */
function sectionize(rendered) {
  const out = document.createDocumentFragment();
  let body = el("div", "body");
  out.appendChild(body);
  while (rendered.firstChild) {
    const node = rendered.firstChild;
    const tag = node.nodeType === 1 ? node.tagName : "";
    if (tag === "H1" || tag === "H2" || tag === "H3") {
      const sec = el("details", "sec");
      sec.open = true;
      const sum = el("summary");
      sum.appendChild(caret());
      sum.appendChild(node);            // the heading itself, not a copy of its text
      sec.appendChild(sum);
      body = el("div", "body");
      sec.appendChild(body);
      out.appendChild(sec);
      continue;
    }
    body.appendChild(node);
  }
  return out;
}
function renderMarkdownInto(host, text) {
  const holder = el("div");
  holder.innerHTML = md.render(text || "");
  foldCode(holder);
  host.appendChild(sectionize(holder));
}
function renderEntry(entry, ordinal) {
  const kind = entry.kind || "message";
  if (DOC.kind === "markdown") {
    const art = el("article", "entry k-document");
    art.dataset.entry = entry.id;
    renderMarkdownInto(art, entry.text);
    return art;
  }
  const box = el("details", "entry k-" + kind.replace(/[^a-z0-9_-]/gi, ""));
  box.dataset.entry = entry.id;
  box.open = true;
  const sum = el("summary");
  sum.setAttribute("data-rb-ui", "");   // header text is chrome, never quotable content
  sum.appendChild(caret());
  sum.appendChild(el("span", "n", "#" + (entry.sourceIndex != null ? entry.sourceIndex : ordinal)));
  sum.appendChild(el("span", "who", entry.role || kind));
  if (kind !== "message") sum.appendChild(el("span", "kindtag", kind));
  if (entry.time) {
    const w = el("span", "when", clockOf(entry.time));
    w.title = String(entry.time);
    sum.appendChild(w);
  }
  sum.appendChild(el("span", "peek", firstLine(entry.text)));
  box.appendChild(sum);
  if (entry.tool) box.appendChild(el("div", "toolline", "tool: " + entry.tool));
  if (entry.input != null) {
    const d = el("details", "code");
    const s = el("summary", null, "Tool input");
    s.setAttribute("data-rb-ui", "");
    d.appendChild(s);
    const pre = el("pre");
    pre.appendChild(el("code", null,
      typeof entry.input === "string" ? entry.input : JSON.stringify(entry.input, null, 2)));
    d.appendChild(pre);
    box.appendChild(d);
  }
  const body = el("div");
  renderMarkdownInto(body, entry.text);
  box.appendChild(body);
  return box;
}

/* ---- canonical text index --------------------------------------------- */
const BLOCK_SEL = "p,li,h1,h2,h3,h4,h5,h6,pre,blockquote,td,th,dt,dd,figcaption,summary,div,section,article,details";
const STRUCT = { DIV: 1, SECTION: 1, ARTICLE: 1, DETAILS: 1, UL: 1, OL: 1, DL: 1, TABLE: 1,
  THEAD: 1, TBODY: 1, TFOOT: 1, TR: 1, BLOCKQUOTE: 1, FIGURE: 1, MAIN: 1 };
function isUI(node, root) {
  let e = node.parentElement;
  while (e) {
    if (e.hasAttribute && e.hasAttribute("data-rb-ui")) return true;
    if (e === root) return false;
    e = e.parentElement;
  }
  return false;
}
function buildIndex(root) {
  const segs = [], byNode = new Map();
  let text = "", lastBlock = null;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
  let node;
  while ((node = walker.nextNode())) {
    if (!node.data) continue;
    const parent = node.parentElement;
    if (!parent) continue;
    if (/^\s*$/.test(node.data) && STRUCT[parent.tagName] && !parent.closest("pre")) continue;
    if (isUI(node, root)) continue;
    const block = parent.closest(BLOCK_SEL);
    if (lastBlock !== null && block !== lastBlock) text += "\n";
    lastBlock = block;
    const seg = { node: node, start: text.length, end: text.length + node.data.length };
    text += node.data;
    segs.push(seg);
    byNode.set(node, seg);
  }
  const headings = [];
  const hs = root.querySelectorAll("h1,h2,h3,h4,h5,h6");
  for (let i = 0; i < hs.length; i++) {
    const h = hs[i];
    const w = document.createTreeWalker(h, NodeFilter.SHOW_TEXT, null);
    const first = w.nextNode();
    const seg = first && byNode.get(first);
    if (seg) headings.push({ offset: seg.start, text: h.textContent.trim(),
      level: Number(h.tagName[1]), el: h });
  }
  return { text: text, segs: segs, byNode: byNode, headings: headings, root: root };
}
function locate(idx, off, isEnd) {
  const segs = idx.segs;
  if (!segs.length) return null;
  let lo = 0, hi = segs.length - 1, hit = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1, s = segs[mid];
    if (off < s.start) hi = mid - 1;
    else if (off > s.end) lo = mid + 1;
    else { hit = mid; break; }
  }
  if (hit < 0) {                       // offset fell in a block separator
    const i = Math.max(0, Math.min(isEnd ? lo - 1 : lo, segs.length - 1));
    const s = segs[i];
    return { node: s.node, offset: isEnd ? s.node.data.length : 0 };
  }
  let s = segs[hit];
  if (!isEnd && off === s.end && segs[hit + 1] && segs[hit + 1].start <= off) s = segs[hit + 1];
  if (isEnd && off === s.start && hit > 0 && segs[hit - 1].end >= off) s = segs[hit - 1];
  return { node: s.node, offset: Math.max(0, Math.min(off - s.start, s.node.data.length)) };
}
function rangeFor(idx, start, end) {
  const a = locate(idx, start, false), b = locate(idx, end, true);
  if (!a || !b) return null;
  const r = document.createRange();
  try { r.setStart(a.node, a.offset); r.setEnd(b.node, b.offset); } catch (e) { return null; }
  return r;
}
function pointOffset(idx, node, offset, isEnd) {
  if (node.nodeType === 3) {
    const seg = idx.byNode.get(node);
    if (seg) return seg.start + Math.min(offset, node.data.length);
  }
  const probe = document.createRange();
  try { probe.setStart(node, offset); probe.collapse(true); } catch (e) { return null; }
  const segs = idx.segs;
  if (isEnd) {
    for (let i = segs.length - 1; i >= 0; i--) {
      const s = segs[i];
      if (probe.comparePoint(s.node, s.node.data.length) <= 0) return s.end;
    }
    return null;
  }
  for (let i = 0; i < segs.length; i++) {
    const s = segs[i];
    if (probe.comparePoint(s.node, 0) >= 0) return s.start;
  }
  return null;
}

/* ---- selection -------------------------------------------------------- */
function entryOf(node) {
  const e = node && (node.nodeType === 1 ? node : node.parentElement);
  return e ? e.closest("[data-entry]") : null;
}
function readSelection() {
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) return null;
  const r = sel.getRangeAt(0);
  const a = entryOf(r.startContainer), b = entryOf(r.endContainer);
  if (!a && !b) return null;
  if (!a || !b) return { error: "Select inside one message or section of the document." };
  if (a !== b) return { error: "That selection spans more than one message. Annotate each message separately." };
  if (isUI(r.startContainer, a) || isUI(r.endContainer, a)) {
    return { error: "That is the message header, not its text. Select inside the message body." };
  }
  const idx = indexes.get(a.dataset.entry);
  if (!idx) return null;
  let start = pointOffset(idx, r.startContainer, r.startOffset, false);
  let end = pointOffset(idx, r.endContainer, r.endOffset, true);
  if (start == null || end == null) return null;
  if (end < start) { const t = start; start = end; end = t; }
  while (start < end && /\s/.test(idx.text[start])) start++;
  while (end > start && /\s/.test(idx.text[end - 1])) end--;
  if (end <= start) return null;
  return { entryId: a.dataset.entry, start: start, end: end, quote: idx.text.slice(start, end) };
}
function labelFor(entryId, offset) {
  const entry = ENTRIES.find(function (e) { return e.id === entryId; });
  const idx = indexes.get(entryId);
  let section = "";
  if (idx) {
    for (let i = 0; i < idx.headings.length; i++) {
      if (idx.headings[i].offset <= offset) section = idx.headings[i].text;
    }
  }
  if (DOC.kind === "markdown") return section || DOC.title;
  const parts = [];
  parts.push("Message " + (entry && entry.sourceIndex != null ? entry.sourceIndex
    : (entry ? ENTRIES.indexOf(entry) + 1 : "?")));
  if (entry && entry.role) parts.push(entry.role);
  else if (entry && entry.kind) parts.push(entry.kind);
  if (entry && entry.kind && entry.kind !== "message") parts.push(entry.kind);
  if (section) parts.push(section);
  return parts.join(" · ");
}

/* ---- annotation store ------------------------------------------------- */
function orderKey(a) {
  if (a.scope === "document") return [0, 0, a.order];
  const i = ENTRIES.findIndex(function (e) { return e.id === a.entryId; });
  return [1, i < 0 ? ENTRIES.length : i, a.start, a.order];
}
function ordered() {
  return anns.slice().sort(function (x, y) {
    const a = orderKey(x), b = orderKey(y);
    for (let i = 0; i < Math.max(a.length, b.length); i++) {
      const d = (a[i] || 0) - (b[i] || 0);
      if (d) return d;
    }
    return 0;
  });
}
function nextOrder() {
  let n = 0;
  anns.forEach(function (a) { if (a.order > n) n = a.order; });
  return n + 1;
}
function anchor(a) {
  RANGES.delete(a.id);
  UNRESOLVED.delete(a.id);
  if (a.scope === "document") return;
  if (a.fingerprint !== DOC.fingerprint || a.anchorVersion !== ANCHOR) { UNRESOLVED.add(a.id); return; }
  const idx = indexes.get(a.entryId);
  if (!idx || idx.text.slice(a.start, a.end) !== a.quote) { UNRESOLVED.add(a.id); return; }
  const r = rangeFor(idx, a.start, a.end);
  if (!r || r.toString().replace(/\s+/g, " ").trim() === "") { UNRESOLVED.add(a.id); return; }
  RANGES.set(a.id, r);
}
function paint() {
  if (!HL_OK) return;
  const mark = new Highlight(), active = new Highlight();
  anns.forEach(function (a) {
    const r = RANGES.get(a.id);
    if (!r) return;
    if (a.id === activeId) active.add(r); else mark.add(r);
  });
  CSS.highlights.set("rb-mark", mark);
  CSS.highlights.set("rb-active", active);
}
function paintSearch() {
  if (!HL_OK) return;
  const all = new Highlight(), on = new Highlight();
  matches.forEach(function (m, i) {
    const idx = indexes.get(m.entryId);
    const r = idx && rangeFor(idx, m.start, m.end);
    if (!r) return;
    if (i === matchAt) on.add(r); else all.add(r);
  });
  CSS.highlights.set("rb-find", all);
  CSS.highlights.set("rb-find-on", on);
}

/* ---- persistence ------------------------------------------------------ */
let saveTimer = null;
function saveSoon() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(save, 300);
}
function save() {
  if (!storageOK) return;
  try {
    localStorage.setItem(KEY, JSON.stringify({
      v: 1, anns: anns, prompt: $("prompt").value, built: promptBuilt,
      stale: promptStale, sent: sent, submissionId: submissionId,
      savedAt: new Date().toISOString(),
    }));
    $("store-state").textContent = "Draft saved in this browser.";
  } catch (e) { storageFailed(e); }
}
function storageFailed(e) {
  storageOK = false;
  const box = $("store-warn");
  box.hidden = false;
  box.textContent = "This browser is not storing drafts (" + (e && e.name ? e.name : "unavailable") +
    "). Your annotations and prompt live only in this tab — closing it loses them. " +
    "Download the prompt as .md before you leave.";
  $("store-state").textContent = "";
}
function restore() {
  let raw = null;
  try { raw = localStorage.getItem(KEY); } catch (e) { storageFailed(e); return; }
  if (!raw) return;
  let data;
  try { data = JSON.parse(raw); } catch (e) { return; }
  if (!data || !Array.isArray(data.anns)) return;
  anns = data.anns.filter(function (a) { return a && a.id && typeof a.comment === "string"; });
  promptBuilt = typeof data.built === "string" ? data.built : null;
  promptStale = !!data.stale;
  submissionId = data.submissionId || null;
  if (typeof data.prompt === "string") $("prompt").value = data.prompt;
  if (data.sent) markSent(null, true);
}

/* ---- annotation UI ---------------------------------------------------- */
function excerpt(text, max) {
  const t = String(text).replace(/\s+/g, " ").trim();
  return t.length > max ? t.slice(0, max - 1) + "…" : t;
}
function renderAnnotations() {
  const list = $("ann-list");
  list.textContent = "";
  const items = ordered();
  $("ann-count").textContent = items.length ? String(items.length) : "";
  $("ann-empty").hidden = items.length > 0;
  const lost = items.filter(function (a) { return UNRESOLVED.has(a.id); }).length;
  const warn = $("anchor-warn");
  warn.hidden = lost === 0;
  if (lost) {
    warn.textContent = lost + (lost === 1 ? " annotation is" : " annotations are") +
      " no longer anchored to a passage in this document — the document may have changed since the review was saved. " +
      "The saved quotes are still included in the prompt.";
  }
  items.forEach(function (a) {
    const li = el("li");
    li.dataset.ann = a.id;
    if (a.id === activeId) li.classList.add("on");
    if (UNRESOLVED.has(a.id)) li.classList.add("unresolved");
    const head = el("div", "a-head");
    head.appendChild(el("span", "a-where", a.scope === "document" ? "Whole document" : a.where));
    const acts = el("div", "a-acts");
    if (a.scope !== "document") {
      const jump = el("button", "link", "jump");
      jump.type = "button";
      jump.onclick = function () { jumpTo(a); };
      acts.appendChild(jump);
    }
    const edit = el("button", "link", "edit");
    edit.type = "button";
    edit.onclick = function () { openEditor({ id: a.id }); };
    acts.appendChild(edit);
    const del = el("button", "link", "delete");
    del.type = "button";
    del.onclick = function () { removeAnnotation(a.id); };
    acts.appendChild(del);
    head.appendChild(acts);
    li.appendChild(head);
    if (a.scope !== "document") li.appendChild(el("div", "a-quote", excerpt(a.quote, 220)));
    if (a.comment.trim()) li.appendChild(el("p", "a-comment", a.comment));
    else li.appendChild(el("p", "a-none", "Marked for attention (no comment)"));
    if (UNRESOLVED.has(a.id)) {
      li.appendChild(el("p", "a-flag",
        "Anchor unresolved — this passage was not found in the document as loaded. " +
        "The saved quote is still used in the prompt."));
    }
    li.onclick = function (ev) {
      if (ev.target.closest("button")) return;
      activeId = a.id; paint(); renderAnnotations();
    };
    list.appendChild(li);
  });
}
function openEditor(target) {
  editing = target;
  const box = $("editor");
  const quote = $("edit-quote");
  let where = "", text = "", q = null;
  if (target.id) {
    const a = anns.find(function (x) { return x.id === target.id; });
    if (!a) return;
    where = a.scope === "document" ? "Note on whole document" : a.where;
    text = a.comment;
    q = a.scope === "document" ? null : a.quote;
  } else if (target.scope === "document") {
    where = "Note on whole document";
  } else {
    where = labelFor(target.sel.entryId, target.sel.start);
    q = target.sel.quote;
  }
  $("edit-where").textContent = where;
  quote.hidden = q == null;
  quote.textContent = q == null ? "" : excerpt(q, 400);
  $("edit-text").value = text;
  box.hidden = false;
  $("edit-text").focus();
}
function closeEditor() { editing = null; $("editor").hidden = true; }
function saveEditor() {
  const comment = $("edit-text").value;
  if (editing && editing.id) {
    const a = anns.find(function (x) { return x.id === editing.id; });
    if (a) a.comment = comment;
  } else if (editing && editing.scope === "document") {
    if (!comment.trim()) { closeEditor(); return; }
    anns.push({
      id: "a" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      order: nextOrder(), fingerprint: DOC.fingerprint, anchorVersion: ANCHOR,
      scope: "document", entryId: null, where: "Whole document",
      start: 0, end: 0, quote: "", before: "", after: "",
      comment: comment, createdAt: new Date().toISOString(),
    });
  } else if (editing && editing.sel) {
    addFromSelection(editing.sel, comment);
  }
  closeEditor();
  afterChange();
}
function addFromSelection(sel, comment) {
  const idx = indexes.get(sel.entryId);
  const a = {
    id: "a" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    order: nextOrder(), fingerprint: DOC.fingerprint, anchorVersion: ANCHOR,
    scope: "entry", entryId: sel.entryId, where: labelFor(sel.entryId, sel.start),
    start: sel.start, end: sel.end, quote: sel.quote,
    before: idx ? idx.text.slice(Math.max(0, sel.start - CONTEXT), sel.start) : "",
    after: idx ? idx.text.slice(sel.end, sel.end + CONTEXT) : "",
    comment: comment || "", createdAt: new Date().toISOString(),
  };
  anns.push(a);
  anchor(a);
  activeId = a.id;
  return a;
}
function removeAnnotation(id) {
  anns = anns.filter(function (a) { return a.id !== id; });
  RANGES.delete(id);
  UNRESOLVED.delete(id);
  if (activeId === id) activeId = null;
  if (editing && editing.id === id) closeEditor();
  afterChange();
}
function afterChange() {
  anns.forEach(function (a) { if (!RANGES.has(a.id) && !UNRESOLVED.has(a.id)) anchor(a); });
  renderAnnotations();
  paint();
  if (promptBuilt !== null) { promptStale = true; }
  refreshPromptState();
  saveSoon();
}
function openAncestors(node) {
  let e = node && (node.nodeType === 1 ? node : node.parentElement);
  while (e) {
    if (e.tagName === "DETAILS") e.open = true;
    e = e.parentElement;
  }
}
function jumpTo(a) {
  const entry = entryEls.get(a.entryId);
  if (!entry) return;
  openAncestors(entry);
  const r = RANGES.get(a.id);
  if (r) {
    openAncestors(r.startContainer);
    const target = r.startContainer.parentElement;
    if (target && target.scrollIntoView) target.scrollIntoView({ block: "center", behavior: "auto" });
  } else {
    entry.scrollIntoView({ block: "start", behavior: "auto" });
  }
  activeId = a.id;
  paint();
  renderAnnotations();
}

/* ---- selection menu --------------------------------------------------- */
function hideMenu() { $("sel-menu").hidden = true; $("sel-menu").className = ""; pendingSel = null; }
function showMenu() {
  const sel = readSelection();
  const menu = $("sel-menu");
  if (!sel) { hideMenu(); return; }
  const range = window.getSelection().getRangeAt(0);
  const rect = range.getBoundingClientRect();
  menu.textContent = "";
  if (sel.error) {
    menu.className = "warn";
    menu.textContent = sel.error;
    pendingSel = null;
  } else {
    menu.className = "";
    pendingSel = sel;
    const hl = el("button", null, "Highlight");
    hl.type = "button";
    hl.onclick = function () { addFromSelection(sel, ""); hideMenu(); afterChange(); };
    const cm = el("button", "primary", "Comment");
    cm.type = "button";
    cm.onclick = function () { hideMenu(); openEditor({ sel: sel }); };
    menu.appendChild(hl);
    menu.appendChild(cm);
  }
  menu.hidden = false;
  const w = menu.offsetWidth, h = menu.offsetHeight;
  let left = rect.left + rect.width / 2 - w / 2;
  left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
  let top = rect.top - h - 8;
  if (top < 8) top = rect.bottom + 8;
  top = Math.max(8, Math.min(top, window.innerHeight - h - 8));
  menu.style.left = left + "px";
  menu.style.top = top + "px";
}

/* ---- search ----------------------------------------------------------- */
function runSearch(q) {
  matches = [];
  matchAt = -1;
  if (q) {
    const needle = q.toLowerCase();
    for (let i = 0; i < ENTRIES.length && matches.length < SEARCH_LIMIT; i++) {
      const id = ENTRIES[i].id, idx = indexes.get(id);
      if (!idx) continue;
      const lower = idx.text.toLowerCase();
      const hay = lower.length === idx.text.length ? lower : idx.text;
      const pin = lower.length === idx.text.length ? needle : q;
      let p = 0;
      while (matches.length < SEARCH_LIMIT) {
        const at = hay.indexOf(pin, p);
        if (at < 0) break;
        matches.push({ entryId: id, start: at, end: at + pin.length });
        p = at + Math.max(1, pin.length);
      }
    }
  }
  const count = $("search-count");
  count.textContent = !q ? "" : (matches.length
    ? (matches.length >= SEARCH_LIMIT ? SEARCH_LIMIT + "+ matches" : "1/" + matches.length)
    : "no match");
  if (matches.length) { matchAt = 0; gotoMatch(0); } else paintSearch();
}
function gotoMatch(i) {
  if (!matches.length) return;
  matchAt = (i + matches.length) % matches.length;
  const m = matches[matchAt];
  const idx = indexes.get(m.entryId);
  const entry = entryEls.get(m.entryId);
  if (entry) openAncestors(entry);
  const r = idx && rangeFor(idx, m.start, m.end);
  if (r) {
    openAncestors(r.startContainer);
    const t = r.startContainer.parentElement;
    if (t && t.scrollIntoView) t.scrollIntoView({ block: "center", behavior: "auto" });
  } else if (entry) entry.scrollIntoView({ block: "start", behavior: "auto" });
  $("search-count").textContent = (matchAt + 1) + "/" + matches.length +
    (matches.length >= SEARCH_LIMIT ? "+" : "");
  paintSearch();
}

/* ---- prompt ----------------------------------------------------------- */
function sourceLine() {
  const s = DOC.source || {};
  const bits = [];
  if (s.name) bits.push(s.name);
  if (s.agent) bits.push(s.agent + " session" + (s.sessionId ? " " + s.sessionId : ""));
  bits.push("sha256 " + DOC.fingerprint);
  return bits.join(" · ");
}
function composePrompt() {
  const items = ordered();
  const out = [];
  out.push('Please address the following feedback on "' + DOC.title + '".');
  out.push("");
  out.push("Source: " + sourceLine());
  if (DOC.scope) out.push("Source scope: " + DOC.scope);
  out.push("");
  items.forEach(function (a, i) {
    let head = (i + 1) + ". " + (a.scope === "document" ? "Whole document" : a.where);
    if (UNRESOLVED.has(a.id)) head += " (anchor unresolved; quote saved from the original selection)";
    out.push(head);
    if (a.scope !== "document") {
      out.push("Original passage:");
      a.quote.split("\n").forEach(function (line) { out.push("> " + line); });
    }
    if (a.comment.trim()) {
      out.push("");
      out.push("My comment:");
      out.push(a.comment.replace(/\s+$/, ""));
    } else {
      out.push("Marked for attention (no comment)");
    }
    out.push("");
  });
  return out.join("\n").replace(/\n+$/, "\n");
}
function refreshPromptState() {
  const state = $("prompt-state");
  const edited = promptBuilt !== null && $("prompt").value !== promptBuilt;
  $("rebuild-prompt").hidden = promptBuilt === null;
  state.className = "muted";
  if (sent) { state.textContent = "Sent. This prompt is final."; return; }
  if (cancelled) { state.textContent = "Review cancelled."; return; }
  if (promptStale) {
    state.className = "stale";
    state.textContent = "Annotations changed after this prompt was built" +
      (edited ? ", and you have edited it by hand." : ".");
  } else if (edited) {
    state.textContent = "Edited by hand. Sent exactly as written.";
  } else if (promptBuilt !== null) {
    state.textContent = "Built from " + anns.length + " annotation" + (anns.length === 1 ? "" : "s") + ".";
  } else {
    state.textContent = anns.length
      ? anns.length + " annotation" + (anns.length === 1 ? "" : "s") + " ready to build into a prompt."
      : "No annotations yet. You can still write a follow-up by hand.";
  }
}
function doBuild(force) {
  const box = $("prompt");
  const edited = promptBuilt !== null && box.value !== promptBuilt;
  const dirty = promptBuilt === null ? box.value.trim() !== "" : edited;
  if (dirty && !force) {
    if (!window.confirm("Rebuilding replaces the prompt text you edited. Discard your edits?")) return;
  }
  box.value = composePrompt();
  promptBuilt = box.value;
  promptStale = false;
  refreshPromptState();
  save();
}

/* ---- delivery --------------------------------------------------------- */
function say(msg, cls) {
  const s = $("send-state");
  s.textContent = msg;
  s.className = cls || "";
}
function markSent(info, restored) {
  sent = true;
  $("prompt").readOnly = true;
  $("send").disabled = true;
  $("send").textContent = "Sent";
  $("build-prompt").disabled = true;
  $("rebuild-prompt").disabled = true;
  $("cancel-review").hidden = true;
  const where = (info && info.savedTo) || (LIVE && LIVE.promptFile) || "the review directory";
  say(restored ? "Already sent from this browser. The agent has the prompt." :
    "Sent. Saved to " + where + ".", "ok");
  refreshPromptState();
}
function newSubmissionId() {
  return "s" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}
async function postJSON(path, body) {
  const res = await fetch(path, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify(body), cache: "no-store",
  });
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  return { status: res.status, data: data };
}
async function send() {
  if (sent || cancelled) return;
  const text = $("prompt").value;
  if (!text.trim()) { say("Nothing to send — the prompt is empty.", "err"); return; }
  if (!submissionId) submissionId = newSubmissionId();
  const btn = $("send");
  btn.disabled = true;
  say("Sending…");
  save();
  try {
    const r = await postJSON("submit", {
      submission_id: submissionId, prompt: text, annotation_count: anns.length,
    });
    if (r.status === 200 && r.data && r.data.status === "accepted") { markSent(r.data); save(); return; }
    if (r.status === 409) {
      say((r.data && r.data.error) || "The review already has a result; this text was not saved.", "err");
      btn.disabled = true;
      return;
    }
    say((r.data && r.data.error) || ("The review command rejected the submission (HTTP " + r.status +
      "). Your text is unchanged."), "err");
    btn.disabled = false;
  } catch (e) {
    const known = await checkStatus();
    if (known === "accepted") { markSent(null); save(); return; }
    if (known === null) {
      say("Could not reach the review command, and it is no longer answering. If it saved your " +
        "prompt it is in " + ((LIVE && LIVE.promptFile) || "the review directory") +
        "; otherwise nothing was sent. Copy or download the prompt so it is not lost, then press " +
        "Confirm & send again if the command is still running.", "err");
    } else {
      say("Network error while sending. Nothing was recorded. Press Confirm & send to retry.", "err");
    }
    btn.disabled = false;
  }
}
async function checkStatus() {
  try {
    const res = await fetch("status", { cache: "no-store" });
    const data = await res.json();
    if (data && data.status === "accepted" && (!submissionId || data.submissionId === submissionId)) {
      return "accepted";
    }
    return data && data.status ? data.status : "open";
  } catch (e) { return null; }
}
async function cancelReview() {
  if (sent || cancelled) return;
  if (!window.confirm("Cancel this review? The agent gets no feedback, and this page can no longer send.")) return;
  try {
    await postJSON("cancel", { reason: "user cancelled" });
    cancelled = true;
    $("send").disabled = true;
    $("cancel-review").hidden = true;
    say("Review cancelled. No feedback was sent. Your notes stay in this page.", "err");
    refreshPromptState();
  } catch (e) {
    say("Could not reach the review command to cancel it.", "err");
  }
}

/* ---- copy / download -------------------------------------------------- */
function download(name, text, mime) {
  const blob = new Blob([text], { type: (mime || "text/plain") + ";charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
}
async function copyText(text, box, label) {
  try {
    await navigator.clipboard.writeText(text);
    say(label + " copied to the clipboard.", "ok");
  } catch (e) {
    if (box) { box.focus(); box.select(); }
    say("Clipboard blocked here. The text is selected — copy it with the keyboard.", "err");
  }
}

/* ---- navigation ------------------------------------------------------- */
function buildNav() {
  const list = $("nav-list");
  list.textContent = "";
  if (DOC.kind === "markdown") {
    const idx = indexes.get(ENTRIES[0] && ENTRIES[0].id);
    if (!idx || !idx.headings.length) { $("nav").hidden = true; document.body.classList.add("nav-off"); return; }
    idx.headings.forEach(function (h, i) {
      if (h.level > 3) return;
      const li = el("li");
      const a = el("a", "h" + Math.min(h.level, 3), h.text || "(untitled)");
      a.href = "#";
      a.onclick = function (ev) {
        ev.preventDefault();
        openAncestors(h.el);
        h.el.scrollIntoView({ block: "start" });
      };
      li.appendChild(a);
      list.appendChild(li);
    });
    return;
  }
  ENTRIES.forEach(function (entry, i) {
    const li = el("li");
    const a = el("a");
    a.href = "#";
    a.appendChild(el("span", "n", "#" + (entry.sourceIndex != null ? entry.sourceIndex : i + 1)));
    a.appendChild(el("span", "who", (entry.role || entry.kind || "entry") + " "));
    a.appendChild(document.createTextNode(firstLine(entry.text)));
    a.title = firstLine(entry.text);
    a.onclick = function (ev) {
      ev.preventDefault();
      const box = entryEls.get(entry.id);
      if (box) { openAncestors(box); box.scrollIntoView({ block: "start" }); }
    };
    li.appendChild(a);
    list.appendChild(li);
  });
}

/* ---- boot ------------------------------------------------------------- */
function boot() {
  document.title = DOC.title;
  $("doc-title").textContent = DOC.title;
  const s = DOC.source || {};
  const note = [];
  if (s.name) note.push(s.name);
  if (s.agent) note.push(s.agent + (s.sessionId ? " · " + s.sessionId : ""));
  note.push(ENTRIES.length + (DOC.kind === "markdown" ? " document" : " entr" + (ENTRIES.length === 1 ? "y" : "ies")));
  if (s.updatedAt) note.push(s.updatedAt);
  $("source-note").textContent = note.join(" · ");
  $("scope-note").textContent = DOC.scope || "";

  const warnings = (DOC.warnings || []).slice();
  if (!HL_OK) {
    warnings.push("This browser cannot paint highlights in the text (CSS Custom Highlight API " +
      "missing). Quotes, comments and the prompt all work; annotated passages just are not tinted.");
  }
  if (warnings.length) {
    const box = $("warnings");
    box.hidden = false;
    box.appendChild(el("strong", null, "Note on this source"));
    const ul = el("ul");
    warnings.forEach(function (w) { ul.appendChild(el("li", null, w)); });
    box.appendChild(ul);
  }

  const host = $("doc-body");
  if (!ENTRIES.length) {
    host.appendChild(el("p", "empty",
      "This document is empty. You can still leave a note on the whole document."));
  }
  ENTRIES.forEach(function (entry, i) {
    const node = renderEntry(entry, i + 1);
    entryEls.set(entry.id, node);
    host.appendChild(node);
    indexes.set(entry.id, buildIndex(node));
  });

  buildNav();
  restore();
  anns.forEach(anchor);
  renderAnnotations();
  paint();
  refreshPromptState();

  if (LIVE) {
    $("send").hidden = false;
    $("cancel-review").hidden = false;
    if (!sent) say("The review command is waiting. Nothing reaches the agent until you press Confirm & send.");
  } else {
    say("Offline copy: no agent is listening. Use Copy or Download .md to hand the prompt back.");
  }

  /* events */
  document.addEventListener("mouseup", function () { setTimeout(showMenu, 0); });
  document.addEventListener("keyup", function (ev) {
    if (ev.shiftKey || ev.key === "Shift") setTimeout(showMenu, 0);
  });
  document.addEventListener("mousedown", function (ev) {
    if (!ev.target.closest("#sel-menu")) hideMenu();
  });
  document.addEventListener("scroll", hideMenu, true);
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") { hideMenu(); if (editing) closeEditor(); return; }
    const inField = /^(INPUT|TEXTAREA|SELECT)$/.test(ev.target.tagName) || ev.target.isContentEditable;
    if (ev.key === "/" && !inField && !ev.metaKey && !ev.ctrlKey) {
      ev.preventDefault();
      $("search-input").focus();
      $("search-input").select();
    }
  });

  $("search-input").addEventListener("input", function (ev) { runSearch(ev.target.value.trim()); });
  $("search-input").addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter") return;
    ev.preventDefault();
    if (matches.length) gotoMatch(matchAt + (ev.shiftKey ? -1 : 1));
    else runSearch(ev.target.value.trim());
  });
  $("search-next").onclick = function () { gotoMatch(matchAt + 1); };
  $("search-prev").onclick = function () { gotoMatch(matchAt - 1); };
  $("expand-all").onclick = function () { setFolds(true); };
  $("collapse-all").onclick = function () { setFolds(false); };
  $("toggle-nav").onclick = function () { toggleCol("nav-off", "toggle-nav"); };
  $("toggle-panel").onclick = function () { toggleCol("panel-off", "toggle-panel"); };
  $("doc-note").onclick = function () { openEditor({ scope: "document" }); };
  $("edit-save").onclick = saveEditor;
  $("edit-cancel").onclick = closeEditor;
  $("build-prompt").onclick = function () { doBuild(false); };
  $("rebuild-prompt").onclick = function () { doBuild(false); };
  $("prompt").addEventListener("input", function () { refreshPromptState(); saveSoon(); });
  $("send").onclick = send;
  $("cancel-review").onclick = cancelReview;
  $("copy").onclick = function () { copyText($("prompt").value, $("prompt"), "Prompt"); };
  $("download").onclick = function () {
    download("followup.md", $("prompt").value, "text/markdown");
    say("Prompt downloaded as followup.md.", "");
  };
  $("copy-source").onclick = function () { copyText(PAYLOAD.raw, null, "Original source"); };
  $("download-source").onclick = function () {
    download(PAYLOAD.rawName || "source.txt", PAYLOAD.raw,
      DOC.kind === "markdown" ? "text/markdown" : "application/json");
  };
  window.addEventListener("beforeprint", function () {
    if (!closedForPrint) {
      closedForPrint = [].slice.call($("doc-body").querySelectorAll("details")).filter(function (d) { return !d.open; });
    }
    setFolds(true, true);
  });
  window.addEventListener("afterprint", function () {
    if (!closedForPrint) return;
    closedForPrint.forEach(function (d) { d.open = false; });
    closedForPrint = null;
  });
  window.addEventListener("beforeunload", function (ev) {
    if (sent || cancelled || !LIVE) return;
    if (!anns.length && !$("prompt").value.trim()) return;
    ev.preventDefault();
    ev.returnValue = "";
  });
  measureTop();
  window.addEventListener("resize", measureTop);
  if (window.ResizeObserver) new ResizeObserver(measureTop).observe(document.querySelector(".top"));
  document.body.classList.remove("loading");
}
function measureTop() {
  const bar = document.querySelector(".top");
  if (bar) document.documentElement.style.setProperty("--top", bar.offsetHeight + "px");
}
let closedForPrint = null;    // folds the reader had closed, restored after printing
function setFolds(open, printing) {
  const all = $("doc-body").querySelectorAll("details");
  for (let i = 0; i < all.length; i++) all[i].open = open;
  if (!printing) { closedForPrint = null; hideMenu(); }
}
function toggleCol(cls, btn) {
  const off = document.body.classList.toggle(cls);
  $(btn).setAttribute("aria-expanded", off ? "false" : "true");
}

boot();
})();
