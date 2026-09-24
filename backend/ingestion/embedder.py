import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# Environment
# ============================================================

env_path = Path(__file__).resolve().parents[1] / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


# ============================================================
# Gemini Embedding 2 Configuration
# ============================================================

MODEL_NAME = "gemini-embedding-2"
OUTPUT_DIMENSIONALITY = 3072

_client = None


# ============================================================
# Gemini Client
# ============================================================

def get_genai_client():
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        _client = genai.Client(api_key=api_key)

    return _client


# ============================================================
# Embed Documents
# ============================================================

def create_embeddings(
    texts: list[str],
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> list[list[float]]:
    """
    Create Gemini Embedding 2 vectors for document chunks.

    Each document is embedded separately using
    RETRIEVAL_DOCUMENT.
    """

    if not texts:
        return []

    client = get_genai_client()

    embeddings = []

    for text in texts:
        if not text or not text.strip():
            continue

        last_error = None

        for attempt in range(max_retries):
            try:
                result = client.models.embed_content(
                    model=MODEL_NAME,
                    contents=text,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=OUTPUT_DIMENSIONALITY,
                    ),
                )

                if not result.embeddings:
                    raise ValueError(
                        "Gemini returned no embedding for document."
                    )

                vector = result.embeddings[0].values

                if not vector:
                    raise ValueError(
                        "Gemini returned an empty document embedding."
                    )

                embeddings.append(vector)
                break

            except Exception as exc:
                last_error = exc

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        else:
            raise RuntimeError(
                f"Failed to create document embedding after "
                f"{max_retries} attempts."
            ) from last_error

    return embeddings


# ============================================================
# Embed Query
# ============================================================

def embed_query(
    query: str,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> list[float]:
    """
    Create a Gemini Embedding 2 vector for a user query.

    Uses RETRIEVAL_QUERY so it can be searched against
    documents embedded with RETRIEVAL_DOCUMENT.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    client = get_genai_client()

    last_error = None

    for attempt in range(max_retries):
        try:
            result = client.models.embed_content(
                model=MODEL_NAME,
                contents=query,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=OUTPUT_DIMENSIONALITY,
                ),
            )

            if not result.embeddings:
                raise ValueError(
                    "Gemini returned no embedding for query."
                )

            vector = result.embeddings[0].values

            if not vector:
                raise ValueError(
                    "Gemini returned an empty query embedding."
                )

            return vector

        except Exception as exc:
            last_error = exc

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    raise RuntimeError(
        f"Failed to create query embedding after "
        f"{max_retries} attempts."
    ) from last_error