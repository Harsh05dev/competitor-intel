"""
agents/categorizer.py — Categorizer Agent

Takes raw, noisy research snippets from the Researcher and organizes
them into clean, structured JSON per competitor.

This agent exists separately from the Researcher because:
- Raw search results are inconsistent and noisy
- Isolating the structuring step makes both agents better at their job
- The Researcher focuses on COVERAGE, the Categorizer on ACCURACY

On iteration 2+, the categorizer merges new data with existing data
using a fill-gaps strategy: only fills null/empty fields, never
overwrites existing good data.
"""

import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

from models.schemas import AgentState
from agents.llm_coerce import (
    as_dict_list,
    as_str_list,
    company_name,
    competitor_has_content,
    fill_competitor,
    normalize_competitor,
)
import config

load_dotenv()

SYSTEM_PROMPT = """You are a data structuring specialist. You receive raw research snippets
about companies and organize them into clean, structured categories.

You MUST respond with ONLY a JSON array in this exact format:
[
  {
    "company_name": "Company A",
    "pricing": "Description of pricing model with specific prices if known",
    "key_features": ["feature 1", "feature 2", "feature 3"],
    "target_audience": "Who they sell to",
    "funding": "Funding stage, amount raised, valuation if known",
    "hiring_signals": ["e.g. 50 open engineering roles", "expanding to EU"],
    "recent_news": ["news item 1", "news item 2"],
    "customer_sentiment": "Overall sentiment from reviews and forums"
  }
]

Rules:
- If information is not available for a field, use null for strings or [] for lists
- Do NOT invent data — only use what is in the provided snippets
- Extract specific numbers, dates, and details, not vague summaries
- Return ONLY the JSON array, no other text"""


class CategorizerAgent:
    def __init__(self, api_key: str | None = None):
        cleaned = (api_key or "").strip()
        self._api_key = cleaned or None
        self.client = None  # initialized lazily on first call

    def _get_client(self):
        if self.client is None:
            api_key = self._api_key or os.getenv("GEMINI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("No GEMINI_API_KEY set. Please enter your API key.")
            self.client = genai.Client(api_key=api_key)
        return self.client

    def categorize(self, state: AgentState) -> Dict[str, Any]:
        existing = state.get("categorized_competitors")
        if not isinstance(existing, list):
            existing = []
        iteration = state.get("iteration", 0)
        research_results = as_dict_list(state.get("research_results"))

        if not research_results:
            print("  [Categorizer] No research results to categorize")
            return {"categorized_competitors": existing}

        # Cap to prevent token overflow with too many competitors
        research_results = research_results[:config.MAX_COMPETITORS]
        print(f"  [Categorizer] Capping to {len(research_results)} competitors")

        print(f"  [Categorizer] Structuring {len(research_results)} competitor entries")

        # Build prompt with all raw snippets
        prompt = "Organize the following raw research snippets into structured JSON:\n\n"
        for comp in research_results:
            name = company_name(comp) or "Unknown"
            snippets = as_str_list(comp.get("raw_snippets"))
            sources = as_str_list(comp.get("sources"))
            prompt += f"--- {name} ---\n"
            for snippet in snippets:
                prompt += f"  • {snippet}\n"
            if sources:
                prompt += f"  Sources: {', '.join(sources[:3])}\n"
            prompt += "\n"

        # Try models
        models_to_try = [
            config.MODEL_NAME,
            "gemini-2.0-flash-lite",
            "gemini-2.5-flash-lite",
        ]
        response = None

        for model in models_to_try:
            try:
                print(f"  [Categorizer] Trying {model}...")
                response = self._get_client().models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.1,
                    )
                )
                print(f"  [Categorizer] Success with {model}")
                break
            except Exception as e:
                print(f"  [Categorizer] {model} failed: {e}")

        if not response:
            print("  [Categorizer] All models failed — returning existing data")
            return {"categorized_competitors": existing}

        new_data = as_dict_list(self._parse_json_list(response.text or ""))
        normalized = self._normalize_rows(new_data)

        # On iteration 2+, merge with existing rather than replacing
        if iteration > 0 and existing:
            merged = self._merge(existing, normalized)
            print(f"  [Categorizer] Merged — {len(merged)} competitors total")
            return {"categorized_competitors": merged}

        print(f"  [Categorizer] Structured {len(normalized)} competitors")
        return {"categorized_competitors": normalized}

    def _normalize_rows(self, rows: List[dict]) -> List[dict]:
        normalized = []
        for row in as_dict_list(rows):
            item = normalize_competitor(row)
            if not item["company_name"]:
                if not competitor_has_content(item):
                    continue
                item["company_name"] = "Unknown"
            normalized.append(item)
        return normalized

    def _merge(self, existing: List[dict], new_data: List[dict]) -> List[dict]:
        """
        Merge strategy for iteration rounds:
        - Match competitors by name (case-insensitive)
        - String fields: fill ONLY if existing value is null/empty
        - List fields: combine and deduplicate
        - New competitors found in re-research: append
        Never overwrites existing data.
        """
        prepared_new = self._normalize_rows(new_data)
        new_map = {}
        unnamed = []
        for comp in prepared_new:
            key = comp.get("company_name", "").strip().lower()
            if not key or key == "unknown":
                unnamed.append(comp)
                continue
            new_map[key] = comp

        merged = []
        seen = set()
        for comp in as_dict_list(existing):
            current = normalize_competitor(comp)
            key = current.get("company_name", "").strip().lower()
            if key and key in new_map:
                current = fill_competitor(current, new_map[key])
                seen.add(key)
            elif not key:
                if not competitor_has_content(current):
                    continue
                current["company_name"] = "Unknown"
            merged.append(current)

        for name_key, comp in new_map.items():
            if name_key not in seen:
                merged.append(comp)
        merged.extend(unnamed)
        return merged

    def _parse_json_list(self, text: str) -> list:
        """Extract JSON array from LLM response."""
        cleaned = text.strip()
        if "```" in cleaned:
            lines   = cleaned.split("\n")
            lines   = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        start = cleaned.find("[")
        end   = cleaned.rfind("]") + 1
        if start == -1 or end == 0:
            print("  [Categorizer] Warning: no JSON array found")
            return []
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError as e:
            print(f"  [Categorizer] JSON parse error: {e}")
            return []
