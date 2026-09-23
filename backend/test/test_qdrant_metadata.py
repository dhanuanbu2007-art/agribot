from backend.vectorstore.qdrant_db import client, COLLECTION_NAME


info = client.get_collection(COLLECTION_NAME)

print("Collection:", COLLECTION_NAME)
print("Total vectors:", info.points_count)

print("\nSample stored documents:")

results = client.scroll(
    collection_name=COLLECTION_NAME,
    limit=10,
    with_payload=True
)

points = results[0]

for index, point in enumerate(points, start=1):

    payload = point.payload

    print(f"\n--- Document {index} ---")
    print("Document:", payload.get("document_name"))
    print("Category:", payload.get("category"))
    print("Page:", payload.get("page_number"))
    print("Text:", payload.get("text", "")[:200])


client.close()