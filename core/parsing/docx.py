from __future__ import annotations

from typing import Any, Dict, List

from docx import Document as DocxDocument


def parse_docx(data: bytes) -> List[Dict[str, Any]]:
    """
    Parse DOCX bytes using python-docx.
    Returns [{content, page, meta}]. DOCX has no pages; treat as a single unit.
    """
    # python-docx requires a file-like object
    import io

    f = io.BytesIO(data)
    doc = DocxDocument(f)
    parts: list[str] = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            parts.append(text)
    content = "\n\n".join(parts)
    return [
        {
            "content": content,
            "page": 1,
            "meta": {"source": "docx"},
        }
    ]

