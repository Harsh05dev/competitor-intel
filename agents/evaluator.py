"""
agents/evaluator.py — Evaluator Agent

The independent quality gate of the system. This agent:
1. Scores the current output 0-100 on 6 weighted criteria
2. Identifies specific gaps in the data
3. Generates targeted search queries to fill those gaps
4. Returns pass/fail based on config.EVALUATION_THRESHOLD

This agent is what makes the system AGENTIC. Without it:
- There is no feedback loop
- There is no quality control
- The system is just a dumb pipeline

The Evaluator MUST be independent from the Analyst — if the same agent
writes and grades the SWOT, the feedback loop has no credibility.
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

from models.schemas import AgentState
import config

load_dotenv()

SYSTEM_PROMPT = """You are a strict quality evaluator for competitive intelligence reports.
You assess completeness and quality using a structured rubric, then identify specific gaps.

You MUST respond with ONLY a JSON object in this exact format:
{
  "breakdown": {
    "competitor_count":  {"score": 0-10, "notes": "explanation"},
    "pricing_coverage":  {"score": 0-10, "notes": "which competitors have/lack pricing"},
    "feature_coverage":  {"score": 0-10, "notes": "explanation"},
    "funding_data":      {"score": 0-10, "notes": "explanation"},
    "hiring_signals":    {"score": 0-10, "notes": "explanation"},
    "swot_depth":        {"score": 0-10, "notes": "explanation"}
  },
  "gaps": [
    "Specific gap 1 — e.g. Missing pricing for Braintree",
    "Specific gap 2 — e.g. No hiring signals for Adyen"
  ],
  "suggested_queries": [
    "Exact search query to fill gap 1",
    "Exact search query to fill gap 2"
  ]
}

Scoring guide (each criterion 0-10, be STRICT):
- competitor_count:  10=4+ found, 7=3 found, 4=2 found, 2=1 found
- pricing_coverage:  10=all have specific pricing, deduct 2-3 per missing
- feature_coverage:  10=all have 3+ features, deduct per sparse competitor
- funding_data:      10=all have funding info, deduct per missing
- hiring_signals:    10=all have hiring data, deduct per missing
- swot_depth:        10=3+ evidence-backed points per SWOT quadrant, 7=2+ each

Only give 8+ if genuinely strong. Be strict.
suggested_queries must be specific web searches (5-10 words each).
Return ONLY the JSON object, no other text."""


class EvaluatorAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = None  # initialized lazily on first call

    def _get_client(self):
        if self.client is None:
            api_key = self.api_key or os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("No GEMINI_API_KEY set. Please enter your API key.")
            self.client = genai.Client(api_key=api_key)
        return self.client

    def evaluate(self, state: AgentState) -> Dict[str, Any]:
        target      = state.get("target_company", "Unknown")
        competitors = state.get("categorized_competitors", [])
        analysis    = state.get("analysis", {})

        print(f"  [Evaluator] Scoring intelligence report for {target}")

        # Build comprehensive prompt showing all current data
        prompt = f"Evaluate this competitive intelligence report for '{target}':\n\n"
        prompt += f"## Competitors Found ({len(competitors)}):\n"

        for comp in competitors:
            prompt += f"\n### {comp.get('company_name', 'Unknown')}\n"
            prompt += f"- Pricing: {comp.get('pricing') or 'MISSING'}\n"
            features = comp.get('key_features') or []
            prompt += f"- Features: {', '.join(features) if features else 'MISSING'}\n"
            prompt += f"- Funding: {comp.get('funding') or 'MISSING'}\n"
            hiring = comp.get('hiring_signals') or []
            prompt += f"- Hiring: {', '.join(hiring) if hiring else 'MISSING'}\n"
            news = comp.get('recent_news') or []
            prompt += f"- News: {', '.join(news[:2]) if news else 'MISSING'}\n"
            prompt += f"- Sentiment: {comp.get('customer_sentiment') or 'MISSING'}\n"

        swot = analysis.get("swot", {})
        prompt += f"\n## SWOT Analysis:\n"
        for quadrant in ["strengths", "weaknesses", "opportunities", "threats"]:
            items = swot.get(quadrant, [])
            prompt += f"- {quadrant.title()}: {len(items)} points\n"
            for item in items[:3]:
                prompt += f"  • {item}\n"

        prompt += f"\n## Threat Ranking: {analysis.get('threat_ranking', [])}\n"
        prompt += f"## Opportunity Gaps: {analysis.get('opportunity_gaps', [])}\n"
        prompt += "\nScore each criterion 0-10. Be strict. Identify specific gaps with exact search queries."

        # Try models
        models_to_try = [
            config.MODEL_NAME,
            "gemini-2.0-flash-lite",
            "gemini-2.5-flash-lite",
        ]
        response = None

        for model in models_to_try:
            try:
                print(f"  [Evaluator] Trying {model}...")
                response = self._get_client().models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.1,
                    )
                )
                print(f"  [Evaluator] Success with {model}")
                break
            except Exception as e:
                print(f"  [Evaluator] {model} failed: {e}")

        if not response:
            print("  [Evaluator] All models failed — assigning default score 50")
            return {
                "evaluation": {
                    "score":             50,
                    "passed":            False,
                    "breakdown":         {},
                    "gaps":              ["API failure during evaluation"],
                    "suggested_queries": []
                }
            }

        result = self._parse_json_object(response.text or "")

        if "error" in result or not result:
            result = {
                "breakdown":         {},
                "gaps":              ["Evaluation parsing failed"],
                "suggested_queries": []
            }

        # Calculate weighted score from breakdown
        score = self._calculate_score(result.get("breakdown", {}))
        result["score"]  = score
        result["passed"] = score >= config.EVALUATION_THRESHOLD

        print(f"  [Evaluator] Score: {score}/100 — {'PASSED ✓' if result['passed'] else 'FAILED ✗'}")
        if result.get("gaps"):
            for gap in result["gaps"]:
                print(f"  [Evaluator]   ✗ {gap}")

        return {"evaluation": result}

    def _calculate_score(self, breakdown: dict) -> int:
        """
        Calculate weighted composite score from the 6-criteria breakdown.
        Each criterion is scored 0-10, then weighted by config.EVAL_WEIGHTS.
        """
        total = 0
        for criterion, weight in config.EVAL_WEIGHTS.items():
            criterion_data = breakdown.get(criterion, {})
            if isinstance(criterion_data, dict):
                raw_score = criterion_data.get("score", 5)
            else:
                raw_score = 5  # default if parsing was off
            total += (raw_score / 10) * weight
        return int(total)

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
            print("  [Evaluator] Warning: no JSON object found")
            return {}
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError as e:
            print(f"  [Evaluator] JSON parse error: {e}")
            return {}
