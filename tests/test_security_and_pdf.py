import sys
import types as module_types
import unittest
from unittest.mock import patch


def _install_dependency_stubs():
    dotenv = module_types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    sys.modules["dotenv"] = dotenv

    google = module_types.ModuleType("google")
    genai = module_types.ModuleType("google.genai")
    genai_types = module_types.ModuleType("google.genai.types")
    genai.Client = object
    genai.types = genai_types
    google.genai = genai
    sys.modules["google"] = google
    sys.modules["google.genai"] = genai
    sys.modules["google.genai.types"] = genai_types

    langgraph = module_types.ModuleType("langgraph")
    graph = module_types.ModuleType("langgraph.graph")
    graph.END = "__end__"

    class FakeStateGraph:
        def __init__(self, state_type):
            self.state_type = state_type

        def add_node(self, *args, **kwargs):
            pass

        def add_edge(self, *args, **kwargs):
            pass

        def add_conditional_edges(self, *args, **kwargs):
            pass

        def set_entry_point(self, *args, **kwargs):
            pass

        def compile(self):
            return self

    graph.StateGraph = FakeStateGraph
    langgraph.graph = graph
    sys.modules["langgraph"] = langgraph
    sys.modules["langgraph.graph"] = graph

    fpdf = module_types.ModuleType("fpdf")
    fpdf.FPDF = object
    sys.modules["fpdf"] = fpdf


_install_dependency_stubs()

import orchestrator
from ui.pdf_export import build_pdf_bytes


class PerRunApiKeyTests(unittest.TestCase):
    def setUp(self):
        self._reset_singletons()

    def tearDown(self):
        self._reset_singletons()

    def _reset_singletons(self):
        orchestrator._researcher = None
        orchestrator._categorizer = None
        orchestrator._analyst = None
        orchestrator._evaluator = None

    def test_explicit_api_key_builds_fresh_agents_each_time(self):
        def make_agent(name):
            return lambda api_key=None: {"name": name, "api_key": api_key}

        with (
            patch.object(orchestrator, "ResearcherAgent", side_effect=make_agent("researcher")) as researcher,
            patch.object(orchestrator, "CategorizerAgent", side_effect=make_agent("categorizer")) as categorizer,
            patch.object(orchestrator, "AnalystAgent", side_effect=make_agent("analyst")) as analyst,
            patch.object(orchestrator, "EvaluatorAgent", side_effect=make_agent("evaluator")) as evaluator,
        ):
            first = orchestrator._get_agents(api_key="user-key")
            second = orchestrator._get_agents(api_key="user-key")

        for agent in first + second:
            self.assertEqual(agent["api_key"], "user-key")
        self.assertIsNot(first[0], second[0])
        self.assertEqual(researcher.call_count, 2)
        self.assertEqual(categorizer.call_count, 2)
        self.assertEqual(analyst.call_count, 2)
        self.assertEqual(evaluator.call_count, 2)


class PdfExportTests(unittest.TestCase):
    def test_long_report_lines_are_not_truncated_before_rendering(self):
        class FakePDF:
            last = None

            def __init__(self):
                self.lines = []
                self.l_margin = 10
                self.epw = 180
                FakePDF.last = self

            def add_page(self):
                pass

            def set_font(self, *args, **kwargs):
                pass

            def set_x(self, value):
                self.x = value

            def multi_cell(self, width, height, text):
                self.lines.append(text)

            def ln(self, height):
                self.lines.append("")

            def output(self):
                return bytearray(b"%PDF-test")

        long_line = "A" * 260
        with patch("ui.pdf_export.FPDF", FakePDF):
            pdf_bytes = build_pdf_bytes(f"{long_line}\n\nshort")

        self.assertEqual(pdf_bytes, b"%PDF-test")
        self.assertEqual(FakePDF.last.lines[0], long_line)
        self.assertEqual(len(FakePDF.last.lines[0]), 260)


if __name__ == "__main__":
    unittest.main()
