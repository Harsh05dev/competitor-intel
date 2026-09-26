"""Coerce noisy Gemini JSON into the shapes the pipeline expects.

The model often returns null, a bare string where a list is required, or a
rubric score like "8/10". Those values crashed retry rounds or erased a
report that had already been built.
"""

from __future__ import annotations

import html
import json
from typing import Any


def escape_html(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def pdf_safe_line(raw_line: str) -> str:
    """Encode one report line for Helvetica without truncating it.

    fpdf2 multi_cell wraps long lines. Cutting the line to a fixed width
    dropped SWOT and comparison text from the downloaded PDF.
    """
    return (raw_line or "").encode("latin-1", "replace").decode("latin-1")


def report_pdf_bytes(report_md: str) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for raw_line in (report_md or "").split("\n"):
        safe = pdf_safe_line(raw_line)
        if safe.strip():
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, text=safe)
        else:
            pdf.ln(4)
    return bytes(pdf.output())


def _item_to_str(item: Any) -> str | None:
    if item is None:
        return None
    if isinstance(item, str):
        text = item.strip()
        return text or None
    if isinstance(item, bool):
        return str(item)
    if isinstance(item, (int, float)):
        return str(item)
    if isinstance(item, dict):
        for key in ("text", "name", "feature", "title", "value", "description"):
            inner = item.get(key)
            if isinstance(inner, str) and inner.strip():
                return inner.strip()
        try:
            return json.dumps(item, sort_keys=True, default=str)
        except TypeError:
            return str(item)
    if isinstance(item, (list, tuple)):
        parts = as_str_list(list(item))
        return "; ".join(parts) if parts else None
    text = str(item).strip()
    return text or None


def as_str_list(value: Any) -> list[str]:
    """Return a deduped list of strings.

    A scalar string stays one entry. It must not be iterated into characters,
    and it must not be concatenated with a list.
    """
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, dict):
        text = _item_to_str(value)
        return [text] if text else []
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        seen: set[str] = set()
        for item in value:
            text = _item_to_str(item)
            if text and text not in seen:
                seen.add(text)
                out.append(text)
        return out
    text = _item_to_str(value)
    return [text] if text else []


def as_dict_list(value: Any) -> list[dict]:
    if isinstance(value, dict):
        return [value]
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def company_key(comp: Any) -> str:
    if not isinstance(comp, dict):
        return ""
    name = comp.get("company_name")
    if not isinstance(name, str):
        return ""
    return name.strip().lower()


_WRAPPED_LIST_KEYS = ("competitors", "companies", "results", "data", "items", "research_results")


def coerce_json_list(parsed: Any) -> list[dict]:
    """Accept a JSON array or an object that wraps one. Drop non-dict rows.

    Only unwrap well-known container keys. A competitor object whose
    `key_features` are themselves objects must stay one row.
    """
    if isinstance(parsed, dict):
        for key in _WRAPPED_LIST_KEYS:
            rows = as_dict_list(parsed.get(key))
            if rows and isinstance(parsed.get(key), list):
                return rows
        return [parsed] if parsed else []
    return as_dict_list(parsed)


def coerce_json_object(parsed: Any) -> dict:
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                return item
    return {}


def coerce_rubric_score(value: Any, default: float = 5.0) -> float:
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        num = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        if "/" in text:
            text = text.split("/", 1)[0].strip()
        if text.endswith("%"):
            text = text[:-1].strip()
        try:
            num = float(text)
        except ValueError:
            return default
    else:
        return default
    if num < 0:
        return 0.0
    if num > 10:
        return 10.0
    return num


def usable_analysis(analysis: Any) -> bool:
    if not isinstance(analysis, dict) or not analysis:
        return False
    swot = analysis.get("swot")
    if isinstance(swot, dict):
        for quadrant in ("strengths", "weaknesses", "opportunities", "threats"):
            if as_str_list(swot.get(quadrant)):
                return True
    if as_dict_list(analysis.get("comparison_matrix")):
        return True
    if as_str_list(analysis.get("threat_ranking")) or as_str_list(analysis.get("opportunity_gaps")):
        return True
    return False


def empty_analysis() -> dict:
    return {
        "swot": {},
        "comparison_matrix": [],
        "threat_ranking": [],
        "opportunity_gaps": [],
    }


def threat_label(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "Low"
