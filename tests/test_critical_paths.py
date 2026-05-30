import os
import unittest
from unittest.mock import patch

from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class AgentApiKeyTests(unittest.TestCase):
    def setUp(self):
        self._old_key = os.environ.pop("GEMINI_API_KEY", None)

    def tearDown(self):
        if self._old_key is not None:
            os.environ["GEMINI_API_KEY"] = self._old_key
        else:
            os.environ.pop("GEMINI_API_KEY", None)

    def test_explicit_api_key_is_used_without_environment(self):
        cases = [
            ("agents.researcher.genai.Client", ResearcherAgent),
            ("agents.categorizer.genai.Client", CategorizerAgent),
            ("agents.analyst.genai.Client", AnalystAgent),
            ("agents.evaluator.genai.Client", EvaluatorAgent),
        ]

        for patch_target, agent_cls in cases:
            with self.subTest(agent=agent_cls.__name__):
                with patch(patch_target) as client_factory:
                    agent_cls(api_key="user-session-key")._get_client()

                client_factory.assert_called_once_with(api_key="user-session-key")
                self.assertNotIn("GEMINI_API_KEY", os.environ)


class EvaluatorScoreTests(unittest.TestCase):
    def test_calculate_score_accepts_numeric_strings(self):
        breakdown = {
            criterion: {"score": "8"}
            for criterion in [
                "competitor_count",
                "pricing_coverage",
                "feature_coverage",
                "funding_data",
                "hiring_signals",
                "swot_depth",
            ]
        }

        self.assertEqual(EvaluatorAgent(api_key="unused")._calculate_score(breakdown), 80)

    def test_calculate_score_clamps_invalid_values(self):
        score = EvaluatorAgent(api_key="unused")._calculate_score(
            {
                "competitor_count": {"score": "11"},
                "pricing_coverage": {"score": "-2"},
                "feature_coverage": {"score": "bad"},
                "funding_data": {"score": None},
                "hiring_signals": {"score": 7},
                "swot_depth": {},
            }
        )

        self.assertEqual(score, 49)


class ResearcherRetryTests(unittest.TestCase):
    def test_retry_api_failure_preserves_existing_results(self):
        class FailingModels:
            def generate_content(self, *args, **kwargs):
                raise RuntimeError("temporary API outage")

        agent = ResearcherAgent(api_key="unused")
        agent.client = type("Client", (), {"models": FailingModels()})()
        existing = [
            {"company_name": "Alpha", "raw_snippets": ["old fact"], "sources": ["old.example"]}
        ]

        result = agent.research(
            {
                "target_company": "Target",
                "industry": "software",
                "iteration": 1,
                "research_results": existing,
                "evaluation": {"suggested_queries": ["alpha pricing"]},
            }
        )

        self.assertEqual(result["research_results"], existing)

    def test_retry_merge_ignores_unnamed_new_results_without_crashing(self):
        class SuccessfulModels:
            def generate_content(self, *args, **kwargs):
                return type(
                    "Response",
                    (),
                    {
                        "text": (
                            '[{"raw_snippets":["missing name"]}, '
                            '{"company_name":"Alpha","raw_snippets":["new fact"],"sources":["new.example"]}]'
                        )
                    },
                )()

        agent = ResearcherAgent(api_key="unused")
        agent.client = type("Client", (), {"models": SuccessfulModels()})()

        result = agent.research(
            {
                "target_company": "Target",
                "industry": "software",
                "iteration": 1,
                "research_results": [
                    {"company_name": "Alpha", "raw_snippets": ["old fact"], "sources": ["old.example"]}
                ],
                "evaluation": {"suggested_queries": ["alpha pricing"]},
            }
        )

        self.assertEqual(
            result["research_results"],
            [
                {
                    "company_name": "Alpha",
                    "raw_snippets": ["old fact", "new fact"],
                    "sources": ["old.example", "new.example"],
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
