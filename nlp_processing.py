"""
nlp_processing.py — NLP enrichment of extracted sections.

Responsibilities:
  1. Clean and normalise narration text (whitespace, punctuation).
  2. Split long narrations into TTS-safe chunks (<= MAX_CHARS characters).
  3. Generate a YouTube-ready title, description and tags from the sections.
  4. Estimate speaking duration (words / average WPM).
"""

from __future__ import annotations

import re
import logging
from typing import List

from extraction_markdown import Section

logger = logging.getLogger(__name__)

MAX_CHARS = 4096   # OpenAI TTS limit per request
AVG_WPM   = 150    # words per minute (narration speed)


# ── Text cleaning ─────────────────────────────────────────────────────────────

_MULTI_SPACE = re.compile(r" {2,}")
_MULTI_NL    = re.compile(r"\n{3,}")


def clean_narration(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _MULTI_NL.sub("\n\n", text)
    text = _MULTI_SPACE.sub(" ", text)
    # Ensure sentences end with proper punctuation before a capital letter
    text = re.sub(r"([a-z])([A-Z])", r"\1. \2", text)
    return text.strip()


# ── Chunking ──────────────────────────────────────────────────────────────────

def split_into_chunks(text: str, max_chars: int = MAX_CHARS) -> List[str]:
    """
    Split *text* into chunks of at most *max_chars* characters, breaking
    preferably at sentence boundaries.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    current   = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            # If a single sentence exceeds max_chars, hard-split it
            while len(sentence) > max_chars:
                chunks.append(sentence[:max_chars])
                sentence = sentence[max_chars:]
            current = sentence

    if current:
        chunks.append(current)

    return chunks


# ── Duration estimation ───────────────────────────────────────────────────────

def estimate_duration(text: str, wpm: int = AVG_WPM) -> float:
    """Return estimated speaking duration in seconds."""
    words = len(text.split())
    return round((words / wpm) * 60, 1)


# ── YouTube metadata ──────────────────────────────────────────────────────────

def generate_metadata(sections: List[Section]) -> dict:
    """
    Build YouTube upload metadata from the list of sections.

    Returns a dict with keys: title, description, tags.
    """
    # Title: first H1 heading, or the first section's title
    title = next(
        (s.title for s in sections if s.level == 1),
        sections[0].title if sections else "Untitled Video",
    )
    # Cap at 100 chars (YouTube limit)
    title = title[:100]

    # Description: section titles as a table of contents + first narration snippet
    toc_lines = [f"{i+1}. {s.title}" for i, s in enumerate(sections)]
    intro = sections[0].narration[:300] + "..." if sections else ""
    description = intro + "\n\n" + "\n".join(toc_lines)

    # Tags: words from titles, de-duplicated, max 500 chars total
    raw_tags: List[str] = []
    for s in sections:
        for word in s.title.split():
            tag = re.sub(r"[^a-zA-Z0-9\- ]", "", word).strip()
            if len(tag) > 2 and tag.lower() not in {t.lower() for t in raw_tags}:
                raw_tags.append(tag)
    tags = raw_tags[:30]  # YouTube accepts up to ~500 chars of tags

    logger.info("Metadata generated — title: '%s', %d tags.", title, len(tags))
    return {"title": title, "description": description, "tags": tags}


# ── Main enrichment entry point ───────────────────────────────────────────────

def process_sections(sections: List[Section]) -> tuple[List[Section], dict]:
    """
    Clean narrations, compute chunks/durations and generate YouTube metadata.
    Returns the enriched section list and the metadata dict.
    """
    for s in sections:
        s.narration = clean_narration(s.narration)
        dur = estimate_duration(s.narration)
        logger.debug("Section %d '%s': ~%.1fs narration.", s.index, s.title, dur)

    metadata = generate_metadata(sections)
    return sections, metadata
