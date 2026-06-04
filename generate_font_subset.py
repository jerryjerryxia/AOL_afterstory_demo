# -*- coding: utf-8 -*-
"""
Rebuilds the bundled game font as a compact subset containing only the
characters this game uses:

  game/body.ttf  <-  Fusion Pixel 12px (proportional, zh_hans)
                     a CJK pixel/dot-gothic typeface (DotGothic16 aesthetic,
                     but with full Simplified-Chinese coverage). OFL licensed.

Run after editing the raw script or adding new Chinese text:
    python generate_font_subset.py

The full source font (~7 MB) is downloaded once into tools/ and cached
there. tools/ is gitignored, so only the small subset in game/ ships
with the game. To change typeface, edit FONT_SOURCE below - the output
filename stays body.ttf, so nothing else needs updating.
"""
import glob
import io
import os
import urllib.request
import zipfile

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
OUT = os.path.join(ROOT, "game", "body.ttf")

# Source pixel font: Fusion Pixel 12px proportional, Simplified-Chinese build.
# Shipped as a per-format .zip on the project's GitHub releases; we cache the
# extracted .ttf in tools/.
FONT_SOURCE = {
    "cache": "fusion-pixel-12px-proportional-zh_hans.ttf",
    "zip_url": (
        "https://github.com/TakWolf/fusion-pixel-font/releases/download/"
        "2026.05.07/fusion-pixel-font-12px-proportional-ttf-v2026.05.07.zip"
    ),
    "member": "fusion-pixel-12px-proportional-zh_hans.ttf",
}

# Raw script files to scan (whichever exist for this project).
RAW_SCRIPTS = ("main_script_raw.txt", "demo_script.txt", "demo_script_eng.txt")


def ensure_source():
    """Return the cached source-font path, downloading + extracting if missing."""
    path = os.path.join(TOOLS, FONT_SOURCE["cache"])
    if not os.path.exists(path):
        os.makedirs(TOOLS, exist_ok=True)
        print(f"Downloading {FONT_SOURCE['zip_url']}")
        data = urllib.request.urlopen(FONT_SOURCE["zip_url"]).read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            with z.open(FONT_SOURCE["member"]) as src, open(path, "wb") as dst:
                dst.write(src.read())
    return path


def collect_chars():
    """Every character that may actually be rendered: the raw script(s) plus
    all .rpy files (UI strings, generated dialogue). We deliberately do NOT
    seed from other fonts sitting in game/ - an unrelated full font there
    would balloon the subset with thousands of never-displayed glyphs."""
    chars = set()
    for name in RAW_SCRIPTS:
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                chars |= set(f.read())
    for path in glob.glob(os.path.join(ROOT, "game", "**", "*.rpy"), recursive=True):
        with open(path, encoding="utf-8") as f:
            chars |= set(f.read())
    for ws in "\n\r\t﻿":
        chars.discard(ws)
    return chars


def main():
    src = ensure_source()
    src_cmap = set(TTFont(src).getBestCmap().keys())

    wanted = collect_chars()
    missing = sorted(c for c in wanted if ord(c) not in src_cmap)
    if missing:
        # Keep only glyphs the source actually has; report the rest so a future
        # typeface swap doesn't quietly lose characters. ascii-safe so it never
        # crashes on a legacy console codepage (e.g. GBK on Windows).
        listed = "".join(missing).encode("ascii", "backslashreplace").decode("ascii")
        print(f"WARNING: {len(missing)} char(s) not in source font, skipped: {listed}")
    text = "".join(sorted(c for c in wanted if ord(c) in src_cmap))
    print(f"Subsetting to {len(text)} characters...")

    font = TTFont(src)
    options = Options()
    options.glyph_names = False      # drop glyph names
    options.hinting = False          # pixel font; hinting irrelevant
    options.layout_features = []     # no GSUB/GPOS shaping for horizontal CJK
    sub = Subsetter(options=options)
    sub.populate(text=text)
    sub.subset(font)
    font.save(OUT)
    print(f"  {os.path.basename(OUT)}  ({os.path.getsize(OUT):,} bytes)")


if __name__ == "__main__":
    main()
