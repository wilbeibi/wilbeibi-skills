#!/usr/bin/env python3
"""Checks for sketch.py: python3 scripts/test_sketch.py

Drawing must be deterministic and self-contained, and the palette must meet WCAG AA in both modes.
`check` must pass a clean figure, name each planted fault, and screenshot light and dark differently.
The browser tests need Chromium/Chrome and are skipped without one; they load no network fonts.
"""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import re
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location("sketch", Path(__file__).with_name("sketch.py"))
sk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sk)

SVG = "{http://www.w3.org/2000/svg}"


def figure(seed=1, font="sans-serif"):
    """Every Pen mark, laid out cleanly."""
    p = sk.Pen(seed)
    p.box(16, 16, 110, 48, fill="sky")
    p.text(71, 45, "request", maxw=100)
    p.arrow(132, 40, 170, 40)
    p.cylinder(176, 14, 108, 60)
    p.text(230, 56, "store", maxw=96)
    p.memory(16, 84, 110, 34)
    p.text(71, 106, "memory", maxw=100)
    p.dots(151, 101)
    p.box(176, 84, 108, 34, fill="wash", dash="7 6")
    p.text(230, 106, "queue", color="ink-2", maxw=96)
    p.poly([(16, 136), (284, 136), (284, 144), (16, 144)], fill="lavender")
    p.line(16, 152, 284, 152)
    p.arrow(284, 162, 16, 162, bend=-4)
    return p.svg(300, 176, label="Every mark", font=font)


def luminance(hex_):
    lin = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))]
    return .2126 * lin[0] + .7152 * lin[1] + .0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + .05) / (lo + .05)


def check(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = sk.main(["check", *map(str, args)])
    return code, out.getvalue() + err.getvalue()


class Drawing(unittest.TestCase):
    def test_same_seed_same_bytes(self):
        self.assertEqual(figure(7), figure(7))
        self.assertNotEqual(figure(7), figure(8))

    def test_svg_is_self_contained(self):
        svg = figure()
        root = ET.fromstring(svg)
        tags = {el.tag.removeprefix(SVG) for el in root.iter()}
        self.assertFalse(tags & {"style", "script", "foreignObject"})
        uses = re.findall(r"var\([^)]*\)", svg)
        self.assertTrue(uses)
        for use in uses:
            self.assertRegex(use, r"^var\(--sk-[a-z0-9-]+,#[0-9a-f]{6}\)$")

    def test_labels_are_escaped(self):
        p = sk.Pen()
        p.text(50, 20, "a < b & c")
        root = ET.fromstring(p.svg(100, 40, label='say "hi"'))
        self.assertEqual(root.find(SVG + "text").text, "a < b & c")
        self.assertEqual(root.get("aria-label"), 'say "hi"')

    def test_unknown_colour_is_refused(self):
        with self.assertRaises(ValueError):
            sk.Pen().box(0, 0, 10, 10, fill="red")

    def test_palette_meets_wcag_aa(self):
        for mode in (0, 1):
            ink, muted = sk.TOKENS["ink"][mode], sk.TOKENS["ink-2"][mode]
            for name, pair in sk.TOKENS.items():
                if name not in ("ink", "ink-2"):
                    self.assertGreaterEqual(contrast(ink, pair[mode]), 4.5, (name, mode))
            for name in ("paper", "wash", "card"):
                self.assertGreaterEqual(contrast(muted, sk.TOKENS[name][mode]), 4.5, (name, mode))

    def test_tokens_css_has_both_modes(self):
        css = sk.TOKENS_CSS
        self.assertIn("--sk-paper: #fbf7ee;", css)
        self.assertIn("prefers-color-scheme: dark", css)
        self.assertIn(':root[data-theme="dark"] { --sk-paper: #22201c;', css)


@unittest.skipUnless(sk.browser(), "needs Chromium or Chrome")
class Check(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_clean_figure_passes_and_shoots_both_modes(self):
        page = self.write("clean.html", sk.page(figure(), "Clean", head=""))
        code, out = check(page, "--shots", self.dir / "shots")
        self.assertEqual(code, 0, out)
        self.assertIn("CHECK OK", out)
        self.assertNotIn("warn", out)
        shots = {p.name: p.read_bytes() for p in (self.dir / "shots").glob("*.png")}
        self.assertEqual(sorted(shots), ["clean-1280-dark.png", "clean-1280-light.png", "clean-375-dark.png", "clean-375-light.png"])
        for name, data in shots.items():
            width = struct.unpack(">I", data[16:20])[0]
            self.assertEqual(width, 2 * int(name.split("-")[1]), name)
        self.assertNotEqual(shots["clean-375-light.png"], shots["clean-375-dark.png"])

    def test_halos_tspans_and_translucent_fills_are_read_as_drawn(self):
        p = sk.Pen()
        p.marks += [
            # the <text> has no fill or size of its own; its tspans do
            f'<text x="100" y="22" text-anchor="middle"><tspan font-size="16" fill="{sk.paint("ink")}">Name</tspan>'
            f'<tspan dx="5" font-size="12" fill="{sk.paint("ink-2")}">2026</tspan></text>',
            # a stroke-only halo under its label
            f'<text x="60" y="56" font-size="14" text-anchor="middle" fill="none" stroke="{sk.paint("paper")}" '
            'stroke-width="5">halo</text>',
            f'<text x="60" y="56" font-size="14" text-anchor="middle" fill="{sk.paint("ink")}">halo</text>',
            # ink on a 16% tint, which is light in light mode and dark in dark mode
            '<rect x="100" y="38" width="80" height="26" rx="6" fill="#c98500" fill-opacity=".16"/>',
            f'<text x="140" y="56" font-size="14" text-anchor="middle" fill="{sk.paint("ink")}">tinted</text>',
        ]
        p.text(4, 9, "now", anchor="start")   # its line box crosses the top edge; its glyphs do not
        page = self.write("drawn.html", sk.page(p.svg(200, 80, label="Read as drawn", font="sans-serif"), "Drawn", head=""))
        code, out = check(page)
        self.assertEqual(code, 0, out)
        self.assertNotIn("FAIL", out)

    def test_fragment_without_dark_palette_passes_with_a_warning(self):
        code, out = check(self.write("fragment.html", figure()))
        self.assertEqual(code, 0, out)
        self.assertIn("warn the figure looks the same in dark mode", out)

    def test_each_planted_fault_is_named(self):
        def one(draw, font="sans-serif"):
            p = sk.Pen()
            p.box(10, 10, 80, 40, fill="sky")
            draw(p)
            return p.svg(200, 80, label="fault", font=font)

        dim = '<text x="150" y="70" font-size="14" text-anchor="middle" fill="#3a3632">dim</text>'
        figures = [
            one(lambda p: p.text(100, 35, "far too long for this box", maxw=60)),
            one(lambda p: (p.text(140, 30, "alpha"), p.text(142, 32, "beta"))),
            one(lambda p: p.text(188, 30, "edge", anchor="start")),
            one(lambda p: p.text(140, 30, "tiny", size=7)),
            one(lambda p: p.box(170, 20, 60, 30)),
            f'<div style="height:{sk.FRAME_H}px"></div>',   # below one frame of page, the check must scroll to see beneath a label
            one(lambda p: p.marks.append(dim)),
            one(lambda p: p.text(140, 30, "missing"), font="'No Such Font', sans-serif"),
            one(lambda p: p.text(140, 30, "cache 缓存"), font="'DejaVu Sans', Helvetica, Arial, sans-serif"),
        ]
        doc = sk.page("\n".join(figures), "Faults", head="").replace("</figure>", '</figure><div style="width:600px;height:1px"></div>')
        code, out = check(self.write("faults.html", doc))
        self.assertEqual(code, 1, out)
        expected = [
            r'^FAIL 375px: the page is \d+px wide, so it scrolls sideways$',
            r'^FAIL the drawing spans x \d+\.\.23\d, y \d+\.\.\d+, past the viewBox \(0 0 200 80\), which cuts it off$',
            r'^FAIL "edge" runs past the edge of the figure$',
            r'^FAIL "far too long for this box" is \d+ wide but has room for 60$',
            r'^FAIL "beta" overlaps "alpha"$',
            r'^FAIL 1 label\(s\) render below 11px; the smallest is 7\.0px \("tiny"\)$',
            r'^FAIL 375px dark, 1280px dark: "dim" has contrast 1\.\d+:1 against what is beneath it; WCAG AA needs 4\.5:1$',
            r'^FAIL no font in "No Such Font" is available, so the labels use a system font: load one$',
            r'^FAIL no font in "DejaVu Sans", "Helvetica", "Arial" has 缓 存, so those characters use a system font: '
            r'load a font that covers them$',
        ]
        fails = [line for line in out.splitlines() if line.startswith("FAIL")]
        for pattern in expected:
            self.assertTrue(any(re.match(pattern, line) for line in fails), f"{pattern}\n{out}")
        self.assertEqual(len(fails), len(expected), out)
        self.assertIn("CHECK FAILED: %d error(s)" % len(expected), out)

    def test_missing_page_is_a_usage_error(self):
        code, out = check(self.dir / "nope.html")
        self.assertEqual(code, 2)
        self.assertIn("no such page", out)


if __name__ == "__main__":
    unittest.main()
