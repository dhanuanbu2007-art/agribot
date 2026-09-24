import re


def create_chunks(text, chunk_size=1000, overlap=200):
    """
    Split text into overlapping chunks while trying to preserve
    natural sentence/paragraph boundaries.

    chunk_size:
        Maximum approximate number of characters per chunk.

    overlap:
        Number of characters carried from the previous chunk
        into the next chunk.
    """

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length
        )

        # If this is not the final chunk,
        # try to move the end toward a natural boundary.
        if end < text_length:

            candidate = text[start:end]

            # Prefer paragraph boundary.
            paragraph_break = candidate.rfind("\n\n")

            # Otherwise prefer sentence boundary.
            sentence_matches = list(
                re.finditer(
                    r"[.!?。！？]\s",
                    candidate
                )
            )

            sentence_break = (
                sentence_matches[-1].end()
                if sentence_matches
                else -1
            )

            # Otherwise prefer a normal word boundary.
            space_break = candidate.rfind(" ")

            if paragraph_break > int(chunk_size * 0.6):
                end = start + paragraph_break

            elif sentence_break > int(chunk_size * 0.6):
                end = start + sentence_break

            elif space_break > int(chunk_size * 0.6):
                end = start + space_break

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        # Stop after the final chunk.
        if end >= text_length:
            break

        # Maintain overlap with the previous chunk.
        start = max(
            end - overlap,
            start + 1
        )

    return chunks