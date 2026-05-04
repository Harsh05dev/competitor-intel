import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai

from models.schemas import AgentState

load_dotenv()


class EvaluatorAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def evaluate(self, state: AgentState) -> Dict[str, Any]:
        data = state.get("categorized_competitors", [])

        prompt = f"""
Evaluate this competitor dataset and return JSON:

{data}

Return:
{{
  "score": int,
  "passed": boolean,
  "gaps": [str],
  "suggested_queries": [str]
}}
"""

        models = [
            "gemini-flash-latest",
            "gemini-pro-latest"
        ]

        response = None

        for m in models:
            try:
                print(f"[Evaluator] Using {m}")
                response = self.client.models.generate_content(
                    model=m,
                    contents=prompt
                )
                break
            except Exception as e:
                print(f"[Evaluator] Failed {m}: {e}")

        if not response:
            return {
                "evaluation": {
                    "score": 0,
                    "passed": False,
                    "gaps": ["API failure"],
                    "suggested_queries": []
                }
            }

        text = response.text

        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            parsed = json.loads(text[start:end])
        except:
            parsed = {
                "score": 0,
                "passed": False,
                "gaps": ["Parse failed"],
                "suggested_queries": []
            }

        parsed["passed"] = parsed.get("score", 0) >= 70

        return {"evaluation": parsed}