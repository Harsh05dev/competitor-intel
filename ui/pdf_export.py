from fpdf import FPDF


def build_pdf_bytes(report_md: str) -> bytes:
    """Render markdown-ish report text to a PDF without dropping long lines."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    for raw_line in report_md.split("\n"):
        safe = raw_line.encode("latin-1", "replace").decode("latin-1")
        if safe.strip():
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, text=safe)
        else:
            pdf.ln(4)

    return bytes(pdf.output())
