from backend.rag.chat import AgriGuideChat


chatbot = AgriGuideChat()


question = "How should fertilizers and nutrients be managed?"


print("\nUser:")
print(question)

print("\nAgriGuide:")

answer = chatbot.chat(question)

print(answer)