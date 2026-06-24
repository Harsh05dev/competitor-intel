import unittest

from agents.analyst import AnalystAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class _FailingModels:
    def generate_content(self, *args, **kwargs):
        raise RuntimeError("quota exhausted")


class _FailingClient:
    models = _FailingModels()


class _Response:
    def __init__(self, text):
        self.text = text


class _SuccessfulModels:
    def __init__(self, text):
        self.text = text

    def generate_content(self, *args, **kwargs):
        return _Response(self.text)


class _SuccessfulClient:
    def __init__(self, text):
        self.models = _SuccessfulModels(text)


class RetryResilienceTests(unittest.TestCase):
    def test_researcher_preserves_existing_results_when_retry_models_fail(self):
        agent = ResearcherAgent(api_key="test-key")
        agent._get_client = lambda: _FailingClient()
        existing = [
            {"company_name": "Acme", "raw_snippets": ["old fact"], "sources": ["old.example"]}
        ]

        result = agent.research(
            {
                "target_company": "Target",
                "industry": "widgets",
                "iteration": 1,
                "evaluation": {"suggested_queries": ["Acme pricing"]},
                "research_results": existing,
            }
        )

        self.assertEqual(result["research_results"], existing)

    def test_researcher_retry_merge_tolerates_malformed_existing_rows(self):
        agent = ResearcherAgent(api_key="test-key")
        agent._get_client = lambda: _SuccessfulClient(
            '[{"company_name":"Acme","raw_snippets":["new fact"],"sources":["new.example"]}]'
        )

        result = agent.research(
            {
                "target_company": "Target",
                "industry": "widgets",
                "iteration": 1,
                "evaluation": {"suggested_queries": ["Acme pricing"]},
                "research_results": [
                    {"raw_snippets": ["orphan fact"]},
                    {"company_name": "Acme", "raw_snippets": ["old fact"], "sources": ["old.example"]},
                    {"company_name": "OddCo", "raw_snippets": "single fact", "sources": None},
                ],
            }
        )

        by_name = {row.get("company_name"): row for row in result["research_results"]}
        self.assertIn("", by_name)
        self.assertEqual(by_name["Acme"]["raw_snippets"], ["old fact", "new fact"])
        self.assertEqual(by_name["Acme"]["sources"], ["old.example", "new.example"])
        self.assertEqual(by_name["OddCo"]["raw_snippets"], ["single fact"])
        self.assertEqual(by_name["OddCo"]["sources"], [])

    def test_analyst_preserves_existing_analysis_when_retry_models_fail(self):
        agent = AnalystAgent(api_key="test-key")
        agent._get_client = lambda: _FailingClient()
        existing_analysis = {
            "swot": {"strengths": ["specific strength"], "weaknesses": [], "opportunities": [], "threats": []},
            "comparison_matrix": [],
            "threat_ranking": [],
            "opportunity_gaps": [],
        }

        result = agent.analyze(
            {
                "target_company": "Target",
                "industry": "widgets",
                "iteration": 1,
                "categorized_competitors": [{"company_name": "Acme"}],
                "analysis": existing_analysis,
            }
        )

        self.assertEqual(result["analysis"], existing_analysis)

    def test_evaluator_coerces_string_scores(self):
        agent = EvaluatorAgent(api_key="test-key")
        breakdown = {
            "competitor_count": {"score": "10"},
            "pricing_coverage": {"score": "8"},
            "feature_coverage": {"score": "7.5"},
            "funding_data": {"score": "bad"},
            "hiring_signals": {"score": None},
            "swot_depth": {"score": 11},
        }

        score = agent._calculate_score(breakdown)

        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
