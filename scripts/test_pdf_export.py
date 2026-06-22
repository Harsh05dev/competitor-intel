import unittest

from ui.pdf_export import pdf_safe_text, write_report_markdown_to_pdf


class FakePdf:
    def __init__(self):
        self.l_margin = 10
        self.epw = 180
        self.cells = []
        self.breaks = 0
        self.x_positions = []

    def set_x(self, value):
        self.x_positions.append(value)

    def multi_cell(self, width, height, text):
        self.cells.append((width, height, text))

    def ln(self, height):
        self.breaks += 1


class PdfExportTests(unittest.TestCase):
    def test_pdf_safe_text_preserves_long_lines(self):
        line = "Pricing detail: " + ("enterprise-rate " * 20)

        safe = pdf_safe_text(line)

        self.assertEqual(line, safe)
        self.assertGreater(len(safe), 200)

    def test_write_report_markdown_to_pdf_does_not_truncate_lines(self):
        line = "Opportunity gap: " + ("self-serve onboarding " * 15)
        pdf = FakePdf()

        write_report_markdown_to_pdf(pdf, f"{line}\n\nshort")

        self.assertEqual(pdf.cells[0][2], line)
        self.assertGreater(len(pdf.cells[0][2]), 200)
        self.assertEqual(pdf.cells[1][2], "short")
        self.assertEqual(pdf.breaks, 1)


if __name__ == "__main__":
    unittest.main()
