"""Typeset text as SVG glyph outlines.

GitHub serves README images with `Content-Security-Policy: default-src 'none'`,
which blocks @font-face (including data: URIs). Display text is therefore drawn
as paths: each glyph is defined once in <defs> and placed with <use>.
Monospace text (prompts, ASCII art, diagram labels) stays as system-font <text>.
Fonts are SIL OFL 1.1 (see the OFL-*.txt files next to them).
"""
from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

DIR = Path(__file__).resolve().parent / "fonts"

MONO = 'ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono","DejaVu Sans Mono",monospace'


class Face:
    def __init__(self, slug, file):
        self.slug, self.file = slug, file

    @lru_cache(maxsize=None)
    def font(self):
        return TTFont(DIR / self.file)

    def glyph(self, ch):
        cmap = self.font().getBestCmap()
        return cmap.get(ord(ch)) or cmap[ord("?")]

    def width(self, text, size):
        """Advance width of `text` at `size`, without kerning."""
        f = self.font()
        return sum(f["hmtx"][self.glyph(c)][0] for c in text) * size / f["head"].unitsPerEm


SANS_REG = Face("ir", "Inter-Regular.ttf")
SANS_BOLD = Face("ib", "Inter-SemiBold.ttf")
SERIF_REG = Face("sr", "InstrumentSerif-Regular.ttf")
SERIF_ITALIC = Face("si", "InstrumentSerif-Italic.ttf")


class Typesetter:
    """Collects the glyphs one SVG uses and renders text runs as <use> references."""

    def __init__(self):
        self.paths = {}

    def _ref(self, face, gname):
        f = face.font()
        gid = f"{face.slug}{f.getGlyphID(gname)}"
        if gid not in self.paths:
            pen = SVGPathPen(f.getGlyphSet())
            f.getGlyphSet()[gname].draw(pen)
            self.paths[gid] = pen.getCommands()
        return gid if self.paths[gid] else None

    def run(self, face, text, x, y, size, cls=None):
        """Return (svg, width) for `text` with its baseline starting at (x, y)."""
        f = face.font()
        upm = f["head"].unitsPerEm
        s = size / upm
        adv, uses = 0, []
        for ch in text:
            g = face.glyph(ch)
            ref = self._ref(face, g)
            if ref:
                uses.append(f'<use xlink:href="#{ref}" x="{adv}"/>')
            adv += f["hmtx"][g][0]
        attr = f' class="{cls}"' if cls else ""
        svg = f'<g{attr} transform="translate({x:.1f} {y:.1f}) scale({s:.5f} {-s:.5f})">' + "".join(uses) + "</g>"
        return svg, adv * s

    def defs(self):
        return "".join(f'<path id="{k}" d="{d}"/>' for k, d in self.paths.items() if d)
