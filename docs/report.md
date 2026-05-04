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
┌─────────────────────────────────────────────────┐
│               Orchestrator (main.py)             │
│                                                  │
│   ┌────────────┐     ┌─────────────────────┐    │
│   │ Researcher │────▶│    Categorizer*      │    │
│   │  Agent     │     │    (pass-through)    │    │
│   └────────────┘     └──────────┬──────────┘    │
│                                 │                │
│                                 ▼                │
│                       ┌─────────────────┐        │
│                       │   Evaluator     │        │
│                       │   Agent         │        │
│                       └────────┬────────┘        │
│                                │                 │
│              ┌─────────────────┴──────────────┐  │
│              │                                │  │
│         score ≥ 70                      score < 70│
│         OR iter ≥ 3                     iter < 3  │
│              │                                │  │
│              ▼                                ▼  │
│         Finalize                          Retry  │
│         Report                        (targeted  │
│                                        queries)  │
└─────────────────────────────────────────────────┘
        │
        ▼
  Streamlit Dashboard (ui/app.py)
```

### 2.2 Components

**Researcher Agent** (`agents/researcher.py`)  
Queries the Gemini API to find 4 competitors of the target company. On the first iteration it performs broad research. On subsequent iterations it receives specific gap-filling queries from the Evaluator and performs targeted research to fill missing data. Returns structured JSON with company names, raw snippets, and source URLs.

**Evaluator Agent** (`agents/evaluator.py`)  
Takes the collected competitor data and scores it on a 0–100 scale. It identifies specific data gaps (e.g. missing pricing data, sparse feature coverage) and generates targeted search queries to address those gaps. If the score is 70 or above, the pipeline finalizes. Otherwise it loops back to the Researcher.

**Orchestrator** (`main.py`)  
Manages the iterative loop between agents. Maintains the full agent state across iterations, enforces the maximum iteration limit (3), and determines when to finalize the report. Acts as the central controller — no agent communicates directly with another.

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
- Evaluator scores the data — if pricing or feature data is sparse, score may be ~60
- Evaluator returns: `score=62, passed=False, gaps=["missing pricing info for Adyen", "no hiring signals"], suggested_queries=["Adyen pricing 2024", "Square hiring engineering"]`

**Round 2 — Targeted Research**
- Orchestrator sees `passed=False` and `iteration=1 < 3`, so loops back
- Researcher receives the suggested queries and performs targeted searches
- Returns enriched data filling the previously identified gaps
- Evaluator re-scores: `score=81, passed=True`
- Orchestrator finalizes and returns the full state to the dashboard

**Round 3 (Safety valve)**
- If after 3 iterations the score is still below 70, the system finalizes anyway with a low-confidence warning displayed in the dashboard

### 3.2 Decision Logic

```python
def should_continue(state):
    if state["evaluation"].get("passed"):
        return False        # quality threshold met
    if state["iteration"] >= 3:
        return False        # safety valve: max iterations reached
    return True             # loop again with targeted queries
```

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
consistent behavior with a 100% first-iteration pass rate:

| Company    | Industry      | Score | Result | Iterations |
|------------|---------------|-------|--------|------------|
| Stripe     | Fintech       | 78    | PASS   | 1          |
| Contextral | AI            | 85    | PASS   | 1          |
| Staytus    | Immigration   | 85    | PASS   | 1          |
| Google     | Search Engine | 75    | PASS   | 1          |
| Canva      | Software      | 72    | PASS   | 1          |

Average score: 79/100. All runs passed on the first iteration.

### 4.2 Evaluation Feedback Loop

The most effective aspect of the system was the Evaluator's ability to generate specific, actionable queries rather than generic ones. For example, rather than suggesting "find more information," it returned queries like "Adyen pricing tiers 2024" or "Square engineering hiring signals" — directly targeted at the identified gaps.

### 4.3 Limitations

- **Model availability:** The Researcher and Evaluator both depend on Gemini model availability. Quota limits or model deprecation can cause failures, which the system handles by falling back to default error states.
- **JSON parsing fragility:** Gemini occasionally returns malformed JSON with markdown fences or extra text. The current parser strips these but edge cases can still cause parse failures.
- **No persistent memory:** Each run starts fresh. There is no caching of previously researched companies, so repeated queries incur the same API cost.
- **Categorizer stub:** The Categorizer agent is currently a pass-through (raw research results are used directly). A full implementation would add structured field extraction for pricing, features, funding, and sentiment.

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
