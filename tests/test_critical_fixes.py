import os
import unittest
from unittest.mock import patch

from agents.researcher import ResearcherAgent
import orchestrator


class _FakeResponse:
    text = """
    [
      {
        "company_name": "Acme",
        "raw_snippets": ["new fact"],
        "sources": ["https://new.example"]
      },
      {
        "raw_snippets": ["missing name should not crash"],
        "sources": ["https://bad.example"]
      }
    ]
    """


class _FakeModels:
    def generate_content(self, **_kwargs):
        return _FakeResponse()


class _FakeClient:
    models = _FakeModels()


class _FakeGraph:
    def __init__(self, _schema):
        self.nodes = {}

    def add_node(self, name, func):
        self.nodes[name] = func

    def add_edge(self, *_args):
        pass

    def add_conditional_edges(self, *_args):
        pass

    def set_entry_point(self, *_args):
        pass

    def compile(self):
        return self


class CriticalFixTests(unittest.TestCase):
    def test_researcher_uses_explicit_api_key_over_process_env(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"}), patch(
            "agents.researcher.genai.Client"
        ) as client_ctor:
            ResearcherAgent(api_key=" session-key ")._get_client()

        client_ctor.assert_called_once_with(api_key="session-key")

    def test_research_retry_skips_unnamed_rows_instead_of_crashing(self):
        agent = ResearcherAgent(api_key="test-key")
        agent.client = _FakeClient()

        result = agent.research(
            {
                "target_company": "Target",
                "industry": "testing",
                "iteration": 1,
                "evaluation": {"suggested_queries": ["Acme pricing"]},
                "research_results": [
                    {"raw_snippets": ["missing name"], "sources": ["https://bad.example"]},
                    {
                        "company_name": "Acme",
                        "raw_snippets": ["old fact"],
                        "sources": ["https://old.example"],
                    },
                ],
            }
        )

        self.assertEqual(len(result["research_results"]), 1)
        self.assertEqual(result["research_results"][0]["company_name"], "Acme")
        self.assertEqual(result["research_results"][0]["raw_snippets"], ["old fact", "new fact"])

    def test_build_graph_creates_run_local_agents_with_session_key(self):
        with patch("orchestrator.StateGraph", _FakeGraph), patch(
            "orchestrator.ResearcherAgent"
        ) as researcher_cls, patch("orchestrator.CategorizerAgent") as categorizer_cls, patch(
            "orchestrator.AnalystAgent"
        ) as analyst_cls, patch(
            "orchestrator.EvaluatorAgent"
        ) as evaluator_cls:
            orchestrator.build_graph(api_key="session-key")

        researcher_cls.assert_called_once_with(api_key="session-key")
        categorizer_cls.assert_called_once_with(api_key="session-key")
        analyst_cls.assert_called_once_with(api_key="session-key")
        evaluator_cls.assert_called_once_with(api_key="session-key")


if __name__ == "__main__":
    unittest.main()
