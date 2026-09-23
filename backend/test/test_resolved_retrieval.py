from backend.retrieval.query_resolver import resolve_search_query
from backend.retrieval.retriever import retrieve_relevant_chunks


# Previous conversation topic
conversation_topic = "black gram"


# User's follow-up question
question = "What about fertilizer?"


# Resolve the follow-up question
search_query = resolve_search_query(
    question=question,
    conversation_topic=conversation_topic
)

print("User question:")
print(question)

print("\nResolved search query:")
print(search_query)


# Retrieve relevant agricultural information
results = retrieve_relevant_chunks(
    search_query,
    top_k=5
)

print("\nRetrieved results:", len(results))


# Display retrieved information
for i, result in enumerate(results, start=1):

    print(f"\n--- Result {i} ---")

    print("Score:", result.score)

    print("Page:", result.payload["page_number"])

    print("Text:")
    print(result.payload["text"])