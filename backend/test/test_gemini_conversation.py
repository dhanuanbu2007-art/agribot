from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL_NAME = "gemini-3.5-flash-lite"

print("Sending first message...")

interaction1 = client.interactions.create(
    model=MODEL_NAME,
    input="My favorite crop is black gram."
)

print("Response 1:")
print(interaction1.output_text)

print("\nSending second message...")

interaction2 = client.interactions.create(
    model=MODEL_NAME,
    previous_interaction_id=interaction1.id,
    input="What crop did I say I like?"
)

print("Response 2:")
print(interaction2.output_text)