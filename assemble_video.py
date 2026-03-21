"""
assemble_video.py — Compose the final MP4 from per-section images and audio.

For each section:
  1. Load the section image and resize to VIDEO_WIDTH x VIDEO_HEIGHT.
  2. Load the narration audio clip; its duration determines the slide duration.
  3. Apply a short fade-in / fade-out on the audio.
  4. Cross-fade transition to the next slide (VIDEO_TRANSITION_DURATION seconds).

The clips are concatenated and exported as:
    output/video/final_video.mp4
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)

import config.settings as cfg
from extraction_markdown import Section

logger = logging.getLogger(__name__)

FINAL_VIDEO_NAME = "final_video.mp4"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_slide_clip(image_path: Path, audio_path: Path) -> ImageClip:
    """
    Return a MoviePy ImageClip whose duration equals the audio file length.
    Audio is attached with fade-in/out.
    """
    audio = AudioFileClip(str(audio_path))
    fade  = min(cfg.AUDIO_FADE_DURATION, audio.duration / 4)
    audio = audio.audio_fadein(fade).audio_fadeout(fade)

    clip = (
        ImageClip(str(image_path))
        .set_duration(audio.duration)
        .resize((cfg.VIDEO_WIDTH, cfg.VIDEO_HEIGHT))
        .set_audio(audio)
    )
    return clip


# ── Main assembly ─────────────────────────────────────────────────────────────

def assemble_video(
    sections: List[Section],
    image_paths: List[Path],
    audio_paths: List[Path],
) -> Path:
    """
    Build and export the final video.  Returns the output path.

    *image_paths* and *audio_paths* must be aligned with *sections*.
    Sections whose image or audio file is missing are skipped with a warning.
    """
    out_path = cfg.OUTPUT_VIDEO_DIR / FINAL_VIDEO_NAME

    if out_path.exists():
        logger.info("Video already exists, skipping assembly: %s", out_path.name)
        return out_path

    clips: List[ImageClip] = []
    for section, img_p, aud_p in zip(sections, image_paths, audio_paths):
        if not img_p.exists():
            logger.warning("Section %d: image missing (%s) — skipped.", section.index, img_p)
            continue
        if not aud_p.exists():
            logger.warning("Section %d: audio missing (%s) — skipped.", section.index, aud_p)
            continue

        logger.info("  Building clip for section %d '%s'", section.index, section.title)
        clip = _make_slide_clip(img_p, aud_p)
        clips.append(clip)

    if not clips:
        raise RuntimeError("No valid clips found — cannot assemble video.")

    logger.info("Concatenating %d clips (transition=%.1fs)…", len(clips), cfg.VIDEO_TRANSITION_DURATION)
    final = concatenate_videoclips(
        clips,
        method="compose",
        padding=-cfg.VIDEO_TRANSITION_DURATION,
    )

    logger.info("Exporting → %s", out_path)
    final.write_videofile(
        str(out_path),
        fps=cfg.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(cfg.OUTPUT_VIDEO_DIR / "temp_audio.m4a"),
        remove_temp=True,
        logger=None,        # suppress MoviePy's verbose bar
    )

    # Release resources
    final.close()
    for clip in clips:
        clip.close()

    logger.info("Video assembly complete: %s", out_path)
    return out_path
