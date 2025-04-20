#!/usr/bin/env python3
"""
compose.py
Creates 2‑, 3‑ and 4‑photo progress collages with a logo in the bottom‑left corner.

Run:  python compose.py
"""

import os
import sys
from pathlib import Path
from typing import List

try:
    from PIL import Image
except ImportError:
    sys.exit("❌  Pillow is not installed. Run  pip install pillow  and try again.")

# ─────────────── Configuration ────────────────
IMAGES_DIR   = Path("images")
OUTPUT_DIR   = Path("output")
LOGO_PATH    = Path("logo.png")     # or .jpg
TARGET_HEIGHT = 1200               # px  (resize larger photos down to this height)
LOGO_MAX_W_PCT = 0.15              # logo will never exceed 15 % of collage width
PADDING = 12                       # px margin for the logo
COLLAGE_BG = (255, 255, 255)       # white background
# ──────────────────────────────────────────────

def load_and_normalise(images: List[Path]) -> List[Image.Image]:
    """Open each image, down‑scaling so every frame has the same height."""
    opened: List[Image.Image] = []
    for p in images:
        img = Image.open(p).convert("RGB")
        if img.height > TARGET_HEIGHT:
            # keep aspect ratio
            w = int(img.width * TARGET_HEIGHT / img.height)
            img = img.resize((w, TARGET_HEIGHT), Image.LANCZOS)
        opened.append(img)
    # now force *exact* same height (min of all) so they line up perfectly
    min_h = min(i.height for i in opened)
    if any(i.height != min_h for i in opened):
        opened = [i.resize((int(i.width * min_h / i.height), min_h),
                           Image.LANCZOS) for i in opened]
    return opened

def stitch_row(frames: List[Image.Image]) -> Image.Image:
    """Return a single‑row collage containing all frames."""
    total_w = sum(f.width for f in frames)
    h = frames[0].height
    canvas = Image.new("RGB", (total_w, h), COLLAGE_BG)
    x = 0
    for f in frames:
        canvas.paste(f, (x, 0))
        x += f.width
    return canvas

def add_logo(base: Image.Image, logo_file: Path) -> Image.Image:
    """Stamp the logo at bottom‑left with padding."""
    if not logo_file.exists():
        return base
    logo = Image.open(logo_file).convert("RGBA")

    # scale logo if it’s too wide
    max_w = int(base.width * LOGO_MAX_W_PCT)
    if logo.width > max_w:
        new_h = int(logo.height * max_w / logo.width)
        logo = logo.resize((max_w, new_h), Image.LANCZOS)

    pos = (PADDING, base.height - logo.height - PADDING)
    base.paste(logo, pos, logo)  # use itself as alpha mask
    return base

def save(img: Image.Image, name: str):
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / f"{name}.jpg"
    img.save(out, quality=92, subsampling=0, optimize=True)
    print(f"✅  wrote {out}")

def main():
    if not IMAGES_DIR.exists():
        sys.exit(f"❌  '{IMAGES_DIR}' folder not found.")
    photos = sorted([p for p in IMAGES_DIR.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
    if len(photos) < 2:
        sys.exit("❌  Need at least two images in the images/ folder.")
    print(f"Found {len(photos)} source images.")

    frames = load_and_normalise(photos)

    for n in (2, 3, 4):
        if n > len(frames):
            continue
        subset = frames[:n]                  # first n photos
        collage = stitch_row(subset)
        collage = add_logo(collage, LOGO_PATH)
        save(collage, f"collage_{n}")

if __name__ == "__main__":
    main()
