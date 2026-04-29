"""Basic Gemini text generation smoke test (no search grounding)."""

from pathlib import Path
import sys

from dotenv import load_dotenv
import google.generativeai as genai

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import GEMINI_API_KEY, MODEL_NAME


def main() -> None:
    load_dotenv()

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_key_here":
        raise RuntimeError("Set GEMINI_API_KEY in .env before running this test.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content("Write one sentence about competitor intelligence.")
    print("Basic Gemini test succeeded.")
    print(response.text)


if __name__ == "__main__":
    main()
