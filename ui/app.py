"""
Competitor Intelligence Dashboard — Streamlit UI (ui/app.py)

Features:
- Demo / Live mode toggle
- Light / Dark theme toggle  
- Custom dropdown for company selection (with demo hint)
- Sidebar open/close fix via session state
- Updated header with tagline
- Footer with team credits
- Lazy API key handling (no key needed for demo mode)
"""

import streamlit as st
import sys
import os
import time
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(
    page_title="Competitor Intel",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session state defaults ─────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "mode" not in st.session_state:
    st.session_state.mode = "demo"
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True
if "selected_company" not in st.session_state:
    st.session_state.selected_company = "Stripe (fintech) ← try demo"
if "custom_company" not in st.session_state:
    st.session_state.custom_company = ""
if "custom_industry" not in st.session_state:
    st.session_state.custom_industry = ""

IS_DARK  = st.session_state.theme == "dark"
IS_DEMO  = st.session_state.mode  == "demo"

# ── Theme variables ────────────────────────────────────────────────────────────
if IS_DARK:
    BG       = "#05050f"
    BG2      = "#080810"
    BG3      = "#0d0d22"
    BORDER   = "#1a1a35"
    TEXT     = "#ffffff"
    TEXT2    = "#9999bb"
    TEXT3    = "#666688"
    TEXT4    = "#444466"
    ACCENT   = "#00d4aa"
    ACC_BG   = "#00d4aa18"
    ACC_BOR  = "#00d4aa50"
    RED      = "#ff6b6b"
    BLUE     = "#60a5fa"
    AMBER    = "#fbbf24"
    SCROLL   = "#1a1a35"
else:
    BG       = "#f4f4f8"
    BG2      = "#ffffff"
    BG3      = "#eeeef5"
    BORDER   = "#d0d0e0"
    TEXT     = "#0a0a1a"
    TEXT2    = "#444466"
    TEXT3    = "#888899"
    TEXT4    = "#aaaacc"
    ACCENT   = "#007a64"
    ACC_BG   = "#007a6415"
    ACC_BOR  = "#007a6450"
    RED      = "#cc3333"
    BLUE     = "#2563eb"
    AMBER    = "#d97706"
    SCROLL   = "#d0d0e0"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

#MainMenu {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ display: none !important; }}
footer {{ display: none !important; }}
.stDeployButton {{ display: none !important; }}
div[data-testid="stToolbar"] {{ display: none !important; }}
.stAppDeployButton {{ display: none !important; }}

* {{ box-sizing: border-box; }}

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background: {BG};
    color: {TEXT};
}}
.stApp {{ background: {BG}; }}

.block-container {{
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
    max-width: 1240px;
}}

section[data-testid="stSidebar"] {{
    background: {BG2} !important;
    border-right: 1px solid {BORDER} !important;
    min-width: 260px !important;
    max-width: 260px !important;
}}
section[data-testid="stSidebar"] > div {{
    padding: 1.5rem 1.2rem !important;
}}

/* ── Sidebar toggle button ── */
.sb-toggle {{
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 9999;
    background: {BG2};
    border: 1px solid {BORDER};
    color: {ACCENT};
    border-radius: 8px;
    padding: 0.4rem 0.7rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    cursor: pointer;
    letter-spacing: 0.05em;
}}

/* ── Logo ── */
.logo-mark {{
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: {ACCENT};
    letter-spacing: 0.25em;
    text-transform: uppercase;
    padding-bottom: 1.2rem;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

/* ── Mode toggle ── */
.mode-toggle {{
    display: flex;
    background: {BG3};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 3px;
    margin-bottom: 1.2rem;
    gap: 3px;
}}
.mode-btn {{
    flex: 1;
    text-align: center;
    padding: 0.4rem 0;
    border-radius: 6px;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.15s;
    color: {TEXT3};
    border: none;
    background: transparent;
}}
.mode-btn.active {{
    background: {ACCENT};
    color: #000;
    font-weight: 700;
}}

.sb-label {{
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: {TEXT3};
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin: 1.4rem 0 0.6rem 0;
}}

.pipe-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.45rem 0.75rem;
    border-radius: 6px;
    margin-bottom: 0.25rem;
    background: {BG3};
    border: 1px solid {BORDER};
}}
.pipe-left {{ display: flex; align-items: center; gap: 0.45rem; }}
.pipe-icon {{ font-size: 0.8rem; }}
.pipe-name {{ font-size: 0.82rem; color: {TEXT2}; font-weight: 500; }}
.pipe-tag {{
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: {TEXT3};
    background: {BORDER};
    padding: 0.12rem 0.45rem;
    border-radius: 4px;
}}

.cfg-block {{
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    color: {TEXT2};
    line-height: 2.1;
    background: {BG3};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 0.8rem 0.9rem;
}}

/* ── Inputs ── */
.stTextInput label {{
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    color: {TEXT3} !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.35rem !important;
}}
.stTextInput > div > div > input {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    color: {TEXT} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.15s !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACC_BG} !important;
}}
.stTextInput > div > div > input::placeholder {{ color: {TEXT4} !important; }}

/* ── Buttons ── */
.stButton > button {{
    background: {ACC_BG} !important;
    color: {ACCENT} !important;
    border: 1px solid {ACC_BOR} !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    padding: 0.7rem 1.5rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
}}
.stButton > button:hover {{
    background: {ACCENT}28 !important;
    border-color: {ACCENT}90 !important;
    box-shadow: 0 0 20px {ACCENT}18 !important;
}}

/* ── Header ── */
.page-header {{
    background: {BG2};
    border-bottom: 1px solid {BORDER};
    padding: 1.4rem 2rem;
    margin: 0 -1rem 2rem -1rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
}}
.page-title {{
    font-family: 'Space Mono', monospace;
    font-size: 1.3rem;
    font-weight: 700;
    color: {TEXT};
    letter-spacing: -0.02em;
}}
.page-pill {{
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: {ACCENT};
    background: {ACC_BG};
    border: 1px solid {ACC_BOR};
    border-radius: 999px;
    padding: 0.2rem 0.8rem;
    letter-spacing: 0.08em;
}}
.page-tagline {{
    font-size: 0.8rem;
    color: {TEXT3};
    font-style: italic;
    margin-left: 0.5rem;
}}
.page-right {{
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}}
.theme-btn {{
    background: {BG3};
    border: 1px solid {BORDER};
    color: {TEXT2};
    border-radius: 6px;
    padding: 0.3rem 0.7rem;
    font-size: 0.8rem;
    cursor: pointer;
    font-family: 'Space Mono', monospace;
}}
.header-mode {{
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: {TEXT3};
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.3rem 0.8rem;
    border: 1px solid {BORDER};
    border-radius: 6px;
    background: {BG3};
}}

/* ── Custom dropdown ── */
.dropdown-wrapper {{ position: relative; margin-bottom: 0.5rem; }}
.dropdown-label {{
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: {TEXT3};
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
    display: block;
}}
.dropdown-selected {{
    background: {BG2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    color: {TEXT};
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    padding: 0.7rem 1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: border-color 0.15s;
    user-select: none;
}}
.dropdown-selected:hover {{ border-color: {ACCENT}; }}
.dropdown-arrow {{ color: {TEXT3}; font-size: 0.75rem; transition: transform 0.2s; }}
.dropdown-arrow.open {{ transform: rotate(180deg); }}
.dropdown-menu {{
    position: absolute;
    top: calc(100% + 4px);
    left: 0; right: 0;
    background: {BG2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    z-index: 1000;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}}
.dropdown-item {{
    padding: 0.65rem 1rem;
    font-size: 0.9rem;
    color: {TEXT2};
    cursor: pointer;
    transition: background 0.1s;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid {BORDER};
    font-family: 'DM Sans', sans-serif;
}}
.dropdown-item:last-child {{ border-bottom: none; }}
.dropdown-item:hover {{ background: {BG3}; color: {TEXT}; }}
.dropdown-item.demo-item {{ color: {ACCENT}; }}
.dropdown-item.demo-item:hover {{ background: {ACC_BG}; }}
.demo-badge {{
    font-family: 'Space Mono', monospace;
    font-size: 0.55rem;
    background: {ACC_BG};
    color: {ACCENT};
    border: 1px solid {ACC_BOR};
    border-radius: 4px;
    padding: 0.1rem 0.4rem;
    letter-spacing: 0.05em;
}}

/* ── Metrics ── */
.metrics-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: {BORDER};
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid {BORDER};
    margin-bottom: 2rem;
}}
.metric-cell {{ background: {BG2}; padding: 1.4rem 1.6rem; }}
.m-label {{
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: {TEXT3};
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}}
.m-value {{ font-family: 'Space Mono', monospace; font-size: 2rem; font-weight: 700; line-height: 1; color: {TEXT}; }}
.m-value.teal  {{ color: {ACCENT}; }}
.m-value.red   {{ color: {RED}; }}
.m-value.blue  {{ color: {BLUE}; }}
.m-value.amber {{ color: {AMBER}; }}
.m-sub {{ font-size: 0.7rem; color: {TEXT3}; margin-top: 0.35rem; font-family: 'Space Mono', monospace; }}

/* ── Sections ── */
.sec-head {{
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: {TEXT3};
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 1.8rem 0 0.9rem 0;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}}
.sec-head::after {{ content: ''; flex: 1; height: 1px; background: {BORDER}; }}

/* ── Competitor cards ── */
.comp-card {{
    background: {BG2};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.15s;
}}
.comp-card:hover {{ border-color: {ACCENT}40; }}
.comp-name {{ font-size: 0.95rem; font-weight: 600; color: {TEXT}; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 0.5rem; }}
.c-dot {{ width: 5px; height: 5px; border-radius: 50%; background: {ACCENT}; flex-shrink: 0; }}
.snippet {{ font-size: 0.83rem; color: {TEXT2}; padding: 0.25rem 0 0.25rem 0.8rem; border-left: 1px solid {BORDER}; margin-bottom: 0.25rem; line-height: 1.55; }}
.src {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; color: {ACCENT}60; margin-top: 0.5rem; }}

/* ── Gaps ── */
.gap-row {{
    padding: 0.65rem 1rem;
    background: {RED}08;
    border: 1px solid {RED}20;
    border-left: 2px solid {RED}60;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.35rem;
    font-size: 0.83rem;
    color: {RED};
    line-height: 1.5;
}}
.q-row {{
    padding: 0.65rem 1rem;
    background: {ACC_BG};
    border: 1px solid {ACC_BOR};
    border-left: 2px solid {ACCENT}60;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.35rem;
    font-size: 0.83rem;
    color: {ACCENT};
    font-family: 'Space Mono', monospace;
    line-height: 1.5;
}}

/* ── Progress ── */
.prog-row {{
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.45rem 0;
    font-size: 0.83rem;
    color: {TEXT2};
    font-family: 'Space Mono', monospace;
}}
.prog-dot {{ width: 5px; height: 5px; border-radius: 50%; background: {ACCENT}; flex-shrink: 0; animation: blink 1s infinite; }}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}

/* ── Demo banner ── */
.demo-banner {{
    background: {ACC_BG};
    border: 1px solid {ACC_BOR};
    border-radius: 8px;
    padding: 0.7rem 1rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    color: {ACCENT};
    letter-spacing: 0.05em;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}}

/* ── Footer ── */
.page-footer {{
    margin-top: 3rem;
    padding: 1.5rem 0 1rem 0;
    border-top: 1px solid {BORDER};
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.footer-left {{
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: {TEXT3};
    letter-spacing: 0.08em;
}}
.footer-right {{
    font-size: 0.75rem;
    color: {TEXT3};
}}
.footer-names {{
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: {ACCENT};
    letter-spacing: 0.05em;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{ background: transparent !important; border-bottom: 1px solid {BORDER} !important; gap: 0 !important; padding: 0 !important; }}
.stTabs [data-baseweb="tab"] {{ font-family: 'Space Mono', monospace !important; font-size: 0.7rem !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: {TEXT3} !important; padding: 0.75rem 1.3rem !important; border-radius: 0 !important; border-bottom: 2px solid transparent !important; background: transparent !important; }}
.stTabs [aria-selected="true"] {{ color: {ACCENT} !important; border-bottom: 2px solid {ACCENT} !important; background: transparent !important; }}

.stProgress > div > div {{ background: {ACCENT} !important; }}
::-webkit-scrollbar {{ width: 3px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {SCROLL}; border-radius: 2px; }}

/* ── Live key warning ── */
.key-warning {{
    background: {AMBER}10;
    border: 1px solid {AMBER}40;
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    font-size: 0.75rem;
    color: {AMBER};
    font-family: 'Space Mono', monospace;
    margin-bottom: 0.8rem;
}}
</style>
""", unsafe_allow_html=True)

# ── Demo Data ──────────────────────────────────────────────────────────────────
DEMO_COMPANIES = [
    ("Stripe (fintech)", "Stripe", "fintech", True),      # demo item
    ("Notion (productivity)", "Notion", "productivity", False),
    ("Figma (design tools)", "Figma", "design tools", False),
    ("Shopify (e-commerce)", "Shopify", "e-commerce", False),
    ("Custom...", None, None, False),
]

DEMO_RESULT = {
    "evaluation": {
        "score": 78,
        "passed": True,
        "gaps": [
            "Missing hiring signals for Square",
            "Missing funding data for Braintree",
        ],
        "suggested_queries": [
            "Square open positions 2025 jobs hiring",
            "Braintree funding valuation 2024",
        ],
        "breakdown": {
            "competitor_count": {"score": 9, "notes": "4 competitors found"},
            "pricing_coverage": {"score": 8, "notes": "3 of 4 have detailed pricing"},
            "feature_coverage": {"score": 9, "notes": "All have 3+ features"},
            "funding_data": {"score": 6, "notes": "Missing Braintree funding"},
            "hiring_signals": {"score": 5, "notes": "Missing Square hiring data"},
            "swot_depth": {"score": 9, "notes": "4+ points per quadrant"},
        },
    },
    "research_results": [
        {
            "company_name": "Square",
            "raw_snippets": [
                "Square charges 2.6% + 10¢ per in-person transaction, 2.9% + 30¢ online",
                "Strong POS hardware ecosystem with Square Terminal and Square Register",
                "150M+ sellers across the US, Canada, Australia, Japan, UK",
                "Block Inc (parent) reported $5.5B gross profit in 2024",
            ],
            "sources": ["https://squareup.com/us/en/payments", "https://block.xyz/investor-relations"],
        },
        {
            "company_name": "Adyen",
            "raw_snippets": [
                "Adyen uses Interchange++ pricing model — complex but cost-effective for large volume",
                "Processes payments for Netflix, Spotify, Uber, Microsoft",
                "€1.79B net revenue in H1 2024, 23% YoY growth",
                "Unified commerce platform connecting online, mobile, and in-store",
            ],
            "sources": ["https://www.adyen.com/pricing", "https://ir.adyen.com"],
        },
        {
            "company_name": "Braintree",
            "raw_snippets": [
                "Braintree (PayPal subsidiary) charges 2.59% + 49¢ per transaction",
                "Supports 130+ currencies across 45+ countries",
                "Acquired by PayPal in 2013 for $800M",
                "Venmo integration gives access to 90M+ Venmo users",
            ],
            "sources": ["https://www.braintreepayments.com/features/rate"],
        },
        {
            "company_name": "Checkout.com",
            "raw_snippets": [
                "Raised $1B Series D at $40B valuation in 2022",
                "Interchange+ pricing with custom enterprise rates",
                "Profitable since 2023, processes $165B+ annually",
                "Strong presence in Europe, MENA, and APAC markets",
            ],
            "sources": ["https://www.checkout.com/blog", "https://techcrunch.com/checkout-com"],
        },
    ],
    "categorized_competitors": [],
    "analysis": {
        "swot": {
            "strengths": [
                "Best-in-class developer experience with industry-leading API documentation and SDKs",
                "Processes $1T+ in payments annually — proven scale and reliability",
                "Full financial infrastructure suite (Billing, Radar, Treasury, Issuing, Atlas)",
                "Growing 38% YoY — onboarding 25,000+ new businesses daily in 2025",
            ],
            "weaknesses": [
                "2.9% + 30¢ flat rate is uncompetitive vs Interchange++ for high-volume merchants",
                "Customer support has historically been weak — account stability concerns",
                "Limited in-person/POS hardware compared to Square's ecosystem",
                "Complex product suite can overwhelm non-technical small business owners",
            ],
            "opportunities": [
                "Expand SMB-friendly tooling to capture non-technical founders currently lost to Square",
                "Leverage Stripe Capital data advantage for embedded finance products",
                "AI-powered fraud detection and smart payment routing as a differentiator",
                "Grow stablecoin/crypto rails as enterprise demand for programmable money increases",
            ],
            "threats": [
                "Square's dominant POS hardware ecosystem captures brick-and-mortar merchants",
                "Adyen's Interchange++ pricing increasingly attractive to enterprise at scale",
                "Checkout.com's $40B valuation and profitability signals credible enterprise competition",
                "Platform risk — Apple Pay, Google Pay reducing card transaction volume",
            ],
        },
        "comparison_matrix": [
            {"company_name": "Square", "pricing_tier": "Flat rate", "primary_strength": "POS hardware ecosystem", "primary_weakness": "Higher online rates", "target_market": "SMB in-person sellers", "threat_level": "High"},
            {"company_name": "Adyen", "pricing_tier": "Interchange++", "primary_strength": "Enterprise pricing at volume", "primary_weakness": "Complex onboarding", "target_market": "Large enterprise", "threat_level": "Medium"},
            {"company_name": "Braintree", "pricing_tier": "Flat rate", "primary_strength": "Venmo/PayPal network access", "primary_weakness": "Less developer-friendly", "target_market": "Mid-market online", "threat_level": "Low"},
            {"company_name": "Checkout.com", "pricing_tier": "Interchange+", "primary_strength": "Global coverage + profitability", "primary_weakness": "Less US brand recognition", "target_market": "Enterprise global", "threat_level": "Medium"},
        ],
        "threat_ranking": ["Square", "Adyen", "Checkout.com", "Braintree"],
        "opportunity_gaps": [
            "Gap 1: No competitor offers a truly non-technical SMB onboarding flow — Stripe could own this",
            "Gap 2: Embedded finance (banking-as-a-service) is underdeveloped across all major competitors",
        ],
    },
    "final_output": "demo",
    "iteration": 2,
    "status": "complete",
    "logs": [
        "[Iter 0] Researcher: found 4 competitors",
        "[Iter 0] Categorizer: structured 4 competitors",
        "[Iter 0] Analyst: generated SWOT with 14 points",
        "[Iter 0] Evaluator: score=61/100 FAILED ✗",
        "[Iter 1] Researcher: found 4 competitors (targeted: hiring + funding gaps)",
        "[Iter 1] Categorizer: merged 4 competitors",
        "[Iter 1] Analyst: generated SWOT with 16 points",
        "[Iter 1] Evaluator: score=78/100 PASSED ✓",
        "[Iter 2] Report formatted (confidence=HIGH)",
    ],
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(f'<div class="logo-mark">⚡ competitor-intel</div>', unsafe_allow_html=True)

        # Mode toggle
        col_d, col_l = st.columns(2)
        with col_d:
            if st.button("⚡ DEMO", key="btn_demo", use_container_width=True):
                st.session_state.mode = "demo"
                st.rerun()
        with col_l:
            if st.button("🔴 LIVE", key="btn_live", use_container_width=True):
                st.session_state.mode = "live"
                st.rerun()

        active_mode = st.session_state.mode
        st.markdown(f'<div style="text-align:center;font-family:Space Mono,monospace;font-size:0.62rem;color:{ACCENT if active_mode==\'demo\' else RED};margin:-0.3rem 0 1rem 0;letter-spacing:0.1em;">{"● DEMO MODE — no key needed" if active_mode==\'demo\' else "● LIVE MODE — API key required"}</div>', unsafe_allow_html=True)

        # API key (only show in live mode)
        if active_mode == "live":
            st.markdown('<div class="sb-label">Gemini API Key</div>', unsafe_allow_html=True)
            api_key_input = st.text_input(
                "key", type="password",
                placeholder="paste your Gemini key here",
                label_visibility="collapsed"
            )
            if api_key_input:
                os.environ["GEMINI_API_KEY"] = api_key_input
                st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.62rem;color:{ACCENT};margin-top:0.2rem;">✓ key loaded</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="key-warning">⚠ paste key to run analysis</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.6rem;color:{TEXT3};margin-top:0.3rem;">get free key → ai.google.dev</div>', unsafe_allow_html=True)

        # Pipeline diagram
        st.markdown('<div class="sb-label">Pipeline</div>', unsafe_allow_html=True)
        for icon, name, tag in [
            ("🔍", "Researcher", "web search"),
            ("🗂", "Categorizer", "structure"),
            ("📊", "Analyst", "SWOT"),
            ("✅", "Evaluator", "quality gate"),
            ("🔁", "Loop", "score < 65"),
            ("📄", "Report", "final"),
        ]:
            st.markdown(f'<div class="pipe-item"><div class="pipe-left"><span class="pipe-icon">{icon}</span><span class="pipe-name">{name}</span></div><span class="pipe-tag">{tag}</span></div>', unsafe_allow_html=True)

        # Config
        st.markdown('<div class="sb-label">Config</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cfg-block">MAX_ITER &nbsp;= 3<br>THRESHOLD = 65<br>MODEL &nbsp;&nbsp;&nbsp;&nbsp;= gemini-2.5-flash-lite<br>AGENTS &nbsp;&nbsp;&nbsp;= 4<br>FRAMEWORK = LangGraph</div>', unsafe_allow_html=True)

        # Theme toggle
        st.markdown('<div class="sb-label">Theme</div>', unsafe_allow_html=True)
        theme_label = "☀ Switch to Light" if IS_DARK else "☾ Switch to Dark"
        if st.button(theme_label, key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if IS_DARK else "dark"
            st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
def render_header():
    mode_label = "DEMO MODE" if IS_DEMO else "LIVE MODE"
    mode_color = ACCENT if IS_DEMO else RED
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">Competitor Intel</div>
        <div class="page-pill">AGENTIC AI · CS 301</div>
        <div class="page-tagline">"Know your market before your market knows you."</div>
        <div class="page-right">
            <div class="header-mode" style="color:{mode_color};border-color:{mode_color}40;">● {mode_label}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Custom Dropdown ────────────────────────────────────────────────────────────
def render_company_dropdown():
    if "dropdown_open" not in st.session_state:
        st.session_state.dropdown_open = False

    selected_label = st.session_state.selected_company
    arrow_class = "open" if st.session_state.dropdown_open else ""

    st.markdown('<span class="dropdown-label">TARGET_COMPANY</span>', unsafe_allow_html=True)

    if st.button(
        f"{selected_label}  ▾",
        key="dropdown_trigger",
        use_container_width=True,
    ):
        st.session_state.dropdown_open = not st.session_state.dropdown_open
        st.rerun()

    if st.session_state.dropdown_open:
        for label, company, industry, is_demo in DEMO_COMPANIES:
            badge = ' <span class="demo-badge">DEMO</span>' if is_demo else ""
            item_class = "dropdown-item demo-item" if is_demo else "dropdown-item"
            btn_key = f"dd_{label.replace(' ','_')}"
            if st.button(f"{'⚡ ' if is_demo else ''}{label}", key=btn_key, use_container_width=True):
                st.session_state.selected_company = label
                st.session_state.dropdown_open = False
                if company:
                    st.session_state.custom_company = company
                    st.session_state.custom_industry = industry
                else:
                    st.session_state.custom_company = ""
                    st.session_state.custom_industry = ""
                st.rerun()

    # Return resolved company/industry
    sel = st.session_state.selected_company
    match = next((c for c in DEMO_COMPANIES if c[0] == sel), None)
    if match and match[1]:
        return match[1], match[2], match[3]
    return None, None, False

# ── Metrics ────────────────────────────────────────────────────────────────────
def render_metrics(score, passed, competitors, iterations):
    sc = "teal" if score >= 65 else "red"
    pv = "PASS" if passed else "FAIL"
    pc = "teal" if passed else "red"
    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-cell">
            <div class="m-label">Quality Score</div>
            <div class="m-value {sc}">{score}</div>
            <div class="m-sub">/ 100 · threshold 65</div>
        </div>
        <div class="metric-cell">
            <div class="m-label">Evaluation</div>
            <div class="m-value {pc}">{pv}</div>
            <div class="m-sub">{"criteria met" if passed else "needs improvement"}</div>
        </div>
        <div class="metric-cell">
            <div class="m-label">Competitors</div>
            <div class="m-value blue">{len(competitors)}</div>
            <div class="m-sub">companies analyzed</div>
        </div>
        <div class="metric-cell">
            <div class="m-label">Iterations</div>
            <div class="m-value amber">{iterations}</div>
            <div class="m-sub">of 3 max</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_competitors(competitors):
    st.markdown('<div class="sec-head">Competitor Data</div>', unsafe_allow_html=True)
    if competitors:
        for c in competitors:
            name     = c.get("company_name", "Unknown")
            snippets = c.get("raw_snippets", [])
            sources  = c.get("sources", [])
            sh = "".join(f'<div class="snippet">· {s}</div>' for s in snippets)
            sr = "".join(f'<div class="src">↗ {s}</div>' for s in sources[:2])
            st.markdown(f'<div class="comp-card"><div class="comp-name"><span class="c-dot"></span>{name}</div>{sh}{sr}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{TEXT3};font-size:0.9rem;padding:1rem 0;">No competitor data returned.</div>', unsafe_allow_html=True)

def render_gaps_and_queries(gaps, queries):
    gc, qc = st.columns(2)
    with gc:
        st.markdown('<div class="sec-head">Data Gaps</div>', unsafe_allow_html=True)
        for g in (gaps or []):
            st.markdown(f'<div class="gap-row">⚠ {g}</div>', unsafe_allow_html=True)
        if not gaps:
            st.markdown(f'<div style="color:{TEXT3};font-size:0.85rem;">No gaps detected.</div>', unsafe_allow_html=True)
    with qc:
        st.markdown('<div class="sec-head">Suggested Queries</div>', unsafe_allow_html=True)
        for q in (queries or []):
            st.markdown(f'<div class="q-row">→ {q}</div>', unsafe_allow_html=True)
        if not queries:
            st.markdown(f'<div style="color:{TEXT3};font-size:0.85rem;">No queries suggested.</div>', unsafe_allow_html=True)

def render_swot(analysis):
    if not analysis or not analysis.get("swot"):
        return
    st.markdown('<div class="sec-head">SWOT Analysis</div>', unsafe_allow_html=True)
    swot = analysis["swot"]
    cols = st.columns(2)
    quadrants = [
        ("Strengths 💪", "strengths", ACCENT),
        ("Weaknesses ⚠️", "weaknesses", RED),
        ("Opportunities 🚀", "opportunities", BLUE),
        ("Threats 🔴", "threats", AMBER),
    ]
    for i, (label, key, color) in enumerate(quadrants):
        with cols[i % 2]:
            items = swot.get(key, [])
            items_html = "".join(f'<div style="font-size:0.83rem;color:{TEXT2};padding:0.3rem 0 0.3rem 0.8rem;border-left:2px solid {color}40;margin-bottom:0.3rem;line-height:1.5;">· {item}</div>' for item in items)
            st.markdown(f'<div style="background:{BG2};border:1px solid {BORDER};border-radius:8px;padding:1rem 1.1rem;margin-bottom:0.8rem;"><div style="font-family:Space Mono,monospace;font-size:0.68rem;color:{color};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.7rem;">{label}</div>{items_html}</div>', unsafe_allow_html=True)

def render_comparison(analysis):
    matrix = (analysis or {}).get("comparison_matrix", [])
    if not matrix:
        return
    st.markdown('<div class="sec-head">Comparison Matrix</div>', unsafe_allow_html=True)
    for row in matrix:
        threat = row.get("threat_level", "Low")
        t_color = RED if threat == "High" else AMBER if threat == "Medium" else TEXT3
        st.markdown(f"""
        <div class="comp-card">
            <div class="comp-name"><span class="c-dot"></span>{row.get('company_name','?')}
                <span style="font-family:Space Mono,monospace;font-size:0.6rem;color:{t_color};margin-left:auto;letter-spacing:0.05em;">▲ {threat.upper()} THREAT</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;font-size:0.8rem;color:{TEXT2};">
                <div><span style="color:{TEXT3};font-size:0.65rem;font-family:Space Mono,monospace;display:block;margin-bottom:0.2rem;">PRICING</span>{row.get('pricing_tier','?')}</div>
                <div><span style="color:{TEXT3};font-size:0.65rem;font-family:Space Mono,monospace;display:block;margin-bottom:0.2rem;">STRENGTH</span>{row.get('primary_strength','?')}</div>
                <div><span style="color:{TEXT3};font-size:0.65rem;font-family:Space Mono,monospace;display:block;margin-bottom:0.2rem;">MARKET</span>{row.get('target_market','?')}</div>
            </div>
        </div>""", unsafe_allow_html=True)

def render_footer():
    st.markdown(f"""
    <div class="page-footer">
        <div class="footer-left">
            ⚡ COMPETITOR-INTEL &nbsp;·&nbsp; AGENTIC AI SYSTEM &nbsp;·&nbsp; CS 301 · NJIT · 2025<br>
            <span style="color:{TEXT3};">Powered by LangGraph + Gemini 2.5 &nbsp;·&nbsp; 4-agent pipeline with iterative refinement</span>
        </div>
        <div style="text-align:right;">
            <div class="footer-right">Built by</div>
            <div class="footer-names">HARSH &nbsp;·&nbsp; RAYANSH &nbsp;·&nbsp; SHIPPY</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Demo runner (fake progress) ────────────────────────────────────────────────
def run_demo(company, industry):
    slot = st.empty()
    bar  = st.progress(0)
    steps = [
        (f"researcher → scanning {industry} competitors...", 0.15, 0.8),
        ("categorizer → structuring raw data...",            0.35, 0.6),
        ("analyst → generating SWOT analysis...",           0.55, 0.7),
        ("evaluator → scoring quality... [iter 1: 61/100]", 0.70, 0.5),
        ("researcher → filling 2 gaps (targeted)...",       0.80, 0.8),
        ("evaluator → rescoring... [iter 2: 78/100] ✓",    0.90, 0.5),
        ("format → compiling final report...",               1.00, 0.4),
    ]
    def status(msg, pct):
        slot.markdown(f'<div class="prog-row"><div class="prog-dot"></div>{msg}</div>', unsafe_allow_html=True)
        bar.progress(pct)
    for msg, pct, delay in steps:
        status(msg, pct)
        time.sleep(delay)
    slot.empty()
    bar.empty()
    result = dict(DEMO_RESULT)
    result["target_company"] = company
    result["industry"] = industry
    return result

# ── Live runner ────────────────────────────────────────────────────────────────
def run_live(company, industry):
    from main import Orchestrator
    slot = st.empty()
    bar  = st.progress(0)
    def status(msg, pct):
        slot.markdown(f'<div class="prog-row"><div class="prog-dot"></div>{msg}</div>', unsafe_allow_html=True)
        bar.progress(pct)
    status("researcher → scanning competitors...", 0.1)
    with st.spinner(""):
        orch = Orchestrator()
        result = orch.run(company=company, industry=industry)
    slot.empty()
    bar.empty()
    return result

# ── Main ───────────────────────────────────────────────────────────────────────
render_sidebar()
render_header()

# Demo mode banner
if IS_DEMO:
    st.markdown(f'<div class="demo-banner">⚡ DEMO MODE — showing pre-computed Stripe vs fintech analysis · switch to LIVE in sidebar to run real analysis</div>', unsafe_allow_html=True)

# Input row
col1, col2, col3 = st.columns([5, 3, 2])

with col1:
    company, industry, is_demo_item = render_company_dropdown()

with col2:
    # Industry field — auto-fill if dropdown selected, editable if custom
    industry_val = industry if industry else st.session_state.get("custom_industry", "")
    if company:
        st.markdown(f'<span class="dropdown-label">INDUSTRY</span>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:{BG2};border:1px solid {BORDER};border-radius:8px;color:{TEXT};font-family:DM Sans,sans-serif;font-size:0.95rem;padding:0.7rem 1rem;">{industry_val}</div>', unsafe_allow_html=True)
    else:
        custom_industry = st.text_input("INDUSTRY", value=st.session_state.custom_industry, placeholder="e.g. fintech, design tools")
        st.session_state.custom_industry = custom_industry
        industry_val = custom_industry

with col3:
    st.markdown('<div style="height:1.9rem"></div>', unsafe_allow_html=True)
    run_btn = st.button("▶ RUN", use_container_width=True)

# Custom company input (only if "Custom..." selected)
if not company:
    custom_co = st.text_input("CUSTOM COMPANY NAME", value=st.session_state.custom_company, placeholder="e.g. Linear, Loom, Figma")
    st.session_state.custom_company = custom_co
    company = custom_co

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# Run
if run_btn:
    if not company or not company.strip():
        st.error("Please select or enter a company.")
        st.stop()

    industry_final = industry_val or st.session_state.custom_industry
    if not industry_final:
        st.error("Industry is required.")
        st.stop()

    if IS_DEMO:
        result = run_demo(company, industry_final)
    else:
        if not os.environ.get("GEMINI_API_KEY", ""):
            st.error("Please paste your Gemini API key in the sidebar first.")
            st.stop()
        try:
            result = run_live(company, industry_final)
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
    analysis    = result.get("analysis", {})

    render_metrics(score, passed, competitors, iterations)

    tab1, tab2, tab3, tab4 = st.tabs(["Competitors", "SWOT & Comparison", "Gaps & Queries", "Raw State"])
    with tab1:
        render_competitors(competitors)
    with tab2:
        render_swot(analysis)
        render_comparison(analysis)
    with tab3:
        render_gaps_and_queries(gaps, queries)
    with tab4:
        st.markdown(f'<div class="sec-head">Agent Execution Logs</div>', unsafe_allow_html=True)
        for log in result.get("logs", []):
            color = ACCENT if "PASSED" in log else RED if "FAILED" in log else TEXT3
            st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:0.72rem;color:{color};padding:0.2rem 0;border-bottom:1px solid {BORDER};">{log}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sec-head" style="margin-top:1.5rem;">Full State JSON</div>', unsafe_allow_html=True)
        st.json(result)

    if not passed and iterations >= 3:
        st.warning("Max iterations reached — report generated with best available data.")

else:
    st.markdown(f"""
    <div style="margin-top:5rem;text-align:center;">
        <div style="font-size:2.5rem;margin-bottom:1rem;opacity:0.15;">⚡</div>
        <div style="font-family:Space Mono,monospace;font-size:0.72rem;color:{TEXT4};letter-spacing:0.25em;text-transform:uppercase;margin-bottom:0.5rem;">System Ready</div>
        <div style="font-family:Space Mono,monospace;font-size:0.78rem;color:{TEXT3};">Select a company from the dropdown → click ▶ RUN</div>
        <div style="font-size:0.75rem;color:{TEXT4};margin-top:0.5rem;">{"Demo mode is active — no API key needed" if IS_DEMO else "Live mode — paste your Gemini key in the sidebar"}</div>
    </div>
    """, unsafe_allow_html=True)

render_footer()
