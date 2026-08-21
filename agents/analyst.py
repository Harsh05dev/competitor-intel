"""
agents/analyst.py — Analyst Agent

Takes structured competitor data from the Categorizer and synthesizes
strategic insights: SWOT analysis, comparison matrix, threat ranking,
and opportunity gaps.

This is where organized data becomes actionable intelligence.
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
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None  # initialized lazily on first call
        self._client_api_key = None

    def _get_client(self):
        api_key = self.api_key or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("No GEMINI_API_KEY set. Please enter your API key.")
        if self.client is None or self._client_api_key != api_key:
            self.client = genai.Client(api_key=api_key)
            self._client_api_key = api_key
        return self.client

    def analyze(self, state: AgentState) -> Dict[str, Any]:
        target      = state.get("target_company", "Unknown")
        industry    = state.get("industry", "")
        competitors = state.get("categorized_competitors", [])
        iteration   = state.get("iteration", 0)
        prior_analysis = state.get("analysis", {})

        if not competitors:
            print("  [Analyst] No categorized data to analyze")
            return {"analysis": {"swot": {}, "comparison_matrix": [], "threat_ranking": [], "opportunity_gaps": []}}

        print(f"  [Analyst] Analyzing {target} against {len(competitors)} competitors")

        # Build structured prompt
        prompt = f"Analyze the competitive landscape for '{target}' in the {industry} industry.\n\n"
        prompt += "Here is structured data on each competitor:\n\n"

        for comp in competitors:
            prompt += f"### {comp.get('company_name', 'Unknown')}\n"
            prompt += f"- Pricing: {comp.get('pricing') or 'Unknown'}\n"
            features = comp.get('key_features') or []
            prompt += f"- Key Features: {', '.join(features) if features else 'Unknown'}\n"
            prompt += f"- Target Audience: {comp.get('target_audience') or 'Unknown'}\n"
            prompt += f"- Funding: {comp.get('funding') or 'Unknown'}\n"
            hiring = comp.get('hiring_signals') or []
            prompt += f"- Hiring Signals: {', '.join(hiring) if hiring else 'None'}\n"
            news = comp.get('recent_news') or []
            prompt += f"- Recent News: {', '.join(news[:2]) if news else 'None'}\n"
            prompt += f"- Customer Sentiment: {comp.get('customer_sentiment') or 'Unknown'}\n\n"

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
            if iteration > 0 and prior_analysis:
                print("  [Analyst] All models failed — preserving prior analysis")
                return {"analysis": prior_analysis}
            print("  [Analyst] All models failed — returning empty analysis")
            return {"analysis": {"swot": {}, "comparison_matrix": [], "threat_ranking": [], "opportunity_gaps": []}}

        analysis = self._parse_json_object(response.text or "")
        if not analysis and iteration > 0 and prior_analysis:
            print("  [Analyst] Empty analysis response — preserving prior analysis")
            return {"analysis": prior_analysis}

        # Log SWOT depth for visibility
        swot = analysis.get("swot") or {}
        for quadrant in ["strengths", "weaknesses", "opportunities", "threats"]:
            items = swot.get(quadrant) if isinstance(swot, dict) else []
            count = len(items) if isinstance(items, list) else 0
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
