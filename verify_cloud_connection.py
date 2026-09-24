"""
verify_cloud_connection.py
Verifies the backend is correctly connected to Qdrant Cloud.
Run from project root: python verify_cloud_connection.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("backend") / ".env")

QDRANT_URL     = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION     = "agriguide_documents"
EXPECTED_DIM   = 1024
EXPECTED_DIST  = "COSINE"
EXPECTED_POINTS = 172

print("=" * 58)
print("  AgriGuide — Qdrant Cloud Connection Verification")
print("=" * 58)

# 1. Check env vars
print("\n[1] Environment variables")
if not QDRANT_URL:
    sys.exit("  FAIL: QDRANT_URL is not set")
if not QDRANT_API_KEY:
    sys.exit("  FAIL: QDRANT_API_KEY is not set")
print(f"  QDRANT_URL  : {QDRANT_URL}")
print(f"  QDRANT_API_KEY : [hidden]")
print("  PASS")

# 2. Connect
print("\n[2] Qdrant Cloud connection")
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    print(f"  Connected OK  |  Collections: {names}")
    print("  PASS")
except Exception as e:
    sys.exit(f"  FAIL: {e}")

# 3. Collection exists
print("\n[3] Collection exists")
if COLLECTION not in names:
    sys.exit(f"  FAIL: '{COLLECTION}' not found in cloud. Found: {names}")
print(f"  '{COLLECTION}' found")
print("  PASS")

# 4. Point count + vector config
print("\n[4] Collection config & point count")
info     = client.get_collection(COLLECTION)
count    = info.points_count
vec      = info.config.params.vectors
dim      = vec.size
distance = vec.distance.name

print(f"  Point count  : {count}  (expected {EXPECTED_POINTS})")
print(f"  Vector dim   : {dim}    (expected {EXPECTED_DIM})")
print(f"  Distance     : {distance} (expected {EXPECTED_DIST})")

checks = [
    (count == EXPECTED_POINTS, f"Point count {count} != {EXPECTED_POINTS}"),
    (dim   == EXPECTED_DIM,    f"Dimension {dim} != {EXPECTED_DIM}"),
    (distance == EXPECTED_DIST, f"Distance {distance} != {EXPECTED_DIST}"),
]
for ok, msg in checks:
    if not ok:
        print(f"  FAIL: {msg}")
        sys.exit(1)
print("  PASS")

# 5. Test retrieval (random vector)
print("\n[5] Test retrieval")
try:
    test_vec = np.random.rand(EXPECTED_DIM).tolist()
    result = client.query_points(
        collection_name=COLLECTION,
        query=test_vec,
        limit=3,
        with_payload=True,
    )
    hits = result.points
    if not hits:
        print("  FAIL: query returned 0 results")
        sys.exit(1)
    h = hits[0]
    payload_keys = list(h.payload.keys()) if h.payload else []
    print(f"  Results returned : {len(hits)}")
    print(f"  Top ID           : {h.id}")
    print(f"  Top score        : {h.score:.4f}")
    print(f"  Payload fields   : {payload_keys}")
    print("  PASS")
except Exception as e:
    sys.exit(f"  FAIL: {e}")

# Summary
print("\n" + "=" * 58)
print("  SUMMARY")
print("=" * 58)
print(f"  Files changed         : backend/vectorstore/qdrant_db.py")
print(f"  Qdrant connection     : Cloud (PASS)")
print(f"  Collection status     : '{COLLECTION}' exists (PASS)")
print(f"  Point count           : {count} / {EXPECTED_POINTS} (PASS)")
print(f"  Vector dim / distance : {dim} / {distance} (PASS)")
print(f"  Test retrieval        : {len(hits)} result(s) returned (PASS)")
print("=" * 58)
print()
