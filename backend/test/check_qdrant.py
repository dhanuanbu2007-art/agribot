from backend.vectorstore.qdrant_db import client, COLLECTION_NAME


collections = client.get_collections().collections

print("Available collections:")

for collection in collections:
    print("-", collection.name)

info = client.get_collection(COLLECTION_NAME)

print("\nVector size:", info.config.params.vectors.size)
print("Distance:", info.config.params.vectors.distance)