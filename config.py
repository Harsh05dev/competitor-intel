import os
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-1.5-flash"
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
