import re
import unicodedata


def clean_text(text):
    """
    Clean extracted PDF text while preserving
    meaningful paragraph and line structure.
    """

    if not text:
        return ""

    # Normalize Unicode text.
    # Helps keep Tamil and other Unicode text consistent.
    text = unicodedata.normalize("NFC", text)

    # Replace tabs and repeated spaces with a single space.
    # Newlines are intentionally preserved here.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces at the beginning/end of each line.
    text = re.sub(r" *\n *", "\n", text)

    # Collapse excessive blank lines into a maximum
    # of one blank line between paragraphs.
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Remove leading/trailing whitespace.
    text = text.strip()

    return text