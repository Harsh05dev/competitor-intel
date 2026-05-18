import unittest
from unittest.mock import patch

import orchestrator
from agents.researcher import ResearcherAgent


class FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key


class FakeAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key


class ApiKeyIsolationTests(unittest.TestCase):
    def setUp(self):
        self._reset_orchestrator_singletons()

    def tearDown(self):
        self._reset_orchestrator_singletons()

    def _reset_orchestrator_singletons(self):
        orchestrator._researcher = None
        orchestrator._categorizer = None
        orchestrator._analyst = None
        orchestrator._evaluator = None

    def test_explicit_agent_key_does_not_read_changed_environment(self):
        with patch("agents.researcher.genai.Client", side_effect=lambda api_key: FakeClient(api_key)):
            agent = ResearcherAgent(api_key="user-key-a")
            first_client = agent._get_client()

            with patch.dict("agents.researcher.os.environ", {"GEMINI_API_KEY": "user-key-b"}):
                second_client = agent._get_client()

        self.assertIs(first_client, second_client)
        self.assertEqual(first_client.api_key, "user-key-a")

    def test_explicit_orchestrator_keys_create_per_run_agents(self):
        patches = [
            patch("orchestrator.ResearcherAgent", FakeAgent),
            patch("orchestrator.CategorizerAgent", FakeAgent),
            patch("orchestrator.AnalystAgent", FakeAgent),
            patch("orchestrator.EvaluatorAgent", FakeAgent),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

        first_agents = orchestrator._get_agents(api_key="user-key-a")
        second_agents = orchestrator._get_agents(api_key="user-key-b")

        self.assertEqual([agent.api_key for agent in first_agents], ["user-key-a"] * 4)
        self.assertEqual([agent.api_key for agent in second_agents], ["user-key-b"] * 4)
        self.assertIsNot(first_agents[0], second_agents[0])

    def test_environment_orchestrator_agents_remain_cached(self):
        patches = [
            patch("orchestrator.ResearcherAgent", FakeAgent),
            patch("orchestrator.CategorizerAgent", FakeAgent),
            patch("orchestrator.AnalystAgent", FakeAgent),
            patch("orchestrator.EvaluatorAgent", FakeAgent),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

        first_agents = orchestrator._get_agents()
        second_agents = orchestrator._get_agents()

        self.assertIs(first_agents[0], second_agents[0])
        self.assertEqual([agent.api_key for agent in first_agents], [None] * 4)


if __name__ == "__main__":
    unittest.main()
