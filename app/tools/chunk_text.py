"""
Text chunking with configurable size, overlap, and sentence-boundary awareness.
"""

import logging
from app.config import settings

logger = logging.getLogger(__name__)


def _find_sentence_boundary(text: str, target_pos: int, window: int = 200) -> int:
    """Try to break at the nearest sentence boundary (. ! ? or newline)."""
    search_start = max(0, target_pos - window)
    search_region = text[search_start:target_pos]

    # Search backwards for sentence-ending punctuation followed by space/newline
    for delim in ["\n\n", "\n", ". ", "! ", "? "]:
        last_pos = search_region.rfind(delim)
        if last_pos != -1:
            return search_start + last_pos + len(delim)

    return target_pos  # Fallback: hard split


def chunk_text(
    text_units: list[dict],
    chunk_size_chars: int | None = None,
    overlap_chars: int | None = None,
) -> list[dict]:
    """Split text units into overlapping chunks with metadata preserved."""
    chunk_size = chunk_size_chars or settings.chunk_size_chars
    overlap = overlap_chars or settings.overlap_chars

    chunks = []
    chunk_index = 0

    for unit in text_units:
        text = unit.get("text", "").strip()
        if not text:
            continue
        start = 0
        while start < len(text):
            raw_end = min(start + chunk_size, len(text))

            # Try to break at a sentence boundary
            if raw_end < len(text):
                end = _find_sentence_boundary(text, raw_end)
            else:
                end = raw_end

            chunk_body = text[start:end].strip()
            if chunk_body:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_body,
                    "page_number": unit.get("page_number"),
                    "slide_number": unit.get("slide_number"),
                    "section_title": unit.get("section_title"),
                    "source_type": unit.get("source_type"),
                })
                chunk_index += 1

            if end >= len(text):
                break
            start = max(0, end - overlap)

    logger.info("Produced %d chunks from %d text units", len(chunks), len(text_units))
    return chunks
