"""
pipeline.py — Main orchestrator for the YouTube AI pipeline.

Usage:
    python pipeline.py                         # uses input/script.md
    python pipeline.py --script path/to/file.md
    python pipeline.py --no-upload             # skip YouTube upload
    python pipeline.py --privacy public        # set upload privacy
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import colorlog

import config.settings as cfg
from extraction_markdown import extract_sections, load_script
from nlp_processing       import process_sections
from generate_audio       import generate_all_audio
from generate_images      import generate_all_images
from generate_thumbnail   import generate_thumbnail
from assemble_video       import assemble_video
from upload_youtube       import upload_video


# ── Logging setup ─────────────────────────────────────────────────────────────

def _setup_logging(verbose: bool = False) -> None:
    level  = logging.DEBUG if verbose else logging.INFO
    fmt    = "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message)s"
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(fmt, datefmt="%H:%M:%S"))
    logging.basicConfig(level=level, handlers=[handler])


logger = logging.getLogger(__name__)


# ── Steps ─────────────────────────────────────────────────────────────────────

def _step(name: str) -> None:
    logger.info("")
    logger.info("━━━ %s ━━━", name)


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run(
    script_path: Path,
    upload: bool = True,
    privacy: str = "private",
    verbose: bool = False,
) -> None:
    _setup_logging(verbose)
    start = time.time()

    logger.info("YouTube AI Pipeline starting…")
    logger.info("Script : %s", script_path)
    logger.info("Upload : %s  |  Privacy : %s", upload, privacy)

    # ── 1. Load & parse script ─────────────────────────────────────────────────
    _step("1 / 6  Extract sections")
    markdown  = load_script(script_path)
    sections  = extract_sections(markdown)

    # ── 2. NLP enrichment ─────────────────────────────────────────────────────
    _step("2 / 6  NLP processing")
    sections, metadata = process_sections(sections)
    logger.info("Video title: '%s'", metadata["title"])

    # ── 3. Audio ───────────────────────────────────────────────────────────────
    _step("3 / 6  Generate audio")
    audio_paths = generate_all_audio(sections)

    # ── 4. Images ──────────────────────────────────────────────────────────────
    _step("4 / 6  Generate images")
    image_paths = generate_all_images(sections)

    # ── 5. Thumbnail ───────────────────────────────────────────────────────────
    _step("5 / 6  Generate thumbnail")
    thumbnail_path = generate_thumbnail(sections, image_paths, metadata)

    # ── 5b. Assemble video ────────────────────────────────────────────────────
    _step("5b / 6  Assemble video")
    video_path = assemble_video(sections, image_paths, audio_paths)

    # ── 6. Upload ──────────────────────────────────────────────────────────────
    if upload:
        _step("6 / 6  Upload to YouTube")
        video_id = upload_video(
            video_path=video_path,
            metadata=metadata,
            thumbnail_path=thumbnail_path,
            privacy=privacy,
        )
        logger.info("Published! https://www.youtube.com/watch?v=%s", video_id)
    else:
        logger.info("Upload skipped. Final video: %s", video_path)

    elapsed = time.time() - start
    logger.info("")
    logger.info("Pipeline finished in %.1f seconds.", elapsed)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="YouTube AI Pipeline — Markdown → YouTube video"
    )
    parser.add_argument(
        "--script",
        type=Path,
        default=cfg.INPUT_SCRIPT,
        help="Path to the input Markdown script (default: input/script.md)",
    )
    parser.add_argument(
        "--no-upload",
        dest="upload",
        action="store_false",
        default=True,
        help="Skip the YouTube upload step",
    )
    parser.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default="private",
        help="YouTube video privacy setting (default: private)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        run(
            script_path=args.script,
            upload=args.upload,
            privacy=args.privacy,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
        sys.exit(1)
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        sys.exit(1)
