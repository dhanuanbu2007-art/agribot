from backend.ingestion.indexer import prepare_chunks
from backend.ingestion.embedder import create_embeddings


chunks = prepare_chunks()

texts = [chunk["text"] for chunk in chunks]

embeddings = create_embeddings(texts)

print("Total chunks:", len(chunks))
print("Total embeddings:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))