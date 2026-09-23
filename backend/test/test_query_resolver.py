from backend.retrieval.query_resolver import resolve_search_query


# Previous conversation topic
conversation_topic = "black gram"


# -----------------------------
# Question 1
# -----------------------------

question1 = "I want to know about black gram cultivation."

search_query1 = resolve_search_query(
    question=question1,
    conversation_topic=conversation_topic
)

print("Question 1:")
print(question1)

print("\nSearch query 1:")
print(search_query1)


# -----------------------------
# Question 2
# -----------------------------

question2 = "What about fertilizer?"

search_query2 = resolve_search_query(
    question=question2,
    conversation_topic=conversation_topic
)

print("\nQuestion 2:")
print(question2)

print("\nSearch query 2:")
print(search_query2)