"""Locks in crash, data-loss, and API-key isolation fixes."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.analyst import AnalystAgent
from agents.categorizer import CategorizerAgent
from agents.evaluator import EvaluatorAgent
from agents.llm_coerce import (
    as_str_list,
    coerce_json_list,
    escape_html,
    pdf_safe_line,
    report_pdf_bytes,
    threat_label,
)
from agents.researcher import ResearcherAgent
from main import Orchestrator
from orchestrator import _make_agents, format_report_node, researcher_node


PRIOR_ANALYSIS = {
    "swot": {
        "strengths": ["Developer API with documented webhooks"],
        "weaknesses": ["Flat-rate pricing loses at high volume"],
        "opportunities": ["Non-technical SMB onboarding"],
        "threats": ["Adyen interchange pricing"],
    },
    "comparison_matrix": [
        {"company_name": "Square", "pricing_tier": "Flat rate", "threat_level": "High"}
    ],
    "threat_ranking": ["Square"],
    "opportunity_gaps": ["SMB onboarding is still awkward for every incumbent"],
}

PRIOR_RESEARCH = [
    {
        "company_name": "Square",
        "raw_snippets": ["2.6% + 10c in-person"],
        "sources": ["squareup.com"],
    },
    {"raw_snippets": ["orphan snippet with no company name"], "sources": []},
]


class _Resp:
    def __init__(self, text):
        self.text = text


class _Models:
    def __init__(self, text=None, error=None, sink=None):
        self.text = text
        self.error = error
        self.sink = sink

    def generate_content(self, **kwargs):
        if self.sink is not None:
            self.sink.append(kwargs.get("contents"))
        if self.error:
            raise self.error
        return _Resp(self.text)


class _Client:
    def __init__(self, models):
        self.models = models


def _patch_client(agent, models):
    agent._get_client = lambda: _Client(models)


def test_categorizer_merge_survives_null_names_dicts_and_strings():
    merged = CategorizerAgent()._merge(
        [
            {
                "company_name": "Acme",
                "pricing": "1%",
                "key_features": [{"name": "vault"}, "api"],
            }
        ],
        [
            {"company_name": None, "pricing": "should-not-apply", "key_features": ["ignored"]},
            {
                "company_name": "Acme",
                "key_features": ["api", "POS hardware"],
                "pricing": "9%",
            },
        ],
    )
    assert merged[0]["pricing"] == "1%"
    assert merged[0]["key_features"] == ["vault", "api", "POS hardware"]

    merged_string = CategorizerAgent()._merge(
        [{"company_name": "Acme", "key_features": "POS hardware"}],
        [{"company_name": "acme", "key_features": ["API"]}],
    )
    assert merged_string[0]["key_features"] == ["POS hardware", "API"]


def test_categorizer_prompt_treats_null_snippets_as_empty():
    agent = CategorizerAgent(api_key="test-key")
    seen = []
    _patch_client(agent, _Models(text="[]", sink=seen))
    result = agent.categorize(
        {
            "iteration": 0,
            "research_results": [
                "not-a-row",
                {"company_name": "Square", "raw_snippets": None, "sources": None},
            ],
            "categorized_competitors": [],
        }
    )
    assert "Square" in seen[0]
    assert result["categorized_competitors"] == []


def test_researcher_retry_keeps_results_when_queries_or_names_are_null():
    agent = ResearcherAgent(api_key="test-key")
    seen = []
    _patch_client(
        agent,
        _Models(
            text='[{"company_name": null, "raw_snippets": ["new fact"], "sources": ["x"]}]',
            sink=seen,
        ),
    )
    out = agent.research(
        {
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "evaluation": {"suggested_queries": None},
            "research_results": PRIOR_RESEARCH,
        }
    )
    names = [row.get("company_name") for row in out["research_results"]]
    assert "Square" in names
    assert any(row.get("raw_snippets") == ["orphan snippet with no company name"] for row in out["research_results"])
    assert "- None" not in seen[0]


def test_researcher_string_query_is_not_split_into_characters():
    agent = ResearcherAgent(api_key="test-key")
    seen = []
    _patch_client(agent, _Models(text="[]", sink=seen))
    query = "Square POS pricing 2025"
    agent.research(
        {
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "evaluation": {"suggested_queries": query},
            "research_results": PRIOR_RESEARCH,
        }
    )
    assert query in seen[0]
    assert "- S\n- q" not in seen[0]


def test_researcher_node_caps_a_string_query_as_one_item():
    class Fake:
        def research(self, state):
            self.state = state
            return {"research_results": [], "iteration": state["iteration"]}

    fake = Fake()
    researcher_node(
        {
            "iteration": 1,
            "evaluation": {"suggested_queries": "Square POS pricing 2025"},
            "logs": [],
            "research_results": [],
        },
        fake,
    )
    assert fake.state["evaluation"]["suggested_queries"] == ["Square POS pricing 2025"]


def test_researcher_api_failure_on_retry_preserves_snippets():
    agent = ResearcherAgent(api_key="test-key")
    _patch_client(agent, _Models(error=RuntimeError("503")))
    out = agent.research(
        {
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 1,
            "evaluation": {"suggested_queries": ["Square hiring"]},
            "research_results": PRIOR_RESEARCH,
        }
    )
    assert out["research_results"] == PRIOR_RESEARCH


def test_analyst_null_swot_and_api_failure_keep_prior_analysis():
    agent = AnalystAgent(api_key="test-key")
    state = {
        "target_company": "Stripe",
        "industry": "fintech",
        "categorized_competitors": [{"company_name": "Square", "pricing": "2.6%"}],
        "analysis": PRIOR_ANALYSIS,
    }
    _patch_client(agent, _Models(text='{"swot": null}'))
    kept = agent.analyze(state)
    assert kept["analysis"]["swot"]["strengths"] == ["Developer API with documented webhooks"]

    _patch_client(agent, _Models(error=RuntimeError("503")))
    kept = agent.analyze(state)
    assert kept["analysis"]["opportunity_gaps"] == PRIOR_ANALYSIS["opportunity_gaps"]


def test_analyst_prompt_does_not_explode_string_features():
    agent = AnalystAgent(api_key="test-key")
    seen = []
    _patch_client(agent, _Models(text='{"swot": {"strengths": ["ok"]}}', sink=seen))
    agent.analyze(
        {
            "target_company": "Stripe",
            "industry": "fintech",
            "categorized_competitors": [
                "skip-me",
                {"company_name": "Square", "key_features": "POS hardware", "hiring_signals": None, "recent_news": None},
            ],
            "analysis": {},
        }
    )
    assert "POS hardware" in seen[0]
    assert "P, O, S" not in seen[0]


def test_evaluator_string_scores_null_breakdown_and_null_swot():
    agent = EvaluatorAgent(api_key="test-key")
    seen = []
    _patch_client(
        agent,
        _Models(
            text=(
                '{"breakdown": {"competitor_count": {"score": "8/10", "notes": "ok"},'
                ' "pricing_coverage": {"score": "8", "notes": "ok"}},'
                ' "gaps": null, "suggested_queries": null}'
            ),
            sink=seen,
        ),
    )
    out = agent.evaluate(
        {
            "target_company": "Stripe",
            "categorized_competitors": [
                {"company_name": "Square", "key_features": "POS hardware", "hiring_signals": None, "recent_news": None}
            ],
            "analysis": {"swot": None},
        }
    )
    # competitor_count 8 * 15 and pricing 8 * 20, remaining four criteria default to 5.
    assert out["evaluation"]["score"] == int((0.8 * 15) + (0.8 * 20) + (0.5 * 20) + (0.5 * 15) + (0.5 * 10) + (0.5 * 20))
    assert out["evaluation"]["suggested_queries"] == []
    assert "POS hardware" in seen[0]
    assert "P, O, S" not in seen[0]

    _patch_client(agent, _Models(text='{"breakdown": null, "gaps": [], "suggested_queries": []}'))
    out = agent.evaluate(
        {
            "target_company": "Stripe",
            "categorized_competitors": [],
            "analysis": {"swot": {"strengths": None, "weaknesses": [], "opportunities": [], "threats": []}},
        }
    )
    assert out["evaluation"]["score"] == 50


def test_format_report_survives_null_swot():
    out = format_report_node(
        {
            "target_company": "Stripe",
            "industry": "fintech",
            "iteration": 2,
            "evaluation": {"score": 80},
            "analysis": {
                "swot": None,
                "comparison_matrix": [{"company_name": "Square", "threat_level": None}],
                "opportunity_gaps": None,
            },
            "logs": [],
        }
    )
    assert "Stripe" in out["final_output"]
    assert "Square" in out["final_output"]


def test_user_api_key_is_not_taken_from_the_process_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    with patch("agents.researcher.genai.Client") as client:
        ResearcherAgent(api_key="user-key")._get_client()
        client.assert_called_once_with(api_key="user-key")


def test_explicit_keys_do_not_share_agents():
    first = _make_agents("user-key-a")
    second = _make_agents("user-key-b")
    repeat = _make_agents("user-key-a")
    assert first[0] is not second[0]
    assert first[0] is not repeat[0]
    assert first[0]._api_key == "user-key-a"
    assert second[0]._api_key == "user-key-b"
    shared = _make_agents(None)
    assert _make_agents("")[0] is shared[0]


def test_orchestrator_forwards_api_key(monkeypatch):
    captured = {}

    def fake(company, industry, api_key=None):
        captured["api_key"] = api_key
        return {"evaluation": {}}

    monkeypatch.setattr("main.run_analysis", fake)
    Orchestrator().run(company="Stripe", industry="fintech", api_key="user-key")
    assert captured["api_key"] == "user-key"


def test_ui_does_not_publish_visitor_keys_on_the_process():
    source = Path("ui/app.py").read_text()
    assert 'os.environ["GEMINI_API_KEY"]' not in source
    assert "api_key.strip()" in source
    assert "analysis_result" in source


def test_pdf_export_keeps_long_report_lines():
    long_line = "Opportunity: " + ("non-technical onboarding gap " * 20)
    assert len(pdf_safe_line(long_line)) > 200
    blob = report_pdf_bytes("# Report\n\n" + long_line)
    assert b"non-technical onboarding gap" in blob or _pdf_text(blob).count("onboarding") >= 1


def test_html_and_threat_fallbacks():
    assert escape_html('<img src=x onerror=alert(1)>') == "&lt;img src=x onerror=alert(1)&gt;"
    assert threat_label(None) == "Low"
    assert threat_label(" High ").upper() == "HIGH"
    assert as_str_list("POS hardware") == ["POS hardware"]
    assert coerce_json_list(
        {"company_name": "Acme", "key_features": [{"name": "vault"}]}
    ) == [{"company_name": "Acme", "key_features": [{"name": "vault"}]}]


def _pdf_text(blob: bytes) -> str:
    import re
    import zlib

    parts = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", blob, re.S):
        raw = match.group(1)
        try:
            parts.append(zlib.decompress(raw).decode("latin-1", "replace"))
        except zlib.error:
            parts.append(raw.decode("latin-1", "replace"))
    return "\n".join(parts)


def test_demo_report_survives_rerun_and_live_key_stays_session_local(monkeypatch):
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    real_sleep = __import__("time").sleep

    def fast_sleep(seconds):
        if seconds >= 1:
            return None
        return real_sleep(seconds)

    monkeypatch.setattr("time.sleep", fast_sleep)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "ui" / "app.py"),
        default_timeout=30,
    )
    app.run()
    app.button(key="run_main").click().run()
    rendered = "\n".join(block.value for block in app.markdown)
    assert "Square" in rendered
    assert "78" in rendered

    app.button(key="theme_btn").click().run()
    rendered = "\n".join(block.value for block in app.markdown)
    assert "Square" in rendered
    assert "78" in rendered
    assert app.download_button

    app.button(key="btn_live").click().run()
    app.text_input(key="gemini_api_key").set_value("user-typed-key").run()
    assert os.environ.get("GEMINI_API_KEY") != "user-typed-key"
