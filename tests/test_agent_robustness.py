import unittest

from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class FailingClientAgent:
    def __call__(self):
        raise RuntimeError("api down")


class AgentRobustnessTests(unittest.TestCase):
    def test_evaluator_coerces_string_scores(self):
        breakdown = {
            "competitor_count": {"score": "8"},
            "pricing_coverage": {"score": "8"},
            "feature_coverage": {"score": "8"},
            "funding_data": {"score": "8"},
            "hiring_signals": {"score": "8"},
            "swot_depth": {"score": "8"},
        }

        self.assertEqual(EvaluatorAgent()._calculate_score(breakdown), 80)

    def test_evaluator_defaults_and_clamps_malformed_scores(self):
        breakdown = {
            "competitor_count": {"score": None},
            "pricing_coverage": {"score": "not-a-number"},
            "feature_coverage": {"score": 99},
            "funding_data": {"score": -3},
            "hiring_signals": {},
            "swot_depth": "bad-shape",
        }

        # Defaults are 5/10, over-range values clamp to 10, negatives clamp to 0.
        self.assertEqual(EvaluatorAgent()._calculate_score(breakdown), 50)

    def test_json_list_parsers_ignore_non_object_items(self):
        payload = '[{"company_name": "A"}, "bad", 7, {"company_name": "B"}]'

        self.assertEqual(
            ResearcherAgent()._parse_json_list(payload),
            [{"company_name": "A"}, {"company_name": "B"}],
        )
        self.assertEqual(
            CategorizerAgent()._parse_json_list(payload),
            [{"company_name": "A"}, {"company_name": "B"}],
        )

    def test_researcher_preserves_retry_results_on_api_failure(self):
        existing = [
            {
                "company_name": "A",
                "raw_snippets": ["known fact"],
                "sources": ["https://example.com"],
            }
        ]
        agent = ResearcherAgent(api_key="test-key")
        agent._get_client = FailingClientAgent()

        result = agent.research(
            {
                "target_company": "Target",
                "industry": "fintech",
                "iteration": 1,
                "research_results": existing,
                "evaluation": {"suggested_queries": ["A pricing"]},
            }
        )

        self.assertEqual(result["research_results"], existing)

    def test_analyst_preserves_retry_analysis_on_api_failure(self):
        existing = {
            "swot": {"strengths": ["existing"], "weaknesses": [], "opportunities": [], "threats": []},
            "comparison_matrix": [],
            "threat_ranking": [],
            "opportunity_gaps": ["existing gap"],
        }
        agent = AnalystAgent(api_key="test-key")
        agent._get_client = FailingClientAgent()

        result = agent.analyze(
            {
                "target_company": "Target",
                "industry": "fintech",
                "iteration": 1,
                "categorized_competitors": [{"company_name": "A"}],
                "analysis": existing,
            }
        )

        self.assertEqual(result["analysis"], existing)


if __name__ == "__main__":
    unittest.main()
