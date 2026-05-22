import json
import os
import unittest
from unittest.mock import patch

from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class _FailingModels:
    def generate_content(self, **kwargs):
        raise RuntimeError("model unavailable")


class _FailingClient:
    models = _FailingModels()


class _SuccessModels:
    def __init__(self, text):
        self._text = text

    def generate_content(self, **kwargs):
        return type("Response", (), {"text": self._text})()


class _SuccessClient:
    def __init__(self, text):
        self.models = _SuccessModels(text)


class CriticalFixTests(unittest.TestCase):
    def test_research_retry_preserves_existing_results_when_models_fail(self):
        existing = [{"company_name": "Acme", "raw_snippets": ["old"], "sources": ["old-url"]}]
        agent = ResearcherAgent(api_key="test-key")
        agent.client = _FailingClient()

        result = agent.research({
            "target_company": "Target",
            "industry": "testing",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": existing,
        })

        self.assertEqual(result["research_results"], existing)

    def test_research_retry_merge_tolerates_missing_fields(self):
        response_text = json.dumps([
            {"company_name": "Acme", "raw_snippets": ["new"], "sources": ["new-url"]},
            {"company_name": None, "raw_snippets": ["ignored"], "sources": []},
        ])
        agent = ResearcherAgent(api_key="test-key")
        agent.client = _SuccessClient(response_text)

        result = agent.research({
            "target_company": "Target",
            "industry": "testing",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": [
                {"raw_snippets": ["unnamed but preserved"]},
                {"company_name": "Acme", "sources": None},
            ],
        })

        self.assertEqual(result["research_results"][0], {"raw_snippets": ["unnamed but preserved"]})
        self.assertEqual(result["research_results"][1]["company_name"], "Acme")
        self.assertEqual(result["research_results"][1]["raw_snippets"], ["new"])
        self.assertEqual(result["research_results"][1]["sources"], ["new-url"])

    def test_evaluator_score_accepts_string_values_and_clamps(self):
        score = EvaluatorAgent(api_key="test-key")._calculate_score({
            "competitor_count": {"score": "10"},
            "pricing_coverage": {"score": "8"},
            "feature_coverage": {"score": 12},
            "funding_data": {"score": "-1"},
            "hiring_signals": {"score": "not-a-number"},
            "swot_depth": {"score": None},
        })

        self.assertEqual(score, 66)

    def test_agents_use_explicit_api_key_over_process_environment(self):
        os.environ["GEMINI_API_KEY"] = "env-key"
        cases = [
            ("agents.researcher.genai.Client", ResearcherAgent),
            ("agents.categorizer.genai.Client", CategorizerAgent),
            ("agents.analyst.genai.Client", AnalystAgent),
            ("agents.evaluator.genai.Client", EvaluatorAgent),
        ]

        for client_path, agent_cls in cases:
            with self.subTest(agent=agent_cls.__name__):
                with patch(client_path) as client_cls:
                    agent_cls(api_key="user-key")._get_client()
                    client_cls.assert_called_once_with(api_key="user-key")


if __name__ == "__main__":
    unittest.main()
