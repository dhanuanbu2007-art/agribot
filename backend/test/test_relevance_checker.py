from backend.retrieval.relevance_checker import is_agriculture_question


questions = [
    "How should I cultivate black gram?",
    "What fertilizer should I use?",
    "What diseases affect rice?",
    "Tell me about irrigation",
    "Who won the cricket match?",
    "What is Python?",
]


for question in questions:
    result = is_agriculture_question(question)

    print(f"{question}")
    print(f"Agriculture question: {result}")
    print()