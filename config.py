import os
from dotenv import load_dotenv
load_dotenv(override=False)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

_DEFAULT_MODEL_CANDIDATES = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
]


def get_model_candidates() -> list[str]:
    raw_candidates = os.getenv("GEMINI_MODEL_CANDIDATES", "")
    if raw_candidates.strip():
        base_candidates = [item.strip() for item in raw_candidates.split(",") if item.strip()]
    else:
        base_candidates = list(_DEFAULT_MODEL_CANDIDATES)

    explicit_model = os.getenv("GEMINI_MODEL", "").strip()
    ordered_candidates = [explicit_model] + base_candidates if explicit_model else base_candidates

    # Deduplicate while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for model_name in ordered_candidates:
        if model_name and model_name not in seen:
            deduped.append(model_name)
            seen.add(model_name)
    return deduped


# Main app/runtime model should be explicit and predictable.
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
