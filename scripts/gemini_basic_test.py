from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[{
        "role": "user",
        "parts": [{"text": "Write one sentence about competitor intelligence."}]
    }]
)

print("Basic Gemini test succeeded.")
print(response.candidates[0].content.parts[0].text)