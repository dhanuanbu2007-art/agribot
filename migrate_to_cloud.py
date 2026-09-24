"""
migrate_to_cloud.py
===================
Migrates ALL points from local Qdrant (file-based ./qdrant_storage)
to Qdrant Cloud, preserving IDs, vectors, and payloads.

Usage (from project root):
    python migrate_to_cloud.py

Security:
    - Reads credentials from backend/.env only
    - QDRANT_API_KEY is NEVER printed or logged
"""
# Force UTF-8 output so special characters work on Windows
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import time
import math
from pathlib import Path
from dotenv import load_dotenv

# ── 1. Load credentials ──────────────────────────────────────────────────────
env_path = Path(__file__).parent / "backend" / ".env"
if not env_path.exists():
    sys.exit(f"[ERROR] .env not found: {env_path}")

load_dotenv(env_path)

QDRANT_URL     = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()

if not QDRANT_URL:
    sys.exit("[ERROR] QDRANT_URL is not set in backend/.env")
if not QDRANT_API_KEY:
    sys.exit("[ERROR] QDRANT_API_KEY is not set in backend/.env")

# ── 2. Configuration ─────────────────────────────────────────────────────────
LOCAL_STORAGE_PATH = "./qdrant_storage"
COLLECTION_NAME    = "agriguide_documents"
BATCH_SIZE         = 100
MAX_RETRIES        = 3
RETRY_DELAY        = 5.0

# ─────────────────────────────────────────────────────────────────────────────

def sep(title=""):
    line = "-" * 62
    if title:
        pad = (62 - len(title) - 2) // 2
        print(f"\n{'-' * pad} {title} {'-' * (62 - pad - len(title) - 2)}")
    else:
        print(line)


def main():
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
    except ImportError:
        sys.exit("[ERROR] qdrant-client not installed. Run: pip install qdrant-client")

    # ── Step 1: Connect to local Qdrant ──────────────────────────────────────
    sep("STEP 1 - Local Qdrant")
    print(f"  Storage path : {Path(LOCAL_STORAGE_PATH).resolve()}")
    try:
        local_client = QdrantClient(path=LOCAL_STORAGE_PATH)
        print("  Status       : Connected [OK]")
    except Exception as exc:
        sys.exit(f"[ERROR] Cannot open local Qdrant: {exc}")

    # ── Step 2: Inspect local collection ─────────────────────────────────────
    sep("STEP 2 - Inspect Local Collection")
    try:
        local_info = local_client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        sys.exit(f"[ERROR] Cannot read collection '{COLLECTION_NAME}': {exc}")

    local_count = local_info.points_count
    vec_cfg     = local_info.config.params.vectors
    vector_size = vec_cfg.size
    distance    = vec_cfg.distance.name   # "Cosine", "Euclid", etc.

    print(f"  Collection   : {COLLECTION_NAME}")
    print(f"  Point count  : {local_count:,}")
    print(f"  Vector dim   : {vector_size}")
    print(f"  Distance     : {distance}")

    if local_count == 0:
        sys.exit("[ERROR] Local collection has 0 points - nothing to migrate.")

    # ── Step 3: Connect to Qdrant Cloud ──────────────────────────────────────
    sep("STEP 3 - Qdrant Cloud Connection")
    print(f"  Cloud URL    : {QDRANT_URL}")
    print(f"  API Key      : [hidden for security]")
    try:
        cloud_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=60,
        )
        cloud_collections = cloud_client.get_collections().collections
        print("  Status       : Connected [OK]")
    except Exception as exc:
        sys.exit(f"[ERROR] Cannot connect to Qdrant Cloud: {exc}")

    existing_names = [c.name for c in cloud_collections]
    if existing_names:
        print(f"  Existing collections: {existing_names}")
    else:
        print("  Cloud cluster is EMPTY (no existing collections) [OK]")

    # ── Step 4: Create cloud collection ──────────────────────────────────────
    sep("STEP 4 - Create / Verify Cloud Collection")

    if COLLECTION_NAME in existing_names:
        cloud_info_pre = cloud_client.get_collection(COLLECTION_NAME)
        pre_count = cloud_info_pre.points_count
        print(f"  Collection already exists with {pre_count:,} points.")
        if pre_count == local_count:
            print("  Cloud already in sync - nothing to upload.")
            run_verification(cloud_client, local_count, vector_size, distance, COLLECTION_NAME)
            local_client.close()
            return
        print(f"  Will upsert all {local_count:,} points to fill any gaps.")
    else:
        distance_enum = getattr(Distance, distance, Distance.COSINE)
        cloud_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=distance_enum),
        )
        print(f"  Created cloud collection '{COLLECTION_NAME}'")
        print(f"  Vector size : {vector_size}  |  Distance : {distance}")

    # ── Step 5: Scroll & upload all points ───────────────────────────────────
    sep("STEP 5 - Migrating Points")
    total_batches = math.ceil(local_count / BATCH_SIZE)
    print(f"  Points total : {local_count:,}")
    print(f"  Batch size   : {BATCH_SIZE}")
    print(f"  Batch count  : ~{total_batches}")
    print()

    offset         = None
    total_uploaded = 0
    batch_num      = 0

    while True:
        # Scroll from local
        try:
            points_batch, next_offset = local_client.scroll(
                collection_name=COLLECTION_NAME,
                limit=BATCH_SIZE,
                offset=offset,
                with_vectors=True,
                with_payload=True,
            )
        except Exception as exc:
            sys.exit(f"\n[ERROR] Failed to scroll local collection: {exc}")

        if not points_batch:
            break

        batch_num += 1

        cloud_points = [
            PointStruct(id=p.id, vector=p.vector, payload=p.payload)
            for p in points_batch
        ]

        # Upload with retries
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                cloud_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=cloud_points,
                    wait=True,
                )
                total_uploaded += len(cloud_points)
                pct = total_uploaded / local_count * 100
                bar_w = 40
                filled = int(pct / 100 * bar_w)
                bar = "#" * filled + "." * (bar_w - filled)
                print(
                    f"\r  [{bar}] {pct:5.1f}%  "
                    f"{total_uploaded:,}/{local_count:,}  "
                    f"batch={batch_num}",
                    end="",
                    flush=True,
                )
                break
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    print()
                    sys.exit(
                        f"\n[ERROR] Batch {batch_num} failed after "
                        f"{MAX_RETRIES} retries: {exc}"
                    )
                print(
                    f"\n  [WARN] Batch {batch_num} attempt {attempt} "
                    f"failed: {exc} — retrying in {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)

        if next_offset is None:
            break
        offset = next_offset

    print(f"\n\n  Upload done: {total_uploaded:,} points [OK]")

    # ── Step 6+7: Verify and test ────────────────────────────────────────────
    run_verification(cloud_client, local_count, vector_size, distance, COLLECTION_NAME)
    local_client.close()


def run_verification(cloud_client, local_count, vector_size, distance, collection_name):
    sep("STEP 6 - Verification")

    try:
        cloud_info  = cloud_client.get_collection(collection_name)
        cloud_count = cloud_info.points_count
        cloud_vec   = cloud_info.config.params.vectors
        cfg_size    = cloud_vec.size
        cfg_dist    = cloud_vec.distance.name
    except Exception as exc:
        print(f"  [WARN] Cannot read cloud collection info: {exc}")
        cloud_count = cfg_size = cfg_dist = None

    count_ok  = cloud_count == local_count
    size_ok   = cfg_size == vector_size
    dist_ok   = cfg_dist == distance

    print(f"  Local  point count : {local_count:,}")
    print(f"  Cloud  point count : {cloud_count}")
    print(f"  Count match        : {'PASS' if count_ok else 'FAIL - mismatch!'}")
    print(f"  Vector dim (cloud) : {cfg_size}  (expected {vector_size})  {'PASS' if size_ok else 'FAIL'}")
    print(f"  Distance (cloud)   : {cfg_dist}  (expected {distance})  {'PASS' if dist_ok else 'FAIL'}")

    sep("STEP 7 - Test Search")
    search_ok = False
    try:
        import numpy as np
        test_vec = np.random.rand(vector_size).tolist()
        result = cloud_client.query_points(
            collection_name=collection_name,
            query=test_vec,
            limit=3,
            with_payload=True,
        )
        hits = result.points
        search_ok = len(hits) > 0
        print(f"  Test query returned : {len(hits)} result(s)  {'PASS' if search_ok else 'FAIL'}")
        if hits:
            h = hits[0]
            payload_keys = list(h.payload.keys()) if h.payload else []
            print(f"  Top result ID       : {h.id}")
            print(f"  Top result score    : {h.score:.4f}")
            print(f"  Payload fields      : {payload_keys}")
    except Exception as exc:
        print(f"  [WARN] Test search failed: {exc}")

    # ── Final Summary ────────────────────────────────────────────────────────
    sep("MIGRATION SUMMARY")
    migration_ok = count_ok and size_ok and dist_ok
    print(f"""
  Local collection name  : {collection_name}
  Local point count      : {local_count:,}
  Cloud collection name  : {collection_name}
  Cloud point count      : {cloud_count}
  Vector dimension       : {vector_size}
  Distance metric        : {distance}
  Migration status       : {'SUCCESS' if migration_ok else 'INCOMPLETE - check logs'}
  Test search status     : {'PASSED' if search_ok else 'FAILED'}
""")
    sep()


if __name__ == "__main__":
    main()
