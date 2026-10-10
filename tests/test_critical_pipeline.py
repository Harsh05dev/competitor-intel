"""Regression tests for live-run crashes, retry data loss, and shared API keys."""

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.llm_coerce import pdf_safe_line, report_pdf_bytes
from agents.researcher import ResearcherAgent
from orchestrator import _agents_for_run, _bind_nodes, format_report_node, prepare_research_state


class _Response:
    def __init__(self, text):
        self.text = text


class _Models:
    def __init__(self, text=None, error=None, sink=None):
        self.text = text
        self.error = error
        self.sink = sink

    def generate_content(self, **kwargs):
        if self.sink is not None:
            self.sink["prompt"] = kwargs.get("contents")
        if self.error is not None:
            raise self.error
        return _Response(self.text)


class _Client:
    def __init__(self, text=None, error=None, sink=None):
        self.models = _Models(text=text, error=error, sink=sink)


def _install(agent, text=None, error=None, sink=None):
    agent.client = _Client(text=text, error=error, sink=sink)
    return agent


def _prior_analysis():
    return {
        "swot": {
            "strengths": ["API"],
            "weaknesses": ["fees"],
            "opportunities": ["smb"],
            "threats": ["adyen"],
        },
        "comparison_matrix": [],
        "threat_ranking": ["Square"],
        "opportunity_gaps": ["SMB onboarding"],
    }


def test_retry_query_string_is_not_split_into_characters():
    prepared = prepare_research_state({
        "iteration": 1,
        "evaluation": {"suggested_queries": "Square POS pricing 2025"},
    })
    assert prepared["evaluation"]["suggested_queries"] == ["Square POS pricing 2025"]

    sink = {}
    agent = _install(
        ResearcherAgent(api_key="test-key"),
        text='[{"company_name": null, "raw_snippets": ["ignored"]}, {"company_name": "Square", "raw_snippets": ["extra fact"], "sources": ["https://squareup.com"]}]',
        sink=sink,
    )
    existing = {
        "company_name": "Square",
        "raw_snippets": ["2.6% + 10c"],
        "sources": ["squareup.com"],
    }
    result = agent.research({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 1,
        "evaluation": {"suggested_queries": "Square POS pricing 2025"},
        "research_results": [
            {"raw_snippets": ["orphan fact"], "sources": []},
            existing,
        ],
    })

    assert "- Square POS pricing 2025" in sink["prompt"]
    assert "\n- S\n" not in sink["prompt"]
    square = next(row for row in result["research_results"] if row["company_name"] == "Square")
    assert square["raw_snippets"] == ["2.6% + 10c", "extra fact"]
    assert "https://squareup.com" in square["sources"]
    assert any("orphan fact" in row["raw_snippets"] for row in result["research_results"])


def test_null_suggested_queries_do_not_crash_retry():
    prepared = prepare_research_state({"iteration": 1, "evaluation": {"suggested_queries": None}})
    assert prepared["evaluation"]["suggested_queries"] == []

    agent = _install(ResearcherAgent(api_key="test-key"), text="[]")
    result = agent.research({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 1,
        "evaluation": {"suggested_queries": None},
        "research_results": [{"company_name": "Square", "raw_snippets": ["2.6% + 10c"], "sources": []}],
    })
    assert result["research_results"][0]["raw_snippets"] == ["2.6% + 10c"]


def test_researcher_node_caps_queries_without_slicing_a_string():
    class FakeResearcher:
        def __init__(self):
            self.seen = None

        def research(self, state):
            self.seen = state["evaluation"]["suggested_queries"]
            return {"research_results": [], "iteration": state["iteration"]}

    fake = FakeResearcher()
    node = _bind_nodes(fake, None, None, None)[0]
    queries = [f"query {i}" for i in range(8)]
    node({"iteration": 1, "logs": [], "evaluation": {"suggested_queries": queries}})
    assert fake.seen == queries[: config.MAX_GAPS_PER_RETRY]
    assert len(fake.seen) == config.MAX_GAPS_PER_RETRY

    node({"iteration": 1, "logs": [], "evaluation": {"suggested_queries": "Square POS pricing 2025"}})
    assert fake.seen == ["Square POS pricing 2025"]


def test_researcher_api_failure_on_retry_keeps_previous_results():
    agent = _install(ResearcherAgent(api_key="test-key"), error=RuntimeError("quota"))
    existing = [{"company_name": "Square", "raw_snippets": ["2.6% + 10c"], "sources": ["squareup.com"]}]
    result = agent.research({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 1,
        "evaluation": {"suggested_queries": ["Square open roles"]},
        "research_results": existing,
    })
    assert result["research_results"] == existing

    empty = agent.research({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 0,
        "research_results": [],
    })
    assert empty["research_results"] == []


def test_first_pass_null_snippets_stay_one_row():
    agent = _install(
        ResearcherAgent(api_key="test-key"),
        text='[{"company_name": "Square", "raw_snippets": null, "sources": null}, {"raw_snippets": ["orphan"]}]',
    )
    result = agent.research({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 0,
    })
    assert result["research_results"][0]["raw_snippets"] == []
    assert result["research_results"][0]["sources"] == []
    assert result["research_results"][1]["raw_snippets"] == ["orphan"]


def test_categorizer_merge_accepts_strings_and_dicts():
    agent = CategorizerAgent(api_key="test-key")
    existing = [
        {
            "company_name": "Square",
            "pricing": None,
            "key_features": "fast checkout",
            "hiring_signals": [{"role": "Engineer"}],
            "recent_news": None,
        },
        {
            "company_name": "Adyen",
            "pricing": "ic++",
            "key_features": ["unified"],
        },
    ]
    new_data = [
        "not-a-company",
        {"company_name": None, "pricing": "free"},
        {
            "company_name": "Square",
            "key_features": [{"name": "API"}, "api"],
            "hiring_signals": "50 open roles",
            "pricing": "2.9%",
        },
        {"company_name": "Adyen", "pricing": "replaced", "key_features": "extra feature"},
    ]
    merged = agent._merge(existing, new_data)
    by_name = {row["company_name"]: row for row in merged}

    assert by_name["Square"]["pricing"] == "2.9%"
    assert by_name["Square"]["key_features"] == ["fast checkout", "API", "api"]
    assert "f" not in by_name["Square"]["key_features"]
    assert "Engineer" in by_name["Square"]["hiring_signals"]
    assert "50 open roles" in by_name["Square"]["hiring_signals"]
    assert by_name["Adyen"]["pricing"] == "ic++"
    assert by_name["Adyen"]["key_features"] == ["unified", "extra feature"]
    assert by_name["Unknown"]["pricing"] == "free"


def test_categorizer_prompt_survives_null_and_string_snippets():
    sink = {}
    agent = _install(
        CategorizerAgent(api_key="test-key"),
        text='[{"company_name": "Square", "key_features": "pos hardware", "pricing": "2.6%"}]',
        sink=sink,
    )
    result = agent.categorize({
        "iteration": 1,
        "research_results": [
            {"company_name": "Square", "raw_snippets": None, "sources": None},
            {"company_name": "Adyen", "raw_snippets": "Interchange++ pricing", "sources": ["adyen.com"]},
            "ignore-me",
        ],
        "categorized_competitors": [{
            "company_name": "Square",
            "pricing": None,
            "key_features": "fast checkout",
        }],
    })
    assert "  • Interchange++ pricing\n" in sink["prompt"]
    assert "  • I\n" not in sink["prompt"]
    square = result["categorized_competitors"][0]
    assert "fast checkout" in square["key_features"]
    assert "pos hardware" in square["key_features"]
    assert "p" not in square["key_features"]


def test_evaluator_string_scores_and_null_breakdown(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    agent = EvaluatorAgent(api_key="test-key")
    assert agent._calculate_score(None) == 50
    perfect = {name: {"score": 10, "notes": ""} for name in config.EVAL_WEIGHTS}
    assert agent._calculate_score(perfect) == 100

    messy_state = {
        "target_company": "Stripe",
        "categorized_competitors": [
            {
                "company_name": "Square",
                "pricing": None,
                "key_features": None,
                "hiring_signals": "50 open roles",
                "recent_news": None,
            },
            "not-a-dict",
        ],
        "analysis": {"swot": None, "threat_ranking": None, "opportunity_gaps": None},
    }
    _install(agent, text=json.dumps({
        "breakdown": None,
        "gaps": None,
        "suggested_queries": None,
    }))
    scored = agent.evaluate(messy_state)
    assert scored["evaluation"]["score"] == 50
    assert scored["evaluation"]["suggested_queries"] == []

    breakdown = {name: {"score": "8/10", "notes": "ok"} for name in config.EVAL_WEIGHTS}
    _install(agent, text=json.dumps({
        "breakdown": breakdown,
        "gaps": [{"gap": "Missing pricing"}],
        "suggested_queries": "Square POS pricing 2025",
    }))
    scored = agent.evaluate(messy_state)
    assert scored["evaluation"]["score"] == 80
    assert scored["evaluation"]["passed"] is True
    assert scored["evaluation"]["suggested_queries"] == ["Square POS pricing 2025"]
    assert scored["evaluation"]["gaps"] == ["Missing pricing"]


def test_analyst_null_fields_do_not_crash_and_retry_keeps_prior_swot():
    sink = {}
    agent = _install(
        AnalystAgent(api_key="test-key"),
        text=json.dumps({
            "swot": {
                "strengths": ["scale"],
                "weaknesses": ["fees"],
                "opportunities": ["smb"],
                "threats": ["adyen"],
            },
            "comparison_matrix": [{
                "company_name": "Square",
                "threat_level": None,
                "pricing_tier": "flat",
                "primary_strength": "pos",
                "primary_weakness": "rates",
                "target_market": "smb",
            }],
            "threat_ranking": None,
            "opportunity_gaps": "SMB onboarding gap",
        }),
        sink=sink,
    )
    result = agent.analyze({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 0,
        "categorized_competitors": [
            {"company_name": "Square", "key_features": None, "hiring_signals": None, "recent_news": "expanding EU"},
            {"company_name": None, "key_features": [{"name": "Radar"}]},
        ],
        "analysis": {"swot": None},
    })
    assert "expanding EU" in sink["prompt"]
    assert "Radar" in sink["prompt"]
    assert result["analysis"]["swot"]["strengths"] == ["scale"]
    assert result["analysis"]["comparison_matrix"][0]["threat_level"] == "Low"
    assert result["analysis"]["opportunity_gaps"] == ["SMB onboarding gap"]

    prior = _prior_analysis()
    _install(agent, text='{"swot": null}')
    kept = agent.analyze({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 1,
        "categorized_competitors": [{"company_name": "Square", "key_features": ["pos"]}],
        "analysis": prior,
    })
    assert kept["analysis"]["swot"]["strengths"] == ["API"]

    _install(agent, error=RuntimeError("quota"))
    kept = agent.analyze({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 1,
        "categorized_competitors": [{"company_name": "Square", "key_features": ["pos"]}],
        "analysis": prior,
    })
    assert kept["analysis"] is prior

    _install(agent, text=json.dumps({"swot": {"strengths": ["new"], "weaknesses": [], "opportunities": [], "threats": []}}))
    replaced = agent.analyze({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 1,
        "categorized_competitors": [{"company_name": "Square", "key_features": ["pos"]}],
        "analysis": prior,
    })
    assert replaced["analysis"]["swot"]["strengths"] == ["new"]


def test_analyst_node_null_swot_does_not_crash():
    class FakeAnalyst:
        def analyze(self, state):
            return {"analysis": {"swot": None}}

    node = _bind_nodes(None, None, FakeAnalyst(), None)[2]
    out = node({"iteration": 1, "logs": []})
    assert out["status"] == "analyzed"
    assert "0 points" in out["logs"][-1]


def test_format_report_survives_null_swot_and_threat():
    out = format_report_node({
        "target_company": "Stripe",
        "industry": "fintech",
        "iteration": 2,
        "evaluation": {"score": 78},
        "logs": [],
        "analysis": {
            "swot": None,
            "comparison_matrix": [
                {"company_name": "Square", "threat_level": None, "pricing_tier": "flat"},
                "bad-row",
            ],
            "opportunity_gaps": None,
        },
    })
    assert "Stripe" in out["final_output"]
    assert "Square" in out["final_output"]
    assert out["status"] == "complete"


def test_explicit_api_keys_are_isolated(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    created = []

    class Recorder:
        def __init__(self, api_key):
            created.append(api_key)
            self.api_key = api_key

    monkeypatch.setattr("google.genai.Client", Recorder)
    first = ResearcherAgent(api_key="visitor-a")
    second = ResearcherAgent(api_key="visitor-b")
    assert first._get_client().api_key == "visitor-a"
    assert second._get_client().api_key == "visitor-b"
    assert created == ["visitor-a", "visitor-b"]
    assert first.client is not second.client
    assert os.environ.get("GEMINI_API_KEY") is None

    monkeypatch.setenv("GEMINI_API_KEY", "deployment-key")
    deployment = ResearcherAgent()
    assert deployment._get_client().api_key == "deployment-key"
    assert deployment._get_client() is deployment.client


def test_visitor_agents_are_not_cached_on_the_singleton():
    env_agents = _agents_for_run(None)
    assert _agents_for_run(None)[0] is env_agents[0]
    visitor = _agents_for_run("visitor-key")
    assert visitor[0] is not env_agents[0]
    assert visitor[0]._api_key == "visitor-key"
    assert env_agents[0]._api_key is None
    assert _agents_for_run("  ")[0] is env_agents[0]
    assert _agents_for_run(None)[0] is env_agents[0]


def test_pdf_keeps_lines_longer_than_200_characters(monkeypatch):
    from fpdf import FPDF

    captured = []
    original = FPDF.multi_cell

    def wrapped(self, *args, **kwargs):
        captured.append(kwargs.get("text"))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(FPDF, "multi_cell", wrapped)
    line = "Evidence " + ("specific market detail " * 20)
    assert len(line) > 200
    assert pdf_safe_line(line) == line
    payload = report_pdf_bytes(line + "\n" + "Strength \u2705 still exports\n")
    assert payload.startswith(b"%PDF")
    assert line in captured


def test_saved_report_survives_theme_toggle_and_key_is_not_global(monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=30)
    app.session_state["analysis_result"] = {
        "evaluation": {
            "score": 78,
            "passed": True,
            "gaps": ["<script>alert(1)</script>"],
            "suggested_queries": None,
        },
        "research_results": [{
            "company_name": "<img src=x>",
            "raw_snippets": ["<b>owned</b>"],
            "sources": [],
        }],
        "analysis": {
            "swot": {"strengths": None, "weaknesses": [], "opportunities": [], "threats": ["priced fairly"]},
            "comparison_matrix": [{
                "company_name": "Square",
                "threat_level": None,
                "pricing_tier": "flat",
                "primary_strength": "pos",
                "target_market": "smb",
            }],
            "opportunity_gaps": [],
        },
        "iteration": 2,
        "logs": ["[Iter 1] Evaluator: score=78/100 PASSED"],
        "target_company": "Stripe",
        "industry": "fintech",
    }
    app.session_state["analysis_company"] = "Stripe"
    app.run()
    assert not app.exception

    blob = "\n".join(element.value for element in app.markdown)
    assert "78" in blob
    assert "<script>alert(1)</script>" not in blob
    assert "&lt;script&gt;" in blob
    assert "LOW THREAT" in blob
    assert len(app.download_button) == 1

    app.button(key="theme_btn").click().run()
    assert not app.exception
    blob = "\n".join(element.value for element in app.markdown)
    assert "78" in blob
    assert len(app.download_button) == 1

    app.session_state["mode"] = "live"
    app.run()
    app.sidebar.text_input(key="gemini_api_key").set_value("visitor-key-xyz").run()
    assert os.environ.get("GEMINI_API_KEY", "") == ""
    assert app.session_state["gemini_api_key"] == "visitor-key-xyz"
