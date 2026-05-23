import unittest
from unittest.mock import patch

import main
import orchestrator
from agents.researcher import ResearcherAgent


class ApiKeyIsolationTests(unittest.TestCase):
    def test_orchestrator_passes_instance_key_to_run_analysis(self):
        with patch("main.run_analysis", return_value={"status": "complete"}) as run_analysis:
            result = main.Orchestrator(api_key="  user-key  ").run(
                company="Acme",
                industry="widgets",
            )

        self.assertEqual(result, {"status": "complete"})
        run_analysis.assert_called_once_with(
            company="Acme",
            industry="widgets",
            api_key="user-key",
        )

    def test_explicit_key_agents_are_not_reused_between_runs(self):
        created = []

        def agent_factory(name):
            class FakeAgent:
                def __init__(self, api_key=None):
                    self.name = name
                    self.api_key = api_key
                    created.append(self)

            return FakeAgent

        with (
            patch("orchestrator.ResearcherAgent", agent_factory("researcher")),
            patch("orchestrator.CategorizerAgent", agent_factory("categorizer")),
            patch("orchestrator.AnalystAgent", agent_factory("analyst")),
            patch("orchestrator.EvaluatorAgent", agent_factory("evaluator")),
        ):
            first = orchestrator._get_agents(api_key="first-key")
            second = orchestrator._get_agents(api_key="second-key")

        self.assertEqual({agent.api_key for agent in first.values()}, {"first-key"})
        self.assertEqual({agent.api_key for agent in second.values()}, {"second-key"})
        for role in first:
            self.assertIsNot(first[role], second[role])
        self.assertEqual(len(created), 8)

    def test_agent_client_uses_explicit_key_before_environment(self):
        with patch("agents.researcher.genai.Client", return_value=object()) as client:
            ResearcherAgent(api_key="session-key")._get_client()

        client.assert_called_once_with(api_key="session-key")


if __name__ == "__main__":
    unittest.main()
