import os
import pathlib
import types
import unittest
from unittest.mock import patch

# Stub optional imports before agent modules load (Streamlit Cloud / bare env).
def _install_optional_dependency_stubs():
    try:
        import dotenv  # noqa: F401
    except Exception:
        dotenv_module = types.ModuleType("dotenv")
        dotenv_module.load_dotenv = lambda *args, **kwargs: None
        import sys
        sys.modules["dotenv"] = dotenv_module

    try:
        import google.genai  # noqa: F401
    except Exception:
        import sys
        google_module = sys.modules.setdefault("google", types.ModuleType("google"))
        genai_module = types.ModuleType("google.genai")
        genai_module.Client = lambda api_key: types.SimpleNamespace(api_key=api_key)
        genai_module.types = types.SimpleNamespace(
            GenerateContentConfig=object,
            Tool=object,
            GoogleSearch=object,
        )
        sys.modules["google.genai"] = genai_module
        setattr(google_module, "genai", genai_module)

    try:
        import langgraph.graph  # noqa: F401
    except Exception:
        import sys
        langgraph_module = sys.modules.setdefault("langgraph", types.ModuleType("langgraph"))
        graph_module = types.ModuleType("langgraph.graph")
        graph_module.END = "__END__"
        graph_module.StateGraph = object
        sys.modules["langgraph.graph"] = graph_module
        setattr(langgraph_module, "graph", graph_module)


_install_optional_dependency_stubs()

import config
import main
import orchestrator
from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class CriticalPathTests(unittest.TestCase):
    def test_agents_prefer_explicit_api_key_over_process_env(self):
        agent_modules = [
            ("agents.researcher.genai.Client", ResearcherAgent),
            ("agents.categorizer.genai.Client", CategorizerAgent),
            ("agents.analyst.genai.Client", AnalystAgent),
            ("agents.evaluator.genai.Client", EvaluatorAgent),
        ]

        with patch.dict(os.environ, {"GEMINI_API_KEY": "shared-process-key"}):
            for client_path, agent_class in agent_modules:
                with self.subTest(agent=agent_class.__name__):
                    client = object()
                    with patch(client_path, return_value=client) as client_factory:
                        agent = agent_class(api_key="session-key")
                        self.assertIs(agent._get_client(), client)
                        self.assertIs(agent._get_client(), client)
                        client_factory.assert_called_once_with(api_key="session-key")

    def test_each_pipeline_run_gets_a_distinct_agent_set(self):
        first = orchestrator._create_agents("first-session-key")
        second = orchestrator._create_agents("second-session-key")

        self.assertTrue(all(agent.api_key == "first-session-key" for agent in first))
        self.assertTrue(all(agent.api_key == "second-session-key" for agent in second))
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_wrapper_passes_key_without_using_process_environment(self):
        with patch("main.run_analysis", return_value={"status": "complete"}) as run:
            result = main.Orchestrator(api_key="session-key").run(
                company="Acme",
                industry="widgets",
            )

        self.assertEqual(result, {"status": "complete"})
        run.assert_called_once_with(
            company="Acme",
            industry="widgets",
            api_key="session-key",
        )

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

    def test_research_retry_null_suggested_queries_preserves_results(self):
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
            "evaluation": {"suggested_queries": None},
            "research_results": existing,
        })

        self.assertEqual(result["research_results"], existing)

    def test_research_retry_merge_skips_unnamed_entries(self):
        agent = ResearcherAgent(api_key="unused")

        parsed = [
            {"raw_snippets": ["orphan fact"], "sources": []},
            {"company_name": "Adyen", "raw_snippets": ["new fact"], "sources": ["adyen.example"]},
        ]
        agent._parse_json_list = lambda text: parsed
        agent._get_client = lambda: types.SimpleNamespace(
            models=types.SimpleNamespace(
                generate_content=lambda *args, **kwargs: types.SimpleNamespace(text="[]")
            )
        )

        # Bypass GenerateContentConfig construction by patching the call path's config usage.
        with patch("agents.researcher.types.GenerateContentConfig", return_value=object()), \
             patch("agents.researcher.types.Tool", return_value=object()), \
             patch("agents.researcher.types.GoogleSearch", return_value=object()):
            result = agent.research({
                "target_company": "Stripe",
                "industry": "fintech",
                "iteration": 1,
                "evaluation": {"suggested_queries": ["Adyen pricing"]},
                "research_results": [
                    {"company_name": "Square", "raw_snippets": ["old"], "sources": []},
                    {"raw_snippets": ["unnamed prior"], "sources": []},
                ],
            })

        names = [r.get("company_name") for r in result["research_results"]]
        self.assertIn("Square", names)
        self.assertIn("Adyen", names)
        self.assertTrue(any(r.get("raw_snippets") == ["unnamed prior"] for r in result["research_results"]))

    def test_research_retry_merge_does_not_explode_string_snippets(self):
        agent = ResearcherAgent(api_key="unused")
        agent._parse_json_list = lambda text: [
            {"company_name": "Square", "raw_snippets": "new pricing fact", "sources": "square.example"},
        ]
        agent._get_client = lambda: types.SimpleNamespace(
            models=types.SimpleNamespace(
                generate_content=lambda *args, **kwargs: types.SimpleNamespace(text="[]")
            )
        )

        with patch("agents.researcher.types.GenerateContentConfig", return_value=object()), \
             patch("agents.researcher.types.Tool", return_value=object()), \
             patch("agents.researcher.types.GoogleSearch", return_value=object()):
            result = agent.research({
                "target_company": "Stripe",
                "industry": "fintech",
                "iteration": 1,
                "evaluation": {"suggested_queries": ["Square pricing"]},
                "research_results": [
                    {"company_name": "Square", "raw_snippets": "old pricing", "sources": None},
                ],
            })

        square = next(r for r in result["research_results"] if r.get("company_name") == "Square")
        self.assertEqual(square["raw_snippets"], ["old pricing", "new pricing fact"])
        self.assertEqual(square["sources"], ["square.example"])

    def test_analyst_retry_failure_preserves_existing_analysis(self):
        class FailingModels:
            def generate_content(self, *args, **kwargs):
                raise RuntimeError("quota exhausted")

        prior = {
            "swot": {"strengths": ["brand"], "weaknesses": [], "opportunities": [], "threats": []},
            "comparison_matrix": [],
            "threat_ranking": ["Square"],
            "opportunity_gaps": ["SMB pricing"],
        }
        agent = AnalystAgent(api_key="unused")
        agent._get_client = lambda: types.SimpleNamespace(models=FailingModels())

        result = agent.analyze({
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "categorized_competitors": [{"company_name": "Square"}],
            "analysis": prior,
        })

        self.assertEqual(result["analysis"], prior)

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
        self.assertEqual(evaluator._calculate_score(None), 50)

    def test_categorizer_merge_skips_null_company_names(self):
        agent = CategorizerAgent(api_key="unused")
        merged = agent._merge(
            existing=[
                {"company_name": "Square", "pricing": "2.6%", "key_features": ["POS"]},
                {"company_name": None, "pricing": "unknown", "key_features": []},
            ],
            new_data=[
                {"company_name": None, "pricing": "should not crash"},
                {"company_name": "Adyen", "pricing": "IC++", "key_features": ["Enterprise"]},
                "not-a-dict",
            ],
        )
        names = [c.get("company_name") for c in merged]
        self.assertIn("Square", names)
        self.assertIn("Adyen", names)
        square = next(c for c in merged if c.get("company_name") == "Square")
        self.assertEqual(square["pricing"], "2.6%")

    def test_categorizer_merge_coerces_string_list_fields(self):
        agent = CategorizerAgent(api_key="unused")
        merged = agent._merge(
            existing=[{"company_name": "Square", "key_features": ["POS"], "hiring_signals": None, "recent_news": "old news"}],
            new_data=[{"company_name": "Square", "key_features": "hardware", "hiring_signals": "50 jobs", "recent_news": ["launch"]}],
        )
        square = merged[0]
        self.assertEqual(square["key_features"], ["POS", "hardware"])
        self.assertEqual(square["hiring_signals"], ["50 jobs"])
        self.assertEqual(square["recent_news"], ["old news", "launch"])

    def test_categorizer_prompt_build_survives_null_snippets(self):
        class DummyModels:
            def generate_content(self, *args, **kwargs):
                return types.SimpleNamespace(text="[]")

        agent = CategorizerAgent(api_key="unused")
        agent._get_client = lambda: types.SimpleNamespace(models=DummyModels())

        with patch("agents.categorizer.types.GenerateContentConfig", return_value=object()):
            result = agent.categorize({
                "iteration": 0,
                "categorized_competitors": [],
                "research_results": [
                    {"company_name": "Square", "raw_snippets": None, "sources": None},
                    "not-a-dict",
                ],
            })

        self.assertEqual(result["categorized_competitors"], [])

    def test_evaluator_prompt_build_survives_null_swot(self):
        class DummyModels:
            def generate_content(self, *args, **kwargs):
                return types.SimpleNamespace(
                    text='{"breakdown": {}, "gaps": [], "suggested_queries": []}'
                )

        agent = EvaluatorAgent(api_key="unused")
        agent._get_client = lambda: types.SimpleNamespace(models=DummyModels())

        with patch("agents.evaluator.types.GenerateContentConfig", return_value=object()):
            result = agent.evaluate({
                "target_company": "Stripe",
                "categorized_competitors": [{"company_name": "Square", "key_features": None}],
                "analysis": {"swot": None, "threat_ranking": None, "opportunity_gaps": None},
            })

        self.assertIn("evaluation", result)
        self.assertIn("score", result["evaluation"])

    def test_format_report_survives_null_swot_and_non_dict_rows(self):
        report = orchestrator.format_report_node({
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "evaluation": {"score": 80},
            "categorized_competitors": [],
            "research_results": [],
            "analysis": {
                "swot": None,
                "comparison_matrix": ["not-a-row", {"company_name": "Square", "pricing_tier": "Flat"}],
                "opportunity_gaps": None,
            },
            "logs": [],
        })
        self.assertIn("Stripe", report["final_output"])
        self.assertIn("Square", report["final_output"])
        self.assertEqual(report["status"], "complete")

    def test_ui_live_mode_isolates_keys_and_preserves_reports(self):
        source = pathlib.Path(__file__).resolve().parents[1].joinpath("ui", "app.py").read_text()
        self.assertNotIn('os.environ["GEMINI_API_KEY"]', source)
        self.assertIn("last_result", source)
        self.assertIn("html.escape", source)
        self.assertNotIn("[:200]", source)


if __name__ == "__main__":
    unittest.main()
