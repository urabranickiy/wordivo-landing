#!/usr/bin/env python3
"""Render favicon.svg, favicon.ico and apple-touch-icon.png from one mark.

The mark is the "W" cut from the wordmark on an ink tile with the brand's
vermilion full stop. Colours come from the tokens in styles.css; if those
change, change them here and re-run:

    ./tools/build_icons.py            # needs Pillow
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
INK, PAPER, ACCENT = "#1A1611", "#F5EFE4", "#D8471B"

# The W as a polygon on a 64-unit grid (same outline as favicon.svg).
W = [(11, 22), (18.2, 22), (23.3, 40.4), (28.9, 22), (35.1, 22), (40.7, 40.4), (45.8, 22),
     (53, 22), (43.6, 48), (36.7, 48), (31.5, 31), (26.3, 48), (19.4, 48)]
DOT = (52, 44.5, 4)
SVG_PATH = ("M11 22h7.2l5.1 18.4L28.9 22h6.2l5.6 18.4L45.8 22H53l-9.4 26h-6.9"
            "l-5.2-17-5.2 17h-6.9z")


def tile(size: int, rounded: bool) -> Image.Image:
    """Draw at 16x and downsample, so the diagonals stay crisp at 16 px."""
    s = 16
    px = size * s
    k = px / 64
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if rounded:
        d.rounded_rectangle((0, 0, px - 1, px - 1), radius=int(14 * k), fill=INK)
    else:
        d.rectangle((0, 0, px - 1, px - 1), fill=INK)
    d.polygon([(x * k, y * k) for x, y in W], fill=PAPER)
    cx, cy, r = DOT
    d.ellipse(((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k), fill=ACCENT)
    return im.resize((size, size), Image.LANCZOS)


def build() -> list[pathlib.Path]:
    out = []
    svg = ROOT / "favicon.svg"
    svg.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="14" fill="{INK}"/>'
        f'<path d="{SVG_PATH}" fill="{PAPER}"/>'
        f'<circle cx="{DOT[0]}" cy="{DOT[1]}" r="{DOT[2]}" fill="{ACCENT}"/></svg>\n')
    out.append(svg)

    ico = ROOT / "favicon.ico"
    tile(48, rounded=True).save(ico, sizes=[(16, 16), (32, 32), (48, 48)])
    out.append(ico)

    apple = ROOT / "apple-touch-icon.png"   # iOS applies its own corner mask
    tile(180, rounded=False).convert("RGB").save(apple, optimize=True)
    out.append(apple)
    return out


if __name__ == "__main__":
    for p in build():
        print(f"wrote {p.relative_to(ROOT)} ({p.stat().st_size:,} bytes)")
