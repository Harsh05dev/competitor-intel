import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.analyst import AnalystAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent
from orchestrator import _get_agents


class _FailingModels:
    def generate_content(self, *args, **kwargs):
        raise RuntimeError("api unavailable")


class _FailingClient:
    models = _FailingModels()


class RegressionTests(unittest.TestCase):
    def test_researcher_retry_failure_preserves_existing_results(self):
        existing = [{"company_name": "Adyen", "raw_snippets": ["old"], "sources": ["source"]}]
        agent = ResearcherAgent(api_key="run-key")
        agent._get_client = lambda: _FailingClient()

        result = agent.research({
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "research_results": existing,
            "evaluation": {"suggested_queries": ["Adyen pricing"]},
        })

        self.assertEqual(result["research_results"], existing)

    def test_researcher_retry_merge_tolerates_missing_optional_fields(self):
        agent = ResearcherAgent()

        merged = agent._merge_results(
            [{"company_name": "Adyen", "raw_snippets": None, "sources": ["old"]}],
            [
                {"company_name": "Adyen", "raw_snippets": ["new"], "sources": None},
                {"raw_snippets": ["cannot match safely"]},
            ],
        )

        self.assertEqual(merged, [{"company_name": "Adyen", "raw_snippets": ["new"], "sources": ["old"]}])

    def test_analyst_retry_failure_preserves_existing_analysis(self):
        existing = {"swot": {"strengths": ["strong API"]}, "comparison_matrix": []}
        agent = AnalystAgent(api_key="run-key")
        agent._get_client = lambda: _FailingClient()

        result = agent.analyze({
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "categorized_competitors": [{"company_name": "Adyen"}],
            "analysis": existing,
        })

        self.assertEqual(result["analysis"], existing)

    def test_evaluator_score_coerces_and_clamps_llm_values(self):
        score = EvaluatorAgent()._calculate_score({
            "competitor_count": {"score": "8"},
            "pricing_coverage": {"score": "not-a-number"},
            "feature_coverage": {"score": None},
            "funding_data": {"score": 12},
            "hiring_signals": {"score": -1},
        })

        self.assertEqual(score, 57)

    def test_per_run_agents_use_explicit_key_without_mutating_environment(self):
        os.environ.pop("GEMINI_API_KEY", None)
        researcher, categorizer, analyst, evaluator = _get_agents(api_key="session-key")

        for module_name, agent in [
            ("agents.researcher.genai.Client", researcher),
            ("agents.categorizer.genai.Client", categorizer),
            ("agents.analyst.genai.Client", analyst),
            ("agents.evaluator.genai.Client", evaluator),
        ]:
            with patch(module_name) as client:
                agent._get_client()
                client.assert_called_once_with(api_key="session-key")

        self.assertNotIn("GEMINI_API_KEY", os.environ)


if __name__ == "__main__":
    unittest.main()
