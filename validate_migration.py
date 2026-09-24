"""
validate_migration.py
=====================

Comprehensive validation script for the Gemini Embedding 2 migration.

Tests:
    1. Old BGE-M3 collection is preserved
    2. New Gemini collection exists and has correct dimensions
    3. English retrieval works
    4. Tamil retrieval works
    5. Tamil final answer works
    6. English final answer works
    10. Conversation history works

Important:
    - Old collection: agriguide_documents
    - New collection: agriguide_gemini_embeddings
    - Old collection is NEVER modified
"""

import sys
import io
import os
import re
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# Windows UTF-8 output
# ============================================================

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace",
    )

if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding="utf-8",
        errors="replace",
    )


# ============================================================
# Environment
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

env_path = PROJECT_ROOT / "backend" / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()


if not QDRANT_URL:
    raise RuntimeError("QDRANT_URL is not configured.")

if not QDRANT_API_KEY:
    raise RuntimeError("QDRANT_API_KEY is not configured.")


# ============================================================
# Expected collections
# ============================================================

OLD_COLLECTION = "agriguide_documents"
NEW_COLLECTION = "agriguide_gemini_embeddings"

EXPECTED_OLD_DIMENSION = 1024
EXPECTED_NEW_DIMENSION = 3072

EXPECTED_DISTANCE = "COSINE"


# ============================================================
# Qdrant
# ============================================================

from qdrant_client import QdrantClient

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60,
)


# ============================================================
# Project imports
# ============================================================

from backend.retrieval.retriever import retrieve_relevant_chunks
from backend.rag.chat import AgriGuideChat


# ============================================================
# Helper
# ============================================================

def print_header(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def get_collection_info(collection_name: str):
    return qdrant.get_collection(collection_name)


def get_collection_names():
    return [
        collection.name
        for collection in qdrant.get_collections().collections
    ]


# ============================================================
# TEST 1
# ============================================================

def test_1_old_collection():
    print_header(
        "TEST 1: Verify Old BGE-M3 Collection Is Preserved"
    )

    collections = get_collection_names()

    assert OLD_COLLECTION in collections, (
        f"Old collection '{OLD_COLLECTION}' not found!"
    )

    info = get_collection_info(OLD_COLLECTION)

    count = info.points_count

    dim = info.config.params.vectors.size

    distance = (
        info.config.params.vectors.distance.name
    )

    print(
        f"  Collection name : {OLD_COLLECTION}"
    )

    print(
        f"  Point count     : {count}"
    )

    print(
        f"  Vector dimension: {dim}"
    )

    print(
        f"  Distance metric : {distance}"
    )

    assert count > 0, (
        "Old collection contains no points!"
    )

    assert dim == EXPECTED_OLD_DIMENSION, (
        f"Expected old dimension "
        f"{EXPECTED_OLD_DIMENSION}, got {dim}"
    )

    assert distance == EXPECTED_DISTANCE, (
        f"Expected COSINE distance, got {distance}"
    )

    print(
        "  Old collection status: PRESERVED"
    )

    print(
        "  RESULT: PASS"
    )

    return count, dim, distance


# ============================================================
# TEST 2
# ============================================================

def test_2_new_collection():
    print_header(
        "TEST 2: Verify New Gemini Embedding 2 Collection"
    )

    collections = get_collection_names()

    assert NEW_COLLECTION in collections, (
        f"New collection '{NEW_COLLECTION}' not found!"
    )

    info = get_collection_info(NEW_COLLECTION)

    count = info.points_count

    dim = info.config.params.vectors.size

    distance = (
        info.config.params.vectors.distance.name
    )

    print(
        f"  Collection name : {NEW_COLLECTION}"
    )

    print(
        f"  Point count     : {count}"
    )

    print(
        f"  Vector dimension: {dim}"
    )

    print(
        f"  Distance metric : {distance}"
    )

    assert count > 0, (
        "New Gemini collection contains no points!"
    )

    assert dim == EXPECTED_NEW_DIMENSION, (
        f"Expected Gemini dimension "
        f"{EXPECTED_NEW_DIMENSION}, got {dim}"
    )

    assert distance == EXPECTED_DISTANCE, (
        f"Expected COSINE distance, got {distance}"
    )

    print(
        "  Gemini collection status: VALID"
    )

    print(
        "  RESULT: PASS"
    )

    return count, dim, distance


# ============================================================
# TEST 3
# ============================================================

def test_3_english_retrieval():
    print_header(
        "TEST 3: English Retrieval Test"
    )

    query = (
        "What are the recommended practices "
        "for rice cultivation?"
    )

    print(
        f"  Query: {query}"
    )

    hits = retrieve_relevant_chunks(
        query,
        top_k=3,
    )

    assert hits, (
        "No chunks returned for English query!"
    )

    print(
        f"  Retrieved chunks: {len(hits)}"
    )

    for index, hit in enumerate(
        hits,
        start=1,
    ):

        payload = hit.payload or {}

        document_name = payload.get(
            "document_name",
            "Unknown",
        )

        category = payload.get(
            "category",
            "Unknown",
        )

        page_number = payload.get(
            "page_number",
            "Unknown",
        )

        text = payload.get(
            "text",
            "",
        )

        print(
            f"\n  Hit {index}:"
        )

        print(
            f"    Score    : {hit.score:.4f}"
        )

        print(
            f"    Document : {document_name}"
        )

        print(
            f"    Category : {category}"
        )

        print(
            f"    Page     : {page_number}"
        )

        print(
            f"    Snippet  : {text[:150]}..."
        )

    print(
        "\n  RESULT: PASS"
    )

    return hits


# ============================================================
# TEST 4
# ============================================================

def test_4_tamil_retrieval():
    print_header(
        "TEST 4: Tamil Retrieval Test"
    )

    query = (
        "நெல் சாகுபடியில் உரங்களை "
        "எப்போது பயன்படுத்த வேண்டும்?"
    )

    print(
        f"  Query: {query}"
    )

    hits = retrieve_relevant_chunks(
        query,
        top_k=3,
    )

    assert hits, (
        "No chunks returned for Tamil query!"
    )

    print(
        f"  Retrieved chunks: {len(hits)}"
    )

    for index, hit in enumerate(
        hits,
        start=1,
    ):

        payload = hit.payload or {}

        document_name = payload.get(
            "document_name",
            "Unknown",
        )

        category = payload.get(
            "category",
            "Unknown",
        )

        page_number = payload.get(
            "page_number",
            "Unknown",
        )

        text = payload.get(
            "text",
            "",
        )

        print(
            f"\n  Hit {index}:"
        )

        print(
            f"    Score    : {hit.score:.4f}"
        )

        print(
            f"    Document : {document_name}"
        )

        print(
            f"    Category : {category}"
        )

        print(
            f"    Page     : {page_number}"
        )

        print(
            f"    Snippet  : {text[:150]}..."
        )

    print(
        "\n  RESULT: PASS"
    )

    return hits


# ============================================================
# TEST 5
# ============================================================

def test_5_tamil_chat():
    print_header(
        "TEST 5: Tamil Final Answer"
    )

    bot = AgriGuideChat()

    query = (
        "நெல் சாகுபடியில் உரங்களை "
        "எப்போது பயன்படுத்த வேண்டும்?"
    )

    print(
        f"  Question: {query}"
    )

    answer = bot.chat(query)

    assert answer, (
        "No answer returned!"
    )

    print(
        "\n  Final Answer:"
    )

    print(
        answer
    )

    has_tamil = bool(
        re.search(
            r"[\u0B80-\u0BFF]",
            answer,
        )
    )

    print(
        f"\n  Contains Tamil characters: "
        f"{has_tamil}"
    )

    assert has_tamil, (
        "Expected Tamil characters "
        "in the final answer!"
    )

    print(
        "  RESULT: PASS"
    )

    return answer


# ============================================================
# TEST 6
# ============================================================

def test_6_english_chat():
    print_header(
        "TEST 6: English Final Answer"
    )

    bot = AgriGuideChat()

    query = (
        "What are the recommended practices "
        "for rice cultivation?"
    )

    print(
        f"  Question: {query}"
    )

    answer = bot.chat(query)

    assert answer, (
        "No answer returned!"
    )

    print(
        "\n  Final Answer:"
    )

    print(
        answer
    )

    assert len(answer.strip()) > 20, (
        "English answer is too short!"
    )

    print(
        "\n  RESULT: PASS"
    )

    return answer


# ============================================================
# TEST 10
# ============================================================

def test_10_conversation_history():
    print_header(
        "TEST 10: Multi-Turn Conversation / History"
    )

    bot = AgriGuideChat()

    # --------------------------------------------------------
    # Turn 1
    # --------------------------------------------------------

    q1 = (
        "How should I prepare land "
        "for tomato cultivation?"
    )

    print(
        f"  Turn 1: {q1}"
    )

    a1 = bot.chat(q1)

    assert a1, (
        "Turn 1 returned no answer!"
    )

    print(
        f"  Turn 1 Crop state    : "
        f"{bot.state.crop}"
    )

    print(
        f"  Turn 1 Subtopic      : "
        f"{bot.state.subtopic}"
    )

    print(
        f"  Turn 1 Answer snippet: "
        f"{a1[:150]}..."
    )


    # --------------------------------------------------------
    # Turn 2
    # --------------------------------------------------------

    q2 = "What about fertilizer?"

    print(
        f"\n  Turn 2 (Follow-up): {q2}"
    )

    a2 = bot.chat(q2)

    assert a2, (
        "Turn 2 returned no answer!"
    )

    print(
        f"  Turn 2 Crop state    : "
        f"{bot.state.crop}"
    )

    print(
        f"  Turn 2 Subtopic      : "
        f"{bot.state.subtopic}"
    )

    print(
        f"  Turn 2 Answer snippet: "
        f"{a2[:150]}..."
    )


    # --------------------------------------------------------
    # Context validation
    # --------------------------------------------------------

    assert bot.state.crop == "tomato", (
        f"Conversation context was not preserved. "
        f"Expected crop 'tomato', "
        f"got '{bot.state.crop}'"
    )

    print(
        "\n  Conversation context preserved."
    )

    print(
        "  RESULT: PASS"
    )

    return a1, a2


# ============================================================
# RUN ALL TESTS
# ============================================================

def run_all_tests():

    print("\n")
    print("=" * 70)
    print(
        "      AGRIGUIDE GEMINI EMBEDDING 2 VALIDATION"
    )
    print("=" * 70)

    print(
        f"\nOld collection : {OLD_COLLECTION}"
    )

    print(
        f"New collection : {NEW_COLLECTION}"
    )

    print(
        f"Old dimension  : {EXPECTED_OLD_DIMENSION}"
    )

    print(
        f"New dimension  : {EXPECTED_NEW_DIMENSION}"
    )


    # ========================================================
    # Test 1
    # ========================================================

    old_count, old_dim, old_distance = (
        test_1_old_collection()
    )


    # ========================================================
    # Test 2
    # ========================================================

    new_count, new_dim, new_distance = (
        test_2_new_collection()
    )


    # ========================================================
    # Important migration consistency check
    # ========================================================

    print_header(
        "MIGRATION CONSISTENCY CHECK"
    )

    print(
        f"  Old collection points: "
        f"{old_count}"
    )

    print(
        f"  New collection points: "
        f"{new_count}"
    )

    assert new_count == old_count, (
        "Point count mismatch between "
        "old and new collections!"
    )

    print(
        "  Point counts match."
    )

    print(
        "  RESULT: PASS"
    )


    # ========================================================
    # Test 3
    # ========================================================

    test_3_english_retrieval()


    # ========================================================
    # Test 4
    # ========================================================

    test_4_tamil_retrieval()


    # ========================================================
    # Test 5
    # ========================================================

    test_5_tamil_chat()


    # ========================================================
    # Test 6
    # ========================================================

    test_6_english_chat()


    # ========================================================
    # Test 10
    # ========================================================

    test_10_conversation_history()


    # ========================================================
    # Final
    # ========================================================

    print("\n")
    print("=" * 70)
    print(
        "       ALL VALIDATION TESTS PASSED"
    )
    print("=" * 70)

    print(
        "\n  Old BGE-M3 collection : PRESERVED"
    )

    print(
        "  New Gemini collection : VALID"
    )

    print(
        "  English retrieval     : PASS"
    )

    print(
        "  Tamil retrieval       : PASS"
    )

    print(
        "  Tamil answer          : PASS"
    )

    print(
        "  English answer        : PASS"
    )

    print(
        "  Conversation history  : PASS"
    )

    print(
        "\n  AgriGuide migration validation "
        "completed successfully!"
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    try:
        run_all_tests()

    except AssertionError as exc:

        print(
            "\n"
            + "=" * 70
        )

        print(
            "VALIDATION FAILED"
        )

        print(
            "=" * 70
        )

        print(
            f"\n  Reason: {exc}"
        )

        sys.exit(1)

    except Exception as exc:

        print(
            "\n"
            + "=" * 70
        )

        print(
            "VALIDATION ERROR"
        )

        print(
            "=" * 70
        )

        print(
            f"\n  Error type: "
            f"{type(exc).__name__}"
        )

        print(
            f"  Error: {exc}"
        )

        sys.exit(1)

    finally:

        try:
            qdrant.close()
        except Exception:
            pass