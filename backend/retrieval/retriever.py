from backend.ingestion.embedder import embed_query
from backend.vectorstore.qdrant_db import client, COLLECTION_NAME


def retrieve_relevant_chunks(question, top_k=5):
    """
    Convert the search query into an embedding using Gemini Embedding 2
    (RETRIEVAL_QUERY task type) and retrieve the most relevant chunks from Qdrant Cloud.
    """

    query_vector = embed_query(question)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True
    )

    return results.points