from backend.ingestion.indexer import prepare_chunks


chunks = prepare_chunks()

print("Total chunks:", len(chunks))

print("\nFirst chunk:")
print("Page:", chunks[0]["page_number"])
print(chunks[0]["text"])