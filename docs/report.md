# Competitor Intelligence Dashboard — Project Report

**Course:** CS 301 — Agentic AI  
**Team:** Harsh, Rayansh, Shippy  
**Repository:** https://github.com/Harsh05dev/competitor-intel

---

## 1. Problem Statement

Manual competitor research is slow, inconsistent, and hard to scale. Analysts typically spend hours searching the web, reading articles, and synthesizing information across dozens of sources — only to produce a report that may already be outdated.

This project addresses that problem by building an automated, agentic competitor intelligence system. Given a target company and its industry, the system autonomously finds key competitors, extracts structured market signals, evaluates the quality of its own research, and iteratively improves until it meets a defined quality threshold. The result is a structured intelligence report delivered through an interactive dashboard — in minutes rather than hours.

---

## 2. System Design

### 2.1 Architecture Overview

The system is composed of four specialized agents orchestrated by a central loop, with a Streamlit web dashboard as the user interface.

```
User Input (company + industry)
        │
        ▼
┌──────────────────────────────────────────────────────────────────┐
│       LangGraph StateGraph (orchestrator.py)                      │
│                                                                   │
│  Researcher → Categorizer → Analyst → Evaluator                   │
│                                            │                      │
│                      ┌─── score < 70 ──────┘                      │
│                      ↓                                            │
│                Researcher (retry)                                 │
│                      │                                            │
│                      └─── score >= 70 ──→ format_report → END     │
│                                                                   │
│  Conditional edge after Evaluator routes between {retry,finalize} │
│  Hard cap: MAX_ITERATIONS = 3 (forces finalize even on low score) │
└──────────────────────────────────────────────────────────────────┘
        │
        ▼
  Streamlit Dashboard (ui/app.py)
```

### 2.2 Components

**Agent 1 — Researcher** (`agents/researcher.py`)  
Queries the Gemini API (with Google Search Grounding) to find 4 competitors of the target company. On the first iteration it performs broad research. On subsequent iterations it receives specific gap-filling queries from the Evaluator and performs targeted research to fill missing data. Returns structured JSON with company names, raw snippets, and source URLs.

**Agent 2 — Categorizer** (`agents/categorizer.py`)  
Takes the raw, noisy snippets produced by the Researcher and organizes them into clean structured records per competitor: pricing, key features, target audience, funding, hiring signals, recent news, and customer sentiment. On retries it does not overwrite previously gathered data — it merges new fields into existing competitor records using a fill-gaps strategy.

**Agent 3 — Analyst** (`agents/analyst.py`)  
Takes structured competitor data and synthesizes strategic insights: SWOT analysis (strengths, weaknesses, opportunities, threats), a comparison matrix with pricing tiers and threat levels, threat ranking, and opportunity gaps. Each SWOT quadrant requires at least 2 evidence-backed points.

**Agent 4 — Evaluator** (`agents/evaluator.py`)  
Takes the collected competitor data and scores it on a 0–100 scale across 6 weighted criteria (competitor count, pricing coverage, feature coverage, funding data, hiring signals, SWOT depth). Identifies specific data gaps (e.g. missing pricing data, sparse feature coverage) and generates targeted search queries to address those gaps. If the score is 70 or above, the pipeline finalizes. Otherwise it loops back to the Researcher. The Evaluator is intentionally independent from the Analyst — the same agent must not both write and grade the analysis.

**Orchestrator** (`orchestrator.py` + `main.py`)  
A LangGraph `StateGraph` whose nodes are the four agents above plus a terminal `format_report` node. Fixed edges run Researcher → Categorizer → Analyst → Evaluator. After the Evaluator, a **conditional edge** (`route_after_evaluation`) inspects the score and iteration count and routes either back to the Researcher (retry) or to `format_report` (finalize). `MAX_ITERATIONS = 3` is the hard safety cap. `main.py` provides a thin `Orchestrator` class wrapper for backward compatibility with the Streamlit UI.

**Streamlit Dashboard** (`ui/app.py`)  
Provides the user interface. Accepts company name and industry as inputs, displays live progress as each agent runs, and presents results in a structured layout with metric cards, tabbed sections for competitor data and gaps, and the full raw agent state.

### 2.3 Data Flow

Each agent receives the full shared state dictionary and returns updates to it. The state includes:

- `target_company` — the company being analyzed
- `industry` — the industry context
- `iteration` — current loop count
- `research_results` — raw competitor data from the Researcher
- `categorized_competitors` — structured competitor records
- `evaluation` — score, pass/fail, gaps, and suggested queries

---

## 3. Agentic Workflow

### 3.1 Iteration Example

Below is a walkthrough of how the system processes a query for **"Stripe" in "fintech"**:

**Round 1 — Broad Research**
- Researcher receives: `company=Stripe, industry=fintech, iteration=0`
- Researcher sends a broad prompt to Gemini: find 4 competitors with facts and sources
- Returns: PayPal, Square, Adyen, Braintree with raw snippets
- Evaluator scores the data — pricing and hiring signals are sparse, so the score lands below threshold
- Evaluator returns: `score=61, passed=False, gaps=["missing pricing info for Adyen", "no hiring signals"], suggested_queries=["Adyen pricing 2024", "Square hiring engineering"]`

**Round 2 — Targeted Research**
- The conditional edge sees `score=61 < 70` and `iteration=1 < 3`, so it routes back to the Researcher
- Researcher receives the suggested queries and performs targeted searches
- Categorizer merges the new fields into the existing competitor records (fill-gaps strategy)
- Evaluator re-scores: `score=78, passed=True`
- Orchestrator finalizes and returns the full state to the dashboard

**Round 3 (Safety valve)**
- If after 3 iterations the score is still below 70, the system finalizes anyway with a low-confidence warning displayed in the dashboard

### 3.2 Decision Logic

The orchestration is a LangGraph `StateGraph`. Each agent is a node; the retry decision is a **conditional edge** off the Evaluator. The graph itself encodes the agentic logic — there is no `while` loop hiding the control flow.

```python
graph = StateGraph(AgentState)

graph.add_node("researcher",   researcher_node)
graph.add_node("categorizer",  categorizer_node)
graph.add_node("analyst",      analyst_node)
graph.add_node("evaluator",    evaluator_node)
graph.add_node("format_report", format_report_node)

graph.add_edge("researcher",  "categorizer")
graph.add_edge("categorizer", "analyst")
graph.add_edge("analyst",     "evaluator")

graph.add_conditional_edges(
    "evaluator",
    route_after_evaluation,   # checks score vs threshold
    {
        "retry":    "researcher",    # loop back with targeted queries
        "finalize": "format_report", # output final report
    }
)
graph.set_entry_point("researcher")
app = graph.compile()
```

`route_after_evaluation(state)` returns `"finalize"` when `score >= EVALUATION_THRESHOLD` or when `iteration >= MAX_ITERATIONS` (the safety valve), and returns `"retry"` otherwise.

### 3.3 Why This Is Agentic

The system demonstrates agentic behavior through:

- **Task decomposition** — research, evaluation, and decision-making are handled by separate specialized components
- **State-based decision making** — the orchestrator decides what to do next based on the current state, not a fixed script
- **Iterative refinement** — the Evaluator's feedback directly shapes the Researcher's next query, creating a genuine improvement loop
- **Self-evaluation** — the system judges its own output quality and acts on that judgment without human intervention

---

## 4. Key Results and Observations

### 4.1 System Behavior

During testing across 5 companies and industries, the system demonstrated
consistent behavior, including one run that exercised the retry loop end-to-end:

| Company    | Industry      | Score      | Result | Iterations |
|------------|---------------|------------|--------|------------|
| Stripe     | Fintech       | 61 → 78    | PASS   | 2          |
| Contextral | AI            | 85         | PASS   | 1          |
| Staytus    | Immigration   | 85         | PASS   | 1          |
| Google     | Search Engine | 75         | PASS   | 1          |
| Canva      | Software      | 72         | PASS   | 1          |

The Stripe run is the most informative case: round 1 scored `61/100` (gaps in Adyen pricing and hiring signals), the conditional edge routed back to the Researcher with targeted queries, and round 2 scored `78/100` and finalized. The other four runs cleared the threshold on the first iteration. Average final score: 79/100.

### 4.2 Evaluation Feedback Loop

The most effective aspect of the system was the Evaluator's ability to generate specific, actionable queries rather than generic ones. For example, rather than suggesting "find more information," it returned queries like "Adyen pricing tiers 2024" or "Square engineering hiring signals" — directly targeted at the identified gaps.

### 4.3 Limitations

- **Model availability:** The Researcher and Evaluator both depend on Gemini model availability. Quota limits or model deprecation can cause failures, which the system handles by falling back to default error states.
- **JSON parsing fragility:** Gemini occasionally returns malformed JSON with markdown fences or extra text. The current parser strips these but edge cases can still cause parse failures.
- **No persistent memory:** Each run starts fresh. There is no caching of previously researched companies, so repeated queries incur the same API cost.
- **Single Gemini family:** All four agents share the same model family (`gemini-2.5-flash-lite`). Diverse model selection per agent (e.g. a stronger model for the Evaluator) could improve scoring rigor, but was out of scope for this term.

---

## 5. Team Contributions

| Team Member | Responsibilities |
|-------------|-----------------|
| Harsh | Project setup, GitHub repo, config.py, smoke tests, README, Phase 0 infrastructure |
| Rayansh | Researcher agent, Evaluator agent, Orchestrator loop, main.py, end-to-end integration |
| Shippy | Streamlit dashboard (ui/app.py), UI design, Phase 4 polish, report.md |

---

## 6. Conclusion

This project successfully demonstrates a multi-agent agentic AI system with a genuine iterative feedback loop. The Evaluator's ability to score its own data quality and generate targeted improvement queries — which the Researcher then acts on — is the core agentic behavior that distinguishes this system from a simple API wrapper. The Streamlit dashboard makes the system accessible and shows the pipeline's progress and outputs in a clear, structured way.
