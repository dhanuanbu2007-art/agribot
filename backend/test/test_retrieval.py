from backend.retrieval.retriever import retrieve_relevant_chunks


questions = [
    "How should fertilizers and nutrients be managed?",
    "How can farmers manage crop diseases and pests?",
    "What are the important practices for crop cultivation?",
    "What agricultural government schemes are available for farmers?"
]


for question in questions:

    print("\n" + "=" * 70)
    print("QUESTION:")
    print(question)
    print("=" * 70)

    results = retrieve_relevant_chunks(
        question,
        top_k=3
    )

    for index, point in enumerate(results, start=1):

        payload = point.payload

        print(f"\n--- Result {index} ---")
        print("Document:", payload.get("document_name"))
        print("Category:", payload.get("category"))
        print("Page:", payload.get("page_number"))
        print("Score:", point.score)

        print("Text:")
        print(payload.get("text", "")[:300])