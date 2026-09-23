from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-m3"

model = SentenceTransformer(MODEL_NAME)


def create_embeddings(texts):
    embeddings = model.encode(
        texts,
        batch_size=8,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return embeddings