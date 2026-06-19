import importlib.util
import unittest

from ui.app_utils import escape_html, pdf_safe_text, report_to_pdf_bytes


class AppUtilsTest(unittest.TestCase):
    def test_escape_html_escapes_dynamic_content(self):
        self.assertEqual(
            escape_html('<img src=x onerror="alert(1)">'),
            '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;',
        )

    def test_pdf_safe_text_does_not_truncate_long_lines(self):
        long_line = "A" * 250
        self.assertEqual(pdf_safe_text(long_line), long_line)

    @unittest.skipIf(importlib.util.find_spec("fpdf") is None, "fpdf is not installed")
    def test_report_to_pdf_bytes_returns_pdf(self):
        pdf_bytes = report_to_pdf_bytes("# Report\n" + ("A" * 250))
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
