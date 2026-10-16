"""Pull JSON out of a Gemini reply without swallowing the payload.

Google Search Grounding often appends citation markers such as ``[1]`` after
a valid array. A first-bracket to last-bracket slice then includes those
markers and ``json.loads`` fails, so a successful research call comes back
empty. The same slice also latches onto an inner ``raw_snippets`` array when
the model returns one competitor object, which turns the company into a list
of strings and crashes the categorizer.

Scan for balanced ``[]`` / ``{}`` spans (quotes are not brackets) and keep
the longest span that parses. A trailing comma inside that span is ignored.
"""

import json
from typing import Any, List, Optional


def parse_json_list(text: str) -> list:
    """Return a list of rows. A single object becomes a one-item list."""
    value = _largest_json(text)
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return _dict_as_rows(value)
    return []


def parse_json_object(text: str) -> dict:
    """Return one JSON object. A one-item array of objects is unwrapped."""
    value = _largest_json(text)
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        dicts = [item for item in value if isinstance(item, dict)]
        if len(dicts) == 1:
            return dicts[0]
    return {}


def _dict_as_rows(value: dict) -> list:
    name = value.get("company_name")
    if isinstance(name, str) and name.strip():
        return [value]
    embedded = _longest_dict_list(value)
    if embedded:
        return embedded
    record_keys = ("raw_snippets", "sources", "key_features", "pricing", "hiring_signals", "recent_news")
    if any(key in value for key in record_keys):
        return [value]
    return []


def _longest_dict_list(value: dict) -> list:
    best: list = []
    for item in value.values():
        if isinstance(item, list) and item and all(isinstance(row, dict) for row in item):
            if len(item) > len(best):
                best = item
        elif isinstance(item, dict):
            nested = _longest_dict_list(item)
            if len(nested) > len(best):
                best = nested
    return best


def _largest_json(text: str) -> Any:
    cleaned = _strip_fences(text or "")
    if not cleaned:
        return None
    best: Any = None
    best_len = -1
    for start, end in _iter_spans(cleaned):
        length = end - start
        if length <= best_len:
            continue
        value = _loads(cleaned[start:end])
        if value is None:
            continue
        best = value
        best_len = length
    return best


def _strip_fences(text: str) -> str:
    cleaned = text.strip().lstrip("\ufeff")
    if "```" not in cleaned:
        return cleaned
    lines = [line for line in cleaned.split("\n") if not line.strip().startswith("```")]
    return "\n".join(lines).strip()


def _iter_spans(text: str):
    in_string = False
    escape = False
    for index, char in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char in "[{":
            end = _match_end(text, index)
            if end is not None:
                yield index, end


def _match_end(text: str, start: int) -> Optional[int]:
    pairs = {"[": "]", "{": "}"}
    stack = [pairs[text[start]]]
    in_string = False
    escape = False
    for index in range(start + 1, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char in pairs:
            stack.append(pairs[char])
            continue
        if char in "]}":
            if not stack or char != stack[-1]:
                return None
            stack.pop()
            if not stack:
                return index + 1
    return None


def _loads(snippet: str) -> Any:
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(_strip_trailing_commas(snippet))
    except json.JSONDecodeError:
        return None


def _strip_trailing_commas(snippet: str) -> str:
    """Drop commas that sit immediately before a closing brace or bracket."""
    out: List[str] = []
    in_string = False
    escape = False
    index = 0
    length = len(snippet)
    while index < length:
        char = snippet[index]
        if in_string:
            out.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        if char == ",":
            look = index + 1
            while look < length and snippet[look] in " \t\r\n":
                look += 1
            if look < length and snippet[look] in "}]":
                index += 1
                continue
        out.append(char)
        index += 1
    return "".join(out)
