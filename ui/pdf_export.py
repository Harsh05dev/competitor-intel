"""PDF export helpers for the Streamlit dashboard."""

from fpdf import FPDF


def _to_pdf_safe_text(text: str) -> str:
    """FPDF's built-in Helvetica font only supports Latin-1."""
    return text.encode("latin-1", "replace").decode("latin-1")


def build_report_pdf_bytes(report_md: str) -> bytes:
    """Render a markdown-ish report to PDF bytes without truncating content."""
    pdf = FPDF()
    pdf.set_compression(False)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    for raw_line in report_md.split("\n"):
        safe = _to_pdf_safe_text(raw_line)
        if safe.strip():
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, text=safe)
        else:
            pdf.ln(4)

    return bytes(pdf.output())
