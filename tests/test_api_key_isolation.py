import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


def _install_dependency_stubs():
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules.setdefault("dotenv", dotenv)

    google = types.ModuleType("google")
    genai = types.ModuleType("google.genai")
    genai_types = types.ModuleType("google.genai.types")
    genai.Client = lambda api_key=None: {"api_key": api_key}
    genai_types.GenerateContentConfig = lambda *args, **kwargs: kwargs
    genai_types.GoogleSearch = lambda *args, **kwargs: object()
    genai_types.Tool = lambda *args, **kwargs: kwargs
    google.genai = genai
    sys.modules.setdefault("google", google)
    sys.modules.setdefault("google.genai", genai)
    sys.modules.setdefault("google.genai.types", genai_types)

    langgraph = types.ModuleType("langgraph")
    langgraph_graph = types.ModuleType("langgraph.graph")

    class FakeStateGraph:
        def __init__(self, *args, **kwargs):
            self.nodes = {}

        def add_node(self, name, fn):
            self.nodes[name] = fn

        def add_edge(self, *args, **kwargs):
            pass

        def add_conditional_edges(self, *args, **kwargs):
            pass

        def set_entry_point(self, *args, **kwargs):
            pass

        def compile(self):
            return self

    langgraph_graph.StateGraph = FakeStateGraph
    langgraph_graph.END = "__END__"
    langgraph.graph = langgraph_graph
    sys.modules.setdefault("langgraph", langgraph)
    sys.modules.setdefault("langgraph.graph", langgraph_graph)


_install_dependency_stubs()


AGENT_MODULES = [
    "agents.researcher",
    "agents.categorizer",
    "agents.analyst",
    "agents.evaluator",
]


class ApiKeyIsolationTests(unittest.TestCase):
    def setUp(self):
        for name in AGENT_MODULES + ["orchestrator", "main"]:
            sys.modules.pop(name, None)

    def tearDown(self):
        for name in AGENT_MODULES + ["orchestrator", "main"]:
            sys.modules.pop(name, None)

    def test_agents_prefer_request_key_over_process_environment(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "deployment-key"}, clear=False):
            for module_name in AGENT_MODULES:
                module = importlib.import_module(module_name)
                class_name = "".join(part.title() for part in module_name.rsplit(".", 1)[1].split("_"))
                if class_name == "Researcher":
                    class_name = "ResearcherAgent"
                elif class_name == "Categorizer":
                    class_name = "CategorizerAgent"
                elif class_name == "Analyst":
                    class_name = "AnalystAgent"
                elif class_name == "Evaluator":
                    class_name = "EvaluatorAgent"

                calls = []

                def fake_client(api_key=None):
                    calls.append(api_key)
                    return {"api_key": api_key}

                with patch.object(module.genai, "Client", side_effect=fake_client):
                    agent = getattr(module, class_name)(api_key="user-key")

                    self.assertEqual(agent._get_client()["api_key"], "user-key")
                    self.assertEqual(agent._get_client()["api_key"], "user-key")
                    self.assertEqual(calls, ["user-key"])

    def test_orchestrator_does_not_reuse_user_key_agents_between_runs(self):
        orchestrator = importlib.import_module("orchestrator")

        first_agents = orchestrator._get_agents(api_key="user-a")
        second_agents = orchestrator._get_agents(api_key="user-b")

        for first, second in zip(first_agents, second_agents):
            self.assertIsNot(first, second)
            self.assertEqual(first._api_key, "user-a")
            self.assertEqual(second._api_key, "user-b")

        self.assertIsNone(orchestrator._researcher)
        self.assertIsNone(orchestrator._categorizer)
        self.assertIsNone(orchestrator._analyst)
        self.assertIsNone(orchestrator._evaluator)

    def test_orchestrator_keeps_env_key_cache_for_non_user_runs(self):
        orchestrator = importlib.import_module("orchestrator")

        first_agents = orchestrator._get_agents()
        second_agents = orchestrator._get_agents()

        for first, second in zip(first_agents, second_agents):
            self.assertIs(first, second)
            self.assertIsNone(first._api_key)

    def test_main_forwards_request_key_without_putting_it_in_state(self):
        main = importlib.import_module("main")

        with patch.object(main, "run_analysis", return_value={"status": "complete"}) as run_analysis:
            result = main.Orchestrator().run("Stripe", "fintech", api_key=" user-key ")

        self.assertEqual(result, {"status": "complete"})
        run_analysis.assert_called_once_with(
            company="Stripe",
            industry="fintech",
            api_key="user-key",
        )


if __name__ == "__main__":
    unittest.main()
