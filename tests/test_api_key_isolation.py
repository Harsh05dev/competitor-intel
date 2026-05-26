import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

import orchestrator
from agents.researcher import ResearcherAgent
from main import Orchestrator


class ApiKeyIsolationTests(unittest.TestCase):
    def setUp(self):
        orchestrator._researcher = None
        orchestrator._categorizer = None
        orchestrator._analyst = None
        orchestrator._evaluator = None

    def test_explicit_key_agents_are_per_run_and_not_global_singletons(self):
        first = orchestrator._get_agents(api_key="USER_KEY_A")
        second = orchestrator._get_agents(api_key="USER_KEY_B")

        self.assertEqual("USER_KEY_A", first[0].api_key)
        self.assertEqual("USER_KEY_B", second[0].api_key)
        self.assertIsNot(first[0], second[0])
        self.assertIsNone(orchestrator._researcher)

    def test_env_backed_agents_remain_singletons_for_non_streamlit_use(self):
        first = orchestrator._get_agents()
        second = orchestrator._get_agents()

        self.assertIs(first[0], second[0])
        self.assertIs(first[1], second[1])

    def test_agent_prefers_explicit_key_over_process_environment(self):
        created_clients = []

        def fake_client(**kwargs):
            created_clients.append(kwargs)
            return object()

        with patch.dict("os.environ", {"GEMINI_API_KEY": "ENV_KEY"}):
            with patch("agents.researcher.genai.Client", side_effect=fake_client):
                agent = ResearcherAgent(api_key="USER_KEY")
                first = agent._get_client()
                second = agent._get_client()

        self.assertIs(first, second)
        self.assertEqual([{"api_key": "USER_KEY"}], created_clients)

    def test_orchestrator_forwards_explicit_key_to_run_analysis(self):
        with patch("main.run_analysis", return_value={"status": "complete"}) as run_analysis:
            result = Orchestrator().run("Stripe", "fintech", api_key="USER_KEY")

        self.assertEqual({"status": "complete"}, result)
        run_analysis.assert_called_once_with(company="Stripe", industry="fintech", api_key="USER_KEY")


if __name__ == "__main__":
    unittest.main()
