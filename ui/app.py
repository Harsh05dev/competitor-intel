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
# Palette: Linear / Resend / Vercel inspired. Deep midnight w/ teal-mint accent.
# Distinct surface elevation BG → BG2 → BG3 so cards visually pop.
if DARK:
    BG, BG2, BG3     = "#07080d", "#11131f", "#1c1f33"
    BORDER           = "#2d3148"
    TEXT, TEXT2, TEXT3, TEXT4 = "#f5f7fb", "#c5c9dd", "#7a82a8", "#4a516e"
    ACCENT           = "#00d4aa"
    RED, BLUE, AMBER = "#f87171", "#818cf8", "#fbbf24"
    SHADOW_LG        = "0 12px 40px -16px rgba(0,0,0,0.55)"
    SHADOW_MD        = "0 8px 24px -10px rgba(0,0,0,0.5)"
    GLOW_STRENGTH    = "55"  # alpha hex for text-shadow glows on dark
else:
    BG, BG2, BG3     = "#f4f6fb", "#ffffff", "#eef0f7"
    BORDER           = "#dadeea"
    TEXT, TEXT2, TEXT3, TEXT4 = "#0a0c14", "#2d3344", "#5a6280", "#8a92ac"
    ACCENT           = "#008566"
    RED, BLUE, AMBER = "#dc2626", "#4f46e5", "#b45309"
    SHADOW_LG        = "0 12px 40px -16px rgba(15,23,42,0.12)"
    SHADOW_MD        = "0 6px 18px -8px rgba(15,23,42,0.10)"
    GLOW_STRENGTH    = "00"  # disable text-shadow on light (alpha 00 = transparent)

ACC_BG  = f"{ACCENT}18"
ACC_BOR = f"{ACCENT}55"
MODE_BADGE_COLOR = ACCENT if DEMO else RED
MODE_BADGE_BG = ACC_BG if DEMO else f"{RED}22"
MODE_BADGE_BORDER = ACC_BOR if DEMO else f"{RED}55"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400..700&display=swap');

/* Header must keep real height — height:0 clips Streamlit's sidebar control */
header[data-testid="stHeader"] {{
    background: transparent !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 999990 !important;
    height: auto !important;
    min-height: 2rem !important;
    padding: 0 !important;
    overflow: visible !important;
}}

/* Collapsed sidebar: fixed chevron so it is never clipped or flush with viewport top */
button[data-testid="collapsedControl"] {{
    position: fixed !important;
    left: 0 !important;
    top: clamp(4rem, 10vh, 6rem) !important;
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
    font-weight: 450;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: {BG};
    color: {TEXT};
}}
/* App canvas: subtle ambient glow at top so the void breathes */
.stApp {{
    background:
        radial-gradient(ellipse 1100px 520px at 50% -120px, {ACCENT}14, transparent 70%),
        radial-gradient(ellipse 800px 400px at 12% 18%, {BLUE}10, transparent 60%),
        {BG} !important;
    background-attachment: fixed !important;
}}
.block-container {{
    padding: 0.35rem 2rem 3rem 2rem !important;
    max-width: 1200px !important;
}}

/* Sidebar — elevated panel with vertical gradient, hairline accent edge */
section[data-testid="stSidebar"] {{
    background:
        linear-gradient(180deg, {BG2} 0%, {BG} 100%) !important;
    border-right: 1px solid {BORDER} !important;
    box-shadow: 1px 0 0 0 {ACCENT}14 inset !important;
}}
section[data-testid="stSidebar"] > div {{
    padding: 0.5rem 1.1rem 1.35rem 1.1rem !important;
}}

.stButton > button {{
    background: {BG3} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    padding: 0.55rem !important;
    width: 100% !important;
    transition: all 0.18s ease !important;
}}
.stButton > button:hover {{
    background: {ACCENT}1f !important;
    border-color: {ACCENT} !important;
    color: {ACCENT} !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px {ACCENT}26;
}}
.stButton > button:active {{ transform: translateY(0); }}

.stTextInput label, .stSelectbox label {{
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    color: {TEXT3} !important;
    font-weight: 700 !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
}}
.stTextInput > div > div > input {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    color: {TEXT} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1rem !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT}26 !important;
}}
.stTextInput > div > div > input::placeholder {{ color: {TEXT3} !important; opacity: 0.85; }}

div[data-baseweb="select"] > div {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    color: {TEXT} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    min-height: 2.8rem !important;
}}
div[data-baseweb="select"] > div:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 3px {ACCENT}26 !important;
}}
div[data-baseweb="select"] svg {{ fill: {ACCENT} !important; }}
div[data-baseweb="popover"] > div > ul {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    padding: 4px !important;
    box-shadow: 0 12px 32px rgba(0,0,0,0.35) !important;
}}
li[role="option"] {{
    background: transparent !important;
    color: {TEXT} !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.8rem !important;
}}
li[role="option"]:hover, li[aria-selected="true"] {{
    background: {ACCENT}1f !important;
    color: {ACCENT} !important;
}}

/* Run button — primary CTA, accent gradient + glow */
.run-btn > div > button {{
    background: linear-gradient(135deg, {ACCENT}33 0%, {ACCENT}1a 100%) !important;
    color: {ACCENT} !important;
    border: 1px solid {ACCENT}80 !important;
    border-radius: 9px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    box-shadow: 0 4px 16px {ACCENT}26, 0 1px 0 {ACCENT}33 inset !important;
}}
.run-btn > div > button:hover {{
    background: linear-gradient(135deg, {ACCENT}4d 0%, {ACCENT}26 100%) !important;
    border-color: {ACCENT} !important;
    box-shadow: 0 8px 24px {ACCENT}40, 0 1px 0 {ACCENT}40 inset !important;
    transform: translateY(-1px);
}}

/* Metric cards — elevated surface w/ tinted shadow + glowing values */
.metrics-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: {BORDER};
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid {BORDER};
    margin: 1.5rem 0;
    box-shadow:
        0 1px 0 rgba(255,255,255,0.03) inset,
        {SHADOW_LG};
}}
.metric-cell {{
    background: linear-gradient(180deg, {BG2} 0%, {BG3} 100%);
    padding: 1.4rem 1.6rem;
    position: relative;
}}
.metric-cell::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, {ACCENT}55, transparent);
}}
.m-label {{ font-family: 'Space Mono', monospace; font-size: 0.62rem; font-weight: 700; color: {TEXT3}; letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 0.55rem; }}
.m-value {{ font-family: 'Space Mono', monospace; font-size: 2.1rem; font-weight: 700; line-height: 1; color: {TEXT}; letter-spacing: -0.02em; }}
.m-value.teal  {{ color: {ACCENT}; text-shadow: 0 0 22px {ACCENT}{GLOW_STRENGTH}; }}
.m-value.red   {{ color: {RED}; text-shadow: 0 0 22px {RED}{GLOW_STRENGTH}; }}
.m-value.blue  {{ color: {BLUE}; text-shadow: 0 0 22px {BLUE}{GLOW_STRENGTH}; }}
.m-value.amber {{ color: {AMBER}; text-shadow: 0 0 22px {AMBER}{GLOW_STRENGTH}; }}
.m-sub {{ font-size: 0.67rem; color: {TEXT3}; margin-top: 0.4rem; font-family: 'Space Mono', monospace; font-weight: 400; }}

.sec-head {{
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    font-weight: 700;
    color: {ACCENT};
    letter-spacing: 0.22em;
    text-transform: uppercase;
    margin: 1.8rem 0 0.9rem 0;
    display: flex;
    align-items: center;
    gap: 0.85rem;
}}
.sec-head::before {{ content: '◆'; font-size: 0.5rem; opacity: 0.7; }}
.sec-head::after {{ content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, {BORDER}, transparent); }}

/* Competitor cards — raised w/ subtle gradient + accent glow on hover */
.comp-card {{
    background: linear-gradient(180deg, {BG2} 0%, {BG2} 100%);
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1.15rem 1.45rem;
    margin-bottom: 0.55rem;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}}
.comp-card::before {{
    content: '';
    position: absolute; top: 0; left: 0; width: 3px; height: 100%;
    background: linear-gradient(180deg, {ACCENT}, {ACCENT}00);
    opacity: 0;
    transition: opacity 0.2s ease;
}}
.comp-card:hover {{
    border-color: {ACCENT}66;
    background: linear-gradient(180deg, {BG3} 0%, {BG2} 100%);
    box-shadow: 0 8px 24px -8px {ACCENT}33, 0 0 0 1px {ACCENT}1a;
    transform: translateY(-1px);
}}
.comp-card:hover::before {{ opacity: 1; }}
.comp-name {{ font-size: 0.97rem; font-weight: 600; color: {TEXT}; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.55rem; letter-spacing: -0.01em; }}
.c-dot {{ width: 6px; height: 6px; border-radius: 50%; background: {ACCENT}; flex-shrink: 0; box-shadow: 0 0 12px {ACCENT}cc, 0 0 0 3px {ACCENT}1a; }}
.snippet {{ font-size: 0.82rem; font-weight: 450; color: {TEXT2}; padding: 0.25rem 0 0.25rem 0.85rem; border-left: 1px solid {BORDER}; margin-bottom: 0.25rem; line-height: 1.55; transition: border-color 0.15s ease; }}
.snippet:hover {{ border-left-color: {ACCENT}; }}
.src {{ font-family: 'Space Mono', monospace; font-size: 0.6rem; color: {ACCENT}; opacity: 0.6; margin-top: 0.45rem; letter-spacing: 0.05em; }}

.gap-row {{ padding: 0.7rem 1rem; background: linear-gradient(135deg, {RED}1f, {RED}0a); border: 1px solid {RED}40; border-left: 3px solid {RED}; border-radius: 0 8px 8px 0; margin-bottom: 0.35rem; font-size: 0.83rem; font-weight: 500; color: {RED}; line-height: 1.5; box-shadow: 0 2px 8px -4px {RED}33; }}
.q-row {{ padding: 0.7rem 1rem; background: linear-gradient(135deg, {ACCENT}26, {ACCENT}0a); border: 1px solid {ACCENT}55; border-left: 3px solid {ACCENT}; border-radius: 0 8px 8px 0; margin-bottom: 0.35rem; font-size: 0.83rem; font-weight: 500; color: {ACCENT}; font-family: 'Space Mono', monospace; line-height: 1.5; box-shadow: 0 2px 8px -4px {ACCENT}33; }}

.prog-row {{ display: flex; align-items: center; gap: 0.6rem; padding: 0.4rem 0; font-size: 0.82rem; color: {TEXT2}; font-family: 'Space Mono', monospace; }}
.prog-dot {{ width: 5px; height: 5px; border-radius: 50%; background: {ACCENT}; flex-shrink: 0; animation: blink 1s infinite; box-shadow: 0 0 8px {ACCENT}80; }}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}
.stProgress > div > div {{ background: {ACCENT} !important; }}

.stTabs [data-baseweb="tab-list"] {{ background: transparent !important; border-bottom: 1px solid {BORDER} !important; gap: 0 !important; padding: 0 !important; }}
.stTabs [data-baseweb="tab"] {{ font-family: 'Space Mono', monospace !important; font-size: 0.68rem !important; font-weight: 700 !important; letter-spacing: 0.12em !important; text-transform: uppercase !important; color: {TEXT3} !important; padding: 0.8rem 1.3rem !important; border-radius: 0 !important; border-bottom: 2px solid transparent !important; background: transparent !important; transition: all 0.18s ease !important; }}
.stTabs [data-baseweb="tab"]:hover {{ color: {TEXT2} !important; background: {ACCENT}0a !important; }}
.stTabs [aria-selected="true"] {{ color: {ACCENT} !important; border-bottom: 2px solid {ACCENT} !important; text-shadow: 0 0 12px {ACCENT}55 !important; }}

/* Sidebar pipeline item hover — subtle accent lift */
.pipe-item:hover {{
    border-color: {ACCENT}80 !important;
    transform: translateX(2px);
    box-shadow: -3px 0 0 0 {ACCENT}, 0 4px 12px -4px {ACCENT}40 !important;
}}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {TEXT3}; }}
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
SIDE_LABEL = f"font-family:'Space Mono',monospace;font-size:0.66rem;font-weight:700;color:{ACCENT};letter-spacing:0.2em;text-transform:uppercase;margin-bottom:0.55rem;display:flex;align-items:center;gap:0.45rem;"
SIDE_LABEL_ICON = f"display:inline-block;width:5px;height:5px;border-radius:50%;background:{ACCENT};box-shadow:0 0 8px {ACCENT}cc;"

with st.sidebar:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0.45rem;font-family:\'Space Mono\',monospace;font-weight:700;padding-bottom:0.85rem;border-bottom:1px solid {BORDER};margin-bottom:1rem;line-height:1.2;"><span style="font-size:1.35rem;line-height:1;color:{ACCENT};filter:drop-shadow(0 0 10px {ACCENT}55);">⚡</span>'
        f'<span style="font-size:1.06rem;background:linear-gradient(90deg,{ACCENT},{BLUE});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:0.14em;text-transform:uppercase;">Competitor Intel</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="font-size:0.66rem;color:{TEXT3};margin:-0.4rem 0 1.1rem 0;line-height:1.55;font-weight:450;">Opens automatically on each visit. If you collapse the sidebar, use the <span style="color:{ACCENT};font-weight:700;">teal «</span> tab on the left — it stays fixed and fully visible.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(f'<div style="{SIDE_LABEL}"><span style="{SIDE_LABEL_ICON}"></span>Mode</div>', unsafe_allow_html=True)
    mc1, mc2 = st.columns(2)
    with mc1:
        if st.button("⚡ DEMO", key="btn_demo"):
            st.session_state.mode = "demo"; st.rerun()
    with mc2:
        if st.button("🔴 LIVE", key="btn_live"):
            st.session_state.mode = "live"; st.rerun()

    mc = ACCENT if DEMO else RED
    mt = "● DEMO — no key needed" if DEMO else "● LIVE — key required"
    st.markdown(
        f'<div style="font-family:\'Space Mono\',monospace;font-size:0.62rem;font-weight:700;color:{mc};text-align:center;margin:0.5rem 0 1.2rem 0;padding:0.35rem;background:{mc}14;border:1px solid {mc}40;border-radius:6px;letter-spacing:0.08em;">{mt}</div>',
        unsafe_allow_html=True,
    )

    live_api_key = ""
    if not DEMO:
        st.markdown(f'<div style="{SIDE_LABEL}"><span style="{SIDE_LABEL_ICON}"></span>Gemini API Key</div>', unsafe_allow_html=True)
        live_api_key = st.text_input("key", type="password", placeholder="paste key here", label_visibility="collapsed", key="gemini_api_key")
        if live_api_key:
            st.markdown(f'<div style="font-family:\'Space Mono\',monospace;font-size:0.62rem;font-weight:700;color:{ACCENT};margin-top:0.35rem;">✓ key loaded</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-family:\'Space Mono\',monospace;font-size:0.62rem;font-weight:700;color:{AMBER};margin-top:0.35rem;">⚠ paste key to run</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-family:\'Space Mono\',monospace;font-size:0.6rem;color:{TEXT3};margin-top:0.35rem;font-weight:500;">free key → <span style="color:{ACCENT};">ai.google.dev</span></div>', unsafe_allow_html=True)
        st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)

    st.markdown(f'<div style="{SIDE_LABEL}"><span style="{SIDE_LABEL_ICON}"></span>Pipeline</div>', unsafe_allow_html=True)
    for icon, name, tag in [("🔍","Researcher","web search"),("🗂","Categorizer","structure"),("📊","Analyst","SWOT"),("✅","Evaluator","quality gate"),("🔁","Loop","score < 70"),("📄","Report","final")]:
        st.markdown(
            f'<div class="pipe-item" style="display:flex;align-items:center;justify-content:space-between;padding:0.5rem 0.75rem;border-radius:8px;margin-bottom:0.3rem;background:linear-gradient(135deg,{BG3} 0%,{BG2} 100%);border:1px solid {BORDER};transition:all 0.18s ease;">'
            f'<div style="display:flex;align-items:center;gap:0.55rem;">'
            f'<span style="font-size:0.95rem;filter:drop-shadow(0 0 6px {ACCENT}40);">{icon}</span>'
            f'<span style="font-size:0.82rem;color:{TEXT};font-weight:600;letter-spacing:0.01em;">{name}</span>'
            f'</div>'
            f'<span style="font-family:\'Space Mono\',monospace;font-size:0.58rem;font-weight:700;color:{ACCENT};background:{ACCENT}1f;border:1px solid {ACCENT}40;padding:0.15rem 0.45rem;border-radius:5px;letter-spacing:0.05em;">{tag}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f'<div style="{SIDE_LABEL}margin-top:1.1rem;"><span style="{SIDE_LABEL_ICON}"></span>Config</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-family:\'Space Mono\',monospace;font-size:0.7rem;line-height:1.95;background:linear-gradient(135deg,{BG3} 0%,{BG2} 100%);border:1px solid {BORDER};border-radius:8px;padding:0.8rem 0.95rem;font-weight:500;">'
        f'<div><span style="color:{TEXT3};">THRESHOLD</span> <span style="color:{TEXT4};">=</span> <span style="color:{ACCENT};font-weight:700;">70</span></div>'
        f'<div><span style="color:{TEXT3};">MAX_ITER</span>&nbsp; <span style="color:{TEXT4};">=</span> <span style="color:{AMBER};font-weight:700;">3</span></div>'
        f'<div><span style="color:{TEXT3};">AGENTS</span>&nbsp;&nbsp;&nbsp; <span style="color:{TEXT4};">=</span> <span style="color:{BLUE};font-weight:700;">4</span></div>'
        f'<div><span style="color:{TEXT3};">FRAMEWORK</span> <span style="color:{TEXT4};">=</span> <span style="color:{TEXT};font-weight:700;">LangGraph</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(f'<div style="{SIDE_LABEL}margin-top:1.1rem;"><span style="{SIDE_LABEL_ICON}"></span>Theme</div>', unsafe_allow_html=True)
    if st.button("☀ Light" if DARK else "☾ Dark", key="theme_btn"):
        st.session_state.theme = "light" if DARK else "dark"; st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:1.15rem;padding:0.45rem 0 0.95rem 0;border-bottom:1px solid {BORDER};margin-bottom:1.25rem;margin-top:0;flex-wrap:wrap;">
    <div style="display:flex;align-items:center;gap:0.55rem;"><span style="font-size:2.1rem;line-height:1;filter:drop-shadow(0 0 14px {ACCENT}55);">⚡</span><div style="font-family:Space Mono,monospace;font-size:2rem;font-weight:700;color:{TEXT};letter-spacing:-0.025em;line-height:1.05;">Competitor Intel</div></div>
    <div style="font-family:Space Mono,monospace;font-size:0.82rem;color:{ACCENT};background:{ACC_BG};border:1px solid {ACC_BOR};border-radius:999px;padding:0.32rem 0.95rem;letter-spacing:0.08em;font-weight:700;">AGENTIC AI · CS 301</div>
    <div style="font-size:1.05rem;color:{TEXT2};font-style:italic;line-height:1.4;max-width:32rem;font-weight:450;">"Know your market before your market knows you."</div>
    <div style="margin-left:auto;font-family:Space Mono,monospace;font-size:0.82rem;font-weight:700;color:{MODE_BADGE_COLOR};background:{MODE_BADGE_BG};border:1px solid {MODE_BADGE_BORDER};border-radius:8px;padding:0.4rem 0.95rem;letter-spacing:0.05em;">● {"DEMO" if DEMO else "LIVE"} MODE</div>
</div>
""", unsafe_allow_html=True)

if DEMO:
    st.markdown(f'<div style="background:linear-gradient(135deg,{ACCENT}1f,{ACCENT}0a);border:1px solid {ACC_BOR};border-radius:9px;padding:0.75rem 1rem;font-family:Space Mono,monospace;font-size:0.82rem;color:{ACCENT};letter-spacing:0.04em;margin-bottom:1.2rem;font-weight:600;box-shadow:0 2px 12px -4px {ACCENT}33;">⚡ DEMO MODE — pre-computed Stripe vs fintech · Switch to LIVE in sidebar for real analysis</div>', unsafe_allow_html=True)

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
    sc = "teal" if score >= 70 else "red"
    pc = "teal" if passed else "red"
    pv = "PASS" if passed else "FAIL"
    st.markdown(f'<div class="metrics-row"><div class="metric-cell"><div class="m-label">Quality Score</div><div class="m-value {sc}">{score}</div><div class="m-sub">/ 100 · threshold 70</div></div><div class="metric-cell"><div class="m-label">Evaluation</div><div class="m-value {pc}">{pv}</div><div class="m-sub">{"criteria met" if passed else "needs work"}</div></div><div class="metric-cell"><div class="m-label">Competitors</div><div class="m-value blue">{len(competitors)}</div><div class="m-sub">companies analyzed</div></div><div class="metric-cell"><div class="m-label">Iterations</div><div class="m-value amber">{iterations}</div><div class="m-sub">of 3 max</div></div></div>', unsafe_allow_html=True)

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

def _build_fallback_report_md(result: dict) -> str:
    """Build a plain-markdown report from result state when final_output is absent (demo mode)."""
    ev = result.get("evaluation", {})
    score = ev.get("score", 0)
    target = result.get("target_company", "Unknown")
    industry = result.get("industry", "")
    iters = result.get("iteration", 1)
    conf = "HIGH" if score >= 70 else "MEDIUM" if score >= 50 else "LOW"

    lines = [
        f"# Competitor Intelligence Report: {target}",
        f"Industry: {industry}  |  Confidence: {conf}  |  Score: {score}/100  |  Iterations: {iters}",
        "",
    ]

    swot = (result.get("analysis") or {}).get("swot", {})
    if swot:
        lines.append("## SWOT Analysis")
        for q in ["strengths", "weaknesses", "opportunities", "threats"]:
            items = swot.get(q, [])
            if items:
                lines.append(f"\n### {q.title()}")
                for item in items:
                    lines.append(f"- {item}")

    matrix = (result.get("analysis") or {}).get("comparison_matrix", [])
    if matrix:
        lines.append("\n## Competitor Comparison")
        for row in matrix:
            lines.append(
                f"- {row.get('company_name','?')}: "
                f"{row.get('pricing_tier','?')} | {row.get('primary_strength','?')} | "
                f"threat={row.get('threat_level','?')}"
            )

    gaps = (result.get("analysis") or {}).get("opportunity_gaps", [])
    if gaps:
        lines.append("\n## Opportunity Gaps")
        for g in gaps:
            lines.append(f"- {g}")

    return "\n".join(lines)


def run_demo_mode(company, industry):
    slot = st.empty(); bar = st.progress(0)
    for msg, pct, delay in [
        (f"researcher → scanning {industry} competitors...", 0.15, 3.9),
        ("categorizer → structuring raw data...",            0.32, 3.7),
        ("analyst → generating SWOT analysis...",           0.50, 3.8),
        ("evaluator → scoring... [iter 1: 61/100 ✗]",      0.65, 3.6),
        ("researcher → filling 2 gaps (targeted)...",       0.78, 3.9),
        ("evaluator → rescoring... [iter 2: 78/100 ✓]",    0.90, 3.6),
        ("format → compiling final report...",               1.00, 3.4),
    ]:
        slot.markdown(f'<div class="prog-row"><div class="prog-dot"></div>{msg}</div>', unsafe_allow_html=True)
        bar.progress(pct); time.sleep(delay)
    slot.empty(); bar.empty()
    return {**DEMO_RESULT, "target_company": company, "industry": industry}

def run_live_mode(company, industry, api_key):
    from main import Orchestrator
    slot = st.empty(); bar = st.progress(0)
    slot.markdown(f'<div class="prog-row"><div class="prog-dot"></div>researcher → scanning competitors...</div>', unsafe_allow_html=True)
    bar.progress(0.1)
    with st.spinner(""):
        result = Orchestrator().run(company=company, industry=industry, api_key=api_key)
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
        if not live_api_key.strip():
            st.error("Paste your Gemini API key in the sidebar first."); st.stop()
        try:
            result = run_live_mode(company_final, industry_final, live_api_key.strip())
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

    try:
        from fpdf import FPDF

        report_md = result.get("final_output", "") or _build_fallback_report_md(result)
        if report_md:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=10)
            for raw_line in report_md.split("\n"):
                safe = raw_line.encode("latin-1", "replace").decode("latin-1")[:200]
                if safe.strip():
                    pdf.set_x(pdf.l_margin)
                    pdf.multi_cell(pdf.epw, 5, text=safe)
                else:
                    pdf.ln(4)
            pdf_bytes = bytes(pdf.output())
            st.download_button(
                "⬇ Download PDF Report",
                data=pdf_bytes,
                file_name=f"{company_final}_competitor_report.pdf",
                mime="application/pdf",
            )
    except Exception:
        pass
else:
    st.markdown(f'<div style="margin-top:5rem;text-align:center;padding:2rem;"><div style="font-size:2.2rem;margin-bottom:1rem;opacity:0.1;">⚡</div><div style="font-family:Space Mono,monospace;font-size:0.68rem;color:{TEXT4};letter-spacing:0.25em;text-transform:uppercase;margin-bottom:0.5rem;">System Ready</div><div style="font-family:Space Mono,monospace;font-size:0.76rem;color:{TEXT3};margin-bottom:0.35rem;">Select a company → click ▶ RUN</div><div style="font-size:0.72rem;color:{TEXT4};">{"Demo mode active — no API key needed" if DEMO else "Live mode — paste your Gemini key in the sidebar"}</div></div>', unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="margin-top:3rem;padding:1.5rem 0 0.6rem 0;border-top:1px solid {BORDER};display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.8rem;">'
    f'<div>'
    f'<div style="font-family:Space Mono,monospace;font-size:0.78rem;font-weight:700;color:{TEXT2};letter-spacing:0.08em;">⚡ COMPETITOR-INTEL · AGENTIC AI SYSTEM · CS 301 · NJIT · 2025</div>'
    f'<div style="font-family:Space Mono,monospace;font-size:0.7rem;color:{TEXT3};margin-top:0.35rem;font-weight:500;">Powered by <span style="color:{ACCENT};font-weight:700;">LangGraph</span> + <span style="color:{BLUE};font-weight:700;">Gemini 2.5</span> · 4-agent pipeline with iterative refinement</div>'
    f'</div>'
    f'<div style="text-align:right;">'
    f'<div style="font-size:0.78rem;color:{TEXT3};margin-bottom:0.2rem;font-weight:500;">Built by</div>'
    f'<div style="font-family:Space Mono,monospace;font-size:0.82rem;font-weight:700;background:linear-gradient(90deg,{ACCENT},{BLUE});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:0.06em;">HARSH · RAYANSH · SHIPPY</div>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)
