import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

import orchestrator
from agents import analyst as analyst_module
from agents import categorizer as categorizer_module
from agents import evaluator as evaluator_module
from agents import researcher as researcher_module
from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent


class FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key


class ApiKeyIsolationTest(unittest.TestCase):
    def test_agents_prefer_explicit_key_over_environment(self):
        os.environ["GEMINI_API_KEY"] = "env-key"
        cases = [
            (researcher_module, ResearcherAgent),
            (categorizer_module, CategorizerAgent),
            (analyst_module, AnalystAgent),
            (evaluator_module, EvaluatorAgent),
        ]

        for module, agent_class in cases:
            with self.subTest(agent=agent_class.__name__):
                with patch.object(module.genai, "Client", FakeClient):
                    agent = agent_class(api_key="user-key")
                    self.assertEqual(agent._get_client().api_key, "user-key")

    def test_run_analysis_creates_agents_per_api_key(self):
        created = []

        class FakeResearcher:
            def __init__(self, api_key=None):
                created.append(("researcher", api_key))

            def research(self, state):
                return {
                    "research_results": [
                        {"company_name": "ExampleCo", "raw_snippets": ["fact"], "sources": ["source"]}
                    ],
                    "iteration": state["iteration"],
                }

        class FakeCategorizer:
            def __init__(self, api_key=None):
                created.append(("categorizer", api_key))

            def categorize(self, state):
                return {
                    "categorized_competitors": [
                        {
                            "company_name": "ExampleCo",
                            "pricing": "usage-based",
                            "key_features": ["feature"],
                            "target_audience": "developers",
                            "funding": "seed",
                            "hiring_signals": ["hiring"],
                            "recent_news": ["launch"],
                            "customer_sentiment": "positive",
                        }
                    ]
                }

        class FakeAnalyst:
            def __init__(self, api_key=None):
                created.append(("analyst", api_key))

            def analyze(self, state):
                return {
                    "analysis": {
                        "swot": {
                            "strengths": ["strong"],
                            "weaknesses": ["weak"],
                            "opportunities": ["open"],
                            "threats": ["threat"],
                        },
                        "comparison_matrix": [],
                        "threat_ranking": [],
                        "opportunity_gaps": [],
                    }
                }

        class FakeEvaluator:
            def __init__(self, api_key=None):
                created.append(("evaluator", api_key))

            def evaluate(self, state):
                return {
                    "evaluation": {
                        "score": 100,
                        "passed": True,
                        "breakdown": {},
                        "gaps": [],
                        "suggested_queries": [],
                    }
                }

        with (
            patch.object(orchestrator, "ResearcherAgent", FakeResearcher),
            patch.object(orchestrator, "CategorizerAgent", FakeCategorizer),
            patch.object(orchestrator, "AnalystAgent", FakeAnalyst),
            patch.object(orchestrator, "EvaluatorAgent", FakeEvaluator),
        ):
            orchestrator.run_analysis("TargetA", "market", api_key="key-a")
            orchestrator.run_analysis("TargetB", "market", api_key="key-b")

        self.assertEqual(
            created,
            [
                ("researcher", "key-a"),
                ("categorizer", "key-a"),
                ("analyst", "key-a"),
                ("evaluator", "key-a"),
                ("researcher", "key-b"),
                ("categorizer", "key-b"),
                ("analyst", "key-b"),
                ("evaluator", "key-b"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
