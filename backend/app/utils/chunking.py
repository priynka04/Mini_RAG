"""Text chunking logic (placeholder)."""


def chunk_text(text: str, size: int = 500):
    """Naive chunker by character length."""
    return [text[i:i+size] for i in range(0, len(text), size)]
