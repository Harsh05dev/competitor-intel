"""
agents/analyst.py — Analyst Agent

Takes structured competitor data from the Categorizer and synthesizes
strategic insights: SWOT analysis, comparison matrix, threat ranking,
and opportunity gaps.

This is where organized data becomes actionable intelligence.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

from models.schemas import AgentState
from .json_extract import parse_json_object
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
    def __init__(self):
        self.client = None  # initialized lazily on first call

    def _get_client(self):
        if self.client is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("No GEMINI_API_KEY set. Please enter your API key.")
            self.client = genai.Client(api_key=api_key)
        return self.client

    def analyze(self, state: AgentState) -> Dict[str, Any]:
        target      = state.get("target_company", "Unknown")
        industry    = state.get("industry", "")
        competitors = state.get("categorized_competitors", [])

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
            print("  [Analyst] All models failed — returning empty analysis")
            return {"analysis": {"swot": {}, "comparison_matrix": [], "threat_ranking": [], "opportunity_gaps": []}}

        analysis = self._parse_json_object(response.text or "")

        # Log SWOT depth for visibility
        swot = analysis.get("swot", {})
        for quadrant in ["strengths", "weaknesses", "opportunities", "threats"]:
            count = len(swot.get(quadrant, []))
            print(f"  [Analyst] {quadrant}: {count} points")

        return {"analysis": analysis}

    def _parse_json_object(self, text: str) -> dict:
        """Extract an analysis object from an LLM response.

        A brace in the preamble must not cause the SWOT object to be dropped.
        """
        data = parse_json_object(text)
        if text and text.strip() and not data:
            print("  [Analyst] Warning: no JSON object found")
        return data
