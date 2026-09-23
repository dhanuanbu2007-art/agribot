from backend.rag.chat import AgriGuideChat


chat = AgriGuideChat()


questions = [
    "I want to know about black gram cultivation.",
    "What about fertilizer?",
    "Who won the cricket match?"
]


for question in questions:

    print("\n" + "=" * 60)
    print("USER:")
    print(question)

    answer = chat.chat(question)

    print("\nAGRIGUIDE:")
    print(answer)