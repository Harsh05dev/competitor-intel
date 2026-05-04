import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai

from models.schemas import AgentState

load_dotenv()


class ResearcherAgent:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def research(self, state: AgentState) -> Dict[str, Any]:
        company = state.get("target_company", "")
        industry = state.get("industry", "")
        queries = state.get("evaluation", {}).get("suggested_queries", [])

        if state.get("iteration", 0) == 0:
            prompt = f"""
Find 4 competitors of {company} in {industry}.

Return ONLY JSON:
[
  {{
    "company_name": "string",
    "raw_snippets": ["fact1", "fact2", "fact3", "fact4"],
    "sources": ["url1"]
  }}
]
"""
        else:
            prompt = f"""
Improve competitor data using:
{queries}

Return ONLY JSON:
[
  {{
    "company_name": "string",
    "raw_snippets": ["fact1", "fact2", "fact3", "fact4"],
    "sources": ["url1"]
  }}
]
"""

        models = [
            "gemini-flash-latest",
            "gemini-pro-latest"
        ]

        response = None

        for m in models:
            try:
                print(f"[Researcher] Using {m}")
                response = self.client.models.generate_content(
                    model=m,
                    contents=prompt
                )
                break
            except Exception as e:
                print(f"[Researcher] Failed {m}: {e}")

        if not response:
            return {
                "research_results": [],
                "iteration": state.get("iteration", 0) + 1
            }

        text = response.text

        try:
            start = text.find("[")
            end = text.rfind("]") + 1
            data = json.loads(text[start:end])
        except:
            data = []

        return {
            "research_results": data,
            "iteration": state.get("iteration", 0) + 1
        }