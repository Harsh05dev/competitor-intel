"""Gemini smoke test with Google Search Grounding enabled."""

from pathlib import Path
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_model_candidates


def main() -> None:
    load_dotenv(override=True)
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not gemini_api_key or gemini_api_key == "your_key_here":
        raise RuntimeError("Set GEMINI_API_KEY in .env before running this test.")

    client = genai.Client(api_key=gemini_api_key)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    models = get_model_candidates()
    last_error: Exception | None = None
    saw_quota_error = False
    saw_invalid_model_or_tool = False

    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Give two current competitors to Stripe and include one cited source per competitor.",
                config=types.GenerateContentConfig(tools=[search_tool]),
            )

            print(f"Grounded Gemini test succeeded using model: {model_name}")
            print(response.text)

            candidates = getattr(response, "candidates", []) or []
            if candidates:
                print(f"Candidates returned: {len(candidates)}")
            else:
                print("No candidate metadata found to confirm citations.")
            return
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            if "resource_exhausted" in message or "429" in message or "quota" in message:
                saw_quota_error = True
            elif "invalid" in message or "not supported" in message:
                saw_invalid_model_or_tool = True
            print(f"Model failed: {model_name} ({exc.__class__.__name__})")
            continue

    if saw_quota_error:
        print("GROUNDING_BLOCKED_QUOTA: All attempted models were blocked by quota/rate limits.")
    elif saw_invalid_model_or_tool:
        print("GROUNDING_UNSUPPORTED_MODEL: Available models do not support this grounding/tool setup.")
    else:
        print("GROUNDING_BLOCKED_UNKNOWN: Grounding failed for all attempted models.")

    raise RuntimeError(f"All configured models failed. Last error: {last_error}")


if __name__ == "__main__":
    main()
