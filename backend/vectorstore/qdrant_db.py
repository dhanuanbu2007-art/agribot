from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


COLLECTION_NAME = "agriguide_documents"

client = QdrantClient(path="./qdrant_storage")


def create_collection():
    collections = client.get_collections().collections

    existing_collections = [
        collection.name for collection in collections
    ]

    if COLLECTION_NAME not in existing_collections:

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=1024,
                distance=Distance.COSINE
            )
        )

        print("Qdrant collection created successfully!")

    else:
        print("Qdrant collection already exists!")


if __name__ == "__main__":
    create_collection()
    client.close()