"""
generate_audio.py — Convert narration text to MP3 files via OpenAI TTS.

One audio file is produced per section:
    output/audio/section_00.mp3
    output/audio/section_01.mp3
    ...

Long narrations are automatically split into chunks (4096-char limit) and
the resulting segments are concatenated with pydub.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from openai import OpenAI

import config.settings as cfg
from extraction_markdown import Section
from nlp_processing import split_into_chunks

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not cfg.OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY is not set in .env")
        _client = OpenAI(api_key=cfg.OPENAI_API_KEY)
    return _client


# ── Core TTS call ─────────────────────────────────────────────────────────────

def _tts_chunk(text: str, out_path: Path) -> None:
    """Call OpenAI TTS for a single text chunk and save to *out_path*."""
    client = _get_client()
    response = client.audio.speech.create(
        model=cfg.OPENAI_TTS_MODEL,
        voice=cfg.OPENAI_TTS_VOICE,
        input=text,
        response_format="mp3",
    )
    response.stream_to_file(str(out_path))
    logger.debug("  TTS chunk saved: %s", out_path.name)


# ── Per-section audio ─────────────────────────────────────────────────────────

def generate_section_audio(section: Section) -> Path:
    """
    Generate an MP3 for *section* and return its path.
    If the narration fits in one chunk, a single API call is made.
    Otherwise chunks are generated and concatenated.
    """
    out_dir = cfg.OUTPUT_AUDIO_DIR
    out_path = out_dir / f"section_{section.index:02d}.mp3"

    if out_path.exists():
        logger.info("Audio already exists, skipping: %s", out_path.name)
        return out_path

    narration = section.narration.strip()
    if not narration:
        logger.warning("Section %d has no narration — skipping audio.", section.index)
        return out_path

    chunks = split_into_chunks(narration)
    logger.info("Section %d '%s': %d TTS chunk(s).", section.index, section.title, len(chunks))

    if len(chunks) == 1:
        _tts_chunk(chunks[0], out_path)
        return out_path

    # Multiple chunks — generate separately, then concatenate
    from pydub import AudioSegment

    segment_paths: List[Path] = []
    for i, chunk in enumerate(chunks):
        seg_path = out_dir / f"section_{section.index:02d}_chunk{i:02d}.mp3"
        _tts_chunk(chunk, seg_path)
        segment_paths.append(seg_path)

    combined = AudioSegment.empty()
    for seg in segment_paths:
        combined += AudioSegment.from_mp3(str(seg))

    combined.export(str(out_path), format="mp3")
    logger.info("  Combined %d chunks → %s", len(chunks), out_path.name)

    # Clean up chunk files
    for seg in segment_paths:
        seg.unlink(missing_ok=True)

    return out_path


# ── Batch generation ──────────────────────────────────────────────────────────

def generate_all_audio(sections: List[Section]) -> List[Path]:
    """Generate audio for every section and return the list of MP3 paths."""
    logger.info("=== Generating audio for %d sections ===", len(sections))
    paths: List[Path] = []
    for section in sections:
        path = generate_section_audio(section)
        paths.append(path)
    logger.info("Audio generation complete.")
    return paths
