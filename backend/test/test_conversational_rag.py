from backend.retrieval.retriever import retrieve_relevant_chunks
from backend.generation.gemini_generator import generate_answer


previous_interaction_id = None


def chat(question):
    global previous_interaction_id

    # Step 1: Retrieve relevant agricultural information
    retrieved_chunks = retrieve_relevant_chunks(
        question,
        top_k=5
    )

    # Step 2: Send question + retrieved context to Gemini
    interaction = generate_answer(
        question=question,
        retrieved_chunks=retrieved_chunks,
        previous_interaction_id=previous_interaction_id
    )

    # Step 3: Save interaction ID for the next message
    previous_interaction_id = interaction.id

    return interaction.output_text


# -----------------------------
# First message
# -----------------------------

question1 = "I want to know about black gram cultivation."

answer1 = chat(question1)

print("\nUSER:")
print(question1)

print("\nAGRIGUIDE:")
print(answer1)


# -----------------------------
# Follow-up message
# -----------------------------

question2 = "What about fertilizer?"

answer2 = chat(question2)

print("\nUSER:")
print(question2)

print("\nAGRIGUIDE:")
print(answer2)