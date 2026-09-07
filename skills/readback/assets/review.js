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
let pendingSel = null;               // selection captured for the menu
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
/* YAML frontmatter is metadata, not prose: markdown-it would render the closing
   `---` as a setext h2 swallowing the whole block. Peel it off and show it as-is. */
function splitFrontmatter(text) {
  const m = /^---[ \t]*\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/.exec(text || "");
  if (!m) return { meta: null, body: text || "" };
  return { meta: m[1], body: (text || "").slice(m[0].length) };
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
    const split = splitFrontmatter(entry.text);
    if (split.meta) art.appendChild(el("pre", "plain frontmatter", split.meta));
    renderMarkdownInto(art, split.body);
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
      v: 2, anns: anns, sent: sent, submissionId: submissionId,
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
  submissionId = data.submissionId || null;
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
  document.body.classList.toggle("has-annotations", items.length > 0);
  const lost = items.filter(function (a) { return UNRESOLVED.has(a.id); }).length;
  const warn = $("anchor-warn");
  warn.hidden = lost === 0;
  if (lost) {
    warn.textContent = lost + (lost === 1 ? " annotation is" : " annotations are") +
      " no longer anchored to a passage in this document — the document may have changed since the review was saved. " +
      "The saved quotes are still included in the prompt.";
  }
  items.forEach(function (a, i) {
    const li = el("li");
    li.dataset.ann = a.id;
    if (a.id === activeId) li.classList.add("on");
    if (UNRESOLVED.has(a.id)) li.classList.add("unresolved");
    const head = el("div", "a-head");
    const where = el("span", "a-where");
    where.appendChild(el("span", "a-number", String(i + 1) + "."));
    where.appendChild(document.createTextNode(a.scope === "document" ? "Whole document" : a.where));
    head.appendChild(where);
    const acts = el("div", "a-acts");
    if (a.scope !== "document") {
      const jump = el("button", "link", "jump");
      jump.type = "button";
      jump.onclick = function () { jumpTo(a); };
      acts.appendChild(jump);
    }
    const del = el("button", "link", "delete");
    del.type = "button";
    del.onclick = function () {
      if (a.comment.trim() && !window.confirm("Delete this note? The comment goes with it.")) return;
      removeAnnotation(a.id);
    };
    acts.appendChild(del);
    head.appendChild(acts);
    li.appendChild(head);
    if (a.scope !== "document") li.appendChild(el("div", "a-quote", excerpt(a.quote, 220)));
    const input = el("textarea");
    input.rows = 3;
    input.placeholder = "Add a comment (optional)";
    input.setAttribute("aria-label", "Comment for annotation " + (i + 1));
    input.value = a.comment;
    input.oninput = function () {
      a.comment = input.value;
      renderReadback();
      saveSoon();
      requestAnimationFrame(layoutMarginalia);
    };
    li.appendChild(input);
    if (UNRESOLVED.has(a.id)) {
      li.appendChild(el("p", "a-flag",
        "Anchor unresolved — this passage was not found in the document as loaded. " +
        "The saved quote is still used in the prompt."));
    }
    li.onclick = function (ev) {
      if (ev.target.closest("button,textarea")) return;
      activeId = a.id; paint(); renderAnnotations();
    };
    list.appendChild(li);
  });
  requestAnimationFrame(layoutMarginalia);
}
function focusComment(id) {
  requestAnimationFrame(function () {
    const card = document.querySelector('[data-ann="' + id + '"]');
    const input = card && card.querySelector("textarea");
    if (input) input.focus();
  });
}
function addDocumentNote() {
  const a = {
    id: "a" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    order: nextOrder(), fingerprint: DOC.fingerprint, anchorVersion: ANCHOR,
    scope: "document", entryId: null, where: "Whole document",
    start: 0, end: 0, quote: "", before: "", after: "",
    comment: "", createdAt: new Date().toISOString(),
  };
  anns.push(a);
  activeId = a.id;
  afterChange();
  focusComment(a.id);
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
  afterChange();
}
function afterChange() {
  anns.forEach(function (a) { if (!RANGES.has(a.id) && !UNRESOLVED.has(a.id)) anchor(a); });
  renderAnnotations();
  paint();
  renderReadback();
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

function narrowLayout() { return window.matchMedia("(max-width:1080px)").matches; }
function marginLeft(width) {
  const doc = $("doc-body").getBoundingClientRect();
  const nav = $("nav").getBoundingClientRect();
  const right = doc.right + 12;
  if (right + width <= window.innerWidth - 8) return right;
  const left = doc.left - width - 12;
  return left >= nav.right + 8 ? left : null;
}
function layoutMarginalia() {
  const cards = $("ann-list").children;
  if (narrowLayout()) {
    for (let i = 0; i < cards.length; i++) {
      cards[i].hidden = false;
      cards[i].style.left = "";
      cards[i].style.top = "";
    }
    return;
  }
  const floor = headerInset() + 10;
  let nextTop = floor;
  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    const a = anns.find(function (x) { return x.id === card.dataset.ann; });
    if (!a) continue;
    let top = floor;
    let visible = a.scope === "document";
    const r = RANGES.get(a.id);
    if (r) {
      const rects = r.getClientRects();
      const rect = rects.length ? rects[0] : r.getBoundingClientRect();
      visible = rect.bottom >= floor && rect.top <= window.innerHeight - 8;
      top = Math.max(floor, rect.top);
    } else if (a.scope !== "document") {
      visible = false;
    }
    const left = marginLeft(card.offsetWidth || 142);
    if (!visible || left == null) { card.hidden = true; continue; }
    card.hidden = false;
    card.style.left = left + "px";
    card.style.top = Math.max(top, nextTop) + "px";
    nextTop = Math.max(top, nextTop) + card.offsetHeight + 8;
  }
}

/* ---- selection menu --------------------------------------------------- */
function hideMenu() {
  const menu = $("sel-menu");
  menu.hidden = true;
  menu.className = "";
  menu.textContent = "";   // the buttons go with it, so no stale handler survives
  pendingSel = null;
}
/* Acting on a selection consumes it. Without this the mouseup that follows the
   click would re-read the same range and put the menu straight back. */
function consumeSelection() {
  const s = window.getSelection();
  if (s && s.removeAllRanges) s.removeAllRanges();
}
function headerInset() {
  const v = getComputedStyle(document.documentElement).getPropertyValue("--top");
  return parseFloat(v) || 0;
}
function selectionRect(fallback) {
  const s = window.getSelection();
  if (s && s.rangeCount) {
    const rects = s.getRangeAt(0).getClientRects();
    if (rects.length) return rects[rects.length - 1];
  }
  return fallback;
}
function placeMenu(menu, rect) {
  const w = menu.offsetWidth, h = menu.offsetHeight;
  const side = !narrowLayout() ? marginLeft(w) : null;
  let left = side;
  let besideSelection = side != null;
  if (left == null && menu.classList.contains("editor")) {
    const right = rect.right + 12;
    const before = rect.left - w - 12;
    if (right + w <= window.innerWidth - 8) { left = right; besideSelection = true; }
    else if (before >= 8) { left = before; besideSelection = true; }
  }
  if (left == null) {
    left = rect.left + rect.width / 2 - w / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
  }
  const floor = headerInset() + 8;
  const desiredTop = besideSelection ? rect.top : rect.bottom + 8;
  const top = Math.max(floor, Math.min(desiredTop, window.innerHeight - h - 8));
  menu.style.left = left + "px";
  menu.style.top = top + "px";
}
function openSelectionEditor(sel, rect) {
  const menu = $("sel-menu");
  pendingSel = sel;
  menu.className = "editor";
  menu.textContent = "";
  menu.appendChild(el("div", "sel-kicker", "Comment on this passage"));
  menu.appendChild(el("div", "sel-quote", "\u201c" + excerpt(sel.quote, 180) + "\u201d"));
  const input = el("textarea");
  input.rows = 3;
  input.placeholder = "What should change? (optional)";
  input.setAttribute("aria-label", "Comment on selected passage");
  menu.appendChild(input);
  const actions = el("div", "sel-actions");
  const cancel = el("button", null, "Cancel");
  cancel.type = "button";
  cancel.onclick = function () { consumeSelection(); hideMenu(); };
  const save = el("button", "primary", "Add comment");
  save.type = "button";
  save.onclick = function () {
    addFromSelection(sel, input.value);
    consumeSelection(); hideMenu(); afterChange();
  };
  actions.appendChild(cancel);
  actions.appendChild(save);
  menu.appendChild(actions);
  menu.hidden = false;
  requestAnimationFrame(function () {
    placeMenu(menu, selectionRect(rect));
    input.focus();
  });
}
function showMenu(fromKeyboard) {
  const sel = readSelection();
  const menu = $("sel-menu");
  if (!sel) { hideMenu(); return; }
  const range = window.getSelection().getRangeAt(0);
  const rects = range.getClientRects();
  /* the last line, not the union: a multi-line selection's bounding box is
     centred over text the reader is still looking at. */
  const rect = rects.length ? rects[rects.length - 1] : range.getBoundingClientRect();
  menu.textContent = "";
  let first = null;
  if (sel.error) {
    menu.className = "warn";
    menu.textContent = sel.error;
    pendingSel = null;
  } else {
    menu.className = "";
    pendingSel = sel;
    const highlight = el("button", null, "Highlight");
    highlight.type = "button";
    highlight.onclick = function () {
      const a = addFromSelection(sel, "");
      consumeSelection(); hideMenu(); afterChange(); focusComment(a.id);
    };
    const comment = el("button", "primary", "Comment");
    comment.type = "button";
    comment.onclick = function () { openSelectionEditor(sel, rect); };
    menu.appendChild(highlight);
    menu.appendChild(comment);
    first = highlight;
  }
  menu.hidden = false;
  placeMenu(menu, rect);
  /* a keyboard selection has no pointer to reach the menu with */
  if (fromKeyboard && first) first.focus();
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
  out.push('Task: Apply the feedback below to "' + DOC.title + '".');
  out.push("");
  out.push("Source: " + sourceLine());
  if (DOC.scope) out.push("Source scope: " + DOC.scope);
  out.push("");
  out.push("Rules: Target is an exact location anchor, not replacement text. Apply Request only and preserve unrelated behavior. If Request is empty, inspect and report; do not invent a change.");
  out.push("");
  items.forEach(function (a, i) {
    out.push((i + 1) + ". Location: " + (a.scope === "document" ? "Whole document" : a.where));
    if (UNRESOLVED.has(a.id)) out.push("Status: anchor unresolved");
    if (a.scope !== "document") {
      out.push("Target (exact; locating only):");
      out.push("<<<");
      out.push(a.quote);
      out.push(">>>");
    }
    out.push("Request: " + (a.comment.trim()
      ? a.comment.replace(/\s+$/, "")
      : "None provided; inspect and report whether action is needed."));
    out.push("");
  });
  return out.join("\n").replace(/\n+$/, "\n");
}
function promptText() { return anns.length ? composePrompt() : ""; }
function renderReadback() {
  const state = $("prompt-state");
  const preview = $("prompt-preview");
  preview.textContent = promptText();
  state.className = "muted";
  if (sent) { state.textContent = "Sent. This prompt is final."; return; }
  if (cancelled) { state.textContent = "Review cancelled."; return; }
  $("send").hidden = !LIVE || !anns.length;
  state.textContent = anns.length
    ? "A live read-back of " + anns.length + " annotation" + (anns.length === 1 ? "." : "s.")
    : "Mark a passage or add a document note; the follow-up is composed here as you work.";
}

/* ---- delivery --------------------------------------------------------- */
function say(msg, cls) {
  const s = $("send-state");
  s.textContent = msg;
  s.className = cls || "";
}
function markSent(info, restored) {
  sent = true;
  $("send").disabled = true;
  $("send").textContent = "Sent";
  $("cancel-review").hidden = true;
  const where = (info && info.savedTo) || (LIVE && LIVE.promptFile) || "the review directory";
  say(restored ? "Already sent from this browser. The agent has the prompt." :
    "Sent. Saved to " + where + ".", "ok");
  renderReadback();
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
  const text = promptText();
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
    $("send").hidden = true;
    $("cancel-review").hidden = true;
    say("Review cancelled. No feedback was sent. Your notes stay in this page.", "err");
    renderReadback();
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
    if (box && box.select) { box.focus(); box.select(); }
    say("Clipboard blocked here. Download the prompt instead.", "err");
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
  renderReadback();

  if (LIVE) {
    if (!sent) {
      $("cancel-review").hidden = false;
      say("The review command is waiting. Nothing reaches the agent until you press Confirm & send.");
    }
  } else {
    say("Offline copy: no agent is listening. Use Copy or Download .md to hand the prompt back.");
  }

  /* events */
  const inChrome = function (node) {
    return node instanceof Element && !!node.closest("#sel-menu,#marginalia,#nav,.top,.notice,.followup");
  };
  document.addEventListener("mouseup", function (ev) {
    if (inChrome(ev.target)) return;
    setTimeout(showMenu, 0);
  });
  document.addEventListener("keyup", function (ev) {
    if (inChrome(ev.target)) return;
    if (ev.shiftKey || ev.key === "Shift") setTimeout(function () { showMenu(true); }, 0);
  });
  document.addEventListener("mousedown", function (ev) {
    const t = ev.target;
    if (!(t instanceof Element) || !t.closest("#sel-menu")) hideMenu();
  });
  document.addEventListener("scroll", function () { hideMenu(); requestAnimationFrame(layoutMarginalia); }, true);
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") { hideMenu(); return; }
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
  $("doc-note").onclick = addDocumentNote;
  $("go-followup").onclick = function () { $("followup").scrollIntoView({ block: "start", behavior: "smooth" }); };
  $("send").onclick = send;
  $("cancel-review").onclick = cancelReview;
  $("copy").onclick = function () { copyText(promptText(), null, "Prompt"); };
  $("download").onclick = function () {
    download("followup.md", promptText(), "text/markdown");
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
    /* offline is where losing the draft is unrecoverable, so it is guarded too */
    if (sent || cancelled) return;
    if (!anns.length) return;
    ev.preventDefault();
    ev.returnValue = "";
  });
  measureTop();
  window.addEventListener("resize", function () { measureTop(); requestAnimationFrame(layoutMarginalia); });
  if (window.ResizeObserver) new ResizeObserver(measureTop).observe(document.querySelector(".top"));
  document.body.classList.remove("loading");
}
function measureTop() {
  const bar = document.querySelector(".top");
  if (bar) document.documentElement.style.setProperty("--top", bar.offsetHeight + "px");
  requestAnimationFrame(layoutMarginalia);
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
