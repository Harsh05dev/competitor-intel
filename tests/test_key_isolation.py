import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

import orchestrator
from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent
from main import Orchestrator


class ApiKeyIsolationTests(unittest.TestCase):
    def setUp(self):
        self._old_key = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "env-key"
        orchestrator._researcher = None
        orchestrator._categorizer = None
        orchestrator._analyst = None
        orchestrator._evaluator = None

    def tearDown(self):
        if self._old_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = self._old_key

    def test_explicit_agent_key_overrides_process_environment(self):
        specs = [
            ("agents.researcher.genai.Client", ResearcherAgent),
            ("agents.categorizer.genai.Client", CategorizerAgent),
            ("agents.analyst.genai.Client", AnalystAgent),
            ("agents.evaluator.genai.Client", EvaluatorAgent),
        ]

        for client_path, agent_cls in specs:
            with self.subTest(agent=agent_cls.__name__), patch(client_path) as client_cls:
                client_cls.side_effect = lambda api_key: {"api_key": api_key}
                agent = agent_cls(api_key="session-key")

                self.assertEqual(agent._get_client(), {"api_key": "session-key"})
                self.assertEqual(agent._get_client(), {"api_key": "session-key"})
                client_cls.assert_called_once_with(api_key="session-key")

    def test_explicit_orchestrator_agents_are_fresh_per_key(self):
        first = orchestrator._get_agents(api_key="key-a")
        second = orchestrator._get_agents(api_key="key-b")

        self.assertEqual([agent.api_key for agent in first], ["key-a"] * 4)
        self.assertEqual([agent.api_key for agent in second], ["key-b"] * 4)
        for left, right in zip(first, second):
            self.assertIsNot(left, right)
        self.assertIsNone(orchestrator._researcher)

    def test_orchestrator_wrapper_forwards_explicit_key(self):
        with patch("main.run_analysis", return_value={"status": "complete"}) as run_analysis:
            result = Orchestrator().run(company="Acme", industry="fintech", api_key="session-key")

        self.assertEqual(result, {"status": "complete"})
        run_analysis.assert_called_once_with(
            company="Acme",
            industry="fintech",
            api_key="session-key",
        )


class ResearcherRetryMergeTests(unittest.TestCase):
    def test_retry_merge_tolerates_missing_fields(self):
        class FakeModels:
            def generate_content(self, *args, **kwargs):
                return type(
                    "Response",
                    (),
                    {
                        "text": """
                        [
                          {"company_name": "Acme", "raw_snippets": ["new"], "sources": ["new-url"]},
                          {"raw_snippets": ["unnamed new"]}
                        ]
                        """
                    },
                )()

        class FakeClient:
            models = FakeModels()

        state = {
            "target_company": "Target",
            "industry": "payments",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": [
                {"raw_snippets": ["unnamed old"]},
                {"company_name": "Acme", "raw_snippets": ["old"], "sources": ["old-url"]},
                {"company_name": "Beta"},
            ],
        }

        agent = ResearcherAgent(api_key="session-key")
        with patch.object(agent, "_get_client", return_value=FakeClient()):
            result = agent.research(state)

        acme = next(item for item in result["research_results"] if item.get("company_name") == "Acme")
        beta = next(item for item in result["research_results"] if item.get("company_name") == "Beta")

        self.assertEqual(acme["raw_snippets"], ["old", "new"])
        self.assertEqual(acme["sources"], ["old-url", "new-url"])
        self.assertEqual(beta["raw_snippets"], [])
        self.assertEqual(beta["sources"], [])
        self.assertTrue(any("unnamed old" in item.get("raw_snippets", []) for item in result["research_results"]))
        self.assertTrue(any("unnamed new" in item.get("raw_snippets", []) for item in result["research_results"]))


if __name__ == "__main__":
    unittest.main()
