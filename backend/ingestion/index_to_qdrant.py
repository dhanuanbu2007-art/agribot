from backend.ingestion.indexer import prepare_chunks
from backend.ingestion.embedder import create_embeddings
from backend.vectorstore.qdrant_db import client, COLLECTION_NAME
from qdrant_client.models import PointStruct


def index_documents():

    print("Preparing chunks from all documents...")

    chunks = prepare_chunks()

    print("Total chunks:", len(chunks))

    if not chunks:
        print("No chunks found. Please check your PDF files.")
        return

    texts = [chunk["text"] for chunk in chunks]

    print("Creating BGE-M3 embeddings...")

    embeddings = create_embeddings(texts)

    print("Embeddings created:", len(embeddings))

    points = []

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):

        points.append(
            PointStruct(
                id=index,
                vector=embedding.tolist(),
                payload={
                    "document_name": chunk["document_name"],
                    "category": chunk["category"],
                    "page_number": chunk["page_number"],
                    "text": chunk["text"]
                }
            )
        )

    print("Uploading vectors to Qdrant...")

    client.upload_points(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print("Documents indexed successfully!")

    print("Total vectors stored:", len(points))

    client.close()


if __name__ == "__main__":
    index_documents()