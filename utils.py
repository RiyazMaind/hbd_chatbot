# utils.py

import unicodedata

def normalize(text: str) -> str:
    """
    Normalize text to ASCII lowercase (for embeddings & comparisons).
    """
    if not text:
        return ""
    return (
        unicodedata.normalize("NFKD", str(text))
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .strip()
    )
