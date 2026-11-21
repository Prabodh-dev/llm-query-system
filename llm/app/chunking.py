"""Split page text into overlapping, page-tagged chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    id: int
    page: int
    text: str


def chunk_pages(pages: list[str], size: int = 1000, overlap: int = 150) -> list[Chunk]:
    if size <= 0 or not 0 <= overlap < size // 2:
        raise ValueError("chunk size must be positive and overlap below half of it")

    chunks: list[Chunk] = []
    for page_number, raw in enumerate(pages, start=1):
        text = re.sub(r"\s+", " ", raw).strip()
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                space = text.rfind(" ", start + size // 2, end)
                if space != -1:
                    end = space
            piece = text[start:end].strip()
            if piece:
                chunks.append(Chunk(id=len(chunks), page=page_number, text=piece))
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
            # begin the next chunk on a word boundary
            if text[start - 1] != " ":
                nxt = text.find(" ", start, end)
                if nxt != -1:
                    start = nxt + 1
    return chunks
