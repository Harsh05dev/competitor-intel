import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.analyst import AnalystAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class _FakeModels:
    def __init__(self, text=None, exc=None):
        self.text = text
        self.exc = exc

    def generate_content(self, **kwargs):
        if self.exc:
            raise self.exc
        return SimpleNamespace(text=self.text)


class _FakeClient:
    def __init__(self, text=None, exc=None):
        self.models = _FakeModels(text=text, exc=exc)


class CriticalRegressionTests(unittest.TestCase):
    def test_evaluator_coerces_and_clamps_rubric_scores(self):
        breakdown = {
            "competitor_count": {"score": "8"},
            "pricing_coverage": {"score": "12"},
            "feature_coverage": {"score": None},
            "funding_data": {"score": {"bad": "shape"}},
            "hiring_signals": {"score": -3},
            "swot_depth": {"score": 7.5},
        }

        score = EvaluatorAgent()._calculate_score(breakdown)

        self.assertEqual(score, 64)

    def test_researcher_retry_failure_preserves_existing_results(self):
        prior_results = [
            {
                "company_name": "Acme",
                "raw_snippets": ["existing fact"],
                "sources": ["https://example.com"],
            }
        ]
        state = {"iteration": 1, "research_results": prior_results, "evaluation": {}}

        result = ResearcherAgent().research(state)

        self.assertEqual(result["research_results"], prior_results)

    def test_researcher_retry_merge_tolerates_missing_fields(self):
        agent = ResearcherAgent(api_key="test-key")
        agent._get_client = lambda: _FakeClient(
            text='[{"company_name":"Acme","raw_snippets":["new fact"],"sources":["https://new.example"]},'
            '{"raw_snippets":["unnamed result"]}]'
        )
        state = {
            "iteration": 1,
            "industry": "fintech",
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": [{"company_name": "Acme", "raw_snippets": ["existing fact"]}],
        }

        result = agent.research(state)

        self.assertEqual(len(result["research_results"]), 1)
        self.assertEqual(result["research_results"][0]["company_name"], "Acme")
        self.assertEqual(result["research_results"][0]["raw_snippets"], ["existing fact", "new fact"])
        self.assertEqual(result["research_results"][0]["sources"], ["https://new.example"])

    def test_analyst_retry_failure_preserves_existing_analysis(self):
        prior_analysis = {
            "swot": {"strengths": ["strong"], "weaknesses": [], "opportunities": [], "threats": []},
            "comparison_matrix": [],
            "threat_ranking": [],
            "opportunity_gaps": [],
        }
        agent = AnalystAgent(api_key="test-key")
        agent._get_client = lambda: _FakeClient(exc=RuntimeError("quota exhausted"))
        state = {
            "iteration": 1,
            "target_company": "TargetCo",
            "industry": "fintech",
            "categorized_competitors": [{"company_name": "Acme"}],
            "analysis": prior_analysis,
        }

        result = agent.analyze(state)

        self.assertEqual(result["analysis"], prior_analysis)

    def test_agent_client_rebuilds_when_environment_key_rotates(self):
        created_keys = []

        def fake_client(api_key):
            created_keys.append(api_key)
            return object()

        agent = ResearcherAgent()

        with patch("agents.researcher.genai.Client", side_effect=fake_client):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "first"}, clear=False):
                first_client = agent._get_client()
            with patch.dict(os.environ, {"GEMINI_API_KEY": "second"}, clear=False):
                second_client = agent._get_client()

        self.assertNotEqual(first_client, second_client)
        self.assertEqual(created_keys, ["first", "second"])


if __name__ == "__main__":
    unittest.main()
