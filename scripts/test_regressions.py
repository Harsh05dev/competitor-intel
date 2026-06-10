import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.append(str(Path(__file__).resolve().parents[1]))

import orchestrator
from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.researcher import ResearcherAgent
from main import Orchestrator
from ui.pdf_export import build_report_pdf_bytes


class CriticalRegressionTests(unittest.TestCase):
    def test_pdf_export_preserves_content_after_200_characters(self):
        marker = "TAIL_MARKER_SURVIVES"
        report_md = "- " + ("A" * 240) + marker

        pdf_bytes = build_report_pdf_bytes(report_md)

        self.assertIn(marker.encode("latin-1"), pdf_bytes)

    def test_agents_prefer_instance_api_key_over_process_environment(self):
        os.environ["GEMINI_API_KEY"] = "ENVIRONMENT_KEY"

        agent_cases = [
            ("agents.researcher.genai.Client", ResearcherAgent),
            ("agents.categorizer.genai.Client", CategorizerAgent),
            ("agents.analyst.genai.Client", AnalystAgent),
            ("agents.evaluator.genai.Client", EvaluatorAgent),
        ]

        for client_path, agent_cls in agent_cases:
            with self.subTest(agent=agent_cls.__name__):
                with patch(client_path) as client_cls:
                    agent_cls(api_key="SESSION_KEY")._get_client()

                client_cls.assert_called_once_with(api_key="SESSION_KEY")

    def test_graph_constructs_fresh_agents_with_run_api_key(self):
        with (
            patch("orchestrator.ResearcherAgent") as researcher,
            patch("orchestrator.CategorizerAgent") as categorizer,
            patch("orchestrator.AnalystAgent") as analyst,
            patch("orchestrator.EvaluatorAgent") as evaluator,
        ):
            orchestrator.build_graph(api_key="SESSION_KEY")

        researcher.assert_called_once_with(api_key="SESSION_KEY")
        categorizer.assert_called_once_with(api_key="SESSION_KEY")
        analyst.assert_called_once_with(api_key="SESSION_KEY")
        evaluator.assert_called_once_with(api_key="SESSION_KEY")

    def test_orchestrator_wrapper_forwards_api_key(self):
        with patch("main.run_analysis") as run_analysis:
            Orchestrator().run(company="Stripe", industry="fintech", api_key="SESSION_KEY")

        run_analysis.assert_called_once_with(
            company="Stripe",
            industry="fintech",
            api_key="SESSION_KEY",
        )


if __name__ == "__main__":
    unittest.main()
