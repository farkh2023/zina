"""
generate_images.py — Generate one illustration per section via DALL-E 3.

Output:
    output/images/section_00.png
    output/images/section_01.png
    ...
"""

from __future__ import annotations

import logging
import requests
from pathlib import Path
from typing import List

from openai import OpenAI

import config.settings as cfg
from extraction_markdown import Section

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not cfg.OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY is not set in .env")
        _client = OpenAI(api_key=cfg.OPENAI_API_KEY)
    return _client


# ── Single image ──────────────────────────────────────────────────────────────

def generate_section_image(section: Section) -> Path:
    """
    Generate an image for *section* and return the saved PNG path.
    Skips generation if the file already exists.
    """
    out_path = cfg.OUTPUT_IMAGES_DIR / f"section_{section.index:02d}.png"

    if out_path.exists():
        logger.info("Image already exists, skipping: %s", out_path.name)
        return out_path

    prompt = section.image_prompt
    logger.info("Section %d — generating image: '%s'", section.index, prompt[:80])

    client   = _get_client()
    response = client.images.generate(
        model=cfg.OPENAI_IMAGE_MODEL,
        prompt=prompt,
        size=cfg.OPENAI_IMAGE_SIZE,
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    _download_image(image_url, out_path)
    logger.info("  Saved: %s", out_path.name)
    return out_path


def _download_image(url: str, dest: Path) -> None:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


# ── Batch ─────────────────────────────────────────────────────────────────────

def generate_all_images(sections: List[Section]) -> List[Path]:
    """Generate images for all sections and return their paths."""
    logger.info("=== Generating images for %d sections ===", len(sections))
    paths: List[Path] = []
    for section in sections:
        path = generate_section_image(section)
        paths.append(path)
    logger.info("Image generation complete.")
    return paths
