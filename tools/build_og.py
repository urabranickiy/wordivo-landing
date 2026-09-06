"""Render assets/img/og.png — the 1200×630 card Telegram, Slack and X show
when someone pastes a wordivo.co link. Pure Pillow, brand tokens from
styles.css, the site's own DM Sans (converted from the bundled woff2 with
fontTools). Re-run after changing the wordmark or the line.

    ./tools/build_og.py            # needs Pillow + fontTools + brotli
"""
from __future__ import annotations

import io
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "og.png"
FONTS = ROOT / "assets" / "fonts"

BG, BG2 = "#FBF9F5", "#F5F2EC"
TEXT, DIM = "#0F1729", "#475569"
PRIMARY, ACCENT = "#4F46E5", "#F97316"


def _ttf() -> bytes:
    """The site ships DM Sans as a variable woff2 (wght 300–700 in one file);
    Pillow reads TrueType, so convert in memory and pick weights via the axis."""
    for f in sorted(FONTS.glob("*.woff2")):
        t = TTFont(f)
        # Google serves per-script subsets; the latin-ext file has no "a".
        has_ascii = ord("a") in t.getBestCmap()
        if "DM Sans" in (t["name"].getDebugName(1) or "") and "fvar" in t and has_ascii:
            t.flavor = None
            buf = io.BytesIO()
            t.save(buf)
            return buf.getvalue()
    raise SystemExit(f"no variable DM Sans in {FONTS}")


_TTF: bytes | None = None


def font(size: int, weight: int = 400) -> ImageFont.FreeTypeFont:
    global _TTF
    if _TTF is None:
        _TTF = _ttf()
    f = ImageFont.truetype(io.BytesIO(_TTF), size)
    axes = f.get_variation_axes()
    f.set_variation_by_axes([weight if a["name"] in (b"Weight", "Weight") else a["default"] for a in axes])
    return f


def build() -> pathlib.Path:
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # the soft corner glows the site paints behind every page
    glow = Image.new("RGB", (W, H), BG)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-300, -250, 520, 330), fill="#ECEAFB")
    gd.ellipse((760, 380, 1500, 900), fill="#FBEFE4")
    from PIL import ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    im = Image.blend(im, glow, 0.9)
    d = ImageDraw.Draw(im)

    # wordmark: "wordivo" + accent dot, as in the nav
    wm = font(64, 700)
    x, y = 80, 72
    d.text((x, y), "wordivo", font=wm, fill=TEXT)
    wx = d.textlength("wordivo", font=wm)
    d.text((x + wx + 2, y), ".", font=wm, fill=ACCENT)

    # headline — two lines, the last word in brand blue
    h1 = font(80, 700)
    d.text((80, 230), "Vocabulary that stays", font=h1, fill=TEXT)
    d.text((80, 322), "in your ", font=h1, fill=TEXT)
    off = d.textlength("in your ", font=h1)
    d.text((80 + off, 322), "memory.", font=h1, fill=PRIMARY)

    sub = font(34)
    d.text((80, 452), "Spaced repetition in Telegram — 22 exercise types, 8 languages,",
           font=sub, fill=DIM)
    d.text((80, 496), "and a share for the teacher who gave you the words.", font=sub, fill=DIM)

    # top-right: the bot handle as a pill, where the nav's CTA sits on the site
    pill = font(30, 500)
    label = "t.me/wordivobot"
    pw = d.textlength(label, font=pill) + 56
    px, py = W - 80 - pw, 80
    d.rounded_rectangle((px, py, px + pw, py + 58), radius=29, fill=PRIMARY)
    d.text((px + 28, py + 12), label, font=pill, fill="white")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, optimize=True)
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size:,} bytes)")
