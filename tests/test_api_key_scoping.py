import os
import unittest
from unittest.mock import patch

import agents.analyst as analyst_module
import agents.categorizer as categorizer_module
import agents.evaluator as evaluator_module
import agents.researcher as researcher_module
import main
import orchestrator


class ApiKeyScopingTest(unittest.TestCase):
    def setUp(self):
        self._old_env = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "env-key"

        orchestrator._researcher = None
        orchestrator._categorizer = None
        orchestrator._analyst = None
        orchestrator._evaluator = None

    def tearDown(self):
        if self._old_env is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = self._old_env

        orchestrator._researcher = None
        orchestrator._categorizer = None
        orchestrator._analyst = None
        orchestrator._evaluator = None

    def test_explicit_agent_key_takes_precedence_over_environment(self):
        cases = [
            (researcher_module, researcher_module.ResearcherAgent),
            (categorizer_module, categorizer_module.CategorizerAgent),
            (analyst_module, analyst_module.AnalystAgent),
            (evaluator_module, evaluator_module.EvaluatorAgent),
        ]

        for module, agent_cls in cases:
            with self.subTest(agent=agent_cls.__name__):
                with patch.object(module.genai, "Client", autospec=True) as client_cls:
                    agent = agent_cls(api_key="user-key")
                    agent._get_client()

                client_cls.assert_called_once_with(api_key="user-key")

    def test_environment_agent_clients_still_cache_for_deployments(self):
        with patch.object(researcher_module.genai, "Client", autospec=True) as client_cls:
            agent = researcher_module.ResearcherAgent()
            agent._get_client()
            agent._get_client()

        client_cls.assert_called_once_with(api_key="env-key")

    def test_explicit_orchestrator_agents_are_fresh_and_do_not_seed_singletons(self):
        first = orchestrator._get_agents(api_key="first-user-key")
        second = orchestrator._get_agents(api_key="second-user-key")

        self.assertIsNot(first[0], second[0])
        self.assertEqual(first[0].api_key, "first-user-key")
        self.assertEqual(second[0].api_key, "second-user-key")
        self.assertIsNone(orchestrator._researcher)

    def test_orchestrator_wrapper_forwards_explicit_key(self):
        with patch.object(main, "run_analysis", return_value={"status": "complete"}) as run_analysis:
            result = main.Orchestrator(api_key="session-key").run(
                company="Stripe",
                industry="fintech",
            )

        self.assertEqual(result, {"status": "complete"})
        run_analysis.assert_called_once_with(
            company="Stripe",
            industry="fintech",
            api_key="session-key",
        )


if __name__ == "__main__":
    unittest.main()
