import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

import orchestrator
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class CorrectnessRegressionTests(unittest.TestCase):
    def test_build_graph_passes_api_key_to_run_local_agents(self):
        with (
            patch.object(orchestrator, "ResearcherAgent") as researcher_cls,
            patch.object(orchestrator, "CategorizerAgent") as categorizer_cls,
            patch.object(orchestrator, "AnalystAgent") as analyst_cls,
            patch.object(orchestrator, "EvaluatorAgent") as evaluator_cls,
        ):
            orchestrator.build_graph(api_key="run-key")

        researcher_cls.assert_called_once_with(api_key="run-key")
        categorizer_cls.assert_called_once_with(api_key="run-key")
        analyst_cls.assert_called_once_with(api_key="run-key")
        evaluator_cls.assert_called_once_with(api_key="run-key")

    def test_evaluator_score_accepts_string_values_and_clamps(self):
        agent = EvaluatorAgent()
        breakdown = {
            "competitor_count": {"score": "8"},
            "pricing_coverage": {"score": "11"},
            "feature_coverage": {"score": "-2"},
            "funding_data": {"score": "bad"},
            "hiring_signals": {"score": None},
            "swot_depth": {"score": 7.5},
        }

        score = agent._calculate_score(breakdown)

        self.assertEqual(score, 59)

    def test_researcher_retry_merge_skips_unnamed_entries(self):
        response = SimpleNamespace(
            text='[{"company_name": "Acme", "raw_snippets": ["new"], "sources": ["new-src"]}, '
            '{"raw_snippets": ["unnamed"]}]'
        )
        fake_client = SimpleNamespace(
            models=SimpleNamespace(generate_content=MagicMock(return_value=response))
        )
        agent = ResearcherAgent(api_key="test-key")
        state = {
            "target_company": "Target",
            "industry": "software",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": [
                {"raw_snippets": ["missing name"]},
                {"company_name": "Acme", "raw_snippets": ["old"], "sources": ["old-src"]},
            ],
        }

        with patch.object(agent, "_get_client", return_value=fake_client):
            result = agent.research(state)

        self.assertEqual(
            result["research_results"],
            [
                {
                    "company_name": "Acme",
                    "raw_snippets": ["old", "new"],
                    "sources": ["old-src", "new-src"],
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
