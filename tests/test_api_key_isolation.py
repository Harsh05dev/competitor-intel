import os
import unittest
from unittest.mock import patch

import orchestrator
from agents.researcher import ResearcherAgent


class FakeAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key


class ApiKeyIsolationTest(unittest.TestCase):
    def setUp(self):
        self._reset_env_agents()

    def tearDown(self):
        self._reset_env_agents()

    def _reset_env_agents(self):
        orchestrator._researcher = None
        orchestrator._categorizer = None
        orchestrator._analyst = None
        orchestrator._evaluator = None

    def test_explicit_api_key_builds_fresh_bound_agents(self):
        with patch.object(orchestrator, "ResearcherAgent", FakeAgent), \
            patch.object(orchestrator, "CategorizerAgent", FakeAgent), \
            patch.object(orchestrator, "AnalystAgent", FakeAgent), \
            patch.object(orchestrator, "EvaluatorAgent", FakeAgent):
            first_run_agents = orchestrator._get_agents(api_key="KEY_A")
            second_run_agents = orchestrator._get_agents(api_key="KEY_B")

        self.assertEqual(["KEY_A"] * 4, [agent.api_key for agent in first_run_agents])
        self.assertEqual(["KEY_B"] * 4, [agent.api_key for agent in second_run_agents])
        for first_agent, second_agent in zip(first_run_agents, second_run_agents):
            self.assertIsNot(first_agent, second_agent)

    def test_env_backed_agents_remain_singletons(self):
        with patch.object(orchestrator, "ResearcherAgent", FakeAgent), \
            patch.object(orchestrator, "CategorizerAgent", FakeAgent), \
            patch.object(orchestrator, "AnalystAgent", FakeAgent), \
            patch.object(orchestrator, "EvaluatorAgent", FakeAgent):
            first_lookup = orchestrator._get_agents()
            second_lookup = orchestrator._get_agents()

        for first_agent, second_agent in zip(first_lookup, second_lookup):
            self.assertIs(first_agent, second_agent)
            self.assertIsNone(first_agent.api_key)

    def test_agent_prefers_explicit_key_over_process_environment(self):
        clients = []

        def fake_client(api_key):
            client = {"api_key": api_key}
            clients.append(client)
            return client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "ENV_KEY"}), \
            patch("agents.researcher.genai.Client", side_effect=fake_client):
            first_agent = ResearcherAgent(api_key="KEY_A")
            second_agent = ResearcherAgent(api_key="KEY_B")

            self.assertEqual("KEY_A", first_agent._get_client()["api_key"])
            self.assertEqual("KEY_A", first_agent._get_client()["api_key"])
            self.assertEqual("KEY_B", second_agent._get_client()["api_key"])

        self.assertEqual(["KEY_A", "KEY_B"], [client["api_key"] for client in clients])


if __name__ == "__main__":
    unittest.main()
