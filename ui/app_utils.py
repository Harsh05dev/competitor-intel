"""Small safety helpers for the Streamlit UI."""

import html


def escape_html(value) -> str:
    """Escape dynamic text before inserting it into unsafe_allow_html templates."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def pdf_safe_text(value) -> str:
    """Convert text to the Latin-1 subset supported by the default FPDF font."""
    if value is None:
        return ""
    return str(value).encode("latin-1", "replace").decode("latin-1")


def report_to_pdf_bytes(report_md: str) -> bytes:
    """Render markdown-ish report text into a simple PDF without truncating lines."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    for raw_line in (report_md or "").split("\n"):
        safe = pdf_safe_text(raw_line)
        if safe.strip():
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, text=safe)
        else:
            pdf.ln(4)

    return bytes(pdf.output())
