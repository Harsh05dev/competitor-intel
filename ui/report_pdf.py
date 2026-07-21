def write_report_lines(pdf, report_markdown: str) -> None:
    """Write every report line to an FPDF document without truncating content."""
    for raw_line in report_markdown.split("\n"):
        safe_line = raw_line.encode("latin-1", "replace").decode("latin-1")
        if safe_line.strip():
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, text=safe_line)
        else:
            pdf.ln(4)
