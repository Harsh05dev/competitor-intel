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
from typing import Dict, Any, List
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
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = None  # initialized lazily on first call
        self._client_api_key = None

    def _get_client(self):
        api_key = self.api_key if self.api_key is not None else os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("No GEMINI_API_KEY set. Please enter your API key.")
        if self.client is None or self._client_api_key != api_key:
            self.client = genai.Client(api_key=api_key)
            self._client_api_key = api_key
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
            if iteration > 0 and state.get("research_results"):
                print("  [Researcher] All models failed — preserving existing research")
                return {
                    "research_results": state["research_results"],
                    "iteration": iteration,
                }
            print("  [Researcher] All models failed — returning empty results")
            return {
                "research_results": [],
                "iteration": iteration,
            }

        # ── Parse JSON response ────────────────────────────────────────────────
        text = response.text or ""
        data = self._parse_json_list(text)

        # ── Merge with existing results on iteration 2+ ────────────────────────
        if iteration > 0 and state.get("research_results"):
            data = self._merge_research_results(state["research_results"], data)

        print(f"  [Researcher] Returning data for {len(data)} competitors")
        return {
            "research_results": data,
            "iteration": iteration,
        }

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

    def _merge_research_results(self, existing_results: List[dict], new_results: List[dict]) -> List[dict]:
        """Merge retry results without assuming every LLM row is perfectly shaped."""
        merged = []
        by_name = {}

        for comp in existing_results:
            normalized = self._normalize_research_result(comp)
            if normalized is None:
                continue
            name = normalized.get("company_name", "")
            if name:
                key = name.lower()
                if key in by_name:
                    self._append_research_fields(by_name[key], normalized)
                    continue
                by_name[key] = normalized
            merged.append(normalized)

        for comp in new_results:
            normalized = self._normalize_research_result(comp)
            if normalized is None:
                continue
            name = normalized.get("company_name", "")
            if name and name.lower() in by_name:
                self._append_research_fields(by_name[name.lower()], normalized)
            else:
                if name:
                    by_name[name.lower()] = normalized
                merged.append(normalized)

        return merged

    def _normalize_research_result(self, comp: Any) -> dict | None:
        if not isinstance(comp, dict):
            return None
        normalized = dict(comp)
        normalized["company_name"] = str(normalized.get("company_name") or "").strip()
        normalized["raw_snippets"] = self._as_list(normalized.get("raw_snippets"))
        normalized["sources"] = self._as_list(normalized.get("sources"))
        return normalized

    def _append_research_fields(self, target: dict, incoming: dict) -> None:
        target["raw_snippets"] = self._dedupe(target.get("raw_snippets", []) + incoming.get("raw_snippets", []))
        target["sources"] = self._dedupe(target.get("sources", []) + incoming.get("sources", []))

    def _as_list(self, value: Any) -> list:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _dedupe(self, values: list) -> list:
        deduped = []
        seen = set()
        for value in values:
            marker = repr(value)
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append(value)
        return deduped
