from backend.ingestion.embedder import create_embeddings


texts = [
    "Black gram farmers should use recommended varieties.",
    "Farmers should monitor pests and diseases in tomato crops."
]

embeddings = create_embeddings(texts)

print("Number of embeddings:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))