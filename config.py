import os
from dotenv import load_dotenv
load_dotenv(override=False)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Keep model configurable from .env for quick quota/workaround switches.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
EVALUATION_THRESHOLD = 75
MAX_ITERATIONS = 3
EVAL_WEIGHTS = {
    "competitor_count": 10,
    "pricing_coverage": 20,
    "feature_coverage": 20,
    "funding_data": 10,
    "hiring_signals": 10,
    "swot_depth": 20,
    "recency": 10,
}
