"""Document processing & chunking placeholder."""

from typing import List


def process_document(text: str) -> List[str]:
    """Split text into chunks. Replace with real logic."""
    # Simple naive split by paragraphs as placeholder
    return [p.strip() for p in text.split("\n\n") if p.strip()]
