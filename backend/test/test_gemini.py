from backend.generation.gemini_generator import generate_answer

question = "What are the recommended practices for black gram?"

context = """
Black gram should be sown at the recommended seed rate and spacing.
Seed treatment with suitable fungicides followed by Rhizobium inoculation
is recommended. Weed management should be carried out around 20-25 days
after sowing.
"""

answer = generate_answer(question, context)

print("\n--- Gemini Answer ---")
print(answer)