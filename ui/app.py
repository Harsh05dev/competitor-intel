"""
Competitor Intelligence Dashboard — Streamlit UI (ui/app.py)

Entry point for the web dashboard. Renders the input form, runs the
agentic pipeline via the Orchestrator, and displays results including
metric cards, competitor data, evaluation gaps, and suggested queries.

Usage:
    streamlit run ui/app.py
"""

import streamlit as st
import sys
import os
import time

# Allow imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import Orchestrator

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Competitor Intel",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
.stDeployButton { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
.stAppDeployButton { display: none !important; }

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #05050f;
    color: #ffffff;
}

.stApp { background: #05050f; }

.block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}

section[data-testid="stSidebar"] {
    background: #080810 !important;
    border-right: 1px solid #1a1a35 !important;
}
section[data-testid="stSidebar"] > div {
    padding: 2rem 1.4rem !important;
}

.logo-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #aaaacc;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #1a1a35;
    margin-bottom: 2rem;
}

.sb-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #8888aa;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin: 1.8rem 0 0.7rem 0;
}

.pipe-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0.8rem;
    border-radius: 6px;
    margin-bottom: 0.3rem;
    background: #0d0d22;
    border: 1px solid #1a1a35;
}
.pipe-left { display: flex; align-items: center; gap: 0.5rem; }
.pipe-icon { font-size: 0.85rem; }
.pipe-name { font-size: 0.85rem; color: #ccccee; font-weight: 500; }
.pipe-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #8888aa;
    background: #ffffff10;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
}

.cfg-block {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #9999bb;
    line-height: 2.2;
    background: #0d0d22;
    border: 1px solid #1a1a35;
    border-radius: 6px;
    padding: 0.9rem 1rem;
}

.stTextInput label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #8888aa !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.4rem !important;
}
.stTextInput > div > div > input {
    background: #0d0d22 !important;
    border: 1px solid #1a1a35 !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00d4aa !important;
    box-shadow: 0 0 0 3px rgba(0,212,170,0.1) !important;
}
.stTextInput > div > div > input::placeholder { color: #444466 !important; }

.stButton > button {
    background: #00d4aa18 !important;
    color: #00d4aa !important;
    border: 1px solid #00d4aa50 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    padding: 0.75rem 1.5rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #00d4aa28 !important;
    border-color: #00d4aa90 !important;
    box-shadow: 0 0 20px rgba(0,212,170,0.12) !important;
}

.page-header {
    display: flex;
    align-items: center;
    gap: 1.2rem;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #1a1a35;
}
.page-title { font-size: 1.6rem; font-weight: 700; color: #ffffff; letter-spacing: -0.03em; }
.page-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #00d4aa;
    background: #00d4aa15;
    border: 1px solid #00d4aa40;
    border-radius: 999px;
    padding: 0.25rem 0.9rem;
    letter-spacing: 0.08em;
}
.page-sub { font-size: 0.82rem; color: #666688; margin-left: auto; font-family: 'JetBrains Mono', monospace; }

.metrics-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: #1a1a35;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #1a1a35;
    margin-bottom: 2.5rem;
}
.metric-cell { background: #080810; padding: 1.6rem 1.8rem; }
.m-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #666688;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.m-value { font-family: 'JetBrains Mono', monospace; font-size: 2.2rem; font-weight: 600; line-height: 1; color: #ffffff; }
.m-value.teal  { color: #00d4aa; }
.m-value.red   { color: #ff6b6b; }
.m-value.blue  { color: #60a5fa; }
.m-value.amber { color: #fbbf24; }
.m-sub { font-size: 0.72rem; color: #555577; margin-top: 0.4rem; font-family: 'JetBrains Mono', monospace; }

.sec-head {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #666688;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 2rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}
.sec-head::after { content: ''; flex: 1; height: 1px; background: #1a1a35; }

.comp-card {
    background: #080810;
    border: 1px solid #1a1a35;
    border-radius: 10px;
    padding: 1.3rem 1.6rem;
    margin-bottom: 0.7rem;
    transition: border-color 0.15s;
}
.comp-card:hover { border-color: #00d4aa40; }
.comp-name { font-size: 1rem; font-weight: 600; color: #ffffff; margin-bottom: 0.9rem; display: flex; align-items: center; gap: 0.6rem; }
.c-dot { width: 6px; height: 6px; border-radius: 50%; background: #00d4aa; flex-shrink: 0; }
.snippet { font-size: 0.85rem; color: #9999bb; padding: 0.28rem 0 0.28rem 0.9rem; border-left: 1px solid #1a1a35; margin-bottom: 0.28rem; line-height: 1.55; }
.src { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #00d4aa60; margin-top: 0.6rem; }

.gap-row {
    padding: 0.7rem 1.1rem;
    background: #ff6b6b08;
    border: 1px solid #ff6b6b20;
    border-left: 2px solid #ff6b6b60;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
    color: #ff9999;
    line-height: 1.55;
}
.q-row {
    padding: 0.7rem 1.1rem;
    background: #00d4aa08;
    border: 1px solid #00d4aa20;
    border-left: 2px solid #00d4aa60;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
    color: #00d4aa;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.55;
}

.prog-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.5rem 0;
    font-size: 0.85rem;
    color: #9999bb;
    font-family: 'JetBrains Mono', monospace;
}
.prog-dot { width: 6px; height: 6px; border-radius: 50%; background: #00d4aa; flex-shrink: 0; animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #1a1a35 !important; gap: 0 !important; padding: 0 !important; }
.stTabs [data-baseweb="tab"] { font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: #555577 !important; padding: 0.8rem 1.4rem !important; border-radius: 0 !important; border-bottom: 2px solid transparent !important; background: transparent !important; }
.stTabs [aria-selected="true"] { color: #00d4aa !important; border-bottom: 2px solid #00d4aa !important; background: transparent !important; }

.stProgress > div > div { background: #00d4aa !important; }
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: #05050f; }
::-webkit-scrollbar-thumb { background: #1a1a35; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


def render_sidebar():
    """Render the left sidebar with API key input, pipeline diagram, and config."""
    with st.sidebar:
        st.markdown('<div class="logo-text">⚡ competitor-intel</div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-label">API Key</div>', unsafe_allow_html=True)
        api_key_input = st.text_input(
            "key", type="password",
            placeholder="paste Gemini key (or use .env)",
            label_visibility="collapsed"
        )
        if api_key_input:
            os.environ["GEMINI_API_KEY"] = api_key_input
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#555577;margin-top:0.3rem;">overrides .env if set</div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-label">Pipeline</div>', unsafe_allow_html=True)
        for icon, name, tag in [
            ("🔍", "Researcher", "round 1+"),
            ("📊", "Evaluator",  "scorer"),
            ("🔁", "Loop",       "score < 70"),
            ("✅", "Report",     "final"),
        ]:
            st.markdown(f'<div class="pipe-item"><div class="pipe-left"><span class="pipe-icon">{icon}</span><span class="pipe-name">{name}</span></div><span class="pipe-tag">{tag}</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-label">Config</div>', unsafe_allow_html=True)
        st.markdown('<div class="cfg-block">MAX_ITER &nbsp;= 3<br>THRESHOLD = 70<br>MODEL &nbsp;&nbsp;&nbsp;&nbsp;= gemini-flash</div>', unsafe_allow_html=True)


def render_header():
    """Render the main page header with title and subtitle."""
    st.markdown("""
    <div class="page-header">
        <div class="page-title">Competitor Intel</div>
        <div class="page-pill">CS 301</div>
        <div class="page-sub">agentic research system</div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(score, passed, competitors, iterations):
    """Render the four metric cards showing score, pass/fail, competitor count, iterations."""
    sc = "teal" if score >= 70 else "red"
    pv = "PASS"  if passed else "FAIL"
    pc = "teal"  if passed else "red"

    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-cell">
            <div class="m-label">Quality Score</div>
            <div class="m-value {sc}">{score}</div>
            <div class="m-sub">/ 100 · threshold 70</div>
        </div>
        <div class="metric-cell">
            <div class="m-label">Evaluation</div>
            <div class="m-value {pc}">{pv}</div>
            <div class="m-sub">{"criteria met" if passed else "needs improvement"}</div>
        </div>
        <div class="metric-cell">
            <div class="m-label">Competitors</div>
            <div class="m-value blue">{len(competitors)}</div>
            <div class="m-sub">companies found</div>
        </div>
        <div class="metric-cell">
            <div class="m-label">Iterations</div>
            <div class="m-value amber">{iterations}</div>
            <div class="m-sub">of 3 max</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_competitors(competitors):
    """Render competitor cards with snippets and source links."""
    st.markdown('<div class="sec-head">Competitor Data</div>', unsafe_allow_html=True)
    if competitors:
        for c in competitors:
            name     = c.get("company_name", "Unknown")
            snippets = c.get("raw_snippets", [])
            sources  = c.get("sources", [])
            sh = "".join(f'<div class="snippet">· {s}</div>' for s in snippets)
            sr = "".join(f'<div class="src">↗ {s}</div>' for s in sources)
            st.markdown(f'<div class="comp-card"><div class="comp-name"><span class="c-dot"></span>{name}</div>{sh}{sr}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#666688;font-size:0.9rem;padding:1rem 0;">No competitor data returned.</div>', unsafe_allow_html=True)


def render_gaps_and_queries(gaps, queries):
    """Render data gaps and suggested queries side by side."""
    gc, qc = st.columns(2)
    with gc:
        st.markdown('<div class="sec-head">Data Gaps</div>', unsafe_allow_html=True)
        if gaps:
            for g in gaps:
                st.markdown(f'<div class="gap-row">⚠ {g}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#666688;font-size:0.85rem;">No gaps detected.</div>', unsafe_allow_html=True)
    with qc:
        st.markdown('<div class="sec-head">Suggested Queries</div>', unsafe_allow_html=True)
        if queries:
            for q in queries:
                st.markdown(f'<div class="q-row">→ {q}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#666688;font-size:0.85rem;">No queries suggested.</div>', unsafe_allow_html=True)


def run_pipeline(company, industry):
    """
    Run the agentic pipeline with live progress updates.

    Wraps the Orchestrator.run() call with status messages and
    a progress bar so the user can see each agent as it executes.

    Returns the full result state dict from the Orchestrator.
    """
    slot = st.empty()
    bar  = st.progress(0)

    def status(msg, pct):
        slot.markdown(f'<div class="prog-row"><div class="prog-dot"></div>{msg}</div>', unsafe_allow_html=True)
        bar.progress(pct)

    status("researcher → scanning competitors...", 0.1)

    with st.spinner(""):
        orch = Orchestrator()
        orig = orch.run

        def patched(company, industry):
            status("evaluator → scoring data quality...", 0.4)
            res = orig(company=company, industry=industry)
            status("decision → checking retry condition...", 0.75)
            time.sleep(0.2)
            status("format → compiling final report...", 0.92)
            time.sleep(0.2)
            return res

        orch.run = patched
        result = orch.run(company=company, industry=industry)

    slot.empty()
    bar.empty()
    return result


# ── Main app ──────────────────────────────────────────────────────────────────
render_sidebar()
render_header()

col1, col2, col3 = st.columns([5, 5, 2])
with col1:
    company = st.text_input("TARGET_COMPANY", value="Stripe", placeholder="e.g. Stripe, Notion, Figma")
with col2:
    industry = st.text_input("INDUSTRY", value="fintech", placeholder="e.g. fintech, productivity")
with col3:
    st.markdown('<div style="height:1.95rem"></div>', unsafe_allow_html=True)
    run_btn = st.button("▶ RUN", use_container_width=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

if run_btn:
    if not company.strip() or not industry.strip():
        st.error("Both fields required.")
        st.stop()

    try:
        result = run_pipeline(company, industry)
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.stop()

    ev          = result.get("evaluation", {})
    score       = ev.get("score", 0)
    passed      = ev.get("passed", False)
    gaps        = ev.get("gaps", [])
    queries     = ev.get("suggested_queries", [])
    competitors = result.get("research_results", [])
    iterations  = result.get("iteration", 1)

    render_metrics(score, passed, competitors, iterations)

    tab1, tab2, tab3 = st.tabs(["Competitors", "Gaps & Queries", "Raw State"])
    with tab1:
        render_competitors(competitors)
    with tab2:
        render_gaps_and_queries(gaps, queries)
    with tab3:
        st.markdown('<div class="sec-head">Full Agent State</div>', unsafe_allow_html=True)
        st.json(result)

    if not passed and iterations >= 3:
        st.warning("Max iterations reached — report generated with low confidence.")

else:
    st.markdown("""
    <div style="margin-top:6rem;text-align:center;">
        <div style="font-size:2rem;margin-bottom:1rem;opacity:0.2;">⚡</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#333355;letter-spacing:0.25em;text-transform:uppercase;margin-bottom:0.6rem;">System Ready</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;color:#444466;">Enter target company + industry → click ▶ RUN</div>
    </div>
    """, unsafe_allow_html=True)
