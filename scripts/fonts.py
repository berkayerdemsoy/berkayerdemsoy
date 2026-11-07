"""Embedded web fonts for the generated SVGs.

An SVG shown through <img> cannot load external resources, so each face is
subset to the characters the SVG uses and inlined as a base64 WOFF.
Fonts are SIL OFL 1.1 (see the OFL-*.txt files next to them).
"""
import base64
import io
import re
from functools import lru_cache
from html import unescape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

DIR = Path(__file__).resolve().parent / "fonts"

MONO = '"Geist Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace'
SERIF = '"Instrument Serif",Georgia,"Times New Roman",serif'
SANS = '"Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif'


class Face:
    def __init__(self, family, file, weight=400, style="normal"):
        self.family, self.file, self.weight, self.style = family, file, weight, style

    @property
    def key(self):
        return f"{self.family}|{self.weight}|{self.style}"

    @lru_cache(maxsize=None)
    def _font(self):
        return TTFont(DIR / self.file)

    def width(self, text, size):
        """Advance width of `text` at `size`, without kerning."""
        f = self._font()
        cmap, hmtx = f.getBestCmap(), f["hmtx"]
        upm = f["head"].unitsPerEm
        units = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text)
        return units * size / upm

    def css(self, chars):
        font = TTFont(DIR / self.file)
        opts = subset.Options()
        opts.flavor = "woff"
        opts.layout_features = ["kern", "liga"]
        opts.name_IDs = []
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(chars)) or " ")
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff"
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        return (f'@font-face{{font-family:"{self.family}";font-weight:{self.weight};font-style:{self.style};'
                f'src:url(data:font/woff;base64,{data}) format("woff")}}')


MONO_REG = Face("Geist Mono", "GeistMono-Regular.ttf", 400)
MONO_BOLD = Face("Geist Mono", "GeistMono-SemiBold.ttf", 600)
SANS_REG = Face("Inter", "Inter-Regular.ttf", 400)
SANS_BOLD = Face("Inter", "Inter-SemiBold.ttf", 600)
SERIF_REG = Face("Instrument Serif", "InstrumentSerif-Regular.ttf", 400)
SERIF_ITALIC = Face("Instrument Serif", "InstrumentSerif-Italic.ttf", 400, "italic")


def embed(svg, faces):
    """Prepend @font-face rules for `faces`, subset to the text the SVG contains."""
    text = unescape("".join(re.findall(r">([^<]+)<", svg)))
    chars = {c for c in text if not c.isspace()} | {" "}
    rules = "".join(f.css(chars) for f in faces)
    return svg.replace("<style>", "<style>" + rules, 1)
