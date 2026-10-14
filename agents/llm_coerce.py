"""Normalize messy Gemini JSON so later stages do not crash or drop data.

Live responses often use null, a bare string, or a dict where the schema
expects a list. Treat those as empty or as one entry. Never walk the
characters of a string, and never hash a dict.
"""

import html
import json
import re
from typing import Any, Dict, List

SWOT_QUADRANTS = ("strengths", "weaknesses", "opportunities", "threats")
_TEXT_KEYS = ("query", "text", "name", "value", "feature", "snippet", "gap", "url", "role")


def html_escape(value: Any) -> str:
    """Escape text before it is interpolated into an HTML template."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _item_text(item: Any) -> str:
    if item is None or isinstance(item, bool):
        return ""
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, (int, float)):
        return str(item)
    if isinstance(item, dict):
        for key in _TEXT_KEYS:
            text = item.get(key)
            if isinstance(text, str) and text.strip():
                return text.strip()
        try:
            return json.dumps(item, ensure_ascii=False, sort_keys=True)
        except TypeError:
            return str(item)
    return str(item).strip()


def as_str_list(value: Any) -> List[str]:
    """Return a list of strings. A string stays one entry, not a list of characters."""
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, dict):
        text = _item_text(value)
        return [text] if text else []
    if isinstance(value, list):
        items = []
        for item in value:
            text = _item_text(item)
            if text:
                items.append(text)
        return items
    text = _item_text(value)
    return [text] if text else []


def as_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return "; ".join(as_str_list(value))
    if isinstance(value, dict):
        return _item_text(value)
    return ""


def as_dict_list(value: Any) -> List[dict]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def dedupe_strings(values: Any) -> List[str]:
    return list(dict.fromkeys(as_str_list(values)))


def company_name(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    name = row.get("company_name")
    if isinstance(name, str):
        return name.strip()
    return ""


def coerce_score(value: Any, default: float = 5.0) -> float:
    """Clamp a rubric score to 0-10. Accepts 8, \"8\", and \"8/10\"."""
    if isinstance(value, bool) or value is None:
        return float(default)
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return float(default)
        if "/" in text:
            text = text.split("/", 1)[0]
        match = re.search(r"\d+(?:\.\d+)?", text)
        if not match:
            return float(default)
        number = float(match.group())
    else:
        return float(default)
    if number < 0:
        return 0.0
    if number > 10:
        return 10.0
    return number


def normalize_research_row(row: Any) -> Dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    return {
        "company_name": company_name(source),
        "raw_snippets": as_str_list(source.get("raw_snippets")),
        "sources": as_str_list(source.get("sources")),
    }


def merge_research_results(existing_rows: Any, new_rows: Any) -> List[dict]:
    """Merge a retry payload into rows already collected. Unnamed new rows are ignored."""
    merged: List[dict] = []
    index_by_name: Dict[str, dict] = {}

    for row in as_dict_list(existing_rows):
        item = normalize_research_row(row)
        merged.append(item)
        key = item["company_name"].lower()
        if key:
            index_by_name[key] = item

    for row in as_dict_list(new_rows):
        item = normalize_research_row(row)
        key = item["company_name"].lower()
        if not key:
            continue
        current = index_by_name.get(key)
        if current is None:
            index_by_name[key] = item
            merged.append(item)
            continue
        current["raw_snippets"] = dedupe_strings(current["raw_snippets"] + item["raw_snippets"])
        current["sources"] = dedupe_strings(current["sources"] + item["sources"])

    return merged


def normalize_competitor(row: Any) -> Dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    return {
        "company_name": company_name(source),
        "pricing": as_text(source.get("pricing")) or None,
        "key_features": as_str_list(source.get("key_features")),
        "target_audience": as_text(source.get("target_audience")) or None,
        "funding": as_text(source.get("funding")) or None,
        "hiring_signals": as_str_list(source.get("hiring_signals")),
        "recent_news": as_str_list(source.get("recent_news")),
        "customer_sentiment": as_text(source.get("customer_sentiment")) or None,
    }


def competitor_has_content(comp: dict) -> bool:
    for field in ("pricing", "target_audience", "funding", "customer_sentiment"):
        if as_text(comp.get(field)):
            return True
    for field in ("key_features", "hiring_signals", "recent_news"):
        if as_str_list(comp.get(field)):
            return True
    return False


def fill_competitor(current: dict, new: dict) -> dict:
    """Fill empty scalar fields and append list fields. Never replace good data."""
    filled = dict(current)
    for field in ("pricing", "target_audience", "funding", "customer_sentiment"):
        if not as_text(filled.get(field)) and as_text(new.get(field)):
            filled[field] = as_text(new.get(field))
    for field in ("key_features", "hiring_signals", "recent_news"):
        filled[field] = dedupe_strings(as_str_list(filled.get(field)) + as_str_list(new.get(field)))
    return filled


def normalize_analysis(analysis: Any) -> Dict[str, Any]:
    source = analysis if isinstance(analysis, dict) else {}
    swot_in = source.get("swot") if isinstance(source.get("swot"), dict) else {}
    matrix = []
    for row in as_dict_list(source.get("comparison_matrix")):
        matrix.append({
            "company_name": company_name(row) or "Unknown",
            "pricing_tier": as_text(row.get("pricing_tier")) or "?",
            "primary_strength": as_text(row.get("primary_strength")) or "?",
            "primary_weakness": as_text(row.get("primary_weakness")) or "?",
            "target_market": as_text(row.get("target_market")) or "?",
            "threat_level": as_text(row.get("threat_level")) or "Low",
        })
    return {
        "swot": {quadrant: as_str_list(swot_in.get(quadrant)) for quadrant in SWOT_QUADRANTS},
        "comparison_matrix": matrix,
        "threat_ranking": as_str_list(source.get("threat_ranking")),
        "opportunity_gaps": as_str_list(source.get("opportunity_gaps")),
    }


def analysis_usable(analysis: Any) -> bool:
    if not isinstance(analysis, dict) or not analysis:
        return False
    swot = analysis.get("swot")
    if isinstance(swot, dict) and any(as_str_list(value) for value in swot.values()):
        return True
    if as_dict_list(analysis.get("comparison_matrix")):
        return True
    if as_str_list(analysis.get("threat_ranking")) or as_str_list(analysis.get("opportunity_gaps")):
        return True
    return False


def swot_point_count(swot: Any) -> int:
    if not isinstance(swot, dict):
        return 0
    return sum(len(as_str_list(value)) for value in swot.values())


def pdf_safe_line(raw_line: str) -> str:
    """Encode one report line for Helvetica without shortening it."""
    return raw_line.encode("latin-1", "replace").decode("latin-1")


def report_pdf_bytes(report_md: str) -> bytes:
    """Build a PDF. Long lines wrap; they are not cut to a fixed width."""
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
