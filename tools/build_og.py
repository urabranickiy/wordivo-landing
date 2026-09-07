"""Render assets/img/og.png — the 1200×630 card Telegram, Slack and X show
when someone pastes a wordivo.co link. Pure Pillow, brand tokens from
styles.css, the site's own fonts (Fraunces for the headline, DM Sans for the
line under it — converted from the bundled woff2 with fontTools). Re-run after
changing the wordmark or the line.

    ./tools/build_og.py            # needs Pillow + fontTools + brotli
"""
from __future__ import annotations

import io
import pathlib

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "og.png"
FONTS = ROOT / "assets" / "fonts"

PAPER, SURFACE = "#F5EFE4", "#FFFCF7"
INK, INK2, INK3 = "#1A1611", "#4B443B", "#7B7267"
ACCENT, MARK, LINE = "#D8471B", "#FFE14D", "#C8BBA3"


def _ttf(family: str, italic: bool = False) -> bytes:
    """Fonts ship as variable woff2 subsets; Pillow reads TrueType, so convert
    in memory. Google serves per-script files — the latin-ext one has no "a",
    so pick the subset whose cmap covers ASCII."""
    for f in sorted(FONTS.glob("*.woff2")):
        t = TTFont(f)
        name = t["name"].getDebugName(1) or ""
        is_italic = bool(t["head"].macStyle & 2) or "Italic" in (t["name"].getDebugName(2) or "")
        if family in name and is_italic == italic and "fvar" in t and ord("a") in t.getBestCmap():
            t.flavor = None
            buf = io.BytesIO()
            t.save(buf)
            return buf.getvalue()
    raise SystemExit(f"no variable {family}{' italic' if italic else ''} in {FONTS}")


_CACHE: dict[tuple[str, bool], bytes] = {}


def font(family: str, size: int, weight: int = 400, italic: bool = False,
         opsz: float | None = None) -> ImageFont.FreeTypeFont:
    key = (family, italic)
    if key not in _CACHE:
        _CACHE[key] = _ttf(family, italic)
    f = ImageFont.truetype(io.BytesIO(_CACHE[key]), size)
    axes = f.get_variation_axes()
    values = []
    for a in axes:
        n = a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
        if "eight" in n:
            values.append(weight)
        elif "ptical" in n and opsz is not None:
            values.append(opsz)
        else:
            values.append(a["default"])
    f.set_variation_by_axes(values)
    return f


def build() -> pathlib.Path:
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)

    # the hero's forgetting curve, drawn along the bottom edge
    pts_forget = [(0, 540), (200, 600), (500, 620), (1200, 628)]
    for i in range(len(pts_forget) - 1):
        d.line([pts_forget[i], pts_forget[i + 1]], fill=LINE, width=2)
    keep = [(0, 540), (200, 592), (200, 546), (480, 590), (480, 542), (800, 584),
            (800, 538), (1200, 566)]
    d.line(keep, fill=ACCENT, width=3, joint="curve")
    for x, y in ((200, 546), (480, 542), (800, 538)):
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=ACCENT, outline=PAPER, width=2)

    # wordmark, as in the nav
    wm = font("Fraunces", 60, 600, opsz=48)
    x, y = 80, 64
    d.text((x, y), "wordivo", font=wm, fill=INK)
    d.text((x + d.textlength("wordivo", font=wm) + 2, y), ".", font=wm, fill=ACCENT)

    # top-right: the bot handle as an ink pill, where the nav's CTA sits
    pill = font("DM Sans", 28, 500)
    label = "t.me/wordivobot"
    pw = d.textlength(label, font=pill) + 56
    px, py = W - 80 - pw, 72
    d.rounded_rectangle((px, py, px + pw, py + 56), radius=28, fill=INK)
    d.text((px + 28, py + 11), label, font=pill, fill=PAPER)

    # headline — two lines; the last word italic on a highlighter stroke
    h1 = font("Fraunces", 86, 500, opsz=144)
    h1i = font("Fraunces", 86, 500, italic=True, opsz=144)
    d.text((80, 190), "Vocabulary that stays", font=h1, fill=INK)
    line2_y = 288
    d.text((80, line2_y), "in your ", font=h1, fill=INK)
    off = d.textlength("in your ", font=h1)
    word = "memory."
    ww = d.textlength(word, font=h1i)
    d.polygon([(80 + off - 6, line2_y + 42), (80 + off + ww + 10, line2_y + 38),
               (80 + off + ww + 6, line2_y + 96), (80 + off - 10, line2_y + 100)], fill=MARK)
    d.text((80 + off, line2_y), word, font=h1i, fill=INK)

    sub = font("DM Sans", 32, 400)
    d.text((80, 418), "Spaced repetition in Telegram — 22 exercise types, 8 languages,",
           font=sub, fill=INK2)
    d.text((80, 460), "and a share for the teacher who gave you the words.", font=sub, fill=INK2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, optimize=True)
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"wrote {p} ({p.stat().st_size:,} bytes)")
