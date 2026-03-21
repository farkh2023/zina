"""
extraction_markdown.py — Parse a Markdown script into structured sections.

Each section becomes one "slide" in the final video:
  - title        : heading text (H1 / H2 / H3)
  - body         : raw Markdown body
  - narration    : plain-text body (markup stripped) — fed to TTS
  - image_prompt : visual description for DALL-E
                   (taken from <!-- img: ... --> comment, or auto-generated)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class Section:
    index: int
    level: int          # heading depth: 1, 2 or 3
    title: str
    body: str           # raw Markdown
    narration: str      # plain text for TTS
    image_prompt: str   # prompt for DALL-E


# ── Internal helpers ──────────────────────────────────────────────────────────

_IMG_COMMENT_RE = re.compile(r"<!--\s*img:\s*(.+?)\s*-->", re.DOTALL)
_HEADING_RE     = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
_LINK_RE        = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MARKUP_RE      = re.compile(r"[*_`~#>\[\]()]")


def _strip_markup(text: str) -> str:
    """Return plain text from Markdown source."""
    text = _LINK_RE.sub(r"\1", text)
    text = _MARKUP_RE.sub("", text)
    return " ".join(text.split())


def _first_sentence(text: str) -> str:
    clean = _strip_markup(text)
    for sep in (".", "!", "?"):
        pos = clean.find(sep)
        if pos != -1:
            return clean[: pos + 1].strip()
    return clean[:120].strip()


def _build_image_prompt(title: str, body: str) -> str:
    m = _IMG_COMMENT_RE.search(body)
    if m:
        return m.group(1).strip()
    first = _first_sentence(body)
    base  = f"{title}. {first}" if first else title
    return f"Cinematic illustration: {base}"


# ── Public API ────────────────────────────────────────────────────────────────

def load_script(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {path}")
    content = path.read_text(encoding="utf-8")
    logger.info("Loaded script '%s' (%d chars).", path.name, len(content))
    return content


def extract_sections(markdown_text: str) -> List[Section]:
    """Split Markdown into sections delimited by H1/H2/H3 headings."""
    lines  = markdown_text.splitlines(keepends=True)
    chunks: list[tuple[int, str, list[str]]] = []

    cur_level: int | None = None
    cur_title: str        = ""
    cur_body:  list[str]  = []

    for line in lines:
        m = _HEADING_RE.match(line.rstrip())
        if m:
            if cur_title:
                chunks.append((cur_level, cur_title, cur_body))
            cur_level = len(m.group(1))
            cur_title = m.group(2).strip()
            cur_body  = []
        else:
            if cur_title:
                cur_body.append(line)

    if cur_title:
        chunks.append((cur_level, cur_title, cur_body))

    if not chunks:
        logger.warning("No headings found — treating whole document as one section.")
        plain = _strip_markup(markdown_text)
        return [
            Section(
                index=0, level=2, title="Introduction",
                body=markdown_text.strip(), narration=plain,
                image_prompt=_build_image_prompt("Introduction", markdown_text),
            )
        ]

    sections: List[Section] = []
    for idx, (level, title, body_lines) in enumerate(chunks):
        body     = "".join(body_lines).strip()
        sections.append(
            Section(
                index=idx, level=level, title=title,
                body=body, narration=_strip_markup(body),
                image_prompt=_build_image_prompt(title, body),
            )
        )
        logger.debug("  [%d] H%d '%s'", idx, level, title)

    logger.info("Extracted %d sections.", len(sections))
    return sections
