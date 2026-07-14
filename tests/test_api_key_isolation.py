import os
import unittest
from unittest.mock import patch

import main
import orchestrator
from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class ApiKeyIsolationTests(unittest.TestCase):
    def test_agents_prefer_their_explicit_api_key(self):
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


if __name__ == "__main__":
    unittest.main()
