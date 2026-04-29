"""Gemini smoke test with Google Search Grounding enabled."""

from pathlib import Path
import sys

from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import protos

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

    search_tool = protos.Tool(
        google_search_retrieval=protos.GoogleSearchRetrieval(
            dynamic_retrieval_config=protos.DynamicRetrievalConfig(
                mode=protos.DynamicRetrievalConfig.Mode.MODE_DYNAMIC
            )
        )
    )

    response = model.generate_content(
        "Give two current competitors to Stripe and include one cited source per competitor.",
        tools=[search_tool],
    )

    print("Grounded Gemini test succeeded.")
    print(response.text)

    candidates = getattr(response, "candidates", []) or []
    if candidates:
        print(f"Candidates returned: {len(candidates)}")
    else:
        print("No candidate metadata found to confirm citations.")


if __name__ == "__main__":
    main()
