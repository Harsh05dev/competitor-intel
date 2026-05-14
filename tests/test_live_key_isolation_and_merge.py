import os
import unittest
from unittest.mock import patch

from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent
from main import Orchestrator


class FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key


class FakeModels:
    def generate_content(self, **_kwargs):
        class Response:
            text = """
            [
              {"company_name": "Acme", "raw_snippets": ["new", "old"], "sources": ["s2"]},
              {"company_name": null, "raw_snippets": ["nameless-new"], "sources": []}
            ]
            """

        return Response()


class FakeResearchClient:
    models = FakeModels()


class LiveKeyIsolationTests(unittest.TestCase):
    def test_agents_use_explicit_key_instead_of_process_environment(self):
        agent_cases = [
            ("agents.researcher.genai.Client", ResearcherAgent),
            ("agents.categorizer.genai.Client", CategorizerAgent),
            ("agents.analyst.genai.Client", AnalystAgent),
            ("agents.evaluator.genai.Client", EvaluatorAgent),
        ]

        for client_path, agent_cls in agent_cases:
            with self.subTest(agent=agent_cls.__name__):
                with patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"}, clear=False):
                    with patch(client_path, side_effect=lambda api_key: FakeClient(api_key)):
                        agent = agent_cls(api_key="session-key")

                        self.assertEqual(agent._get_client().api_key, "session-key")

    def test_env_backed_agents_refresh_when_environment_key_changes(self):
        with patch("agents.researcher.genai.Client", side_effect=lambda api_key: FakeClient(api_key)):
            agent = ResearcherAgent()

            with patch.dict(os.environ, {"GEMINI_API_KEY": "first-key"}, clear=False):
                first_client = agent._get_client()

            with patch.dict(os.environ, {"GEMINI_API_KEY": "second-key"}, clear=False):
                second_client = agent._get_client()

        self.assertEqual(first_client.api_key, "first-key")
        self.assertEqual(second_client.api_key, "second-key")
        self.assertIsNot(first_client, second_client)

    def test_orchestrator_forwards_session_key_to_analysis(self):
        with patch("main.run_analysis", return_value={"status": "complete"}) as run_analysis:
            result = Orchestrator().run(company="Stripe", industry="fintech", api_key="session-key")

        self.assertEqual(result, {"status": "complete"})
        run_analysis.assert_called_once_with(
            company="Stripe",
            industry="fintech",
            api_key="session-key",
        )


class RetryMergeTests(unittest.TestCase):
    def test_researcher_retry_merge_survives_missing_company_names(self):
        agent = ResearcherAgent(api_key="session-key")
        agent._get_client = lambda: FakeResearchClient()
        state = {
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Acme pricing"]},
            "research_results": [
                {"company_name": None, "raw_snippets": ["nameless-old"], "sources": []},
                {"company_name": "Acme", "raw_snippets": ["old"], "sources": ["s1"]},
            ],
        }

        result = agent.research(state)

        acme = next(item for item in result["research_results"] if item.get("company_name") == "Acme")
        self.assertEqual(acme["raw_snippets"], ["old", "new"])
        self.assertEqual(acme["sources"], ["s1", "s2"])
        self.assertTrue(
            any(item.get("raw_snippets") == ["nameless-old"] for item in result["research_results"])
        )

    def test_categorizer_merge_survives_missing_company_names(self):
        agent = CategorizerAgent(api_key="session-key")
        existing = [
            {
                "company_name": None,
                "pricing": None,
                "key_features": [],
                "target_audience": None,
                "funding": None,
                "hiring_signals": [],
                "recent_news": [],
                "customer_sentiment": None,
            },
            {
                "company_name": "Acme",
                "pricing": None,
                "key_features": ["old feature"],
                "target_audience": None,
                "funding": None,
                "hiring_signals": [],
                "recent_news": [],
                "customer_sentiment": None,
            },
        ]
        new_data = [
            {
                "company_name": "Acme",
                "pricing": "Free tier",
                "key_features": ["new feature", "old feature"],
                "target_audience": "Developers",
                "funding": None,
                "hiring_signals": ["10 open roles"],
                "recent_news": [],
                "customer_sentiment": None,
            },
            {"company_name": None, "pricing": "Unknown"},
        ]

        merged = agent._merge(existing, new_data)

        acme = next(item for item in merged if item.get("company_name") == "Acme")
        self.assertEqual(acme["pricing"], "Free tier")
        self.assertEqual(acme["key_features"], ["old feature", "new feature"])
        self.assertEqual(acme["target_audience"], "Developers")
        self.assertEqual(acme["hiring_signals"], ["10 open roles"])
        self.assertTrue(any(item.get("company_name") is None for item in merged))


if __name__ == "__main__":
    unittest.main()
