"""
crop_sprites.py — Run this ONCE to extract individual sprites from spritesheet.png.
Usage:  py assets/crop_sprites.py

Reads:  assets/spritesheet.png
Writes: assets/sprites/*.png  (individual transparent-background sprites)

Auto-trims dark background and makes it transparent.
"""

import os
import sys

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image

SHEET_PATH = os.path.join(ROOT, "assets", "spritesheet.png")
OUT_DIR = os.path.join(ROOT, "assets", "sprites")

# Background brightness threshold — pixels with max(R,G,B) below this
# are considered background and will be made transparent.
BG_THRESHOLD = 45


def _make_bg_transparent(img, threshold=BG_THRESHOLD):
    """Replace dark background pixels with transparency."""
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if max(r, g, b) <= threshold:
                pixels[x, y] = (0, 0, 0, 0)
    return img


def _auto_trim(img, padding=2):
    """Crop to content bounding box with optional padding."""
    bbox = img.getbbox()  # finds non-zero (non-transparent) bounding box
    if bbox is None:
        return img
    x1, y1, x2, y2 = bbox
    # Add padding
    w, h = img.size
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)
    return img.crop((x1, y1, x2, y2))


def _extract(sheet, x, y, w, h):
    """Crop a region, remove BG, and auto-trim."""
    sw, sh = sheet.size
    # Clamp to sheet bounds
    x = max(0, min(x, sw - 1))
    y = max(0, min(y, sh - 1))
    w = min(w, sw - x)
    h = min(h, sh - y)
    region = sheet.crop((x, y, x + w, y + h))
    region = _make_bg_transparent(region)
    region = _auto_trim(region)
    return region


# ── Sprite regions for 1024×1536 sheet ─────────────────────────────────────
# These are (name, x, y, w, h) — measured for the actual 1024×1536 layout.
# The spritesheet has rows of content on a dark textured background.
REGIONS = [
    # Row 1: Title banner (full width, top section)
    ("title",            70,   10,  890, 190),

    # Row 2: Player characters
    ("player1",         120,  195,  210, 200),
    ("player2",         540,  195,  210, 200),

    # Row 3: Treasure icons (cash / gold / diamond)
    ("cash_big",         30,  400,  200, 160),
    ("gold_big",        230,  400,  200, 160),
    ("diamond_big",     430,  400,  200, 160),

    # Row 3 right side: Wall textures
    ("perm_wall",       620,  390,  380, 130),
    ("temp_wall",       620,  530,  380, 130),

    # Row 4: Misc icons
    ("clock",            30,  560,  155, 135),
    ("crate",           190,  560,  210, 120),
    ("hourglass",       405,  560,  130, 135),

    # Row 5: Score icons (small)
    ("score_cash",       30,  700,  160,  65),
    ("score_gold",      195,  700,  160,  65),
    ("score_diamond",   355,  700,  160,  65),

    # Row 5 right: Buttons
    ("btn_move",        530,  690,  200,  75),
    ("btn_place_wall",  740,  690,  250,  75),

    # Row 6: Turn panel + confirm/cancel
    ("panel_turn",       20,  780,  490,  80),
    ("btn_confirm",     530,  780,  220,  75),
    ("btn_cancel",      760,  780,  230,  75),

    # Row 7: Victory / Game Over banners
    ("victory",          20,  880,  490, 105),
    ("game_over",       520,  880,  480, 105),

    # Row 8: Win / Lose / Draw badges
    ("badge_win",        50, 1010,  250, 200),
    ("badge_lose",      360, 1010,  250, 200),
    ("badge_draw",      670, 1010,  260, 200),
]


def crop_sprites():
    if not os.path.exists(SHEET_PATH):
        print(f"ERROR: Sprite sheet not found at:\n  {SHEET_PATH}")
        print("Please save the sprite sheet image as 'assets/spritesheet.png' first.")
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)

    sheet = Image.open(SHEET_PATH).convert("RGBA")
    sw, sh = sheet.size
    print(f"Sprite sheet size: {sw} x {sh}")

    for name, x, y, w, h in REGIONS:
        sprite = _extract(sheet, x, y, w, h)
        out_path = os.path.join(OUT_DIR, f"{name}.png")
        sprite.save(out_path, "PNG")
        fw, fh = sprite.size
        print(f"  {name}.png  ({fw}x{fh})")

    print(f"\nDone! {len(REGIONS)} sprites saved to {OUT_DIR}")


if __name__ == "__main__":
    crop_sprites()
