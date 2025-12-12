import unicodedata

def normalize(text: str) -> str:
    """
    Normalize text to ASCII lowercase, removing accents and extra spaces.
    Used for embeddings & comparisons.
    """
    if not text:
        return ""
    # Normalize to NFKD, encode to ASCII (ignoring non-ASCII), decode, lowercase, and strip
    return (
        unicodedata.normalize("NFKD", str(text))
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .strip()
    )