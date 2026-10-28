import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from .env"
    )

client = genai.Client(api_key=api_key)

model_name = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

print("Connecting to Gemini...")

response = client.models.generate_content(
    model=model_name,
    contents=(
        "You are SheetPilot AI. "
        "Introduce yourself in one sentence."
    ),
)

print("\nGemini response:")
print(response.text)

print("\nGemini connection successful!")