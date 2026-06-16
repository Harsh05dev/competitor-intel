import importlib
import os
import sys
import types
import unittest


class FakeStateGraph:
    def __init__(self, _state_type):
        self.nodes = {}
        self.entry_point = None

    def add_node(self, name, func):
        self.nodes[name] = func

    def add_edge(self, _source, _dest):
        pass

    def add_conditional_edges(self, _source, _router, _routes):
        pass

    def set_entry_point(self, name):
        self.entry_point = name

    def compile(self):
        return self

    def invoke(self, initial_state):
        state = dict(initial_state)
        for node_name in ["researcher", "categorizer", "analyst", "evaluator", "format_report"]:
            state.update(self.nodes[node_name](state))
        return state


class ApiKeyIsolationTest(unittest.TestCase):
    def setUp(self):
        self.created_client_keys = []

        google_module = types.ModuleType("google")
        genai_module = types.ModuleType("google.genai")

        class FakeClient:
            def __init__(_self, api_key):
                self.created_client_keys.append(api_key)

        genai_module.Client = FakeClient
        google_module.genai = genai_module

        genai_types_module = types.ModuleType("google.genai.types")
        genai_module.types = genai_types_module

        langgraph_module = types.ModuleType("langgraph")
        graph_module = types.ModuleType("langgraph.graph")
        graph_module.StateGraph = FakeStateGraph
        graph_module.END = "__end__"
        langgraph_module.graph = graph_module

        self.stubbed_modules = {
            "google": google_module,
            "google.genai": genai_module,
            "google.genai.types": genai_types_module,
            "langgraph": langgraph_module,
            "langgraph.graph": graph_module,
        }
        self.previous_modules = {name: sys.modules.get(name) for name in self.stubbed_modules}
        sys.modules.update(self.stubbed_modules)

        for module_name in [
            "orchestrator",
            "main",
            "agents.researcher",
            "agents.categorizer",
            "agents.analyst",
            "agents.evaluator",
        ]:
            sys.modules.pop(module_name, None)

        os.environ.pop("GEMINI_API_KEY", None)

    def tearDown(self):
        for module_name, previous in self.previous_modules.items():
            if previous is None:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = previous

        for module_name in [
            "orchestrator",
            "main",
            "agents.researcher",
            "agents.categorizer",
            "agents.analyst",
            "agents.evaluator",
        ]:
            sys.modules.pop(module_name, None)

    def test_explicit_api_key_is_scoped_to_each_run(self):
        orchestrator = importlib.import_module("orchestrator")

        orchestrator.ResearcherAgent.research = lambda agent, state: (
            agent._get_client()
            and {"research_results": [], "iteration": state["iteration"]}
        )
        orchestrator.CategorizerAgent.categorize = lambda agent, state: (
            agent._get_client()
            and {"categorized_competitors": []}
        )
        orchestrator.AnalystAgent.analyze = lambda agent, state: (
            agent._get_client()
            and {"analysis": {"swot": {}, "comparison_matrix": [], "threat_ranking": [], "opportunity_gaps": []}}
        )
        orchestrator.EvaluatorAgent.evaluate = lambda agent, state: (
            agent._get_client()
            and {"evaluation": {"score": 100, "passed": True, "breakdown": {}, "gaps": [], "suggested_queries": []}}
        )

        first_result = orchestrator.run_analysis("Acme", "fintech", api_key="first-user-key")
        second_result = orchestrator.run_analysis("Beta", "fintech", api_key="second-user-key")

        self.assertEqual(
            self.created_client_keys,
            ["first-user-key"] * 4 + ["second-user-key"] * 4,
        )
        self.assertNotIn("api_key", first_result)
        self.assertNotIn("api_key", second_result)
        self.assertNotEqual(os.environ.get("GEMINI_API_KEY"), "second-user-key")


if __name__ == "__main__":
    unittest.main()
