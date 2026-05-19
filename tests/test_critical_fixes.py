import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent
from orchestrator import _get_agents


class _FakeResponse:
    text = """
    [
      {"company_name": "Acme", "raw_snippets": ["new fact"], "sources": ["https://example.com"]},
      {"raw_snippets": ["unnamed fact"], "sources": []}
    ]
    """


class _FakeModels:
    def generate_content(self, **_kwargs):
        return _FakeResponse()


class _FakeClient:
    models = _FakeModels()


class CriticalFixTests(unittest.TestCase):
    def test_researcher_retry_merge_tolerates_malformed_entries(self):
        agent = ResearcherAgent(api_key="user-key")
        agent.client = _FakeClient()
        state = {
            "target_company": "Target",
            "industry": "widgets",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": [
                {"company_name": "Acme", "raw_snippets": ["old fact"], "sources": None},
                {"raw_snippets": ["existing unnamed"]},
            ],
        }

        result = agent.research(state)

        acme = next(item for item in result["research_results"] if item.get("company_name") == "Acme")
        self.assertEqual(acme["raw_snippets"], ["old fact", "new fact"])
        self.assertEqual(acme["sources"], ["https://example.com"])
        self.assertEqual(len(result["research_results"]), 3)

    def test_evaluator_accepts_string_scores_from_llm_json(self):
        breakdown = {
            name: {"score": "8", "notes": "string score"}
            for name in [
                "competitor_count",
                "pricing_coverage",
                "feature_coverage",
                "funding_data",
                "hiring_signals",
                "swot_depth",
            ]
        }

        self.assertEqual(EvaluatorAgent()._calculate_score(breakdown), 80)

    def test_explicit_api_key_does_not_use_process_environment(self):
        old_env_key = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "env-key"
        try:
            with patch("agents.researcher.genai.Client") as client_factory:
                agent = ResearcherAgent(api_key="user-key")
                agent._get_client()
                client_factory.assert_called_once_with(api_key="user-key")
        finally:
            if old_env_key is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = old_env_key

    def test_orchestrator_builds_per_run_agents_for_explicit_key(self):
        agents = _get_agents(api_key="user-key")

        self.assertTrue(all(agent.api_key == "user-key" for agent in agents))


if __name__ == "__main__":
    unittest.main()
