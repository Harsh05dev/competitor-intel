"""PDF export helpers for competitor intelligence reports."""

from fpdf import FPDF


def _sanitize_pdf_text(text: str) -> str:
    """Convert text to the Latin-1 subset supported by the configured PDF font."""
    return text.encode("latin-1", "replace").decode("latin-1")


def _iter_pdf_lines(report_md: str):
    """Yield sanitized report lines without dropping content."""
    for raw_line in report_md.split("\n"):
        yield _sanitize_pdf_text(raw_line)


def build_pdf_bytes(report_md: str) -> bytes:
    """Render markdown-ish report text into a downloadable PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    for safe in _iter_pdf_lines(report_md):
        if safe.strip():
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, text=safe)
        else:
            pdf.ln(4)

    return bytes(pdf.output())
