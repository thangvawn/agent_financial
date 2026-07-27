"""Chunking and section packing utility for Telegram message size limit (4096 chars)."""

from __future__ import annotations

MAX_CHUNK_CHARS = 3800


def pack_sections(sections: list[str], max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Packs text sections into message chunks safely below max_chars."""
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    for sec in sections:
        sec_len = len(sec)
        if current_len + sec_len + 2 > max_chars:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [sec]
                current_len = sec_len
            else:
                chunks.append(sec)
                current_chunk = []
                current_len = 0
        else:
            current_chunk.append(sec)
            current_len += sec_len + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks
