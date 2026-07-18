import sys
import types
import unittest


def _install_optional_dependency_stubs():
    try:
        import dotenv  # noqa: F401
    except Exception:
        dotenv_module = types.ModuleType("dotenv")
        dotenv_module.load_dotenv = lambda *args, **kwargs: None
        sys.modules["dotenv"] = dotenv_module

    try:
        import google.genai  # noqa: F401
    except Exception:
        google_module = sys.modules.setdefault("google", types.ModuleType("google"))
        genai_module = types.ModuleType("google.genai")
        genai_module.Client = lambda api_key: types.SimpleNamespace(api_key=api_key)
        genai_module.types = types.SimpleNamespace()
        sys.modules["google.genai"] = genai_module
        setattr(google_module, "genai", genai_module)

    try:
        import langgraph.graph  # noqa: F401
    except Exception:
        langgraph_module = sys.modules.setdefault("langgraph", types.ModuleType("langgraph"))
        graph_module = types.ModuleType("langgraph.graph")
        graph_module.END = "__END__"
        graph_module.StateGraph = object
        sys.modules["langgraph.graph"] = graph_module
        setattr(langgraph_module, "graph", graph_module)


_install_optional_dependency_stubs()

import orchestrator


class ApiKeyIsolationTests(unittest.TestCase):
    def test_explicit_keys_create_isolated_per_run_agents(self):
        saved_agents = (
            orchestrator._researcher,
            orchestrator._categorizer,
            orchestrator._analyst,
            orchestrator._evaluator,
        )
        try:
            orchestrator._researcher = None
            orchestrator._categorizer = None
            orchestrator._analyst = None
            orchestrator._evaluator = None

            agents_a = orchestrator._get_agents(api_key="user-a-key")
            agents_b = orchestrator._get_agents(api_key="user-b-key")

            self.assertTrue(all(agent.api_key == "user-a-key" for agent in agents_a))
            self.assertTrue(all(agent.api_key == "user-b-key" for agent in agents_b))
            self.assertTrue(all(a is not b for a, b in zip(agents_a, agents_b)))
            self.assertIsNone(orchestrator._researcher)
            self.assertIsNone(orchestrator._categorizer)
            self.assertIsNone(orchestrator._analyst)
            self.assertIsNone(orchestrator._evaluator)
        finally:
            (
                orchestrator._researcher,
                orchestrator._categorizer,
                orchestrator._analyst,
                orchestrator._evaluator,
            ) = saved_agents


if __name__ == "__main__":
    unittest.main()
