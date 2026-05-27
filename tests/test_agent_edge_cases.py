import unittest

from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent
import config


class _FailingModels:
    def generate_content(self, *args, **kwargs):
        raise RuntimeError("model unavailable")


class _FailingClient:
    models = _FailingModels()


class ResearcherRetryTests(unittest.TestCase):
    def test_retry_failure_preserves_existing_research_results(self):
        agent = ResearcherAgent()
        agent._get_client = lambda: _FailingClient()
        existing_results = [
            {
                "company_name": "Acme",
                "raw_snippets": ["existing pricing fact"],
                "sources": ["https://example.com/acme"],
            }
        ]
        state = {
            "target_company": "TargetCo",
            "industry": "payments",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": existing_results,
        }

        result = agent.research(state)

        self.assertEqual(result["research_results"], existing_results)
        self.assertEqual(result["iteration"], 1)

    def test_retry_merge_tolerates_schema_incomplete_rows(self):
        agent = ResearcherAgent()
        existing_results = [
            {"raw_snippets": ["orphan fact"]},
            {"company_name": "Acme", "raw_snippets": ["old fact"], "sources": ["source-a"]},
        ]
        new_results = [
            {"company_name": "Acme", "raw_snippets": ["new fact"], "sources": ["source-a", "source-b"]},
            {"raw_snippets": ["unnamed retry fact"], "sources": ["source-c"]},
            {"company_name": "Beta", "sources": "source-d"},
        ]

        merged = agent._merge_results(existing_results, new_results)

        self.assertEqual(merged[0]["raw_snippets"], ["orphan fact"])
        acme = next(comp for comp in merged if comp.get("company_name") == "Acme")
        self.assertEqual(acme["raw_snippets"], ["old fact", "new fact"])
        self.assertEqual(acme["sources"], ["source-a", "source-b"])
        beta = next(comp for comp in merged if comp.get("company_name") == "Beta")
        self.assertEqual(beta["raw_snippets"], [])
        self.assertEqual(beta["sources"], ["source-d"])


class EvaluatorScoreTests(unittest.TestCase):
    def test_calculate_score_accepts_numeric_strings(self):
        agent = EvaluatorAgent()
        breakdown = {
            criterion: {"score": "8"}
            for criterion in config.EVAL_WEIGHTS
        }

        self.assertEqual(agent._calculate_score(breakdown), 80)

    def test_calculate_score_defaults_invalid_values_and_clamps_range(self):
        agent = EvaluatorAgent()

        invalid_breakdown = {
            criterion: {"score": "not-a-number"}
            for criterion in config.EVAL_WEIGHTS
        }
        high_breakdown = {
            criterion: {"score": 12}
            for criterion in config.EVAL_WEIGHTS
        }
        low_breakdown = {
            criterion: {"score": -2}
            for criterion in config.EVAL_WEIGHTS
        }

        self.assertEqual(agent._calculate_score(invalid_breakdown), 50)
        self.assertEqual(agent._calculate_score(high_breakdown), 100)
        self.assertEqual(agent._calculate_score(low_breakdown), 0)


if __name__ == "__main__":
    unittest.main()
