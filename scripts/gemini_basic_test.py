"""Basic Gemini text generation smoke test (no search grounding)."""

from pathlib import Path
import os
import sys

from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_model_candidates


def main() -> None:
    load_dotenv(override=True)
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not gemini_api_key or gemini_api_key == "your_key_here":
        raise RuntimeError("Set GEMINI_API_KEY in .env before running this test.")

    genai.configure(api_key=gemini_api_key)
    models = get_model_candidates()
    last_error: Exception | None = None

    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Write one sentence about competitor intelligence.")
            print(f"Basic Gemini test succeeded using model: {model_name}")
            print(response.text)
            return
        except GoogleAPICallError as exc:
            last_error = exc
            print(f"Model failed: {model_name} ({exc.__class__.__name__})")
            continue

    raise RuntimeError(f"All configured models failed. Last error: {last_error}")


if __name__ == "__main__":
    main()
