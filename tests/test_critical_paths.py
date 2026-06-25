import importlib
import sys
import types
import unittest


def _install_optional_dependency_stubs():
    try:
        import dotenv  # noqa: F401
    except Exception:
        dotenv_module = types.ModuleType("dotenv")
        dotenv_module.load_dotenv = lambda *args, **kwargs: None
        sys.modules["dotenv"] = dotenv_module

    try:
        import google.genai  # noqa: F401
    except Exception:
        google_module = sys.modules.setdefault("google", types.ModuleType("google"))
        genai_module = types.ModuleType("google.genai")
        genai_module.Client = lambda api_key: types.SimpleNamespace(api_key=api_key)
        genai_module.types = types.SimpleNamespace()
        sys.modules["google.genai"] = genai_module
        setattr(google_module, "genai", genai_module)

    try:
        import langgraph.graph  # noqa: F401
    except Exception:
        langgraph_module = sys.modules.setdefault("langgraph", types.ModuleType("langgraph"))
        graph_module = types.ModuleType("langgraph.graph")
        graph_module.END = "__END__"
        graph_module.StateGraph = object
        sys.modules["langgraph.graph"] = graph_module
        setattr(langgraph_module, "graph", graph_module)


_install_optional_dependency_stubs()

import config
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class CriticalPathTests(unittest.TestCase):
    def test_per_run_api_key_agents_do_not_populate_global_singletons(self):
        import orchestrator

        saved_agents = (
            orchestrator._researcher,
            orchestrator._categorizer,
            orchestrator._analyst,
            orchestrator._evaluator,
        )
        try:
            orchestrator._researcher = None
            orchestrator._categorizer = None
            orchestrator._analyst = None
            orchestrator._evaluator = None

            agents_a = orchestrator._get_agents(api_key="user-a-key")
            agents_b = orchestrator._get_agents(api_key="user-b-key")

            self.assertTrue(all(agent.api_key == "user-a-key" for agent in agents_a))
            self.assertTrue(all(agent.api_key == "user-b-key" for agent in agents_b))
            self.assertTrue(all(a is not b for a, b in zip(agents_a, agents_b)))
            self.assertIsNone(orchestrator._researcher)
            self.assertIsNone(orchestrator._categorizer)
            self.assertIsNone(orchestrator._analyst)
            self.assertIsNone(orchestrator._evaluator)

            global_agents_a = orchestrator._get_agents()
            global_agents_b = orchestrator._get_agents()
            self.assertTrue(all(a is b for a, b in zip(global_agents_a, global_agents_b)))
            self.assertTrue(all(agent.api_key is None for agent in global_agents_a))
        finally:
            (
                orchestrator._researcher,
                orchestrator._categorizer,
                orchestrator._analyst,
                orchestrator._evaluator,
            ) = saved_agents

    def test_research_retry_failure_preserves_existing_results(self):
        class FailingModels:
            def generate_content(self, *args, **kwargs):
                raise RuntimeError("quota exhausted")

        existing = [
            {
                "company_name": "Square",
                "raw_snippets": ["old pricing data"],
                "sources": ["square.example"],
            }
        ]
        agent = ResearcherAgent(api_key="unused")
        agent._get_client = lambda: types.SimpleNamespace(models=FailingModels())

        result = agent.research({
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Square pricing"]},
            "research_results": existing,
        })

        self.assertEqual(result["research_results"], existing)
        self.assertEqual(result["iteration"], 1)

    def test_research_and_categorizer_merge_ignore_schema_invalid_items(self):
        researcher = ResearcherAgent(api_key="unused")
        self.assertEqual(
            researcher._normalize_results([
                {"company_name": None, "raw_snippets": ["bad"]},
                {"raw_snippets": ["missing name"]},
                "not a dict",
                {"company_name": " Square ", "raw_snippets": "new fact", "sources": None},
            ]),
            [{"company_name": "Square", "raw_snippets": ["new fact"], "sources": []}],
        )

        categorizer = CategorizerAgent(api_key="unused")
        merged = categorizer._merge(
            [
                {
                    "company_name": "Square",
                    "pricing": None,
                    "key_features": ["POS"],
                    "target_audience": None,
                    "funding": None,
                    "hiring_signals": [],
                    "recent_news": [],
                    "customer_sentiment": None,
                }
            ],
            [
                "not a dict",
                {"company_name": None, "pricing": "bad"},
                {
                    "company_name": "Square",
                    "pricing": "2.9% + 30c",
                    "key_features": "hardware",
                    "hiring_signals": None,
                    "recent_news": ["launch"],
                },
            ],
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["pricing"], "2.9% + 30c")
        self.assertEqual(merged[0]["key_features"], ["POS", "hardware"])
        self.assertEqual(merged[0]["recent_news"], ["launch"])

    def test_evaluator_score_calculation_coerces_and_clamps_model_values(self):
        evaluator = EvaluatorAgent(api_key="unused")

        string_scores = {
            criterion: {"score": "8/10"}
            for criterion in config.EVAL_WEIGHTS
        }
        self.assertEqual(evaluator._calculate_score(string_scores), 80)

        huge_scores = {
            criterion: {"score": 80}
            for criterion in config.EVAL_WEIGHTS
        }
        self.assertEqual(evaluator._calculate_score(huge_scores), 100)

        invalid_scores = {
            criterion: {"score": None}
            for criterion in config.EVAL_WEIGHTS
        }
        self.assertEqual(evaluator._calculate_score(invalid_scores), 50)


if __name__ == "__main__":
    unittest.main()
