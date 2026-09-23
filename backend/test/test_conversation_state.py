from backend.retrieval.conversation_state import update_conversation_topic


conversation_topic = None


# First question
question1 = "I want to know about black gram cultivation."

conversation_topic = update_conversation_topic(
    question1,
    conversation_topic
)

print("Question 1:")
print(question1)

print("Conversation topic:")
print(conversation_topic)


# Follow-up question
question2 = "What about fertilizer?"

conversation_topic = update_conversation_topic(
    question2,
    conversation_topic
)

print("\nQuestion 2:")
print(question2)

print("Conversation topic:")
print(conversation_topic)


# Another follow-up
question3 = "What diseases affect it?"

conversation_topic = update_conversation_topic(
    question3,
    conversation_topic
)

print("\nQuestion 3:")
print(question3)

print("Conversation topic:")
print(conversation_topic)


# New crop
question4 = "Tell me about rice cultivation."

conversation_topic = update_conversation_topic(
    question4,
    conversation_topic
)

print("\nQuestion 4:")
print(question4)

print("Conversation topic:")
print(conversation_topic)