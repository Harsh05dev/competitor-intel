"""Basic Gemini text generation smoke test (no search grounding)."""

from pathlib import Path
import os
import sys

from dotenv import load_dotenv
import google.generativeai as genai

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import MODEL_NAME


def main() -> None:
    load_dotenv(override=True)
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not gemini_api_key or gemini_api_key == "your_key_here":
        raise RuntimeError("Set GEMINI_API_KEY in .env before running this test.")

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content("Write one sentence about competitor intelligence.")
    print("Basic Gemini test succeeded.")
    print(response.text)


if __name__ == "__main__":
    main()
