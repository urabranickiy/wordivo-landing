#!/usr/bin/env python3
"""Guards for the static site. Exit 1 on any finding.

1. No third-party origins. Every page used to pull Google Fonts and cdnjs,
   which sends the visitor's IP away before consent (LG München I,
   3 O 17493/20). Fonts and scripts are self-hosted now; this keeps it so.
2. Every internal link and asset resolves to a file in the repo.
3. Every page carries the meta a shared link needs (canonical, og:image).
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ALLOWED_HOSTS = {"wordivo.co", "app.wordivo.co", "t.me"}
URL = re.compile(r"""(?:src|href|url)\s*[=(]\s*["']?\s*(https?://[^"')\s]+)""", re.I)
LOCAL = re.compile(r"""(?:src|href)\s*=\s*["'](?!https?:|mailto:|#|data:)([^"'#?]+)""", re.I)
REQUIRED_META = ('rel="canonical"', 'property="og:image"', 'property="og:title"', 'rel="icon"')


def main() -> int:
    findings: list[str] = []
    pages = sorted(ROOT.glob("*.html"))
    files = pages + [ROOT / "styles.css"] + sorted((ROOT / "assets").rglob("*.css"))
    for f in files:
        text = f.read_text(encoding="utf-8")
        for url in URL.findall(text):
            host = re.sub(r"^https?://", "", url).split("/")[0]
            if host not in ALLOWED_HOSTS:
                findings.append(f"{f.name}: third-party origin {url}")
        for ref in LOCAL.findall(text):
            target = (ROOT / ref.lstrip("/")) if ref.startswith("/") else (f.parent / ref)
            if not target.exists():
                findings.append(f"{f.name}: broken link {ref}")
    for page in pages:
        if page.name == "404.html":
            continue
        head = page.read_text(encoding="utf-8").split("</head>", 1)[0]
        for needle in REQUIRED_META:
            if needle not in head:
                findings.append(f"{page.name}: missing {needle}")
    for line in findings:
        print("  ", line)
    print(f"{len(findings)} finding(s) across {len(pages)} pages.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
