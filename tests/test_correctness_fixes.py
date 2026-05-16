import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent
from main import Orchestrator


class ApiKeyIsolationTests(unittest.TestCase):
    def test_orchestrator_passes_explicit_api_key_to_run_analysis(self):
        with patch("main.run_analysis", return_value={"status": "complete"}) as run_analysis:
            result = Orchestrator(api_key=" user-key ").run(company="Stripe", industry="fintech")

        self.assertEqual(result, {"status": "complete"})
        run_analysis.assert_called_once_with(
            company="Stripe",
            industry="fintech",
            api_key="user-key",
        )

    def test_agents_use_explicit_key_instead_of_process_environment(self):
        cases = [
            ("agents.researcher.genai.Client", ResearcherAgent),
            ("agents.categorizer.genai.Client", CategorizerAgent),
            ("agents.analyst.genai.Client", AnalystAgent),
            ("agents.evaluator.genai.Client", EvaluatorAgent),
        ]

        with patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"}):
            for client_path, agent_cls in cases:
                with self.subTest(agent=agent_cls.__name__):
                    with patch(client_path, return_value=object()) as client_ctor:
                        agent_cls(api_key="user-key")._get_client()

                client_ctor.assert_called_once_with(api_key="user-key")


class ResearcherRetryMergeTests(unittest.TestCase):
    def test_retry_merge_ignores_malformed_items_without_crashing(self):
        fake_models = SimpleNamespace(
            generate_content=Mock(
                return_value=SimpleNamespace(
                    text="""[
                        {
                            "company_name": "Acme",
                            "raw_snippets": ["new snippet"],
                            "sources": ["https://new.example"]
                        },
                        {
                            "raw_snippets": ["unnamed snippet"],
                            "sources": ["https://unnamed.example"]
                        }
                    ]"""
                )
            )
        )

        state = {
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": [
                {"raw_snippets": ["malformed snippet"], "sources": ["https://old.example"]},
                {
                    "company_name": "Acme",
                    "raw_snippets": ["old snippet"],
                    "sources": ["https://acme.example"],
                },
            ],
        }

        with patch.object(ResearcherAgent, "_get_client", return_value=SimpleNamespace(models=fake_models)):
            result = ResearcherAgent(api_key="user-key").research(state)

        acme = next(item for item in result["research_results"] if item.get("company_name") == "Acme")
        self.assertEqual(acme["raw_snippets"], ["old snippet", "new snippet"])
        self.assertEqual(acme["sources"], ["https://acme.example", "https://new.example"])
        self.assertTrue(
            any(item.get("raw_snippets") == ["malformed snippet"] for item in result["research_results"])
        )
        self.assertTrue(
            any(item.get("raw_snippets") == ["unnamed snippet"] for item in result["research_results"])
        )


if __name__ == "__main__":
    unittest.main()
