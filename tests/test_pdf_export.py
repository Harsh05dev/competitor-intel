import unittest

from ui.pdf_export import _iter_pdf_lines, build_pdf_bytes


class PdfExportTests(unittest.TestCase):
    def test_long_report_lines_are_not_truncated(self):
        tail = "TAIL_MARKER_MUST_SURVIVE"
        long_line = "- " + ("detailed competitive evidence " * 12) + tail

        rendered_lines = list(_iter_pdf_lines(long_line))

        self.assertEqual(1, len(rendered_lines))
        self.assertEqual(len(long_line), len(rendered_lines[0]))
        self.assertTrue(rendered_lines[0].endswith(tail))

    def test_pdf_generation_accepts_long_lines(self):
        report_md = "# Report\n\n- " + ("long but spaced report content " * 30)

        pdf_bytes = build_pdf_bytes(report_md)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
