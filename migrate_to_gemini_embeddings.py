"""
migrate_to_gemini_embeddings.py
===============================

Migrates agriculture document chunks from the BGE-M3 collection
('agriguide_documents') to the new Gemini Embedding 2 collection
('agriguide_gemini_embeddings') in Qdrant Cloud.

Rules & Safety:
- Preserves existing document IDs and payloads.
- Generates new 3072-dimensional embeddings using Gemini Embedding 2.
- Uses RETRIEVAL_DOCUMENT for document chunks.
- Creates the target collection with 3072 dimensions and COSINE distance.
- NEVER modifies or deletes the original 'agriguide_documents' collection.
- Safe to run multiple times because Qdrant upsert uses the original IDs.
- Never prints or exposes API keys.

Usage:
    python migrate_to_gemini_embeddings.py
"""

import sys
import io
import os
import time
import math
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# Windows UTF-8 terminal support
# ============================================================

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace"
    )

if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding="utf-8",
        errors="replace"
    )


# ============================================================
# Load environment variables
# ============================================================

env_path = Path(__file__).resolve().parent / "backend" / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()


if not GEMINI_API_KEY:
    sys.exit("[ERROR] GEMINI_API_KEY is not set.")

if not QDRANT_URL:
    sys.exit("[ERROR] QDRANT_URL is not set.")

if not QDRANT_API_KEY:
    sys.exit("[ERROR] QDRANT_API_KEY is not set.")


# ============================================================
# Configuration
# ============================================================

SOURCE_COLLECTION = "agriguide_documents"
TARGET_COLLECTION = "agriguide_gemini_embeddings"

EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIM = 3072
EMBED_TASK_TYPE = "RETRIEVAL_DOCUMENT"

# This controls how many chunks the migration processes
# in one migration batch.
BATCH_SIZE = 10

MAX_RETRIES = 3
RETRY_DELAY = 3.0


# ============================================================
# Utility
# ============================================================

def banner(text: str):
    print("\n" + "=" * 65)
    print(f"  {text}")
    print("=" * 65)


# ============================================================
# Gemini Embedding 2
# ============================================================

def get_gemini_embeddings_batch(
    genai_client,
    texts,
    model=EMBEDDING_MODEL,
    task_type=EMBED_TASK_TYPE,
):
    """
    Generate one Gemini Embedding 2 vector for each text.

    IMPORTANT:
    Gemini Embedding 2 should receive each text separately.
    Multiple inputs in one embed_content call can result in
    an aggregated embedding.

    Each document therefore gets its own API request.

    Uses:
        RETRIEVAL_DOCUMENT

    Returns:
        list[list[float]]
    """

    from google.genai import types

    embeddings = []

    for text_index, text in enumerate(texts, start=1):

        if not text or not text.strip():
            raise ValueError(
                f"Empty document text at batch item {text_index}."
            )

        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                response = genai_client.models.embed_content(
                    model=model,
                    contents=text,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=EMBEDDING_DIM,
                    ),
                )

                if not response.embeddings:
                    raise ValueError(
                        "Gemini returned no embedding."
                    )

                vector = response.embeddings[0].values

                if not vector:
                    raise ValueError(
                        "Gemini returned an empty embedding."
                    )

                if len(vector) != EMBEDDING_DIM:
                    raise ValueError(
                        f"Unexpected embedding dimension: "
                        f"{len(vector)}. "
                        f"Expected {EMBEDDING_DIM}."
                    )

                embeddings.append(vector)

                break

            except Exception as exc:

                last_error = exc

                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        f"Failed to embed document "
                        f"{text_index} after "
                        f"{MAX_RETRIES} attempts."
                    ) from last_error

                sleep_sec = RETRY_DELAY * (2 ** (attempt - 1))

                print(
                    f"\n    [WARN] Embedding item "
                    f"{text_index} attempt {attempt} failed: "
                    f"{exc}"
                )

                print(
                    f"    Retrying in {sleep_sec:.1f}s..."
                )

                time.sleep(sleep_sec)

    return embeddings


# ============================================================
# Main Migration
# ============================================================

def main():

    banner("AgriGuide: Migration to Gemini Embedding 2")


    # ========================================================
    # Import clients
    # ========================================================

    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
    )
    from google import genai


    # ========================================================
    # Connect to services
    # ========================================================

    print(
        "[1] Connecting to Qdrant Cloud & Google GenAI..."
    )

    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60,
    )

    genai_client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    print("    Qdrant Cloud: Connected")
    print("    Google GenAI: Client initialized")


    # ========================================================
    # STEP 1
    # Verify original BGE-M3 collection
    # ========================================================

    banner("STEP 1: Verify Backup / Source Collection")

    collections = [
        c.name
        for c in qdrant.get_collections().collections
    ]

    print(
        f"  Existing collections: {collections}"
    )

    if SOURCE_COLLECTION not in collections:
        sys.exit(
            f"  [ERROR] Source collection "
            f"'{SOURCE_COLLECTION}' not found "
            f"in Qdrant Cloud!"
        )

    src_info = qdrant.get_collection(
        SOURCE_COLLECTION
    )

    src_count = src_info.points_count

    print(
        f"  Source collection '{SOURCE_COLLECTION}':"
    )

    print(
        f"    - Point count: {src_count}"
    )

    print(
        f"    - Vector dim : "
        f"{src_info.config.params.vectors.size}"
    )

    print(
        f"    - Distance   : "
        f"{src_info.config.params.vectors.distance.name}"
    )

    print(
        "  NOTE: This source collection "
        "will NOT be modified or deleted."
    )


    # ========================================================
    # STEP 2
    # Read existing points and payloads
    # ========================================================

    banner(
        "STEP 2: Read Agriculture Document Chunks from Source"
    )

    print(
        f"  Fetching all points and payloads "
        f"from '{SOURCE_COLLECTION}'..."
    )

    all_points = []

    offset = None

    while True:

        points_batch, next_offset = qdrant.scroll(
            collection_name=SOURCE_COLLECTION,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not points_batch:
            break

        all_points.extend(points_batch)

        if next_offset is None:
            break

        offset = next_offset


    total_chunks = len(all_points)

    print(
        f"  Total chunks found: {total_chunks}"
    )

    if total_chunks == 0:
        sys.exit(
            "  [ERROR] No chunks found "
            "in source collection."
        )


    # ========================================================
    # Validate sample payload
    # ========================================================

    sample_point = all_points[0]

    print(
        f"  Sample Chunk ID: {sample_point.id}"
    )

    if sample_point.payload:

        print(
            "  Sample Payload keys: "
            f"{list(sample_point.payload.keys())}"
        )

        for key, value in sample_point.payload.items():

            if (
                isinstance(value, str)
                and len(value) > 60
            ):
                value_string = value[:60] + "..."
            else:
                value_string = str(value)

            print(
                f"    - {key}: {value_string}"
            )


    # ========================================================
    # STEP 3
    # Create target collection
    # ========================================================

    banner(
        "STEP 3: Create Target Collection: "
        + TARGET_COLLECTION
    )

    if TARGET_COLLECTION not in collections:

        print(
            f"  Creating new collection "
            f"'{TARGET_COLLECTION}'..."
        )

        qdrant.create_collection(
            collection_name=TARGET_COLLECTION,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )

        print(
            f"  Collection '{TARGET_COLLECTION}' "
            f"created successfully!"
        )

        print(
            f"  Dimension: {EMBEDDING_DIM}"
        )

        print(
            "  Distance: COSINE"
        )

    else:

        target_info = qdrant.get_collection(
            TARGET_COLLECTION
        )

        target_dimension = (
            target_info.config.params.vectors.size
        )

        target_distance = (
            target_info.config.params.vectors.distance.name
        )

        print(
            f"  Collection '{TARGET_COLLECTION}' "
            f"already exists."
        )

        print(
            f"  Existing points: "
            f"{target_info.points_count}"
        )

        print(
            f"  Vector dimension: "
            f"{target_dimension}"
        )

        print(
            f"  Distance: "
            f"{target_distance}"
        )

        if target_dimension != EMBEDDING_DIM:

            sys.exit(
                f"[ERROR] Existing target collection "
                f"dimension {target_dimension} "
                f"does not match expected "
                f"{EMBEDDING_DIM}."
            )


    # ========================================================
    # STEP 4
    # Generate embeddings and upload
    # ========================================================

    banner(
        "STEP 4: Generate Gemini Embedding 2 "
        "Vectors & Upload"
    )

    print(
        f"  Model       : {EMBEDDING_MODEL}"
    )

    print(
        f"  Task Type   : {EMBED_TASK_TYPE}"
    )

    print(
        f"  Dimension   : {EMBEDDING_DIM}"
    )

    print(
        f"  Batch Size  : {BATCH_SIZE}"
    )

    print()

    total_batches = math.ceil(
        total_chunks / BATCH_SIZE
    )

    successfully_embedded = 0
    successfully_uploaded = 0

    failed_chunks = []


    # ========================================================
    # Process batches
    # ========================================================

    for batch_index in range(total_batches):

        start_index = (
            batch_index * BATCH_SIZE
        )

        end_index = min(
            start_index + BATCH_SIZE,
            total_chunks,
        )

        batch = all_points[
            start_index:end_index
        ]

        batch_number = batch_index + 1

        print(
            f"\n  Processing batch "
            f"{batch_number}/{total_batches}"
        )

        print(
            f"  Chunks: "
            f"{start_index + 1}-{end_index}"
        )


        # ----------------------------------------------------
        # Extract document text
        # ----------------------------------------------------

        batch_texts = []

        for point in batch:

            text = ""

            if point.payload:
                text = point.payload.get(
                    "text",
                    ""
                )

            if not text or not text.strip():

                failed_chunks.append(
                    {
                        "id": point.id,
                        "error": "Empty document text",
                    }
                )

                continue

            batch_texts.append(text)


        if len(batch_texts) != len(batch):

            print(
                "  [WARN] Some chunks have "
                "empty text and will be skipped."
            )


        # ----------------------------------------------------
        # Generate Gemini embeddings
        # ----------------------------------------------------

        try:

            vectors = get_gemini_embeddings_batch(
                genai_client=genai_client,
                texts=batch_texts,
                model=EMBEDDING_MODEL,
                task_type=EMBED_TASK_TYPE,
            )

            successfully_embedded += len(vectors)

        except Exception as exc:

            print(
                f"\n  [ERROR] Failed to embed "
                f"batch {batch_number}/"
                f"{total_batches}: {exc}"
            )

            for point in batch:

                failed_chunks.append(
                    {
                        "id": point.id,
                        "error": str(exc),
                    }
                )

            continue


        # ----------------------------------------------------
        # Create Qdrant points
        # ----------------------------------------------------

        qdrant_points = []

        vector_index = 0

        for point in batch:

            text = ""

            if point.payload:
                text = point.payload.get(
                    "text",
                    ""
                )

            if not text or not text.strip():
                continue

            vector = vectors[vector_index]

            vector_index += 1

            qdrant_points.append(
                PointStruct(
                    id=point.id,
                    vector=vector,
                    payload=point.payload,
                )
            )


        # ----------------------------------------------------
        # Upload to Qdrant
        # ----------------------------------------------------

        try:

            qdrant.upsert(
                collection_name=TARGET_COLLECTION,
                points=qdrant_points,
                wait=True,
            )

            successfully_uploaded += (
                len(qdrant_points)
            )

        except Exception as exc:

            print(
                f"\n  [ERROR] Failed to upload "
                f"batch {batch_number}/"
                f"{total_batches}: {exc}"
            )

            for point in batch:

                failed_chunks.append(
                    {
                        "id": point.id,
                        "error": str(exc),
                    }
                )

            continue


        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        percentage = (
            end_index / total_chunks
        ) * 100

        completed_blocks = int(
            percentage // 2.5
        )

        progress_bar = (
            "#"
            * completed_blocks
            + "."
            * (40 - completed_blocks)
        )

        print(
            f"\r  [{progress_bar}] "
            f"{percentage:5.1f}% "
            f"({end_index}/{total_chunks} chunks)",
            end="",
            flush=True,
        )


    print(
        "\n\n  Embedding and upload completed!"
    )


    # ========================================================
    # STEP 5
    # Verify target collection
    # ========================================================

    banner(
        "STEP 5: Target Collection Verification"
    )

    target_info = qdrant.get_collection(
        TARGET_COLLECTION
    )

    target_count = target_info.points_count

    target_dimension = (
        target_info.config.params.vectors.size
    )

    target_distance = (
        target_info.config.params.vectors.distance.name
    )

    print(
        f"  Target collection : "
        f"{TARGET_COLLECTION}"
    )

    print(
        f"  Point count       : "
        f"{target_count} "
        f"(expected {total_chunks})"
    )

    print(
        f"  Vector dimension  : "
        f"{target_dimension} "
        f"(expected {EMBEDDING_DIM})"
    )

    print(
        f"  Distance metric   : "
        f"{target_distance} "
        f"(expected COSINE)"
    )


    # ========================================================
    # STEP 6
    # Verify old collection untouched
    # ========================================================

    banner(
        "STEP 6: Verify Backup Collection Untouched"
    )

    backup_info = qdrant.get_collection(
        SOURCE_COLLECTION
    )

    print(
        f"  Backup collection : "
        f"{SOURCE_COLLECTION}"
    )

    print(
        f"  Backup point count: "
        f"{backup_info.points_count} "
        f"(remains {src_count})"
    )

    print(
        f"  Backup vector dim : "
        f"{backup_info.config.params.vectors.size}"
    )

    print(
        "  Status             : UNTOUCHED [SAFE]"
    )


    # ========================================================
    # STEP 7
    # Test retrieval using Gemini Embedding 2
    # ========================================================

    banner(
        "STEP 7: Test Retrieval on New Collection"
    )

    from google.genai import types

    test_query = (
        "What are the recommended practices "
        "for rice cultivation?"
    )

    print(
        f"  Query: '{test_query}'"
    )


    # Use RETRIEVAL_QUERY for the search query.
    query_response = (
        genai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=test_query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=EMBEDDING_DIM,
            ),
        )
    )

    if not query_response.embeddings:

        sys.exit(
            "[ERROR] Gemini returned no "
            "query embedding."
        )


    query_vector = (
        query_response.embeddings[0].values
    )


    if len(query_vector) != EMBEDDING_DIM:

        sys.exit(
            f"[ERROR] Query vector dimension "
            f"{len(query_vector)} does not match "
            f"expected {EMBEDDING_DIM}."
        )


    search_result = qdrant.query_points(
        collection_name=TARGET_COLLECTION,
        query=query_vector,
        limit=2,
        with_payload=True,
    )


    print(
        f"  Retrieved "
        f"{len(search_result.points)} "
        f"points successfully:"
    )


    for index, hit in enumerate(
        search_result.points,
        start=1,
    ):

        document_name = (
            hit.payload.get("document_name")
            if hit.payload
            else None
        )

        category = (
            hit.payload.get("category")
            if hit.payload
            else None
        )

        print(
            f"    [{index}] "
            f"ID={hit.id} "
            f"Score={hit.score:.4f} "
            f"Doc={document_name} "
            f"Cat={category}"
        )


    # ========================================================
    # STEP 8
    # Final migration summary
    # ========================================================

    banner(
        "MIGRATION SUMMARY REPORT"
    )

    print(
        f"  Total chunks found           : "
        f"{total_chunks}"
    )

    print(
        f"  Successfully embedded chunks : "
        f"{successfully_embedded}"
    )

    print(
        f"  Successfully uploaded points : "
        f"{successfully_uploaded}"
    )

    print(
        f"  Failed chunks                : "
        f"{len(failed_chunks)}"
    )

    print(
        f"  Old collection "
        f"'{SOURCE_COLLECTION}'        : "
        f"{backup_info.points_count} points preserved"
    )

    print(
        f"  New collection "
        f"'{TARGET_COLLECTION}' : "
        f"{target_count} points active"
    )

    print(
        f"  Vector dimension             : "
        f"{target_dimension}"
    )

    print(
        f"  Distance metric              : "
        f"{target_distance}"
    )

    print("=" * 65)


    # ========================================================
    # Final result
    # ========================================================

    if failed_chunks:

        print(
            "\n  [WARN] Some chunks failed:"
        )

        for failed_chunk in failed_chunks:

            print(
                f"    - Chunk ID "
                f"{failed_chunk['id']}: "
                f"{failed_chunk['error']}"
            )

        sys.exit(
            1
        )

    else:

        if target_count != total_chunks:

            print(
                "\n  [ERROR] Target point count "
                "does not match source point count."
            )

            sys.exit(1)


        if target_dimension != EMBEDDING_DIM:

            print(
                "\n  [ERROR] Target vector dimension "
                "does not match Gemini Embedding 2."
            )

            sys.exit(1)


        if backup_info.points_count != src_count:

            print(
                "\n  [ERROR] Backup collection point "
                "count changed unexpectedly."
            )

            sys.exit(1)


        print(
            "\n  MIGRATION COMPLETED SUCCESSFULLY!\n"
        )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()