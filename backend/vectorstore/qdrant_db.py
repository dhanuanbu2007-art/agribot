import os
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Load credentials from backend/.env
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Production collection using Gemini Embedding 2 (backup collection remains 'agriguide_documents')
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "agriguide_gemini_embeddings")
VECTOR_DIMENSION = 3072
DISTANCE_METRIC = Distance.COSINE

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60,
)


def create_collection(collection_name: str = COLLECTION_NAME, vector_size: int = VECTOR_DIMENSION):
    collections = client.get_collections().collections

    existing_collections = [
        collection.name for collection in collections
    ]

    if collection_name not in existing_collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=DISTANCE_METRIC
            )
        )
        print(f"Qdrant collection '{collection_name}' created successfully! (dim={vector_size})")
    else:
        print(f"Qdrant collection '{collection_name}' already exists!")


if __name__ == "__main__":
    create_collection()
    client.close()