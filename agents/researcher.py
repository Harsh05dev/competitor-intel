"""
agents/researcher.py — Researcher Agent

Responsible for discovering competitors and gathering raw intelligence.
Uses Google Search Grounding (built into the Gemini API) for real web search.

Round 1 (iteration == 0): broad research — find exactly 4 competitors and gather
  pricing, features, funding, hiring, news, and sentiment for each.

Round 2+ (iteration > 0): targeted research — use the Evaluator's
  suggested_queries to fill specific gaps identified in the previous round.
  Does NOT redo broad research — only searches for what's missing.
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

from models.schemas import AgentState
import config

load_dotenv()

SYSTEM_PROMPT = """You are a competitive intelligence researcher. Your job is to find detailed,
current information about companies and their competitors using web search.

When given a company name and industry, identify exactly 4 competitors and gather:
- Pricing model and specific price points
- Key product features and differentiators
- Recent funding rounds, acquisitions, or valuation
- Job postings or hiring signals (are they growing?)
- Recent news or product launches (last 12 months)
- Customer reviews or sentiment (from G2, Reddit, etc.)

When given specific follow-up queries (round 2+), focus ONLY on finding
that exact missing information. Do not redo broad research.

ALWAYS respond with a JSON array in this exact format:
[
  {
    "company_name": "Competitor Name",
    "raw_snippets": ["specific fact 1", "specific fact 2", "specific fact 3"],
    "sources": ["url1", "url2"]
  }
]

Return ONLY the JSON array, no other text."""


class ResearcherAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None  # initialized lazily on first call

    def _get_client(self):
        if self.client is None:
            api_key = self.api_key or os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("No GEMINI_API_KEY set. Please enter your API key.")
            self.client = genai.Client(api_key=api_key)
        return self.client

    def research(self, state: AgentState) -> Dict[str, Any]:
        company   = state.get("target_company", "")
        industry  = state.get("industry", "")
        iteration = state.get("iteration", 0)
        queries   = state.get("evaluation", {}).get("suggested_queries", [])

        if iteration == 0:
            # ── Round 1: broad research ────────────────────────────────────────
            print(f"  [Researcher] Round 1 — broad search for {company} competitors")
            prompt = (
                f"Find exactly 4 competitors of '{company}' in the {industry} industry. "
                f"Return ONLY these 4 — no more. For EACH competitor, search for: pricing details, key features, "
                f"recent funding, hiring signals, recent news, and customer sentiment. "
                f"Include specific numbers, dates, and facts."
            )
        else:
            # ── Round 2+: targeted gap-filling ────────────────────────────────
            print(f"  [Researcher] Round {iteration + 1} — targeted search for {len(queries)} gaps")
            query_list = "\n".join(f"- {q}" for q in queries)
            prompt = (
                f"Search for specific competitor information about companies in the {industry} industry. "
                f"Find answers to these exact questions:\n{query_list}\n\n"
                f"Return only the new information found as a JSON array."
            )

        # ── Try models with Google Search Grounding ────────────────────────────
        models_to_try = [
            config.MODEL_NAME,
            "gemini-2.0-flash-lite",
            "gemini-2.5-flash-lite",
        ]
        response = None

        for model in models_to_try:
            try:
                print(f"  [Researcher] Trying {model} with Google Search Grounding...")
                response = self._get_client().models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1,
                    )
                )
                print(f"  [Researcher] Success with {model}")
                break
            except Exception as e:
                print(f"  [Researcher] {model} failed: {e}")
                # Fallback: try without grounding if search tool fails
                try:
                    print(f"  [Researcher] Retrying {model} without grounding...")
                    response = self._get_client().models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.1,
                        )
                    )
                    print(f"  [Researcher] Success (no grounding)")
                    break
                except Exception as e2:
                    print(f"  [Researcher] {model} also failed without grounding: {e2}")

        if not response:
            print("  [Researcher] All models failed — preserving existing results")
            return {
                "research_results": state.get("research_results", []) if iteration > 0 else [],
                "iteration": iteration,
            }

        # ── Parse JSON response ────────────────────────────────────────────────
        text = response.text or ""
        data = self._sanitize_results(self._parse_json_list(text))

        # ── Merge with existing results on iteration 2+ ────────────────────────
        if iteration > 0 and state.get("research_results"):
            data = self._merge_results(state["research_results"], data)
        print(f"  [Researcher] Returning data for {len(data)} competitors")
        return {
            "research_results": data,
            "iteration": iteration,
        }

    def _merge_results(self, existing_results: list, new_results: list) -> list:
        """Merge retry findings without assuming perfect LLM-shaped data."""
        merged = []
        index = {}

        for result in existing_results:
            if not isinstance(result, dict):
                continue
            key = self._company_key(result)
            if key:
                index[key] = len(merged)
            merged.append(result)

        for new_comp in new_results:
            key = self._company_key(new_comp)
            if not key:
                continue
            if key in index:
                existing = merged[index[key]]
                snippets = self._dedupe(
                    self._as_list(existing.get("raw_snippets")) +
                    self._as_list(new_comp.get("raw_snippets"))
                )
                sources = self._dedupe(
                    self._as_list(existing.get("sources")) +
                    self._as_list(new_comp.get("sources"))
                )
                existing["raw_snippets"] = snippets
                existing["sources"] = sources
            else:
                index[key] = len(merged)
                merged.append(new_comp)
        return merged

    def _sanitize_results(self, data: list) -> list:
        sanitized = []
        if not isinstance(data, list):
            return sanitized
        for item in data:
            if not isinstance(item, dict) or not self._company_key(item):
                continue
            item["raw_snippets"] = self._as_list(item.get("raw_snippets"))
            item["sources"] = self._as_list(item.get("sources"))
            sanitized.append(item)
        return sanitized

    @staticmethod
    def _company_key(result: dict) -> str:
        name = result.get("company_name") if isinstance(result, dict) else None
        return name.strip().lower() if isinstance(name, str) else ""

    @staticmethod
    def _as_list(value: Any) -> list:
        if isinstance(value, list):
            return value
        if value:
            return [value]
        return []

    @staticmethod
    def _dedupe(values: list) -> list:
        deduped = []
        seen = set()
        for value in values:
            marker = value if isinstance(value, (str, int, float, bool, type(None))) else repr(value)
            if marker not in seen:
                seen.add(marker)
                deduped.append(value)
        return deduped

    def _parse_json_list(self, text: str) -> list:
        """Extract a JSON array from LLM response, handling markdown fences."""
        cleaned = text.strip()
        # Strip markdown fences
        if "```" in cleaned:
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        # Find the array
        start = cleaned.find("[")
        end   = cleaned.rfind("]") + 1
        if start == -1 or end == 0:
            print("  [Researcher] Warning: no JSON array found in response")
            return []
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError as e:
            print(f"  [Researcher] JSON parse error: {e}")
            return []
