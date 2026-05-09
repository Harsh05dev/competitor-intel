"""
Competitor Intelligence Dashboard — ui/app.py
Clean rewrite: sidebar always accessible, native selectbox, demo/live toggle, theme toggle.
"""

import streamlit as st
import streamlit.components.v1 as components
import sys, os, time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(
    page_title="Competitor Intel",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session defaults ───────────────────────────────────────────────────────────
for k, v in [("theme", "dark"), ("mode", "demo")]:
    if k not in st.session_state:
        st.session_state[k] = v

# First load of a session: expand sidebar (Streamlit may restore "collapsed" from the browser).
if not st.session_state.get("_sidebar_session_opened"):
    st.session_state._sidebar_session_opened = True
    components.html(
        """
        <script>
        (function () {
            try {
                function tryExpand() {
                    var doc = window.parent.document;
                    var btn = doc.querySelector('button[data-testid="collapsedControl"]');
                    if (btn) {
                        var r = btn.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0) { btn.click(); }
                    }
                }
                tryExpand();
                setTimeout(tryExpand, 250);
            } catch (e) {}
        })();
        </script>
        """,
        height=0,
        width=0,
    )

DARK = st.session_state.theme == "dark"
DEMO = st.session_state.mode  == "demo"

# ── Colors ─────────────────────────────────────────────────────────────────────
if DARK:
    BG, BG2, BG3     = "#05050f", "#080810", "#0d0d22"
    BORDER           = "#1a1a35"
    TEXT, TEXT2, TEXT3, TEXT4 = "#ffffff", "#9999bb", "#666688", "#333355"
    ACCENT           = "#00d4aa"
    RED, BLUE, AMBER = "#ff6b6b", "#60a5fa", "#fbbf24"
else:
    BG, BG2, BG3     = "#f0f0f7", "#ffffff", "#e8e8f0"
    BORDER           = "#ccccdd"
    TEXT, TEXT2, TEXT3, TEXT4 = "#0a0a1a", "#444466", "#888899", "#bbbbcc"
    ACCENT           = "#007a64"
    RED, BLUE, AMBER = "#cc2222", "#1d4ed8", "#b45309"

ACC_BG  = f"{ACCENT}18"
ACC_BOR = f"{ACCENT}55"
MODE_BADGE_COLOR = ACCENT if DEMO else RED
MODE_BADGE_BG = ACC_BG if DEMO else f"{RED}22"
MODE_BADGE_BORDER = ACC_BOR if DEMO else f"{RED}55"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600;700&display=swap');

/* Header must keep real height — height:0 clips Streamlit's sidebar control */
header[data-testid="stHeader"] {{
    background: transparent !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 999990 !important;
    height: auto !important;
    min-height: 2.75rem !important;
    padding: 0.35rem 0 0 0 !important;
    overflow: visible !important;
}}

/* Collapsed sidebar: fixed chevron so it is never clipped or flush with viewport top */
button[data-testid="collapsedControl"] {{
    position: fixed !important;
    left: 0 !important;
    top: clamp(5rem, 14vh, 7.5rem) !important;
    z-index: 999999 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: {ACC_BG} !important;
    border: 2px solid {ACCENT} !important;
    border-left: none !important;
    border-radius: 0 10px 10px 0 !important;
    color: {ACCENT} !important;
    min-width: 2.5rem !important;
    width: 2.5rem !important;
    min-height: 3.75rem !important;
    height: auto !important;
    margin: 0 !important;
    padding: 0.35rem !important;
    opacity: 1 !important;
    visibility: visible !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5) !important;
}}
button[data-testid="collapsedControl"] svg,
button[data-testid="collapsedControl"] img {{
    width: 1.35rem !important;
    height: 1.35rem !important;
}}

#MainMenu {{ visibility: hidden; }}
footer {{ display: none !important; }}
.stDeployButton {{ display: none !important; }}
.stAppDeployButton {{ display: none !important; }}

* {{ box-sizing: border-box; }}
html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background: {BG};
    color: {TEXT};
}}
.stApp {{ background: {BG}; }}
.block-container {{
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1200px !important;
}}

section[data-testid="stSidebar"] {{
    background: {BG2} !important;
    border-right: 1px solid {BORDER} !important;
}}
section[data-testid="stSidebar"] > div {{
    padding: 1.5rem 1.1rem !important;
}}

.stButton > button {{
    background: {BG3} !important;
    color: {TEXT2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 7px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    padding: 0.5rem !important;
    width: 100% !important;
    transition: all 0.15s !important;
}}
.stButton > button:hover {{
    border-color: {ACCENT} !important;
    color: {ACCENT} !important;
}}

.stTextInput label, .stSelectbox label {{
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    color: {TEXT3} !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
}}
.stTextInput > div > div > input {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    color: {TEXT} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1rem !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT}18 !important;
}}
.stTextInput > div > div > input::placeholder {{ color: {TEXT4} !important; }}

div[data-baseweb="select"] > div {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    color: {TEXT} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    min-height: 2.8rem !important;
}}
div[data-baseweb="select"] > div:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT}18 !important;
}}
div[data-baseweb="select"] svg {{ fill: {ACCENT} !important; }}
div[data-baseweb="popover"] > div > ul {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    padding: 4px !important;
}}
li[role="option"] {{
    background: transparent !important;
    color: {TEXT2} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.8rem !important;
}}
li[role="option"]:hover, li[aria-selected="true"] {{
    background: {ACCENT}18 !important;
    color: {ACCENT} !important;
}}

.run-btn > div > button {{
    background: {ACCENT}22 !important;
    color: {ACCENT} !important;
    border: 1px solid {ACCENT}60 !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
}}
.run-btn > div > button:hover {{
    background: {ACCENT}35 !important;
    border-color: {ACCENT} !important;
}}

.metrics-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: {BORDER};
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid {BORDER};
    margin: 1.5rem 0;
}}
.metric-cell {{ background: {BG2}; padding: 1.3rem 1.5rem; }}
.m-label {{ font-family: 'Space Mono', monospace; font-size: 0.6rem; color: {TEXT3}; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 0.5rem; }}
.m-value {{ font-family: 'Space Mono', monospace; font-size: 1.9rem; font-weight: 700; line-height: 1; color: {TEXT}; }}
.m-value.teal  {{ color: {ACCENT}; }}
.m-value.red   {{ color: {RED}; }}
.m-value.blue  {{ color: {BLUE}; }}
.m-value.amber {{ color: {AMBER}; }}
.m-sub {{ font-size: 0.67rem; color: {TEXT3}; margin-top: 0.3rem; font-family: 'Space Mono', monospace; }}

.sec-head {{
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: {TEXT3};
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 1.5rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}}
.sec-head::after {{ content: ''; flex: 1; height: 1px; background: {BORDER}; }}

.comp-card {{
    background: {BG2};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.15s;
}}
.comp-card:hover {{ border-color: {ACCENT}40; }}
.comp-name {{ font-size: 0.92rem; font-weight: 600; color: {TEXT}; margin-bottom: 0.7rem; display: flex; align-items: center; gap: 0.5rem; }}
.c-dot {{ width: 5px; height: 5px; border-radius: 50%; background: {ACCENT}; flex-shrink: 0; }}
.snippet {{ font-size: 0.82rem; color: {TEXT2}; padding: 0.22rem 0 0.22rem 0.75rem; border-left: 1px solid {BORDER}; margin-bottom: 0.22rem; line-height: 1.5; }}
.src {{ font-family: 'Space Mono', monospace; font-size: 0.6rem; color: {ACCENT}55; margin-top: 0.4rem; }}

.gap-row {{ padding: 0.6rem 0.9rem; background: {RED}08; border: 1px solid {RED}20; border-left: 2px solid {RED}60; border-radius: 0 7px 7px 0; margin-bottom: 0.3rem; font-size: 0.82rem; color: {RED}; line-height: 1.45; }}
.q-row {{ padding: 0.6rem 0.9rem; background: {ACC_BG}; border: 1px solid {ACC_BOR}; border-left: 2px solid {ACCENT}60; border-radius: 0 7px 7px 0; margin-bottom: 0.3rem; font-size: 0.82rem; color: {ACCENT}; font-family: 'Space Mono', monospace; line-height: 1.45; }}

.prog-row {{ display: flex; align-items: center; gap: 0.6rem; padding: 0.4rem 0; font-size: 0.82rem; color: {TEXT2}; font-family: 'Space Mono', monospace; }}
.prog-dot {{ width: 5px; height: 5px; border-radius: 50%; background: {ACCENT}; flex-shrink: 0; animation: blink 1s infinite; }}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}
.stProgress > div > div {{ background: {ACCENT} !important; }}

.stTabs [data-baseweb="tab-list"] {{ background: transparent !important; border-bottom: 1px solid {BORDER} !important; gap: 0 !important; padding: 0 !important; }}
.stTabs [data-baseweb="tab"] {{ font-family: 'Space Mono', monospace !important; font-size: 0.67rem !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: {TEXT3} !important; padding: 0.7rem 1.2rem !important; border-radius: 0 !important; border-bottom: 2px solid transparent !important; background: transparent !important; }}
.stTabs [aria-selected="true"] {{ color: {ACCENT} !important; border-bottom: 2px solid {ACCENT} !important; }}

::-webkit-scrollbar {{ width: 3px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 2px; }}
</style>
""", unsafe_allow_html=True)

# ── Demo data ──────────────────────────────────────────────────────────────────
DEMO_RESULT = {
    "evaluation": {
        "score": 78, "passed": True,
        "gaps": ["Missing hiring signals for Square", "Missing funding data for Braintree"],
        "suggested_queries": ["Square open positions 2025", "Braintree funding valuation 2024"],
    },
    "research_results": [
        {"company_name": "Square",       "raw_snippets": ["2.6% + 10¢ in-person, 2.9% + 30¢ online", "Strong POS hardware — Square Terminal and Register", "150M+ sellers globally", "Block Inc $5.5B gross profit 2024"], "sources": ["squareup.com"]},
        {"company_name": "Adyen",        "raw_snippets": ["Interchange++ pricing — best for high volume", "Processes Netflix, Spotify, Uber, Microsoft", "€1.79B net revenue H1 2024, +23% YoY", "Unified online + mobile + in-store platform"], "sources": ["adyen.com"]},
        {"company_name": "Braintree",    "raw_snippets": ["2.59% + 49¢ per transaction", "130+ currencies, 45+ countries", "PayPal subsidiary — acquired 2013 for $800M", "Venmo integration — 90M+ users"], "sources": ["braintreepayments.com"]},
        {"company_name": "Checkout.com", "raw_snippets": ["$1B Series D at $40B valuation (2022)", "Interchange+ with custom enterprise rates", "Profitable since 2023, $165B+ processed annually", "Strong EU, MENA, APAC coverage"], "sources": ["checkout.com"]},
    ],
    "analysis": {
        "swot": {
            "strengths":     ["Best-in-class developer API — industry-leading docs and SDKs", "Processes $1T+ annually — proven at scale", "Full infrastructure: Billing, Radar, Treasury, Issuing, Atlas", "38% YoY growth — 25K+ new businesses daily"],
            "weaknesses":    ["2.9% + 30¢ flat rate loses to Interchange++ at high volume", "Customer support historically weak", "Limited POS hardware vs Square's ecosystem", "Complex product suite overwhelms non-technical SMBs"],
            "opportunities": ["SMB-friendly onboarding for non-technical founders", "AI-powered fraud detection as differentiator", "Embedded finance / banking-as-a-service expansion", "Stablecoin/crypto payment rails for enterprise"],
            "threats":       ["Square dominates brick-and-mortar with POS hardware", "Adyen's Interchange++ increasingly attractive at enterprise scale", "Checkout.com's $40B valuation signals serious competition", "Apple/Google Pay reducing card transaction volume"],
        },
        "comparison_matrix": [
            {"company_name": "Square",       "pricing_tier": "Flat rate",     "primary_strength": "POS hardware ecosystem",          "primary_weakness": "Higher online rates",        "target_market": "SMB in-person",    "threat_level": "High"},
            {"company_name": "Adyen",        "pricing_tier": "Interchange++", "primary_strength": "Enterprise pricing at volume",    "primary_weakness": "Complex onboarding",         "target_market": "Large enterprise", "threat_level": "Medium"},
            {"company_name": "Braintree",    "pricing_tier": "Flat rate",     "primary_strength": "Venmo/PayPal network access",     "primary_weakness": "Less developer-friendly",    "target_market": "Mid-market online","threat_level": "Low"},
            {"company_name": "Checkout.com", "pricing_tier": "Interchange+",  "primary_strength": "Global coverage + profitability", "primary_weakness": "Less US brand recognition", "target_market": "Enterprise global","threat_level": "Medium"},
        ],
        "opportunity_gaps": ["No competitor offers truly non-technical SMB onboarding — Stripe could own this", "Embedded finance underdeveloped across all major competitors"],
    },
    "iteration": 2, "status": "complete",
    "logs": [
        "[Iter 0] Researcher: found 4 competitors",
        "[Iter 0] Categorizer: structured 4 competitors",
        "[Iter 0] Analyst: generated SWOT with 14 points",
        "[Iter 0] Evaluator: score=61/100 FAILED ✗",
        "[Iter 1] Researcher: targeted — 2 gaps filled",
        "[Iter 1] Categorizer: merged 4 competitors",
        "[Iter 1] Analyst: generated SWOT with 16 points",
        "[Iter 1] Evaluator: score=78/100 PASSED ✓",
        "[Iter 2] Report formatted (confidence=HIGH)",
    ],
}

COMPANY_OPTIONS = [
    "⚡ Stripe / fintech  ← demo",
    "Notion / productivity",
    "Figma / design tools",
    "Shopify / e-commerce",
    "Custom (type below)",
]
COMPANY_MAP = {
    "⚡ Stripe / fintech  ← demo": ("Stripe", "fintech"),
    "Notion / productivity":        ("Notion", "productivity"),
    "Figma / design tools":         ("Figma", "design tools"),
    "Shopify / e-commerce":         ("Shopify", "e-commerce"),
    "Custom (type below)":          (None, None),
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.68rem;color:{ACCENT};letter-spacing:0.22em;text-transform:uppercase;padding-bottom:1.1rem;border-bottom:1px solid {BORDER};margin-bottom:1.3rem;">⚡ Competitor Intel</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:0.6rem;color:{TEXT4};margin:-0.6rem 0 1rem 0;line-height:1.4;">Opens automatically on each visit. If you collapse the sidebar, use the <span style="color:{ACCENT};font-weight:600;">teal «</span> tab on the left — it stays fixed and fully visible.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.6rem;color:{TEXT3};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.5rem;">Mode</div>', unsafe_allow_html=True)
    mc1, mc2 = st.columns(2)
    with mc1:
        if st.button("⚡ DEMO", key="btn_demo"):
            st.session_state.mode = "demo"; st.rerun()
    with mc2:
        if st.button("🔴 LIVE", key="btn_live"):
            st.session_state.mode = "live"; st.rerun()

    mc = ACCENT if DEMO else RED
    mt = "● DEMO — no key needed" if DEMO else "● LIVE — key required"
    st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.58rem;color:{mc};text-align:center;margin:0.3rem 0 1rem 0;">{mt}</div>', unsafe_allow_html=True)

    if not DEMO:
        st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.6rem;color:{TEXT3};letter-spacing:0.13em;text-transform:uppercase;margin-bottom:0.4rem;">Gemini API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input("key", type="password", placeholder="paste key here", label_visibility="collapsed")
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.58rem;color:{ACCENT};margin-top:0.2rem;">✓ key loaded</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.58rem;color:{AMBER};margin-top:0.2rem;">⚠ paste key to run</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.56rem;color:{TEXT3};margin-top:0.2rem;">free key → ai.google.dev</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.6rem;color:{TEXT3};letter-spacing:0.13em;text-transform:uppercase;margin-bottom:0.5rem;">Pipeline</div>', unsafe_allow_html=True)
    for icon, name, tag in [("🔍","Researcher","web search"),("🗂","Categorizer","structure"),("📊","Analyst","SWOT"),("✅","Evaluator","quality gate"),("🔁","Loop","score < 70"),("📄","Report","final")]:
        st.markdown(f'<div style="display:flex;align-items:center;justify-content:space-between;padding:0.38rem 0.65rem;border-radius:6px;margin-bottom:0.2rem;background:{BG3};border:1px solid {BORDER};"><div style="display:flex;align-items:center;gap:0.4rem;"><span style="font-size:0.78rem;">{icon}</span><span style="font-size:0.78rem;color:{TEXT2};font-weight:500;">{name}</span></div><span style="font-family:Space Mono,monospace;font-size:0.56rem;color:{TEXT3};background:{BORDER};padding:0.1rem 0.38rem;border-radius:4px;">{tag}</span></div>', unsafe_allow_html=True)

    st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.6rem;color:{TEXT3};letter-spacing:0.13em;text-transform:uppercase;margin:0.9rem 0 0.5rem 0;">Config</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.67rem;color:{TEXT2};line-height:2;background:{BG3};border:1px solid {BORDER};border-radius:6px;padding:0.7rem 0.85rem;">THRESHOLD = 70<br>MAX_ITER &nbsp;= 3<br>AGENTS &nbsp;&nbsp;&nbsp;= 4<br>FRAMEWORK = LangGraph</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.6rem;color:{TEXT3};letter-spacing:0.13em;text-transform:uppercase;margin:0.9rem 0 0.5rem 0;">Theme</div>', unsafe_allow_html=True)
    if st.button("☀ Light" if DARK else "☾ Dark", key="theme_btn"):
        st.session_state.theme = "light" if DARK else "dark"; st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:1rem;padding:1.1rem 0 1.1rem 0;border-bottom:1px solid {BORDER};margin-bottom:1.4rem;flex-wrap:wrap;">
    <div style="font-family:Space Mono,monospace;font-size:1.2rem;font-weight:700;color:{TEXT};">Competitor Intel</div>
    <div style="font-family:Space Mono,monospace;font-size:0.58rem;color:{ACCENT};background:{ACC_BG};border:1px solid {ACC_BOR};border-radius:999px;padding:0.18rem 0.7rem;letter-spacing:0.07em;">AGENTIC AI · CS 301</div>
    <div style="font-size:0.76rem;color:{TEXT3};font-style:italic;">"Know your market before your market knows you."</div>
    <div style="margin-left:auto;font-family:Space Mono,monospace;font-size:0.58rem;color:{MODE_BADGE_COLOR};background:{MODE_BADGE_BG};border:1px solid {MODE_BADGE_BORDER};border-radius:6px;padding:0.22rem 0.65rem;">● {"DEMO" if DEMO else "LIVE"} MODE</div>
</div>
""", unsafe_allow_html=True)

if DEMO:
    st.markdown(f'<div style="background:{ACC_BG};border:1px solid {ACC_BOR};border-radius:8px;padding:0.6rem 0.9rem;font-family:Space Mono,monospace;font-size:0.68rem;color:{ACCENT};letter-spacing:0.04em;margin-bottom:1.1rem;">⚡ DEMO MODE — pre-computed Stripe vs fintech · Switch to LIVE in sidebar for real analysis</div>', unsafe_allow_html=True)

# ── Inputs ─────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([5, 3, 2])
with col1:
    selected = st.selectbox("TARGET_COMPANY", COMPANY_OPTIONS, index=0)
    resolved_co, resolved_ind = COMPANY_MAP[selected]
with col2:
    if resolved_ind:
        st.text_input("INDUSTRY", value=resolved_ind, disabled=True)
        industry_final = resolved_ind
    else:
        industry_final = st.text_input("INDUSTRY", placeholder="e.g. fintech, design tools")
with col3:
    st.markdown("<div style='height:1.82rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("▶ RUN", use_container_width=True, key="run_main")

company_final = resolved_co
if not resolved_co:
    company_final = st.text_input("CUSTOM COMPANY NAME", placeholder="e.g. Linear, Loom, Webflow")

st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

# ── Render functions ────────────────────────────────────────────────────────────
def render_metrics(score, passed, competitors, iterations):
    sc = "teal" if score >= 65 else "red"
    pc = "teal" if passed else "red"
    pv = "PASS" if passed else "FAIL"
    st.markdown(f'<div class="metrics-row"><div class="metric-cell"><div class="m-label">Quality Score</div><div class="m-value {sc}">{score}</div><div class="m-sub">/ 100 · threshold 65</div></div><div class="metric-cell"><div class="m-label">Evaluation</div><div class="m-value {pc}">{pv}</div><div class="m-sub">{"criteria met" if passed else "needs work"}</div></div><div class="metric-cell"><div class="m-label">Competitors</div><div class="m-value blue">{len(competitors)}</div><div class="m-sub">companies analyzed</div></div><div class="metric-cell"><div class="m-label">Iterations</div><div class="m-value amber">{iterations}</div><div class="m-sub">of 3 max</div></div></div>', unsafe_allow_html=True)

def render_competitors(competitors):
    st.markdown('<div class="sec-head">Competitor Data</div>', unsafe_allow_html=True)
    for c in competitors:
        sh = "".join(f'<div class="snippet">· {s}</div>' for s in c.get("raw_snippets", []))
        sr = "".join(f'<div class="src">↗ {s}</div>' for s in c.get("sources", [])[:2])
        st.markdown(f'<div class="comp-card"><div class="comp-name"><span class="c-dot"></span>{c.get("company_name","?")}</div>{sh}{sr}</div>', unsafe_allow_html=True)

def render_swot(analysis):
    swot = (analysis or {}).get("swot", {})
    if not swot: return
    st.markdown('<div class="sec-head">SWOT Analysis</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, (label, key, color) in enumerate([("Strengths 💪","strengths",ACCENT),("Weaknesses ⚠️","weaknesses",RED),("Opportunities 🚀","opportunities",BLUE),("Threats 🔴","threats",AMBER)]):
        rows = "".join(f'<div style="font-size:0.8rem;color:{TEXT2};padding:0.25rem 0 0.25rem 0.7rem;border-left:2px solid {color}40;margin-bottom:0.25rem;line-height:1.45;">· {item}</div>' for item in swot.get(key, []))
        html = f'<div style="background:{BG2};border:1px solid {BORDER};border-radius:8px;padding:0.85rem 1rem;margin-bottom:0.65rem;"><div style="font-family:Space Mono,monospace;font-size:0.6rem;color:{color};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.55rem;">{label}</div>{rows}</div>'
        with (c1 if i % 2 == 0 else c2):
            st.markdown(html, unsafe_allow_html=True)

def render_comparison(analysis):
    matrix = (analysis or {}).get("comparison_matrix", [])
    if not matrix: return
    st.markdown('<div class="sec-head">Comparison Matrix</div>', unsafe_allow_html=True)
    for row in matrix:
        t = row.get("threat_level", "Low")
        tc = RED if t == "High" else AMBER if t == "Medium" else TEXT3
        st.markdown(f'<div class="comp-card"><div class="comp-name"><span class="c-dot"></span>{row.get("company_name","?")} <span style="font-family:Space Mono,monospace;font-size:0.57rem;color:{tc};margin-left:auto;">▲ {t.upper()} THREAT</span></div><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;font-size:0.8rem;color:{TEXT2};"><div><span style="color:{TEXT3};font-size:0.58rem;font-family:Space Mono,monospace;display:block;margin-bottom:0.12rem;">PRICING</span>{row.get("pricing_tier","?")}</div><div><span style="color:{TEXT3};font-size:0.58rem;font-family:Space Mono,monospace;display:block;margin-bottom:0.12rem;">STRENGTH</span>{row.get("primary_strength","?")}</div><div><span style="color:{TEXT3};font-size:0.58rem;font-family:Space Mono,monospace;display:block;margin-bottom:0.12rem;">MARKET</span>{row.get("target_market","?")}</div></div></div>', unsafe_allow_html=True)

def render_gaps(gaps, queries):
    gc, qc = st.columns(2)
    with gc:
        st.markdown('<div class="sec-head">Data Gaps</div>', unsafe_allow_html=True)
        for g in (gaps or []): st.markdown(f'<div class="gap-row">⚠ {g}</div>', unsafe_allow_html=True)
        if not gaps: st.markdown(f'<div style="color:{TEXT3};font-size:0.82rem;">No gaps detected.</div>', unsafe_allow_html=True)
    with qc:
        st.markdown('<div class="sec-head">Suggested Queries</div>', unsafe_allow_html=True)
        for q in (queries or []): st.markdown(f'<div class="q-row">→ {q}</div>', unsafe_allow_html=True)
        if not queries: st.markdown(f'<div style="color:{TEXT3};font-size:0.82rem;">No queries suggested.</div>', unsafe_allow_html=True)

def run_demo_mode(company, industry):
    slot = st.empty(); bar = st.progress(0)
    for msg, pct, delay in [
        (f"researcher → scanning {industry} competitors...", 0.15, 0.9),
        ("categorizer → structuring raw data...",            0.32, 0.7),
        ("analyst → generating SWOT analysis...",           0.50, 0.8),
        ("evaluator → scoring... [iter 1: 61/100 ✗]",      0.65, 0.6),
        ("researcher → filling 2 gaps (targeted)...",       0.78, 0.9),
        ("evaluator → rescoring... [iter 2: 78/100 ✓]",    0.90, 0.6),
        ("format → compiling final report...",               1.00, 0.4),
    ]:
        slot.markdown(f'<div class="prog-row"><div class="prog-dot"></div>{msg}</div>', unsafe_allow_html=True)
        bar.progress(pct); time.sleep(delay)
    slot.empty(); bar.empty()
    return {**DEMO_RESULT, "target_company": company, "industry": industry}

def run_live_mode(company, industry):
    from main import Orchestrator
    slot = st.empty(); bar = st.progress(0)
    slot.markdown(f'<div class="prog-row"><div class="prog-dot"></div>researcher → scanning competitors...</div>', unsafe_allow_html=True)
    bar.progress(0.1)
    with st.spinner(""):
        result = Orchestrator().run(company=company, industry=industry)
    slot.empty(); bar.empty()
    return result

# ── Run ─────────────────────────────────────────────────────────────────────────
if run_btn:
    if not company_final or not company_final.strip():
        st.error("Please select or enter a company name."); st.stop()
    if not industry_final or not industry_final.strip():
        st.error("Industry is required."); st.stop()
    if DEMO:
        result = run_demo_mode(company_final, industry_final)
    else:
        if not os.environ.get("GEMINI_API_KEY", ""):
            st.error("Paste your Gemini API key in the sidebar first."); st.stop()
        try:
            result = run_live_mode(company_final, industry_final)
        except Exception as e:
            st.error(f"Pipeline error: {e}"); st.stop()

    ev = result.get("evaluation", {})
    render_metrics(ev.get("score",0), ev.get("passed",False), result.get("research_results",[]), result.get("iteration",1))

    t1, t2, t3, t4 = st.tabs(["Competitors", "SWOT & Comparison", "Gaps & Queries", "Raw State"])
    with t1: render_competitors(result.get("research_results", []))
    with t2: render_swot(result.get("analysis",{})); render_comparison(result.get("analysis",{}))
    with t3: render_gaps(ev.get("gaps",[]), ev.get("suggested_queries",[]))
    with t4:
        st.markdown('<div class="sec-head">Agent Execution Logs</div>', unsafe_allow_html=True)
        for log in result.get("logs", []):
            color = ACCENT if "PASSED" in log else RED if "FAILED" in log else TEXT3
            st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.68rem;color:{color};padding:0.17rem 0;border-bottom:1px solid {BORDER}33;">{log}</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-head" style="margin-top:1rem;">Full JSON State</div>', unsafe_allow_html=True)
        st.json(result)

    if not ev.get("passed") and result.get("iteration",1) >= 3:
        st.warning("Max iterations reached — report generated with best available data.")
else:
    st.markdown(f'<div style="margin-top:5rem;text-align:center;padding:2rem;"><div style="font-size:2.2rem;margin-bottom:1rem;opacity:0.1;">⚡</div><div style="font-family:Space Mono,monospace;font-size:0.68rem;color:{TEXT4};letter-spacing:0.25em;text-transform:uppercase;margin-bottom:0.5rem;">System Ready</div><div style="font-family:Space Mono,monospace;font-size:0.76rem;color:{TEXT3};margin-bottom:0.35rem;">Select a company → click ▶ RUN</div><div style="font-size:0.72rem;color:{TEXT4};">{"Demo mode active — no API key needed" if DEMO else "Live mode — paste your Gemini key in the sidebar"}</div></div>', unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown(f'<div style="margin-top:3rem;padding:1.2rem 0 0.5rem 0;border-top:1px solid {BORDER};display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;"><div><div style="font-family:Space Mono,monospace;font-size:0.6rem;color:{TEXT3};letter-spacing:0.07em;">⚡ COMPETITOR-INTEL · AGENTIC AI SYSTEM · CS 301 · NJIT · 2025</div><div style="font-family:Space Mono,monospace;font-size:0.56rem;color:{TEXT4};margin-top:0.22rem;">Powered by LangGraph + Gemini 2.5 · 4-agent pipeline with iterative refinement</div></div><div style="text-align:right;"><div style="font-size:0.7rem;color:{TEXT3};">Built by</div><div style="font-family:Space Mono,monospace;font-size:0.62rem;color:{ACCENT};letter-spacing:0.05em;">HARSH · RAYANSH · SHIPPY</div></div></div>', unsafe_allow_html=True)
