import streamlit as st
import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import Orchestrator

st.set_page_config(
    page_title="Competitor Intel",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}
.stApp { background: #0a0a0f; }
.main-header {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #e8e8f0 0%, #a78bfa 50%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
}
.sub-header {
    font-size: 0.95rem;
    color: #6b6b8a;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}
.score-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #2d2d4e;
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
}
.score-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: #a78bfa;
    line-height: 1;
}
.score-label {
    font-size: 0.75rem;
    color: #6b6b8a;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.4rem;
}
.badge-pass {
    display: inline-block;
    background: #064e3b;
    color: #6ee7b7;
    border: 1px solid #059669;
    border-radius: 999px;
    padding: 0.3rem 1rem;
    font-size: 0.8rem;
    font-weight: 600;
}
.badge-fail {
    display: inline-block;
    background: #450a0a;
    color: #fca5a5;
    border: 1px solid #dc2626;
    border-radius: 999px;
    padding: 0.3rem 1rem;
    font-size: 0.8rem;
    font-weight: 600;
}
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #a78bfa;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.8rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #2d2d4e;
}
.competitor-card {
    background: #111127;
    border: 1px solid #2d2d4e;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
}
.competitor-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #e8e8f0;
    margin-bottom: 0.5rem;
}
.snippet-item {
    font-size: 0.85rem;
    color: #9090b0;
    padding: 0.2rem 0 0.2rem 1rem;
    border-left: 2px solid #3d3d6e;
    margin-bottom: 0.3rem;
}
.gap-item {
    background: #1a0a0a;
    border-left: 3px solid #dc2626;
    border-radius: 0 8px 8px 0;
    padding: 0.6rem 1rem;
    margin-bottom: 0.4rem;
    font-size: 0.875rem;
    color: #fca5a5;
}
.query-item {
    background: #0a1a0a;
    border-left: 3px solid #059669;
    border-radius: 0 8px 8px 0;
    padding: 0.6rem 1rem;
    margin-bottom: 0.4rem;
    font-size: 0.875rem;
    color: #6ee7b7;
}
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #2d2d4e, transparent);
    margin: 2rem 0;
}
.step-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #a78bfa;
    display: inline-block;
    margin-right: 0.6rem;
}
section[data-testid="stSidebar"] { background: #0d0d1a; border-right: 1px solid #1d1d3e; }
.stTextInput > div > div > input {
    background: #111127 !important;
    border: 1px solid #2d2d4e !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
}
.stTextInput > div > div > input:focus { border-color: #a78bfa !important; }
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    width: 100% !important;
}
.stTabs [data-baseweb="tab-list"] { background: #111127; border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: #6b6b8a; font-size: 0.85rem; }
.stTabs [aria-selected="true"] { background: #1d1d4e !important; color: #a78bfa !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;color:#a78bfa;">⚙️ Settings</p>', unsafe_allow_html=True)
    api_key_input = st.text_input("Gemini API Key", type="password", placeholder="Leave blank to use .env")
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
    st.markdown("---")
    st.markdown('<p style="font-size:0.85rem;font-weight:700;color:#6b6b8a;text-transform:uppercase;letter-spacing:0.1em;">System Architecture</p>', unsafe_allow_html=True)
    st.markdown("""
<div style="font-size:0.8rem;color:#6b6b8a;line-height:2.2;">
🔍 <b style="color:#a78bfa">Researcher</b> — finds competitors<br>
📊 <b style="color:#60a5fa">Evaluator</b> — scores data quality<br>
🔁 <b style="color:#34d399">Loop</b> — retries if score &lt; 70<br>
✅ <b style="color:#f59e0b">Finalizer</b> — outputs report
</div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<p style="font-size:0.75rem;color:#3d3d6e;">Max iterations: 3 · Threshold: 70</p>', unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">Competitor Intel</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Agentic AI Research System · CS 301</div>', unsafe_allow_html=True)

# ── Inputs ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    company = st.text_input("Target Company", value="Stripe", placeholder="e.g. Stripe, Notion, Figma")
with col2:
    industry = st.text_input("Industry", value="fintech", placeholder="e.g. fintech, productivity")
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶ Analyze", use_container_width=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Run ──────────────────────────────────────────────────────────────────────
if run_btn:
    if not company.strip() or not industry.strip():
        st.error("Please enter both a company name and industry.")
        st.stop()

    status_box = st.empty()
    progress_bar = st.progress(0)

    def update_status(msg, pct):
        status_box.markdown(f'<div style="padding:0.6rem 0;font-size:0.875rem;color:#9090b0;"><span class="step-dot"></span>{msg}</div>', unsafe_allow_html=True)
        progress_bar.progress(pct)

    update_status("🔍 Researcher agent scanning competitors...", 0.15)

    with st.spinner("Running agentic pipeline..."):
        try:
            orchestrator = Orchestrator()
            original_run = orchestrator.run

            def instrumented_run(company, industry):
                update_status("📊 Evaluator scoring data quality...", 0.45)
                res = original_run(company=company, industry=industry)
                update_status("🔁 Checking if retry needed...", 0.75)
                time.sleep(0.3)
                update_status("✅ Compiling final report...", 0.95)
                time.sleep(0.3)
                return res

            orchestrator.run = instrumented_run
            result = orchestrator.run(company=company, industry=industry)

        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()

    status_box.empty()
    progress_bar.empty()

    # ── Extract ───────────────────────────────────────────────────────────────
    evaluation  = result.get("evaluation", {})
    score       = evaluation.get("score", 0)
    passed      = evaluation.get("passed", False)
    gaps        = evaluation.get("gaps", [])
    queries     = evaluation.get("suggested_queries", [])
    competitors = result.get("research_results", [])
    iterations  = result.get("iteration", 1)

    # ── Score Cards ───────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">📈 Results Overview</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        color = "#6ee7b7" if score >= 70 else "#fca5a5"
        st.markdown(f'<div class="score-card"><div class="score-value" style="color:{color}">{score}</div><div class="score-label">Quality Score</div></div>', unsafe_allow_html=True)
    with m2:
        badge = '<span class="badge-pass">✓ PASSED</span>' if passed else '<span class="badge-fail">✗ FAILED</span>'
        st.markdown(f'<div class="score-card"><div style="padding-top:0.5rem">{badge}</div><div class="score-label" style="margin-top:0.8rem">Evaluation</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="score-card"><div class="score-value" style="color:#60a5fa">{len(competitors)}</div><div class="score-label">Competitors Found</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="score-card"><div class="score-value" style="color:#f59e0b">{iterations}</div><div class="score-label">Iterations Run</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🏢 Competitors", "⚠️ Gaps & Queries", "🔎 Raw State"])

    with tab1:
        st.markdown('<p class="section-title">Competitor Intelligence</p>', unsafe_allow_html=True)
        if competitors:
            for comp in competitors:
                name     = comp.get("company_name", "Unknown")
                snippets = comp.get("raw_snippets", [])
                sources  = comp.get("sources", [])
                snippets_html = "".join(f'<div class="snippet-item">• {s}</div>' for s in snippets)
                sources_html  = ""
                if sources:
                    links = " · ".join(f'<a href="{s}" target="_blank" style="color:#60a5fa;font-size:0.75rem;">{s[:50]}</a>' for s in sources)
                    sources_html = f'<div style="margin-top:0.6rem;font-size:0.75rem;color:#4b4b6b;">🔗 {links}</div>'
                st.markdown(f'<div class="competitor-card"><div class="competitor-name">🏢 {name}</div>{snippets_html}{sources_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#6b6b8a;font-style:italic;">No competitor data returned.</p>', unsafe_allow_html=True)

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<p class="section-title">⚠️ Data Gaps</p>', unsafe_allow_html=True)
            if gaps:
                for g in gaps:
                    st.markdown(f'<div class="gap-item">⚠ {g}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#6b6b8a;font-style:italic;">No gaps — data looks complete!</p>', unsafe_allow_html=True)
        with col_b:
            st.markdown('<p class="section-title">💡 Suggested Queries</p>', unsafe_allow_html=True)
            if queries:
                for q in queries:
                    st.markdown(f'<div class="query-item">→ {q}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#6b6b8a;font-style:italic;">No additional queries suggested.</p>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<p class="section-title">🔎 Full Agent State</p>', unsafe_allow_html=True)
        st.json(result)

    if not passed and iterations >= 3:
        st.warning("⚠️ Max iterations reached. Report generated with low confidence.")

else:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;color:#3d3d6e;">
        <div style="font-size:3rem;margin-bottom:1rem;">🔍</div>
        <div style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:700;color:#4b4b7b;margin-bottom:0.5rem;">
            Enter a company and industry to begin
        </div>
        <div style="font-size:0.85rem;color:#3d3d6e;">
            The agentic pipeline will research, evaluate, and refine results automatically
        </div>
    </div>
    """, unsafe_allow_html=True)