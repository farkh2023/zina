"""
generate_thumbnail.py — Create a YouTube thumbnail (1280x720 px).

Strategy:
  1. Use the first section's image as a background.
  2. Overlay a semi-transparent dark band at the bottom.
  3. Draw the video title in large white text.

Output: output/thumbnail/thumbnail.png
"""

from __future__ import annotations

import logging
import textwrap
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont

import config.settings as cfg
from extraction_markdown import Section

logger = logging.getLogger(__name__)

THUMB_W, THUMB_H = 1280, 720
FONT_SIZE_TITLE  = 72
FONT_SIZE_SUB    = 36
OVERLAY_ALPHA    = 180   # 0–255


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates = [
        "arial.ttf", "Arial.ttf",
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for name in font_candidates:
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def generate_thumbnail(
    sections: List[Section],
    image_paths: List[Path],
    metadata: dict,
) -> Path:
    """
    Build and save the thumbnail, return its path.
    *image_paths* must be aligned with *sections* (same order).
    """
    out_path = cfg.OUTPUT_THUMBNAIL_DIR / "thumbnail.png"

    if out_path.exists():
        logger.info("Thumbnail already exists, skipping.")
        return out_path

    # ── Background: first available image ─────────────────────────────────────
    bg_image: Image.Image | None = None
    for p in image_paths:
        if p.exists():
            bg_image = Image.open(p).convert("RGB")
            break

    if bg_image is None:
        logger.warning("No background image found — using solid colour.")
        bg_image = Image.new("RGB", (THUMB_W, THUMB_H), color=(20, 20, 40))
    else:
        bg_image = bg_image.resize((THUMB_W, THUMB_H), Image.LANCZOS)

    # ── Dark overlay band ──────────────────────────────────────────────────────
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    band_top = int(THUMB_H * 0.55)
    draw.rectangle([(0, band_top), (THUMB_W, THUMB_H)], fill=(0, 0, 0, OVERLAY_ALPHA))

    bg_rgba = bg_image.convert("RGBA")
    combined = Image.alpha_composite(bg_rgba, overlay).convert("RGB")

    # ── Text ───────────────────────────────────────────────────────────────────
    title = metadata.get("title", sections[0].title if sections else "Video")
    draw2 = ImageDraw.Draw(combined)

    font_title = _load_font(FONT_SIZE_TITLE)
    font_sub   = _load_font(FONT_SIZE_SUB)

    wrapped = textwrap.fill(title, width=28)
    draw2.text((60, band_top + 20), wrapped, font=font_title, fill="white")

    if sections:
        sub_text = f"{len(sections)} sections"
        draw2.text((60, THUMB_H - 55), sub_text, font=font_sub, fill=(200, 200, 200))

    combined.save(str(out_path), "PNG")
    logger.info("Thumbnail saved: %s", out_path.name)
    return out_path
