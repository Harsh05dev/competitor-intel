"""
orchestrator.py — LangGraph StateGraph Orchestrator

This is the core agentic component of the system. Instead of a simple
while-loop, we use a LangGraph StateGraph where:

  - Each agent is a NODE in the graph
  - Connections between agents are EDGES
  - The retry decision is a CONDITIONAL EDGE

This means the graph itself encodes the agentic logic — not hidden
inside an if/else buried in a loop. The conditional edge after the
Evaluator is what makes this system genuinely agentic.

Graph structure:
    researcher → categorizer → analyst → evaluator
                                              │
                    ┌─────── score < threshold ──────┘
                    │         (retry)
                    ▼
              researcher (round 2+, targeted queries)
                    │
                    └─────── score >= threshold OR max iter ──→ format_report → END

Usage:
    from orchestrator import build_graph, run_analysis
    result = run_analysis("Stripe", "fintech")
"""

from typing import Optional

from langgraph.graph import StateGraph, END

from models.schemas import AgentState
from agents.researcher import ResearcherAgent
from agents.categorizer import CategorizerAgent
from agents.analyst import AnalystAgent
from agents.evaluator import EvaluatorAgent
import config

# ── Lazy agent singletons (avoid import-time Gemini client / Streamlit crash) ─
_researcher  = None
_categorizer = None
_analyst     = None
_evaluator   = None


def _get_agents(api_key: Optional[str] = None):
    if api_key is not None:
        return (
            ResearcherAgent(api_key=api_key),
            CategorizerAgent(api_key=api_key),
            AnalystAgent(api_key=api_key),
            EvaluatorAgent(api_key=api_key),
        )

    global _researcher, _categorizer, _analyst, _evaluator
    if _researcher is None:
        _researcher = ResearcherAgent()
        _categorizer = CategorizerAgent()
        _analyst = AnalystAgent()
        _evaluator = EvaluatorAgent()
    return _researcher, _categorizer, _analyst, _evaluator


# ── NODE FUNCTIONS ─────────────────────────────────────────────────────────────
# Each node takes the full AgentState and returns a dict of updated fields.
# LangGraph merges the returned dict into the existing state automatically.

def _researcher_node(state: AgentState, researcher: ResearcherAgent) -> dict:
    """
    Node 1 — Researcher
    Round 1: broad search to find competitors.
    Round 2+: targeted search using Evaluator's suggested_queries.
    """
    # Cap suggested queries to prevent prompt overflow
    ev = state.get("evaluation", {})
    if ev.get("suggested_queries"):
        state = {
            **state,
            "evaluation": {
                **ev,
                "suggested_queries": ev["suggested_queries"][: config.MAX_GAPS_PER_RETRY],
            },
        }
    print(f"\n[Graph] → researcher_node (iteration {state['iteration']})")
    result = researcher.research(state)
    log_entry = f"[Iter {state['iteration']}] Researcher: found {len(result.get('research_results', []))} competitors"
    return {
        **result,
        "status": "researched",
        "logs": state.get("logs", []) + [log_entry],
    }


def researcher_node(state: AgentState) -> dict:
    _get_agents()
    return _researcher_node(state, _researcher)


def _categorizer_node(state: AgentState, categorizer: CategorizerAgent) -> dict:
    """
    Node 2 — Categorizer
    Transforms raw snippets into structured JSON per competitor.
    On iteration 2+, merges new data with existing data (fills gaps only).
    """
    print(f"\n[Graph] → categorizer_node (iteration {state['iteration']})")
    result = categorizer.categorize(state)
    log_entry = f"[Iter {state['iteration']}] Categorizer: structured {len(result.get('categorized_competitors', []))} competitors"
    return {
        **result,
        "status": "categorized",
        "logs": state.get("logs", []) + [log_entry],
    }


def categorizer_node(state: AgentState) -> dict:
    _get_agents()
    return _categorizer_node(state, _categorizer)


def _analyst_node(state: AgentState, analyst: AnalystAgent) -> dict:
    """
    Node 3 — Analyst
    Synthesizes structured competitor data into SWOT analysis,
    comparison matrix, threat ranking, and opportunity gaps.
    """
    print(f"\n[Graph] → analyst_node (iteration {state['iteration']})")
    result = analyst.analyze(state)
    swot = result.get("analysis", {}).get("swot", {})
    total_points = sum(len(v) for v in swot.values() if isinstance(v, list))
    log_entry = f"[Iter {state['iteration']}] Analyst: generated SWOT with {total_points} points"
    return {
        **result,
        "status": "analyzed",
        "logs": state.get("logs", []) + [log_entry],
    }


def analyst_node(state: AgentState) -> dict:
    _get_agents()
    return _analyst_node(state, _analyst)


def _evaluator_node(state: AgentState, evaluator: EvaluatorAgent) -> dict:
    """
    Node 4 — Evaluator (the quality gate)
    Scores the current output 0-100 on 6 weighted criteria.
    Identifies specific gaps and generates targeted search queries.
    The score determines which path the conditional edge takes.
    """
    print(f"\n[Graph] → evaluator_node (iteration {state['iteration']})")
    result = evaluator.evaluate(state)
    score  = result.get("evaluation", {}).get("score", 0)
    passed = result.get("evaluation", {}).get("passed", False)
    log_entry = f"[Iter {state['iteration']}] Evaluator: score={score}/100 {'PASSED ✓' if passed else 'FAILED ✗'}"
    return {
        **result,
        "iteration": state["iteration"] + 1,
        "status": "evaluated",
        "logs": state.get("logs", []) + [log_entry],
    }


def evaluator_node(state: AgentState) -> dict:
    _get_agents()
    return _evaluator_node(state, _evaluator)


def format_report_node(state: AgentState) -> dict:
    """
    Terminal node — formats all accumulated state into the final output.
    Runs once when the graph decides to finalize (score >= threshold OR max iter).
    No LLM call needed here — just assembles the report from existing state.
    """
    print(f"\n[Graph] → format_report_node")
    ev    = state.get("evaluation", {})
    score = ev.get("score", 0)
    comps = state.get("categorized_competitors", []) or state.get("research_results", [])
    analysis = state.get("analysis", {})
    swot  = analysis.get("swot", {})
    iters = state["iteration"]
    conf  = "HIGH" if score >= config.EVALUATION_THRESHOLD else "MEDIUM" if score >= 50 else "LOW"

    # Build a clean markdown report from all state data
    lines = []
    lines.append(f"# Competitor Intelligence Report: {state['target_company']}")
    lines.append(f"**Industry:** {state['industry']}  |  **Confidence:** {conf}  |  **Score:** {score}/100  |  **Iterations:** {iters}")
    lines.append("")

    # SWOT section
    if swot:
        lines.append("## SWOT Analysis")
        for quadrant in ["strengths", "weaknesses", "opportunities", "threats"]:
            items = swot.get(quadrant, [])
            if items:
                lines.append(f"\n### {quadrant.title()}")
                for item in items:
                    lines.append(f"- {item}")

    # Comparison matrix
    matrix = analysis.get("comparison_matrix", [])
    if matrix:
        lines.append("\n## Competitor Comparison")
        lines.append("| Company | Pricing | Strength | Weakness | Market | Threat |")
        lines.append("|---------|---------|----------|----------|--------|--------|")
        for row in matrix:
            lines.append(
                f"| {row.get('company_name','?')} "
                f"| {row.get('pricing_tier','?')} "
                f"| {row.get('primary_strength','?')} "
                f"| {row.get('primary_weakness','?')} "
                f"| {row.get('target_market','?')} "
                f"| {row.get('threat_level','?')} |"
            )

    # Opportunity gaps
    gaps = analysis.get("opportunity_gaps", [])
    if gaps:
        lines.append("\n## Opportunity Gaps")
        for g in gaps:
            lines.append(f"- {g}")

    # Low confidence warning
    if score < config.EVALUATION_THRESHOLD:
        lines.append(f"\n> ⚠️ **Low confidence** — max iterations ({config.MAX_ITERATIONS}) reached before score threshold ({config.EVALUATION_THRESHOLD}) was met.")

    final_output = "\n".join(lines)
    log_entry = f"[Iter {iters}] Report formatted (confidence={conf})"

    return {
        "final_output": final_output,
        "status": "complete",
        "logs": state.get("logs", []) + [log_entry],
    }


# ── ROUTING FUNCTION (the conditional edge) ────────────────────────────────────

def route_after_evaluation(state: AgentState) -> str:
    """
    This function is the conditional edge after the Evaluator node.
    It checks the score and iteration count and returns a string key
    that LangGraph uses to decide which node to visit next.

    Returns:
        "retry"    → go back to researcher_node for targeted re-research
        "finalize" → go to format_report_node and end
    """
    score     = state.get("evaluation", {}).get("score", 0)
    iteration = state.get("iteration", 0)

    if score >= config.EVALUATION_THRESHOLD:
        print(f"\n[Graph] ✓ Score {score} >= {config.EVALUATION_THRESHOLD} → FINALIZE")
        return "finalize"
    elif iteration >= config.MAX_ITERATIONS:
        print(f"\n[Graph] ⚠ Max iterations ({config.MAX_ITERATIONS}) reached → FINALIZE with low confidence")
        return "finalize"
    else:
        print(f"\n[Graph] ✗ Score {score} < {config.EVALUATION_THRESHOLD}, iter {iteration}/{config.MAX_ITERATIONS} → RETRY")
        return "retry"


# ── GRAPH BUILDER ──────────────────────────────────────────────────────────────

def build_graph(api_key: Optional[str] = None):
    """
    Constructs and compiles the LangGraph StateGraph.

    Nodes:    researcher, categorizer, analyst, evaluator, format_report
    Edges:    researcher→categorizer→analyst→evaluator (fixed, always)
    Cond edge: evaluator → {retry: researcher, finalize: format_report}
    """
    researcher, categorizer, analyst, evaluator = _get_agents(api_key=api_key)
    graph = StateGraph(AgentState)

    # ── Register nodes ─────────────────────────────────────────────────────────
    graph.add_node("researcher",   lambda state: _researcher_node(state, researcher))
    graph.add_node("categorizer",  lambda state: _categorizer_node(state, categorizer))
    graph.add_node("analyst",      lambda state: _analyst_node(state, analyst))
    graph.add_node("evaluator",    lambda state: _evaluator_node(state, evaluator))
    graph.add_node("format_report", format_report_node)

    # ── Fixed edges (always flow forward) ──────────────────────────────────────
    graph.add_edge("researcher",  "categorizer")
    graph.add_edge("categorizer", "analyst")
    graph.add_edge("analyst",     "evaluator")

    # ── THE CONDITIONAL EDGE ───────────────────────────────────────────────────
    # After the evaluator runs, route_after_evaluation() decides the next node.
    # This is what makes the system agentic — the graph branches on quality score.
    graph.add_conditional_edges(
        "evaluator",           # source node
        route_after_evaluation, # routing function
        {
            "retry":    "researcher",    # loop back for targeted re-research
            "finalize": "format_report", # proceed to final report
        }
    )

    # ── Terminal edge ──────────────────────────────────────────────────────────
    graph.add_edge("format_report", END)

    # ── Entry point ────────────────────────────────────────────────────────────
    graph.set_entry_point("researcher")

    return graph.compile()


# ── PUBLIC API ─────────────────────────────────────────────────────────────────

def run_analysis(company: str, industry: str, api_key: Optional[str] = None) -> AgentState:
    """
    Main entry point. Takes company + industry, returns the complete final state.
    Called by main.py Orchestrator wrapper and by ui/app.py indirectly.
    """
    app = build_graph(api_key=api_key)

    initial_state: AgentState = {
        "target_company":          company,
        "industry":                industry,
        "iteration":               0,
        "research_results":        [],
        "categorized_competitors": [],
        "analysis":                {},
        "evaluation":              {},
        "final_output":            "",
        "status":                  "initialized",
        "logs":                    [],
    }

    print(f"\n{'='*55}")
    print(f"  Competitor Intelligence — LangGraph Orchestrator")
    print(f"  Target: {company} | Industry: {industry}")
    print(f"{'='*55}")

    result = app.invoke(initial_state)

    print(f"\n{'='*55}")
    print(f"  COMPLETE | Score: {result['evaluation'].get('score', 0)}/100")
    print(f"  Iterations: {result['iteration']} | Status: {result['status']}")
    print(f"{'='*55}\n")

    return result
