import json
import os
import sys
import types
import unittest


def install_dependency_stubs():
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules.setdefault("dotenv", dotenv)

    google = types.ModuleType("google")
    genai = types.ModuleType("google.genai")
    genai_types = types.ModuleType("google.genai.types")

    class Client:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = types.SimpleNamespace()

    class GenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class GoogleSearch:
        pass

    class Tool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    genai.Client = Client
    genai_types.GenerateContentConfig = GenerateContentConfig
    genai_types.GoogleSearch = GoogleSearch
    genai_types.Tool = Tool
    google.genai = genai
    genai.types = genai_types

    sys.modules.setdefault("google", google)
    sys.modules.setdefault("google.genai", genai)
    sys.modules.setdefault("google.genai.types", genai_types)


install_dependency_stubs()

from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class FailingModels:
    def generate_content(self, **kwargs):
        raise RuntimeError("model unavailable")


class StaticModels:
    def __init__(self, text):
        self.text = text

    def generate_content(self, **kwargs):
        return types.SimpleNamespace(text=self.text)


class AgentResilienceTests(unittest.TestCase):
    def test_agents_use_explicit_api_key_before_environment(self):
        os.environ["GEMINI_API_KEY"] = "env-key"
        for agent_cls in [ResearcherAgent, CategorizerAgent, AnalystAgent, EvaluatorAgent]:
            with self.subTest(agent=agent_cls.__name__):
                agent = agent_cls(api_key="user-key")
                self.assertEqual(agent._get_client().api_key, "user-key")

    def test_researcher_retry_failure_preserves_existing_results(self):
        existing = [
            {
                "company_name": "Square",
                "raw_snippets": ["existing pricing"],
                "sources": ["square.example"],
            }
        ]
        agent = ResearcherAgent(api_key="test-key")
        agent.client = types.SimpleNamespace(models=FailingModels())

        result = agent.research(
            {
                "target_company": "Stripe",
                "industry": "fintech",
                "iteration": 1,
                "evaluation": {"suggested_queries": ["Square hiring"]},
                "research_results": existing,
            }
        )

        self.assertEqual(result["research_results"], existing)

    def test_researcher_retry_merge_skips_malformed_records(self):
        response = json.dumps(
            [
                {"raw_snippets": ["missing company"], "sources": ["bad.example"]},
                {
                    "company_name": "Square",
                    "raw_snippets": ["new hiring signal"],
                    "sources": ["jobs.example"],
                },
            ]
        )
        agent = ResearcherAgent(api_key="test-key")
        agent.client = types.SimpleNamespace(models=StaticModels(response))

        result = agent.research(
            {
                "target_company": "Stripe",
                "industry": "fintech",
                "iteration": 1,
                "evaluation": {"suggested_queries": ["Square hiring"]},
                "research_results": [
                    {"company_name": "Square", "raw_snippets": ["existing pricing"]},
                    {"raw_snippets": ["nameless existing record"], "sources": []},
                ],
            }
        )

        self.assertEqual(len(result["research_results"]), 1)
        square = result["research_results"][0]
        self.assertEqual(square["company_name"], "Square")
        self.assertEqual(square["raw_snippets"], ["existing pricing", "new hiring signal"])
        self.assertEqual(square["sources"], ["jobs.example"])

    def test_analyst_retry_failure_preserves_existing_analysis(self):
        existing = {
            "swot": {"strengths": ["existing strength"]},
            "comparison_matrix": [{"company_name": "Square"}],
        }
        agent = AnalystAgent(api_key="test-key")
        agent.client = types.SimpleNamespace(models=FailingModels())

        result = agent.analyze(
            {
                "target_company": "Stripe",
                "industry": "fintech",
                "iteration": 1,
                "categorized_competitors": [{"company_name": "Square"}],
                "analysis": existing,
            }
        )

        self.assertEqual(result["analysis"]["swot"]["strengths"], ["existing strength"])
        self.assertEqual(result["analysis"]["comparison_matrix"], [{"company_name": "Square"}])

    def test_analyst_normalizes_null_swot_without_crashing(self):
        agent = AnalystAgent(api_key="test-key")
        agent.client = types.SimpleNamespace(
            models=StaticModels('{"swot": null, "comparison_matrix": [{"company_name": "Square"}]}')
        )

        result = agent.analyze(
            {
                "target_company": "Stripe",
                "industry": "fintech",
                "iteration": 0,
                "categorized_competitors": [{"company_name": "Square"}],
                "analysis": {},
            }
        )

        self.assertEqual(
            result["analysis"]["swot"],
            {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
        )
        self.assertEqual(result["analysis"]["comparison_matrix"], [{"company_name": "Square"}])

    def test_evaluator_coerces_malformed_breakdown_scores(self):
        agent = EvaluatorAgent()

        score = agent._calculate_score(
            {
                "competitor_count": {"score": "8"},
                "pricing_coverage": {"score": "7.5"},
                "feature_coverage": {"score": None},
                "funding_data": {"score": "bad"},
                "hiring_signals": {"score": 20},
                "swot_depth": {"score": -1},
            }
        )

        self.assertEqual(score, 54)


if __name__ == "__main__":
    unittest.main()
