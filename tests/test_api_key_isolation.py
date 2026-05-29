import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.researcher import ResearcherAgent
from main import Orchestrator


class ApiKeyIsolationTests(unittest.TestCase):
    def test_explicit_agent_key_takes_precedence_without_mutating_environment(self):
        original_env_key = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "deployment-key"
        try:
            with patch("agents.researcher.genai.Client") as client_cls:
                ResearcherAgent(api_key=" user-key ")._get_client()

            client_cls.assert_called_once_with(api_key="user-key")
            self.assertEqual(os.environ["GEMINI_API_KEY"], "deployment-key")
        finally:
            if original_env_key is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = original_env_key

    def test_orchestrator_forwards_explicit_api_key_per_run(self):
        with patch("main.run_analysis", return_value={"status": "complete"}) as run_analysis:
            result = Orchestrator(api_key=" user-key ").run(
                company="Stripe",
                industry="fintech",
            )

        self.assertEqual(result, {"status": "complete"})
        run_analysis.assert_called_once_with(
            company="Stripe",
            industry="fintech",
            api_key="user-key",
        )


if __name__ == "__main__":
    unittest.main()
