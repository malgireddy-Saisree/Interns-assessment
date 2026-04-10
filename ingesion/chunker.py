"""
chunker.py
Splits a document's text into overlapping chunks suitable for embedding.
Uses a simple recursive character splitter — no heavy framework required.
"""
from __future__ import annotations
 
import re
from dataclasses import dataclass, field
from typing import List
 
from ingestion.blob_loader import BlobDocument
 
 
@dataclass
class Chunk:
    chunk_id: str          # e.g. "my_doc.pdf::0"
    source: str            # blob name
    text: str              # chunk text
    metadata: dict = field(default_factory=dict)
 
 
class RecursiveChunker:
    """
    Splits text by trying paragraph breaks, then sentence breaks,
    then hard character limits — in that priority order.
 
    Parameters
    ----------
    chunk_size : int
        Target maximum characters per chunk.
    chunk_overlap : int
        Number of characters to repeat at the start of the next chunk
        to preserve cross-boundary context.
    """
 
    SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]
 
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
 
    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
 
    def chunk_document(self, doc: BlobDocument) -> List[Chunk]:
        """Return a list of Chunk objects for a single BlobDocument."""
        raw_chunks = self._split(doc.content)
        chunks: List[Chunk] = []
        for i, text in enumerate(raw_chunks):
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.name}::{i}",
                    source=doc.name,
                    text=text,
                    metadata={
                        **doc.metadata,
                        "chunk_index": i,
                        "chunk_count": len(raw_chunks),  # back-filled below
                    },
                )
            )
        # Back-fill accurate chunk_count now that we know the total
        total = len(chunks)
        for c in chunks:
            c.metadata["chunk_count"] = total
        return chunks
 
    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
 
    def _split(self, text: str) -> List[str]:
        """Recursively split *text* until all pieces fit within chunk_size."""
        return self._recursive_split(text, self.SEPARATORS)
 
    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
 
        sep = separators[0] if separators else ""
        rest = separators[1:]
 
        pieces = text.split(sep) if sep else list(text)
        merged: List[str] = []
        current = ""
 
        for piece in pieces:
            candidate = (current + sep + piece) if current else piece
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    merged.append(current)
                # If the piece itself is too large, recurse with the next sep
                if len(piece) > self.chunk_size and rest:
                    merged.extend(self._recursive_split(piece, rest))
                    current = ""
                else:
                    current = piece
 
        if current:
            merged.append(current)
 
        # Apply overlap: prepend tail of previous chunk to each chunk
        if self.chunk_overlap == 0 or len(merged) <= 1:
            return merged
 
        overlapped: List[str] = [merged[0]]
        for i in range(1, len(merged)):
            tail = merged[i - 1][-self.chunk_overlap :]
            overlapped.append(tail + merged[i])
        return overlapped
 
 