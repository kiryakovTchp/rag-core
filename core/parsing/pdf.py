from __future__ import annotations

from typing import Any, Dict, List

import fitz  # PyMuPDF
import pymupdf4llm


def parse_pdf(data: bytes) -> List[Dict[str, Any]]:
    """
    Parse PDF bytes using PyMuPDF4LLM / PyMuPDF into pages with content.
    Returns a list of dicts: {content, page, meta}
    """
    pages: List[Dict[str, Any]] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        # Try to use PyMuPDF4LLM helpers for best quality
        try:
            md = pymupdf4llm.to_markdown(doc)
            # Fallback to page-by-page extraction to preserve page numbers
            if not md:
                raise ValueError("empty md")
            # When full-document markdown is produced, split per page markers if present
            # Otherwise, provide a single-page aggregate
            pages.append({"content": md, "page": 1, "meta": {"source": "pdf"}})
        except Exception:
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text")
                pages.append({"content": text, "page": i, "meta": {"source": "pdf"}})
    return pages

