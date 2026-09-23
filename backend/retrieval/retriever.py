from backend.ingestion.embedder import create_embeddings
from backend.vectorstore.qdrant_db import client, COLLECTION_NAME


def retrieve_relevant_chunks(question, top_k=5):
    """
    Convert the search query into an embedding
    and retrieve the most relevant chunks from Qdrant.
    """

    query_embedding = create_embeddings([question])[0]

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=top_k,
        with_payload=True
    )

    return results.points