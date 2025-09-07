from __future__ import annotations

from typing import Any, Dict, List


def parse_txt(text: str) -> List[Dict[str, Any]]:
    """
    Return a list of pages-like dicts: {content, page, meta}
    For plain text, treat as a single page.
    """
    return [
        {
            "content": text,
            "page": 1,
            "meta": {"source": "txt"},
        }
    ]

