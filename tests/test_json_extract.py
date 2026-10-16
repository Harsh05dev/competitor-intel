"""Grounded Gemini replies must not be discarded or turned into snippet strings."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.json_extract import parse_json_list, parse_json_object


CITATION = """
[
  {"company_name": "Square", "raw_snippets": ["2.9% + 30c online"], "sources": ["https://squareup.com/pricing"]}
]
[1] https://squareup.com/pricing
[2] https://www.g2.com/products/square
"""

SINGLE = """
{
  "company_name": "Square",
  "raw_snippets": ["2.6% + 10c", "POS hardware"],
  "sources": ["https://squareup.com"]
}
"""

SINGLE_ONE_ARRAY = """
{
  "company_name": "Square",
  "raw_snippets": ["2.6% + 10c", "POS hardware"],
  "sources": "https://squareup.com"
}
"""

TRAILING_COMMA = """
[
  {"company_name": "Square", "raw_snippets": ["a"], "sources": ["u"]},
]
"""

PREAMBLE = """
Note {draft}:
{"swot": {"strengths": ["API"], "weaknesses": [], "opportunities": [], "threats": []}, "comparison_matrix": [], "threat_ranking": [], "opportunity_gaps": []}
"""


class JsonExtractTests(unittest.TestCase):
    def test_grounding_citations_keep_the_competitor_array(self):
        rows = parse_json_list(CITATION)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company_name"], "Square")
        self.assertEqual(rows[0]["raw_snippets"], ["2.9% + 30c online"])
        self.assertEqual(rows[0]["sources"], ["https://squareup.com/pricing"])

    def test_single_object_with_two_arrays_is_kept(self):
        rows = parse_json_list(SINGLE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company_name"], "Square")
        self.assertEqual(rows[0]["raw_snippets"], ["2.6% + 10c", "POS hardware"])

    def test_single_object_is_not_split_into_snippet_strings(self):
        # The old slice returned ["2.6% + 10c", "POS hardware"], and the
        # categorizer then crashed on str.get.
        rows = parse_json_list(SINGLE_ONE_ARRAY)
        self.assertEqual(len(rows), 1)
        self.assertIsInstance(rows[0], dict)
        self.assertEqual(rows[0].get("company_name"), "Square")
        self.assertEqual(rows[0].get("raw_snippets"), ["2.6% + 10c", "POS hardware"])

    def test_trailing_comma_array_parses(self):
        rows = parse_json_list(TRAILING_COMMA)
        self.assertEqual(rows[0]["company_name"], "Square")

    def test_wrapper_object_uses_the_embedded_rows(self):
        text = '{"competitors": [{"company_name": "Adyen", "raw_snippets": ["ic++"], "sources": ["https://adyen.com"]}]}'
        rows = parse_json_list(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company_name"], "Adyen")

    def test_bracket_inside_a_string_is_not_a_citation(self):
        text = """
[{"company_name": "Square", "raw_snippets": ["see [1] for price"], "sources": ["u"]}]
[1] https://example.com
"""
        rows = parse_json_list(text)
        self.assertEqual(rows[0]["raw_snippets"], ["see [1] for price"])

    def test_markdown_fence_plus_citation(self):
        text = """```json
[{"company_name": "Checkout.com", "raw_snippets": ["$40B"], "sources": ["https://checkout.com"]}]
```
[1] https://checkout.com
"""
        rows = parse_json_list(text)
        self.assertEqual(rows[0]["company_name"], "Checkout.com")

    def test_clean_array_is_unchanged(self):
        text = '[{"company_name": "Square"}, {"company_name": "Adyen"}]'
        rows = parse_json_list(text)
        self.assertEqual([row["company_name"] for row in rows], ["Square", "Adyen"])

    def test_preamble_brace_does_not_drop_the_analysis_object(self):
        data = parse_json_object(PREAMBLE)
        self.assertEqual(data["swot"]["strengths"], ["API"])

    def test_analysis_object_survives_a_trailing_citation(self):
        text = """
{"swot": {"strengths": ["docs"], "weaknesses": ["price"], "opportunities": [], "threats": []}, "comparison_matrix": [{"company_name": "Square", "threat_level": "High"}], "opportunity_gaps": ["SMB"]}
[1] https://squareup.com
"""
        data = parse_json_object(text)
        self.assertEqual(data["swot"]["strengths"], ["docs"])
        self.assertEqual(data["comparison_matrix"][0]["company_name"], "Square")

    def test_prose_and_empty_input_return_empty(self):
        self.assertEqual(parse_json_list(""), [])
        self.assertEqual(parse_json_list("no json here"), [])
        self.assertEqual(parse_json_object(""), {})
        self.assertEqual(parse_json_object("no json here"), {})

    def test_agents_parse_the_payloads_that_used_to_crash(self):
        from agents.analyst import AnalystAgent
        from agents.categorizer import CategorizerAgent
        from agents.evaluator import EvaluatorAgent
        from agents.researcher import ResearcherAgent

        researched = ResearcherAgent()._parse_json_list(CITATION)
        self.assertEqual(researched[0]["company_name"], "Square")

        categorized = CategorizerAgent()._parse_json_list(SINGLE_ONE_ARRAY)
        for row in categorized:
            self.assertEqual(row.get("company_name"), "Square")

        analysis = AnalystAgent()._parse_json_object(PREAMBLE)
        self.assertEqual(analysis["swot"]["strengths"], ["API"])

        evaluation = EvaluatorAgent()._parse_json_object(
            'Note {draft}: {"breakdown": {"swot_depth": {"score": 8, "notes": "ok"}}, "gaps": [], "suggested_queries": []}'
        )
        self.assertEqual(evaluation["breakdown"]["swot_depth"]["score"], 8)


if __name__ == "__main__":
    unittest.main()
