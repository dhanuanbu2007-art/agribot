from backend.vectorstore.qdrant_db import client, COLLECTION_NAME


info = client.get_collection(COLLECTION_NAME)

print("Vectors stored in Qdrant:", info.points_count)