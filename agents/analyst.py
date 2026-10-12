"""
agents/analyst.py — Analyst Agent

Takes structured competitor data from the Categorizer and synthesizes
strategic insights: SWOT analysis, comparison matrix, threat ranking,
and opportunity gaps.

This is where organized data becomes actionable intelligence.
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

from models.schemas import AgentState
from agents.llm_coerce import (
    analysis_usable,
    as_dict_list,
    as_str_list,
    as_text,
    company_name,
    normalize_analysis,
)
import config

load_dotenv()

SYSTEM_PROMPT = """You are a strategic competitive analyst. Given structured data about a
company's competitors, you produce high-quality strategic analysis.

You MUST respond with ONLY a JSON object in this exact format:
{
  "swot": {
    "strengths": ["strength 1 with specific evidence", "strength 2"],
    "weaknesses": ["weakness 1 with specific evidence", "weakness 2"],
    "opportunities": ["opportunity 1", "opportunity 2"],
    "threats": ["threat 1", "threat 2"]
  },
  "comparison_matrix": [
    {
      "company_name": "Competitor A",
      "pricing_tier": "Free / Freemium / Mid-range / Premium / Enterprise",
      "primary_strength": "Their single biggest advantage",
      "primary_weakness": "Their single biggest weakness",
      "target_market": "Who they primarily sell to",
      "threat_level": "Low / Medium / High"
    }
  ],
  "threat_ranking": ["Most threatening first", "Second most threatening"],
  "opportunity_gaps": [
    "Gap 1: Something no competitor does well that the target could exploit",
    "Gap 2: Another actionable opportunity"
  ]
}

Rules:
- Each SWOT quadrant MUST have at least 2 points, ideally 3-4
- Back every claim with specific evidence from the data (numbers, dates, features)
- Threat ranking must be ordered from most to least threatening
- Opportunity gaps must be specific and actionable, not generic
- Return ONLY the JSON object, no other text"""


class AnalystAgent:
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

    def _keep_prior(self, state: AgentState, candidate: Any) -> Dict[str, Any] | None:
        """On a retry, ignore an empty or null analysis so the previous SWOT survives."""
        if state.get("iteration", 0) <= 0:
            return None
        prior = state.get("analysis")
        if analysis_usable(prior) and not analysis_usable(candidate):
            return prior
        return None

    def analyze(self, state: AgentState) -> Dict[str, Any]:
        target      = state.get("target_company", "Unknown")
        industry    = state.get("industry", "")
        competitors = as_dict_list(state.get("categorized_competitors"))

        if not competitors:
            print("  [Analyst] No categorized data to analyze")
            prior = self._keep_prior(state, None)
            return {"analysis": prior if prior is not None else normalize_analysis({})}

        print(f"  [Analyst] Analyzing {target} against {len(competitors)} competitors")

        # Build structured prompt
        prompt = f"Analyze the competitive landscape for '{target}' in the {industry} industry.\n\n"
        prompt += "Here is structured data on each competitor:\n\n"

        for comp in competitors:
            features = as_str_list(comp.get("key_features"))
            hiring = as_str_list(comp.get("hiring_signals"))
            news = as_str_list(comp.get("recent_news"))
            prompt += f"### {company_name(comp) or 'Unknown'}\n"
            prompt += f"- Pricing: {as_text(comp.get('pricing')) or 'Unknown'}\n"
            prompt += f"- Key Features: {', '.join(features) if features else 'Unknown'}\n"
            prompt += f"- Target Audience: {as_text(comp.get('target_audience')) or 'Unknown'}\n"
            prompt += f"- Funding: {as_text(comp.get('funding')) or 'Unknown'}\n"
            prompt += f"- Hiring Signals: {', '.join(hiring) if hiring else 'None'}\n"
            prompt += f"- Recent News: {', '.join(news[:2]) if news else 'None'}\n"
            prompt += f"- Customer Sentiment: {as_text(comp.get('customer_sentiment')) or 'Unknown'}\n\n"

        prompt += (
            f"Produce a SWOT analysis for {target} relative to these competitors, "
            f"a comparison matrix, threat ranking (most to least threatening), "
            f"and specific opportunity gaps {target} could exploit."
        )

        # Try models
        models_to_try = [
            config.MODEL_NAME,
            "gemini-2.0-flash-lite",
            "gemini-2.5-flash-lite",
        ]
        response = None

        for model in models_to_try:
            try:
                print(f"  [Analyst] Trying {model}...")
                response = self._get_client().models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.2,
                    )
                )
                print(f"  [Analyst] Success with {model}")
                break
            except Exception as e:
                print(f"  [Analyst] {model} failed: {e}")

        if not response:
            prior = self._keep_prior(state, None)
            if prior is not None:
                print("  [Analyst] All models failed — keeping previous analysis")
                return {"analysis": prior}
            print("  [Analyst] All models failed — returning empty analysis")
            return {"analysis": normalize_analysis({})}

        analysis = self._parse_json_object(response.text or "")
        prior = self._keep_prior(state, analysis)
        if prior is not None:
            print("  [Analyst] Retry response had no usable analysis — keeping previous analysis")
            return {"analysis": prior}

        analysis = normalize_analysis(analysis)

        # Log SWOT depth for visibility
        swot = analysis.get("swot") or {}
        for quadrant in ["strengths", "weaknesses", "opportunities", "threats"]:
            count = len(as_str_list(swot.get(quadrant)))
            print(f"  [Analyst] {quadrant}: {count} points")

        return {"analysis": analysis}

    def _parse_json_object(self, text: str) -> dict:
        """Extract JSON object from LLM response."""
        cleaned = text.strip()
        if "```" in cleaned:
            lines   = cleaned.split("\n")
            lines   = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        start = cleaned.find("{")
        end   = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            print("  [Analyst] Warning: no JSON object found")
            return {}
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError as e:
            print(f"  [Analyst] JSON parse error: {e}")
            return {}
