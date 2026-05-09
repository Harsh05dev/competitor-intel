import importlib
import os
import sys
import types as py_types
import unittest
from pathlib import Path


def install_dependency_stubs():
    dotenv = py_types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    sys.modules["dotenv"] = dotenv

    google = py_types.ModuleType("google")
    genai = py_types.ModuleType("google.genai")
    genai_types = py_types.ModuleType("google.genai.types")

    class FakeClient:
        created_keys = []

        def __init__(self, api_key):
            self.api_key = api_key
            FakeClient.created_keys.append(api_key)

    class GenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class GoogleSearch:
        pass

    class Tool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    genai.Client = FakeClient
    genai.types = genai_types
    genai_types.GenerateContentConfig = GenerateContentConfig
    genai_types.GoogleSearch = GoogleSearch
    genai_types.Tool = Tool

    google.genai = genai
    sys.modules["google"] = google
    sys.modules["google.genai"] = genai
    sys.modules["google.genai.types"] = genai_types
    return FakeClient


FakeClient = install_dependency_stubs()


class ApiKeyIsolationTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("GEMINI_API_KEY", None)
        FakeClient.created_keys.clear()

    def test_user_supplied_keys_are_not_cached_on_shared_agents(self):
        agent_classes = [
            ("agents.researcher", "ResearcherAgent"),
            ("agents.categorizer", "CategorizerAgent"),
            ("agents.analyst", "AnalystAgent"),
            ("agents.evaluator", "EvaluatorAgent"),
        ]

        for module_name, class_name in agent_classes:
            with self.subTest(agent=class_name):
                module = importlib.import_module(module_name)
                agent = getattr(module, class_name)()

                first_client = agent._get_client("user-a-key")
                second_client = agent._get_client("user-b-key")

                self.assertEqual("user-a-key", first_client.api_key)
                self.assertEqual("user-b-key", second_client.api_key)
                self.assertIsNone(agent.client)
                self.assertIsNot(first_client, second_client)

    def test_explicit_key_does_not_leak_into_environment_fallback_cache(self):
        module = importlib.import_module("agents.researcher")
        agent = module.ResearcherAgent()

        explicit_client = agent._get_client("session-key")
        self.assertEqual("session-key", explicit_client.api_key)
        self.assertIsNone(agent.client)

        os.environ["GEMINI_API_KEY"] = "deployment-key"
        env_client = agent._get_client()
        self.assertEqual("deployment-key", env_client.api_key)
        self.assertIs(agent.client, env_client)

    def test_streamlit_ui_does_not_store_user_keys_in_process_environment(self):
        app_source = Path(__file__).resolve().parents[1].joinpath("ui", "app.py").read_text()

        self.assertNotIn('os.environ["GEMINI_API_KEY"]', app_source)
        self.assertIn('key="gemini_api_key"', app_source)
        self.assertIn("api_key=api_key", app_source)


if __name__ == "__main__":
    unittest.main()
