#!/usr/bin/env python3
"""Hand-drawn figures as static SVG, and a browser check that they read at phone and desktop width.

    sketch.py check PAGE.html [--width 375 --width 1280] [--min-px 11] [--shots DIR]

As a library, put this directory on sys.path:

    from sketch import Pen, page
    p = Pen(seed=7)
    p.box(20, 20, 120, 50, fill="sky"); p.text(80, 50, "cache", maxw=110)
    Path("fig.html").write_text(page(p.svg(160, 90, label="One cache"), "Cache"))

The wobble comes from a seeded generator, so the same calls give the same bytes and the figure
needs no script. Colours are presentation attributes `var(--sk-<name>, <light value>)`: the SVG
renders in the light palette anywhere, and a page that includes TOKENS_CSS also gets the dark one.

`check` loads the page in headless Chromium, light and dark, at each width. It looks at every
top-level <svg> with a viewBox that is not aria-hidden, and fails on: a label wider than its
`maxw`; overlapping labels; text or drawing past the viewBox; a page that scrolls sideways; text
rendered below --min-px; text under WCAG AA contrast (4.5:1, or 3:1 from 24 px) against what is
painted beneath it; characters that no font in the label's font-family has, which the browser
silently draws in a system font. A label is read as drawn: the box around its glyphs' ink, not its
line box; each tspan in its own size and fill; translucent fills blended onto what lies beneath.
Text that paints no fill, like a halo under a label, is not a label. 375 px is the narrowest
common phone viewport; 11 px is the smallest text size in Apple's iOS guidelines and in
Material's type scale.
Exit 0 clean, 1 a check failed or no browser was found, 2 usage.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import html
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile

# name: (light, dark). Ink stays above 5.7:1 on every colour in both modes; muted ink-2 reaches
# 4.5:1 only on paper, wash and card. test_sketch.py holds both to WCAG AA.
TOKENS = {
    "paper": ("#fbf7ee", "#22201c"), "ink": ("#1d1b18", "#ece5d3"), "ink-2": ("#6e675b", "#a39b8c"),
    "wash": ("#f1ead8", "#2d2a24"), "card": ("#fffdf8", "#2b2823"), "lid": ("#e4ddcc", "#3a362f"),
    "sky": ("#cfe5f3", "#29404f"), "sky-2": ("#a9cfe8", "#36566b"), "lemon": ("#fbe28a", "#6a5517"),
    "ochre": ("#eec27f", "#6b4b1b"), "coral": ("#f5b4a3", "#6e3426"), "lavender": ("#d8ccf1", "#463a66"),
}
_LIGHT = " ".join(f"--sk-{k}: {v[0]};" for k, v in TOKENS.items())
_DARK = " ".join(f"--sk-{k}: {v[1]};" for k, v in TOKENS.items())
TOKENS_CSS = (f":root {{ {_LIGHT} }}\n"
              f'@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ {_DARK} }} }}\n'
              f':root[data-theme="dark"] {{ {_DARK} }}\n')
FONT = "'Patrick Hand', Virgil, 'Comic Sans MS', 'Chalkboard SE', sans-serif"
FONT_LINK = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap">'
BROWSERS = (
    "chromium", "chromium-browser", "google-chrome", "google-chrome-stable",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)
FRAME_H = 3000     # each width's frame is this tall, so a figure lays out without scrolling
KINDS = ("empty", "sideways", "clipped", "outside", "wide", "overlap", "tiny", "contrast", "font")


class Fail(Exception):
    """The browser pass could not run: exit 1."""


def n(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def paint(name: str) -> str:
    """A palette colour as var(--sk-<name>, <light value>)."""
    if name not in TOKENS:
        raise ValueError(f"unknown colour {name!r}; use one of: {', '.join(TOKENS)}")
    return f"var(--sk-{name},{TOKENS[name][0]})"


def spline(pts, closed=False) -> str:
    """Catmull-Rom through pts, as cubic Béziers."""
    if len(pts) == 2:
        (ax, ay), (bx, by) = pts
        return f"M{n(ax)} {n(ay)}L{n(bx)} {n(by)}"
    P = [pts[-1], *pts, pts[0], pts[1]] if closed else [pts[0], *pts, pts[-1]]
    d = f"M{n(P[1][0])} {n(P[1][1])}"
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(p2[0])} {n(p2[1])}"
    return d + ("Z" if closed else "")


class Pen:
    """Marks in painting order: later calls draw on top. Units are viewBox units, which are
    CSS px when the figure shows at full size. Colours are TOKENS names."""

    def __init__(self, seed: int = 1):
        self.rnd = random.Random(seed)
        self.marks: list[str] = []

    def _j(self, a: float) -> float:
        return self.rnd.uniform(-a, a)

    def _ink(self, d: str, weight=2.1, dash=None, color="ink") -> None:
        dash = f' stroke-dasharray="{dash}"' if dash else ""
        self.marks.append(f'<path d="{d}" fill="none" stroke="{paint(color)}" stroke-width="{n(weight)}"{dash}/>')

    def _stroke(self, p0, p1, amp=0.7, seg=30, over=1.6) -> str:
        """One pen stroke: a slight bow, a small tremor, and ends that run past the corner."""
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        ux, uy, nx, ny = dx / L, dy / L, -dy / L, dx / L
        k = max(1, round(L / seg))
        bow = self._j(amp) * min(1.0, L / 40)
        pts = [(x0 - ux * over + self._j(.4), y0 - uy * over + self._j(.4))]
        for i in range(1, k):
            t = i / k
            o = bow * 1.8 * math.sin(math.pi * t) + self._j(amp * .35)
            pts.append((x0 + dx * t + nx * o, y0 + dy * t + ny * o))
        pts.append((x1 + ux * over + self._j(.4), y1 + uy * over + self._j(.4)))
        return spline(pts)

    def _shaky(self, pts, a):
        return [(x + self._j(a), y + self._j(a)) for x, y in pts]

    def line(self, x0, y0, x1, y1, weight=2.1, dash=None, color="ink") -> None:
        self._ink(self._stroke((x0, y0), (x1, y1), over=0 if dash else 1.6), weight, dash, color)

    def poly(self, pts, fill: str) -> None:
        """A flat wash with no outline, for a band or a region."""
        d = "M" + "L".join(f"{n(x + self._j(.6))} {n(y + self._j(.6))}" for x, y in pts) + "Z"
        self.marks.append(f'<path d="{d}" fill="{paint(fill)}"/>')

    def box(self, x, y, w, h, fill=None, r=7.0, dash=None, weight=2.1) -> None:
        """Rounded box drawn as one loop that overshoots its start, over a flat fill.
        Small boxes wobble less."""
        r, amp = min(r, w / 2, h / 2), min(0.9, min(w, h) / 50)
        base = []

        def arc(cx, cy, a0):
            base.extend((cx + r * math.cos(a0 + math.pi / 6 * i), cy + r * math.sin(a0 + math.pi / 6 * i)) for i in range(4))

        def edge(p0, p1):
            k = max(1, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) // 12))
            base.extend((p0[0] + (p1[0] - p0[0]) * i / k, p0[1] + (p1[1] - p0[1]) * i / k) for i in range(1, k))

        arc(x + r, y + r, math.pi); edge((x + r, y), (x + w - r, y))
        arc(x + w - r, y + r, 1.5 * math.pi); edge((x + w, y + r), (x + w, y + h - r))
        arc(x + w - r, y + h - r, 0); edge((x + w - r, y + h), (x + r, y + h))
        arc(x + r, y + h - r, .5 * math.pi); edge((x, y + h - r), (x, y + r))
        m = len(base)
        extra = min(5, max(3, m // 10))
        ph = [self.rnd.uniform(0, 2 * math.pi) for _ in range(4)]
        drift = self.rnd.choice([-1, 1]) * 1.3
        loop = []
        for i in range(m + extra):
            t = i / m
            ox = amp * math.sin(4 * math.pi * t + ph[0]) + .5 * amp * math.sin(10 * math.pi * t + ph[1])
            oy = amp * math.sin(6 * math.pi * t + ph[2]) + .5 * amp * math.sin(8 * math.pi * t + ph[3])
            past = drift * (i - m) / extra if i > m else 0.0
            loop.append((base[i % m][0] + ox + past, base[i % m][1] + oy + past))
        if fill:
            self.marks.append(f'<path d="{spline(self._shaky(base, .5), closed=True)}" fill="{paint(fill)}"/>')
        self._ink(spline(loop), weight, dash)

    def arrow(self, x0, y0, x1, y1, bend=0.0, weight=2.1, dash=None, color="ink") -> None:
        """bend bows the middle that many units off the straight line, to the left of travel
        (up, for an arrow pointing right); one big curved arrow is a retry or feedback loop."""
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        cx, cy = (x0 + x1) / 2 + dy / L * bend * 2, (y0 + y1) / 2 - dx / L * bend * 2
        k = max(2, round(L / 30))
        pts = []
        for i in range(k + 1):
            t = i / k
            x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1
            y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1
            pts.append((x, y) if i in (0, k) else (x + self._j(.35), y + self._j(.35)))
        self._ink(spline(pts), weight, dash, color)
        tx, ty = x1 - cx, y1 - cy
        T = math.hypot(tx, ty) or 1.0
        bx, by = -tx / T * 9, -ty / T * 9
        head = "".join(self._stroke((x1 + bx * math.cos(a) - by * math.sin(a), y1 + bx * math.sin(a) + by * math.cos(a)),
                                    (x1, y1), amp=.2, over=0) for a in (-.45, .45))
        self._ink(head, weight, None, color)

    def text(self, x, y, s: str, size=14.0, anchor="middle", color="ink", maxw=0.0) -> None:
        """y is the baseline: centre a label in a box at the box's middle + size * 0.35.
        maxw is the room the label has; `check` fails a label that renders wider."""
        room = f' data-maxw="{n(maxw)}"' if maxw else ""
        self.marks.append(f'<text x="{n(x)}" y="{n(y)}" font-size="{n(size)}" text-anchor="{anchor}" '
                          f'fill="{paint(color)}"{room}>{html.escape(s, quote=False)}</text>')

    def dots(self, x, y) -> None:
        """Three dots: more of the same."""
        self.marks.extend(f'<circle cx="{n(x + dx + self._j(.4))}" cy="{n(y + self._j(.4))}" r="1.7" '
                          f'fill="{paint("ink-2")}"/>' for dx in (-7, 0, 7))

    def memory(self, x, y, w, h, fill="lemon") -> None:
        """A memory module: a box with contact pins along its lower edge (they hang 6 below it)."""
        pins = "".join(self._stroke((px, y + h + 1), (px, y + h + 6), amp=.15, over=0)
                       for px in (x + 11 + 8 * i for i in range(int((w - 22) // 8) + 1)))
        self._ink(pins, weight=1.5)
        self.box(x, y, w, h, fill=fill, r=6)

    def cylinder(self, x, y, w, h, fill="card", ry=7.0) -> None:
        """Storage: the lid takes the top 2 * ry, so put labels below y + 2 * ry."""
        cx, rx, yt, yb = x + w / 2, w / 2, y + ry, y + h - ry

        def arc(yc, a0, a1, k=14):
            return [(cx + rx * math.cos(a0 + (a1 - a0) * i / k), yc + ry * math.sin(a0 + (a1 - a0) * i / k))
                    for i in range(k + 1)]

        lid = arc(yt, 0, 2 * math.pi, 24)[:-1]
        body = spline(self._shaky(arc(yb, math.pi, 0) + arc(yt, 0, math.pi), .4), closed=True)
        self.marks.append(f'<path d="{body}" fill="{paint(fill)}"/>')
        self.marks.append(f'<path d="{spline(self._shaky(lid, .3), closed=True)}" fill="{paint("lid")}"/>')
        self._ink(spline(self._shaky(lid, .5), closed=True))
        self._ink(self._stroke((cx - rx, yt), (cx - rx, yb), amp=.4, over=0)
                  + self._stroke((cx + rx, yt), (cx + rx, yb), amp=.4, over=0))
        self._ink(spline(self._shaky(arc(yb, math.pi, 0), .5)))

    def svg(self, w, h, label: str, paper=True, font=FONT) -> str:
        """The figure as one self-contained <svg> with no <style>, <script> or <foreignObject>,
        so it can be pasted into any page. It shows at w px wide and shrinks to fit narrower
        columns. label is the alt text: say what the figure shows."""
        bg = f'<rect width="{n(w)}" height="{n(h)}" rx="12" fill="{paint("paper")}"/>' if paper else ""
        family = html.escape(font.replace('"', "'"), quote=False)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(w)} {n(h)}" width="{n(w)}" height="{n(h)}" '
                f'role="img" aria-label="{html.escape(label)}" font-family="{family}" '
                f'stroke-linecap="round" stroke-linejoin="round" style="display:block;max-width:100%;height:auto;margin:0 auto">'
                f'{bg}{"".join(self.marks)}</svg>')


def page(svg: str, title: str, caption: str = "", lang: str = "en", head: str = FONT_LINK) -> str:
    """A standalone page around one figure, with the dark palette: for previewing and for `check`.
    head loads the fonts: pass the stylesheet link for every web font named in Pen.svg(font=...)."""
    width = re.match(r'<svg[^>]*?\swidth="([\d.]+)"', svg)
    font = re.match(r'<svg[^>]*?\sfont-family="([^"]*)"', svg)
    cap = f"\n<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
{head}
<style>
{TOKENS_CSS}body {{ margin: 0; padding: 24px 16px; background: var(--sk-paper); color: var(--sk-ink); }}
figure {{ margin: 0 auto;{f" max-width: {width.group(1)}px;" if width else ""} }}
figcaption {{ margin-top: 12px; font: 18px/1.4 {html.unescape(font.group(1)) if font else FONT}; }}
</style>
</head>
<body>
<figure>
{svg}{cap}
</figure>
</body>
</html>
"""


# ── check ──────────────────────────────────────────────────────────────────

CHECK_JS = r"""
const MIN_PX = @MIN_PX@;
const GENERIC = new Set(['serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui', 'math', 'emoji',
  'fangsong', 'ui-serif', 'ui-sans-serif', 'ui-monospace', 'ui-rounded']);
const UNDRAWN = 'defs, marker, clipPath, mask, pattern, symbol';
const rgb = c => (c.match(/[\d.]+/g) || []).map(Number);
const lum = c => c.slice(0, 3).map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
  .reduce((s, v, i) => s + v * [.2126, .7152, .0722][i], 0);
const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + .05) / (y + .05); };
const over = (c, a, under) => c.slice(0, 3).map((v, i) => v * a + under[i] * (1 - a));
const clip = s => { s = s.trim().replace(/\s+/g, ' '); return '"' + (s.length > 32 ? s.slice(0, 31) + '…' : s) + '"'; };
const families = s => (s.match(/"[^"]*"|'[^']*'|[^,]+/g) || []).map(f => f.trim().replace(/^["']|["']$/g, ''))
  .filter(f => f && !GENERIC.has(f.toLowerCase()));
// labels overlap when their ink does, by more than a pixel each way
const hit = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1
  && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1;

// how much of a paint shows: its alpha, times fill-opacity and the opacity of the element and its ancestors
function shows(win, el, c, fillOpacity) {
  let a = c === 'none' ? 0 : (/^rgb/.test(c) ? rgb(c)[3] ?? 1 : 1) * fillOpacity;
  for (; el && a > 0; el = el.parentElement) a *= +win.getComputedStyle(el).opacity;
  return a;
}

// the colour beneath a point, with translucent fills blended onto the first opaque one;
// null when nothing beneath is opaque or a gradient or pattern is in the way
function beneath(win, x, y) {
  win.scrollTo(0, y - win.innerHeight / 2);   // elementsFromPoint sees only what is in view
  const els = win.document.elementsFromPoint(x, y - win.scrollY), layers = [];
  win.scrollTo(0, 0);
  for (const el of els) {
    if (el instanceof win.SVGTextContentElement) continue;
    const svg = el instanceof win.SVGElement, cs = win.getComputedStyle(el);
    if (svg && !(el instanceof win.SVGGeometryElement)) continue;
    const c = svg ? cs.fill : cs.backgroundColor, a = shows(win, el, c, svg ? +cs.fillOpacity : 1);
    if (a <= 0) continue;
    if (!/^rgb/.test(c)) return null;
    layers.push([rgb(c), a]);
    if (a > .995) return layers.reduceRight((under, [c, a]) => over(c, a, under), [0, 0, 0]);
  }
  return null;
}

// one canvas per document, to measure glyphs and compare fonts
const pads = new WeakMap();
function pad(doc) {
  let g = pads.get(doc);
  if (!g) {
    const c = doc.createElement('canvas'); c.width = c.height = 48;
    g = c.getContext('2d', {willReadFrequently: true}); pads.set(doc, g);
  }
  return g;
}

// a font has a character when its glyph differs from the one two different generic fonts draw
function has(doc, fam, ch) {
  const g = pad(doc);
  const draw = font => { g.clearRect(0, 0, 48, 48); g.font = font; g.fillText(ch, 6, 34); return g.getImageData(0, 0, 48, 48).data; };
  return ['monospace', 'serif'].some(gen => { const a = draw(`30px "${fam}", ${gen}`), b = draw(`30px ${gen}`); return a.some((v, i) => v !== b[i]); });
}

// a label's runs: each text node with the size and fill it is drawn in, and a box around its ink;
// none when it paints no fill, like a halo under a label
function runs(win, t, k) {
  const doc = win.document, g = pad(doc), out = [], walk = doc.createTreeWalker(t, win.NodeFilter.SHOW_TEXT);
  for (let node; (node = walk.nextNode());) {
    const el = node.parentElement, s = node.data.trim();
    if (!s || !(el instanceof win.SVGTextContentElement)) continue;
    const cs = win.getComputedStyle(el), a = shows(win, el, cs.fill, +cs.fillOpacity), range = doc.createRange();
    range.selectNodeContents(node);
    const r = range.getBoundingClientRect(), px = parseFloat(cs.fontSize) * k;
    if (a <= 0 || !r.width) continue;
    // the line box is the font's ascent and descent at the rendered size; the glyphs fill only part of it
    g.font = `${cs.fontStyle} ${cs.fontWeight} ${px}px ${cs.fontFamily}`;
    const m = g.measureText(s);
    out.push({s, cs, a, px, left: r.left, right: r.right, top: r.top + (m.fontBoundingBoxAscent - m.actualBoundingBoxAscent || 0),
      bottom: r.bottom - (m.fontBoundingBoxDescent - m.actualBoundingBoxDescent || 0)});
  }
  return out;
}

function inspect(win, w) {
  const doc = win.document, de = doc.documentElement, issues = [], tiny = [], fonts = new Map();
  const add = (kind, detail) => issues.push({kind, detail});
  win.scrollTo(0, 0);
  const out = {width: w, height: Math.ceil(de.getBoundingClientRect().height), labels: 0, issues,
    dark: win.matchMedia('(prefers-color-scheme: dark)').matches, colors: [win.getComputedStyle(doc.body).backgroundColor]};
  if (de.scrollWidth > de.clientWidth + 1) add('sideways', `the page is ${de.scrollWidth}px wide, so it scrolls sideways`);
  const svgs = [...doc.querySelectorAll('svg')].filter(s => !s.ownerSVGElement && !s.closest('[aria-hidden="true"]')
    && s.viewBox.baseVal && s.viewBox.baseVal.width && s.getBoundingClientRect().width);
  if (!svgs.length) add('empty', 'no <svg> with a viewBox on the page');
  for (const svg of svgs) {
    const vb = svg.viewBox.baseVal, m = svg.getScreenCTM(), scale = Math.hypot(m.a, m.b), first = svg.querySelector('rect');
    const left = m.a * vb.x + m.c * vb.y + m.e, top = m.b * vb.x + m.d * vb.y + m.f;
    const right = left + vb.width * scale, bottom = top + vb.height * scale;
    const unit = (v, o, base) => Math.round(base + (v - o) / scale);
    if (first) out.colors.push(win.getComputedStyle(first).fill);
    let ink = null;
    for (const el of svg.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon, image, use')) {
      const r = el.getBoundingClientRect();
      if (el.closest(UNDRAWN) || !(r.width || r.height)) continue;
      ink = ink ? {left: Math.min(ink.left, r.left), top: Math.min(ink.top, r.top), right: Math.max(ink.right, r.right),
        bottom: Math.max(ink.bottom, r.bottom)} : {left: r.left, top: r.top, right: r.right, bottom: r.bottom};
    }
    if (ink && (ink.left < left - 1 || ink.top < top - 1 || ink.right > right + 1 || ink.bottom > bottom + 1))
      add('clipped', `the drawing spans x ${unit(ink.left, left, vb.x)}..${unit(ink.right, left, vb.x)}, `
        + `y ${unit(ink.top, top, vb.y)}..${unit(ink.bottom, top, vb.y)}, past the viewBox `
        + `(${vb.x} ${vb.y} ${vb.width} ${vb.height}), which cuts it off`);
    const labels = [];
    for (const t of svg.querySelectorAll('text')) {
      const tm = t.getScreenCTM(), rs = tm && !t.closest(UNDRAWN) ? runs(win, t, Math.hypot(tm.a, tm.b)) : [];
      if (rs.length) labels.push({t, rs, name: clip(t.textContent), box: {left: Math.min(...rs.map(r => r.left)),
        top: Math.min(...rs.map(r => r.top)), right: Math.max(...rs.map(r => r.right)), bottom: Math.max(...rs.map(r => r.bottom))}});
    }
    out.labels += labels.length;
    labels.forEach(({t, rs, name, box: q}, i) => {
      const room = parseFloat(t.dataset.maxw), len = t.getComputedTextLength();
      if (room && len > room + .5) add('wide', `${name} is ${Math.round(len)} wide but has room for ${room}`);
      if (q.left < left - 1 || q.top < top - 1 || q.right > right + 1 || q.bottom > bottom + 1)
        add('outside', `${name} runs past the edge of the figure`);
      for (let j = 0; j < i; j++) if (hit(q, labels[j].box)) add('overlap', `${name} overlaps ${labels[j].name}`);
      const px = Math.min(...rs.map(r => r.px));
      if (px < MIN_PX - .05) tiny.push([px, name]);
      let worst = null;
      for (const r of rs) {
        out.colors.push(r.cs.fill);
        const bg = /^rgb/.test(r.cs.fill) && beneath(win, (r.left + r.right) / 2, (r.top + r.bottom) / 2);
        if (bg) {
          const k = contrast(over(rgb(r.cs.fill), r.a, bg), bg), need = r.px >= 24 ? 3 : 4.5;
          if (k < need && !(worst && worst.k <= k)) worst = {k, need};
        }
        const fams = families(r.cs.fontFamily);
        if (fams.length) {
          const key = fams.map(f => `"${f}"`).join(', '), entry = fonts.get(key) || {fams, chars: new Set()};
          for (const ch of r.s) if (ch.trim()) entry.chars.add(ch);
          fonts.set(key, entry);
        }
      }
      if (worst) add('contrast', `${name} has contrast ${(Math.floor(worst.k * 100) / 100).toFixed(2)}:1 against what is `
        + `beneath it; WCAG AA needs ${worst.need}:1`);
    });
  }
  if (tiny.length) {
    tiny.sort((a, b) => a[0] - b[0]);
    add('tiny', `${tiny.length} label(s) render below ${MIN_PX}px; the smallest is ${tiny[0][0].toFixed(1)}px (${tiny[0][1]})`);
  }
  for (const [key, {fams, chars}] of fonts) {
    const miss = [...chars].filter(ch => !fams.some(f => has(doc, f, ch)));
    if (miss.length === chars.size) add('font', `no font in ${key} is available, so the labels use a system font: load one`);
    else if (miss.length) add('font', `no font in ${key} has ${miss.slice(0, 16).join(' ')}${miss.length > 16 ? ' …' : ''}, `
      + 'so those characters use a system font: load a font that covers them');
  }
  return out;
}

addEventListener('load', async () => {
  const report = {pages: []};
  try {
    const frames = [...document.querySelectorAll('iframe')];
    for (const f of frames) f.contentDocument.documentElement.getBoundingClientRect();   // start every font load
    await Promise.all(frames.map(f => f.contentDocument.fonts.ready));
    for (const f of frames) report.pages.push(inspect(f.contentWindow, +f.dataset.w));
  } catch (e) { report.error = String(e && e.stack || e); }
  const s = document.createElement('script');
  s.type = 'application/json'; s.id = 'sketch-report';
  s.textContent = JSON.stringify(report).replace(/</g, '\\u003c');
  document.body.append(s);
});
"""


def browser() -> str | None:
    for name in (os.environ.get("SKETCH_BROWSER"), *BROWSERS):
        if name and (shutil.which(name) or Path(name).exists()):
            return shutil.which(name) or name
    return None


def chrome(doc: Path, dark: bool, args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory(prefix="sketch-chrome-") as profile:
        cmd = [browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio", "--no-first-run",
               "--allow-file-access-from-files", f"--user-data-dir={profile}", "--virtual-time-budget=5000",
               f"--blink-settings=preferredColorScheme={0 if dark else 1}", *(["--force-dark-mode"] if dark else []),
               *args, doc.as_uri()]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise Fail(f"the browser did not finish within {timeout} s") from None


def frames(url: str, widths, height: int, script: str = "") -> str:
    """One iframe per width: Chromium will not lay a window out narrower than 500 px, but a frame it will."""
    tags = "".join(f'<iframe src="{html.escape(url)}" data-w="{w}" '
                   f'style="display:block;border:0;width:{w}px;height:{height}px"></iframe>' for w in widths)
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>html, body {{ margin: 0; }}</style></head>'
            f'<body>{tags}{script}</body></html>')


def target(doc: Path, tmp: Path) -> str:
    """A page without a doctype is a fragment: check it inside a standard skeleton, as a host would show it."""
    text = doc.read_text(encoding="utf-8", errors="replace").lstrip("﻿")
    if re.match(r"\s*(<!--.*?-->\s*)*<!doctype", text, flags=re.I | re.S):
        return doc.resolve().as_uri()
    wrapped = tmp / "fragment.html"
    wrapped.write_text('<!doctype html><html><head><meta charset="utf-8">'
                       '<meta name="viewport" content="width=device-width, initial-scale=1">'
                       f'<base href="{doc.resolve().parent.as_uri()}/"></head><body>{text}</body></html>', encoding="utf-8")
    return wrapped.as_uri()


def measure(wrap: Path, dark: bool) -> dict:
    run = chrome(wrap, dark, ["--window-size=1296,800", "--force-device-scale-factor=1", "--dump-dom"])
    m = re.search(r'<script[^>]*id="sketch-report"[^>]*>(.*?)</script>', run.stdout, flags=re.S)
    if not m:
        raise Fail("the page produced no check report (browser exit %d): %s" % (run.returncode, run.stderr.strip()[-400:]))
    report = json.loads(m.group(1))
    if report.get("error"):
        raise Fail(f"the check script failed in {'dark' if dark else 'light'} mode: {report['error']}")
    return report


def cmd_check(args) -> int:
    if not args.page.is_file():
        print(f"sketch.py: no such page: {args.page}", file=sys.stderr)
        return 2
    if not browser():
        print("FAIL no Chromium/Chrome found; set SKETCH_BROWSER")
        return 1
    widths = sorted(set(args.width or (375, 1280)))
    errors, warns = [], []
    with tempfile.TemporaryDirectory(prefix="sketch-check-") as tmp:
        url = target(args.page, Path(tmp))
        wrap = Path(tmp, "check.html")
        wrap.write_text(frames(url, widths, FRAME_H, "<script>%s</script>" % CHECK_JS.replace("@MIN_PX@", repr(args.min_px))),
                        encoding="utf-8")
        with ThreadPoolExecutor(2) as pool:
            light, dark = pool.map(lambda d: measure(wrap, d), (False, True))
        hits: dict = {}   # one line per fault, naming only the widths and modes it shows in
        for report, mode in ((light, "light"), (dark, "dark")):
            if any(p["dark"] != (mode == "dark") for p in report["pages"]):
                errors.append(f"the browser did not render {mode} mode, so that pass checked nothing")
            for p in report["pages"]:
                for issue in p["issues"]:
                    hits.setdefault((KINDS.index(issue["kind"]), issue["detail"]), {}).setdefault(p["width"], set()).add(mode)
        for (_, detail), at in sorted(hits.items()):
            everywhere = len(at) == len(widths) and all(len(modes) == 2 for modes in at.values())
            where = ", ".join(f"{w}px" + ("" if len(modes) == 2 else " " + min(modes)) for w, modes in sorted(at.items()))
            errors.append(detail if everywhere else f"{where}: {detail}")
        if [p["colors"] for p in light["pages"]] == [p["colors"] for p in dark["pages"]]:
            warns.append("the figure looks the same in dark mode: put sketch.TOKENS_CSS in the page's stylesheet")
        if args.shots:
            args.shots.mkdir(parents=True, exist_ok=True)

            def shoot(job):
                w, mode, h = job
                one = Path(tmp, f"shot-{w}-{mode}.html")
                one.write_text(frames(url, [w], h), encoding="utf-8")
                png = args.shots.resolve() / f"{args.page.stem}-{w}-{mode}.png"
                png.unlink(missing_ok=True)
                chrome(one, mode == "dark", [f"--window-size={w},{h}", "--force-device-scale-factor=2", f"--screenshot={png}"])
                return png

            jobs = [(p["width"], mode, max(50, min(p["height"], 6000)))
                    for mode, report in (("light", light), ("dark", dark)) for p in report["pages"]]
            with ThreadPoolExecutor(4) as pool:
                for png in pool.map(shoot, jobs):
                    if png.exists():
                        print("shot", png)
                    else:
                        warns.append(f"no screenshot written: {png}")
    for line in errors:
        print("FAIL", line)
    for line in warns:
        print("warn", line)
    print(f"{light['pages'][0]['labels']} labels at {', '.join(map(str, widths))} px, light and dark")
    print("CHECK FAILED: %d error(s)" % len(errors) if errors else "CHECK OK" + (" (with warnings)" if warns else ""))
    return 1 if errors else 0


def positive(s: str) -> int:
    v = int(s)
    if v < 1:
        raise argparse.ArgumentTypeError("must be a positive number of px")
    return v


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check", help="check a page's figures in headless Chromium, light and dark")
    p.add_argument("page", type=Path)
    p.add_argument("--width", type=positive, action="append", help="viewport width in CSS px; repeat it (default 375 and 1280)")
    p.add_argument("--min-px", type=float, default=11.0, help="smallest rendered text size in px (default 11)")
    p.add_argument("--shots", type=Path, metavar="DIR", help="also write one PNG per width and colour scheme")
    p.set_defaults(fn=cmd_check)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except Fail as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
