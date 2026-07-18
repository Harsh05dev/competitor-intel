import unittest
from pathlib import Path

from ui.report_pdf import write_report_lines


class FakePdf:
    l_margin = 10
    epw = 190

    def __init__(self):
        self.lines = []
        self.blank_lines = 0

    def set_x(self, value):
        self.x = value

    def multi_cell(self, width, height, text):
        self.lines.append(text)

    def ln(self, height):
        self.blank_lines += 1


class ReportRegressionTests(unittest.TestCase):
    def test_pdf_writer_preserves_lines_longer_than_200_characters(self):
        long_line = "competitor intelligence " * 20
        pdf = FakePdf()

        write_report_lines(pdf, f"{long_line}\n\nsummary")

        self.assertEqual(pdf.lines, [long_line, "summary"])
        self.assertEqual(pdf.blank_lines, 1)

    def test_saved_result_survives_theme_rerun(self):
        try:
            from streamlit.testing.v1 import AppTest
        except ImportError:
            self.skipTest("Streamlit testing support is unavailable")

        result = {
            "target_company": "Saved Co",
            "industry": "testing",
            "iteration": 1,
            "research_results": [],
            "analysis": {},
            "evaluation": {"score": 80, "passed": True, "gaps": [], "suggested_queries": []},
            "logs": [],
            "final_output": "# Saved report",
        }
        app_path = Path(__file__).parents[1] / "ui" / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=10)
        app.session_state["last_result"] = result

        app.run()
        self.assertEqual(len(app.tabs), 4)

        app.button(key="theme_btn").click().run()
        self.assertEqual(len(app.tabs), 4)
        self.assertEqual(app.session_state["last_result"], result)


if __name__ == "__main__":
    unittest.main()
