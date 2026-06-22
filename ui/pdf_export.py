"""PDF export helpers for Streamlit report downloads."""


def pdf_safe_text(raw_line: str) -> str:
    """Convert text to the Latin-1 subset supported by the current PDF font."""
    return raw_line.encode("latin-1", "replace").decode("latin-1")


def write_report_markdown_to_pdf(pdf, report_md: str) -> None:
    """Write report markdown to an FPDF instance without truncating content."""
    for raw_line in report_md.split("\n"):
        safe = pdf_safe_text(raw_line)
        if safe.strip():
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, text=safe)
        else:
            pdf.ln(4)


def build_report_pdf(report_md: str) -> bytes:
    """Build PDF bytes for a markdown report."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    write_report_markdown_to_pdf(pdf, report_md)
    return bytes(pdf.output())
