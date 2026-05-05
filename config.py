import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

EVALUATION_THRESHOLD = 70  # lowered from 75, more realistic for free tier
MAX_ITERATIONS = 3
MAX_COMPETITORS = 4  # hard cap — prevents 14-competitor explosion
MAX_GAPS_PER_RETRY = 6  # cap gaps sent back to Researcher

EVAL_WEIGHTS = {
    "competitor_count": 15,
    "pricing_coverage": 20,
    "feature_coverage": 20,
    "funding_data": 15,
    "hiring_signals": 10,
    "swot_depth": 20,
}
