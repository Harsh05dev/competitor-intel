# Project Specification & System Design Document

## AI-Powered Competitor Intelligence Dashboard

**Team:** Harsh, Rayansh, Shippy
**Course:** Agentic AI — Track 2 Project
**Timeline:** 3 Weeks
**Budget:** $0 target, $10 absolute max
**Version:** 2.0 (Finalized)

---

## Table of Contents

1. Problem Statement
2. Solution Overview
3. Decisions Log (Why We Chose What We Chose)
4. Features (MVP)
5. User Flow
6. System Architecture
7. Agent Design & Prompt Specifications
8. LangGraph Orchestrator Design
9. Data Flow & Schemas
10. Tech Stack
11. APIs & Tools Used
12. Learning Plan
13. Day-by-Day Implementation Schedule
14. Task List (Unassigned — Team Assigns Internally)
15. How This Meets Every Grading Criterion
16. Demo Strategy
17. Risks & Limitations
18. Repository Structure

---

## 1. Problem Statement

Competitive analysis is one of the most common and most tedious tasks in business. Founders, product managers, and sales teams spend 4-8 hours manually researching competitors: Googling company names, reading pricing pages, checking Crunchbase for funding, scanning job boards for hiring signals, and assembling findings in a messy spreadsheet.

Three core problems:

- **Slow.** A thorough analysis takes hours of manual work per company.
- **Incomplete.** Humans forget sources, miss competitors, skip categories.
- **Stale.** The report is outdated the moment it's finished.

Enterprise tools (Crayon at $25K/year, Klue at $30K/year) exist but are inaccessible to startups and students.

**Our goal:** Build a multi-agent AI system that takes a company name + industry as input and produces a complete, quality-controlled competitive intelligence report — automatically, with iterative self-improvement, for $0 in API costs.

---

## 2. Solution Overview

A 4-agent system orchestrated by a LangGraph StateGraph with a conditional feedback loop. The system demonstrates genuine agentic behavior:

- **Task decomposition** — 4 specialized agents, each handling a distinct subtask
- **State-based decision making** — LangGraph conditional edges route the workflow based on evaluation scores
- **Iterative refinement** — Evaluator agent scores output and sends targeted gaps back for re-research
- **Typed data contracts** — agents communicate through structured schemas

**What makes it agentic (not just a pipeline):** The Evaluator is an independent quality gate. When it scores the output below 75/100, the graph routes back to the Researcher with specific gap-filling queries. The system loops until quality passes or max retries (3) are exhausted.

---

## 3. Decisions Log

These are the key decisions made during planning, with rationale for each. This section exists so any team member (or the prof) can understand WHY we made each choice.

| Decision | Choice | Why |
|----------|--------|-----|
| Framework | LangGraph for orchestration, raw SDK calls for agents | Prof's resources emphasize LangGraph. Hybrid approach shows we learned LangGraph while keeping agent code simple. |
| LLM Model | Gemini 2.0 Flash (free tier) | Fastest, most generous free tier, reliable JSON output. Supports ~180 calls needed for testing without hitting limits. |
| Web Search | Google Search Grounding (built into Gemini API) | Free, no separate API key, integrated into the same SDK. This alone saves the entire $10 budget vs paid alternatives. |
| Paid API Fallback | Claude/GPT only if Gemini fails at a specific task | Budget protection. Free first, paid only as last resort. |
| Agent Count | 4 agents (Researcher, Categorizer, Analyst, Evaluator) | Reporter dropped — formatting is a presentation concern handled by the Orchestrator. 4 agents where each is genuinely necessary beats 5 where one is padding. |
| Why no Reporter agent | Formatting moved to Orchestrator | "We chose not to create a separate Reporter agent because report formatting is a presentation concern, not a reasoning task. Our Orchestrator handles the final output template, keeping agent count focused on agents that actually reason." |
| Why Evaluator is separate | Independent quality gate | If the agent that writes the SWOT also grades it, the feedback loop loses credibility. Independent evaluation is what makes the system agentic. |
| Frontend | Streamlit | Team has tutorial-level React experience. Streamlit builds in hours vs days. Prof grades agentic design, not frontend polish. |
| Dashboard features | Progress bar + status text (no live graph visualization) | 80% of demo impact with 20% of effort. Agent logs in expandable section for detail. |
| PDF export | Simple — markdown dumped to basic PDF | Fancy styling is post-class startup work. Class submission just needs readable output. |
| Input | Company name + industry | Industry prevents ambiguity ("Mercury" — fintech or car brand?). Simple enough for a powerful live demo. |
| Output | Streamlit dashboard + downloadable PDF report | Dashboard for the live demo, PDF as a tangible deliverable. |
| Budget target | $0 (Gemini free tier for everything) | $10 max only if Gemini fails and we need Claude/GPT fallback. |

---

## 4. Features (MVP)

**Input:**
- Company name (required)
- Industry (required)

**Processing:**
- Automatically identify top 4-5 competitors via Google Search Grounding
- Gather and structure data per competitor: pricing, features, funding, hiring signals, news, sentiment
- Generate SWOT analysis and competitor comparison matrix
- Score report quality (0-100) on 7 weighted criteria
- Automatically re-research specific gaps when score < 75
- Cap iterations at 3 with graceful degradation
- Track iteration count and score progression

**Output:**
- Streamlit dashboard with:
  - Score card (confidence score, iterations used, competitors found)
  - Progress bar with status text during execution
  - Tabbed report: Executive Summary | SWOT | Comparison | Recommendations
  - Expandable agent logs section
  - Score progression display (if multiple iterations)
- Downloadable PDF report (simple markdown-to-PDF conversion)

**NOT in scope for class submission:**
- User accounts or authentication
- Historical tracking or diffing
- CRM integration
- Fancy PDF styling
- React/Vercel frontend
- Real-time monitoring or alerts

---

## 5. User Flow

```
1. User opens Streamlit app (streamlit run app.py)
2. User enters company name: "Stripe" and industry: "Payment Processing"
3. User clicks "Analyze"
4. Dashboard shows progress:
   → "Researching competitors in Payment Processing..."
   → "Structuring competitor data..."
   → "Generating SWOT analysis..."
   → "Evaluating quality... Score: 62/100 — Needs improvement"
   → "Re-researching 3 specific gaps..."
   → "Re-evaluating... Score: 83/100 — Passed!"
   → "Formatting final report..."
5. Dashboard displays:
   → Score cards at the top
   → Tabbed report sections
   → "Download PDF" button
   → Expandable agent execution logs
```

---

## 6. System Architecture

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     STREAMLIT UI (app.py)                       │
│   [Company Name] [Industry] [Analyze Button]                   │
│   [Progress Bar + Status]                                      │
│   [Score Cards] [Tabbed Report] [Download PDF] [Agent Logs]    │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│              LANGGRAPH ORCHESTRATOR (orchestrator.py)           │
│                                                                │
│   StateGraph with 4 nodes + conditional edges                  │
│                                                                │
│   ┌────────────┐    ┌─────────────┐    ┌──────────┐           │
│   │ RESEARCHER │───→│ CATEGORIZER │───→│ ANALYST  │           │
│   │  (node 1)  │    │  (node 2)   │    │ (node 3) │           │
│   └────────────┘    └─────────────┘    └────┬─────┘           │
│         ▲                                    │                 │
│         │                                    ▼                 │
│         │                              ┌───────────┐           │
│         │        CONDITIONAL           │ EVALUATOR │           │
│         │        EDGE                  │ (node 4)  │           │
│         │                              └─────┬─────┘           │
│         │                                    │                 │
│         │         score < 75                 │  score >= 75    │
│         └──── AND iter < 3 ─────────────────┤                 │
│                                              │                 │
│                                              ▼                 │
│                                     [ Format + END ]           │
│                                                                │
│   Safety valve: if iteration == 3, proceed with low-confidence │
│   warning regardless of score                                  │
└────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐┌────────────┐┌──────────┐┌──────────────┐
│  Gemini API  ││ Gemini API ││Gemini API││  Gemini API  │
│  + Google    ││  (no       ││(no       ││  (no         │
│  Search      ││  search)   ││search)   ││  search)     │
│  Grounding   ││            ││          ││              │
│              ││            ││          ││              │
│  RESEARCHER  ││CATEGORIZER ││ ANALYST  ││  EVALUATOR   │
└──────────────┘└────────────┘└──────────┘└──────────────┘
```

### Component Responsibilities

| Component | Role | Uses Web Search? |
|-----------|------|-----------------|
| Orchestrator | LangGraph StateGraph — defines nodes, edges, conditional routing, state management | No |
| Researcher | Find competitors + gather raw data (pricing, features, funding, hiring, news, sentiment) | YES — Google Search Grounding |
| Categorizer | Transform noisy raw snippets into clean structured JSON per competitor | No |
| Analyst | Synthesize structured data into SWOT analysis + comparison matrix + threat ranking + opportunity gaps | No |
| Evaluator | Score output 0-100 on 7 weighted criteria, identify specific gaps, generate targeted re-search queries | No |

### Why Each Agent is Necessary (Remove-and-Break Test)

- **Remove Researcher** → no data, nothing works
- **Remove Categorizer** → Analyst gets raw messy text, SWOT quality drops drastically. Especially important with free-tier Gemini whose search output can be noisy.
- **Remove Analyst** → organized data but no strategic insights, no SWOT, no threat ranking
- **Remove Evaluator** → no quality control, no feedback loop, system becomes a dumb pipeline (this is what makes it agentic)

---

## 7. Agent Design & Prompt Specifications

### Agent 1: Researcher

**Purpose:** Discover competitors and gather raw intelligence.

**Round 1 (broad):** Given company name + industry, identify 4-5 competitors and search for data on each.

**Round 2+ (targeted):** Given specific queries from Evaluator, search ONLY for those gaps. Does not redo broad research.

**LLM:** Gemini 2.0 Flash with Google Search Grounding enabled.

**System prompt:**
```
You are a competitive intelligence researcher. Your job is to find detailed,
current information about companies and their competitors.

When given a company name and industry, you will:
1. Identify the top 4-5 competitors in the same market
2. For each competitor, gather: pricing details, key product features,
   recent funding/acquisitions, job postings or hiring signals, recent news,
   and customer sentiment.

When given specific follow-up queries (to fill gaps from a previous round),
focus narrowly on finding that exact information. Do not redo broad research.

ALWAYS respond with a JSON object in this exact format:
{
    "target_company": "the company being analyzed",
    "industry": "the industry",
    "competitors_found": [
        {
            "company_name": "Competitor A",
            "raw_snippets": ["snippet 1 from search", "snippet 2", ...],
            "sources": ["url1", "url2", ...]
        }
    ]
}

Return ONLY the JSON object, no other text.
```

---

### Agent 2: Categorizer

**Purpose:** Transform noisy raw snippets into clean structured JSON. Exists separately because Gemini's search results can be inconsistent — isolating the structuring step improves data quality.

**Merge behavior (Round 2+):** New data fills null/empty fields from previous rounds. Lists are combined and deduplicated. Existing data is NEVER overwritten.

**LLM:** Gemini 2.0 Flash (no web search).

**System prompt:**
```
You are a data structuring specialist. You receive raw research snippets
about companies and organize them into clean, structured categories.

You MUST respond with ONLY a JSON object in this exact format:
{
    "categorized_competitors": [
        {
            "company_name": "Company A",
            "pricing": "Description of pricing model with specific prices if available",
            "key_features": ["feature 1", "feature 2", "feature 3"],
            "target_audience": "Who they sell to",
            "funding": "Funding stage, amount raised, valuation if known",
            "hiring_signals": ["signal 1 e.g. '50 open engineering roles'"],
            "recent_news": ["news item 1", "news item 2"],
            "customer_sentiment": "Overall sentiment from reviews/forums"
        }
    ]
}

Rules:
- If information is not available for a field, set it to null (strings) or [] (lists)
- Do NOT invent data. Only use what is in the provided snippets.
- Extract specific numbers, dates, and details — not vague summaries.
- Return ONLY the JSON, no other text.
```

---

### Agent 3: Analyst

**Purpose:** Synthesize structured data into strategic insights.

**LLM:** Gemini 2.0 Flash (no web search).

**System prompt:**
```
You are a strategic competitive analyst. Given structured data about a
company's competitors, you produce high-quality strategic analysis.

You MUST respond with ONLY a JSON object in this exact format:
{
    "swot": {
        "strengths": ["strength 1 — with specific evidence", ...],
        "weaknesses": ["weakness 1 — with specific evidence", ...],
        "opportunities": ["opportunity 1", ...],
        "threats": ["threat 1", ...]
    },
    "comparison_matrix": [
        {
            "company_name": "Competitor A",
            "pricing_tier": "Free / Freemium / Mid-range / Premium / Enterprise",
            "primary_strength": "Their single biggest advantage",
            "primary_weakness": "Their single biggest weakness",
            "target_market": "Who they primarily sell to",
            "threat_level": "Low / Medium / High"
        }
    ],
    "threat_ranking": ["Most threatening competitor first", "Second", ...],
    "opportunity_gaps": [
        "Gap 1: Something no competitor does well that target could exploit",
        "Gap 2: ..."
    ]
}

Rules:
- Each SWOT quadrant must have AT LEAST 2 points, ideally 3-4
- Back every claim with evidence from the data
- Threat ranking ordered from most to least threatening
- Opportunity gaps must be specific and actionable
- Return ONLY the JSON, no other text.
```

---

### Agent 4: Evaluator

**Purpose:** Independent quality gate. Scores output, identifies gaps, generates targeted search queries for re-research. This agent is what makes the system agentic.

**LLM:** Gemini 2.0 Flash (no web search).

**Scoring rubric (7 criteria, weights sum to 100):**

| Criterion | Weight | Score 10 | Score 5 | Score 0 |
|-----------|--------|----------|---------|---------|
| competitor_count | 10% | 4+ found | 2-3 found | 0-1 found |
| pricing_coverage | 20% | All have specific pricing | Half have pricing | None have pricing |
| feature_coverage | 20% | All have 3+ features | All have 1-2 | No features listed |
| funding_data | 10% | All have funding info | Half have it | None |
| hiring_signals | 10% | All have hiring data | Half | None |
| swot_depth | 20% | 3+ points per quadrant with evidence | 2 per quadrant | Less than 2 |
| recency | 10% | Data from last 12 months | Mixed recency | Clearly outdated |

**System prompt:**
```
You are a quality evaluator for competitive intelligence reports.
You assess completeness and quality, then identify specific gaps.

You MUST respond with ONLY a JSON object in this exact format:
{
    "breakdown": {
        "competitor_count": {"score": 0-10, "notes": "explanation"},
        "pricing_coverage": {"score": 0-10, "notes": "which competitors have/lack pricing"},
        "feature_coverage": {"score": 0-10, "notes": "explanation"},
        "funding_data": {"score": 0-10, "notes": "explanation"},
        "hiring_signals": {"score": 0-10, "notes": "explanation"},
        "swot_depth": {"score": 0-10, "notes": "explanation"},
        "recency": {"score": 0-10, "notes": "explanation"}
    },
    "gaps": [
        "Specific gap description 1",
        "Specific gap description 2"
    ],
    "suggested_queries": [
        "Exact search query to fill gap 1",
        "Exact search query to fill gap 2"
    ]
}

Scoring guide (each criterion 0-10):
- competitor_count: 10 if >=4 found, 7 if 3, 4 if 2, 2 if 1
- pricing_coverage: 10 if all have specific pricing, deduct 2-3 per missing
- feature_coverage: 10 if all have 3+ features, deduct per sparse
- funding_data: 10 if all have funding info, deduct per missing
- hiring_signals: 10 if all have hiring data, deduct per missing
- swot_depth: 10 if 3+ points per quadrant with evidence, 7 if 2+ each
- recency: 10 if current (last 12 months), lower if outdated

Be STRICT. Only give 8+ if genuinely strong.
suggested_queries should be specific web searches that would fill the gaps.
Return ONLY the JSON, no other text.
```

---

## 8. LangGraph Orchestrator Design

This is the core agentic component. The Orchestrator is a LangGraph StateGraph, NOT a while loop with if/else statements.

### State Definition

```python
class AgentState(TypedDict):
    target_company: str
    industry: str
    iteration: int
    research_results: list[dict]
    categorized_competitors: list[dict]
    analysis: dict
    evaluation: dict
    final_output: str
    status: str
    logs: list[str]
```

### Graph Structure

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)

# Add nodes (each is a Python function that takes state, returns updated state)
graph.add_node("researcher", researcher_node)
graph.add_node("categorizer", categorizer_node)
graph.add_node("analyst", analyst_node)
graph.add_node("evaluator", evaluator_node)
graph.add_node("format_report", format_report_node)

# Add fixed edges (always flow forward)
graph.add_edge("researcher", "categorizer")
graph.add_edge("categorizer", "analyst")
graph.add_edge("analyst", "evaluator")

# THE CONDITIONAL EDGE — this is what makes it agentic
graph.add_conditional_edges(
    "evaluator",
    route_after_evaluation,   # function that checks score + iteration
    {
        "retry": "researcher",       # loop back if score < 75 and iter < 3
        "finalize": "format_report", # proceed if passed or max iterations
    }
)

graph.add_edge("format_report", END)
graph.set_entry_point("researcher")

app = graph.compile()
```

### Routing Function

```python
def route_after_evaluation(state: AgentState) -> str:
    score = state["evaluation"].get("score", 0)
    iteration = state["iteration"]

    if score >= 75:
        return "finalize"    # quality passed
    elif iteration >= 3:
        return "finalize"    # max retries, proceed with warning
    else:
        return "retry"       # loop back for targeted re-research
```

### What Each Node Function Does

Each node is a plain Python function that:
1. Reads from `state`
2. Calls Gemini 2.0 Flash with the agent's system prompt
3. Parses the JSON response
4. Returns updated state

```python
def researcher_node(state: AgentState) -> dict:
    # If first iteration: broad research
    # If iteration 2+: targeted research using state["evaluation"]["suggested_queries"]
    # Calls Gemini with Google Search Grounding
    # Returns {"research_results": [...], "iteration": state["iteration"] + 1}

def categorizer_node(state: AgentState) -> dict:
    # Takes state["research_results"]
    # Structures into JSON
    # If iteration 2+: merges with existing state["categorized_competitors"]
    # Returns {"categorized_competitors": [...]}

def analyst_node(state: AgentState) -> dict:
    # Takes state["categorized_competitors"]
    # Generates SWOT + comparison matrix
    # Returns {"analysis": {...}}

def evaluator_node(state: AgentState) -> dict:
    # Takes state["categorized_competitors"] + state["analysis"]
    # Scores on rubric, identifies gaps
    # Returns {"evaluation": {"score": int, "gaps": [...], "suggested_queries": [...]}}

def format_report_node(state: AgentState) -> dict:
    # Takes all state data
    # Formats into final markdown sections
    # Returns {"final_output": "formatted report string", "status": "complete"}
```

---

## 9. Data Flow & Schemas

### Data Transformation Pipeline

```
INPUT: {"target_company": "Stripe", "industry": "Payment Processing"}
    │
    ▼
STAGE 1 — Researcher
    Output: [{ company_name, raw_snippets: str[], sources: str[] }]
    Shape: Raw, noisy text snippets from web search
    │
    ▼
STAGE 2 — Categorizer
    Output: [{ company_name, pricing, key_features[], target_audience,
               funding, hiring_signals[], recent_news[], customer_sentiment }]
    Shape: Clean, structured JSON per competitor
    │
    ▼
STAGE 3 — Analyst
    Output: { swot: {S,W,O,T}, comparison_matrix[], threat_ranking[], opportunity_gaps[] }
    Shape: Strategic synthesis
    │
    ▼
STAGE 4 — Evaluator
    Output: { score: int, passed: bool, breakdown: {}, gaps: str[], suggested_queries: str[] }
    Shape: Quality assessment
    │
    ├── IF NOT PASSED: suggested_queries fed back to Stage 1 ──▲
    │
    └── IF PASSED: all state fed into format_report_node
                    │
                    ▼
                  OUTPUT: Formatted markdown report + PDF
```

### Merge Strategy for Iterations

When Round 2+ produces new categorized data:

1. Match new data to existing competitors by name (case-insensitive)
2. String fields (pricing, funding): fill ONLY if existing value is null/empty
3. List fields (features, news): combine both lists, deduplicate
4. New competitors found in re-research are appended
5. Existing data is NEVER overwritten

This prevents iteration from destroying earlier findings.

---

## 10. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Language | Python 3.11+ | Team familiarity, best LLM library support |
| LLM | Gemini 2.0 Flash (free tier) | Fast, generous limits, reliable JSON output |
| Web Search | Google Search Grounding (Gemini API) | Free, integrated, no separate key |
| Orchestration | LangGraph | Prof's course resources teach it, conditional edges show agentic design |
| Agent Framework | Raw google-genai SDK | Simple function calls, no unnecessary abstraction |
| Frontend | Streamlit | Zero frontend expertise needed, fast to build |
| PDF Export | markdown → PDF (e.g., fpdf2 or md2pdf) | Simple, no styling overhead |
| Version Control | GitHub with branches per person | Prevents merge conflicts during parallel work |
| Fallback LLM | Claude API (paid, $10 max budget) | Only if Gemini fails at a specific task |

### Cost Breakdown

| Component | Cost |
|-----------|------|
| Gemini 2.0 Flash API | $0 (free tier) |
| Google Search Grounding | $0 (included with Gemini) |
| LangGraph | $0 (open source) |
| Streamlit | $0 (open source) |
| Claude API fallback | $0-10 (only if needed) |
| **Total** | **$0 target, $10 max** |

---

## 11. APIs & Tools Used

| API/Tool | Purpose | Used By | Cost |
|----------|---------|---------|------|
| Gemini 2.0 Flash (`gemini-2.0-flash`) | LLM for all 4 agents | All agents | Free |
| Google Search Grounding | Real-time web search | Researcher only | Free |
| LangGraph | Orchestration graph with conditional edges | Orchestrator | Free |
| google-genai Python SDK | Gemini API calls | All agents | Free |
| Streamlit | Dashboard UI | app.py | Free |
| fpdf2 or md2pdf | PDF generation | Report export | Free |

### API Call Estimate

| Phase | Calls per Analysis | Analyses | Total Calls |
|-------|-------------------|----------|-------------|
| Per iteration | 4 (one per agent) | — | — |
| Per analysis (avg 2 iterations) | 8 | — | — |
| Testing phase | — | 15 | ~120 |
| Demo | — | 3 | ~24 |
| **Total** | — | — | **~144 calls** |

Gemini 2.0 Flash free tier: 15 RPM, 1500 RPD. 144 total calls is well within limits even spread across 2-3 days of testing.

---

## 12. Learning Plan

### Required Resources (Complete Before Building)

| Priority | Resource | Time | What You Learn |
|----------|----------|------|---------------|
| 1 | "Building Effective Agents with LangGraph" (YouTube) | 2-3 hrs | LangGraph nodes, edges, conditional edges, StateGraph pattern |
| 2 | "Agentic AI with LangChain and LangGraph" (Coursera/IBM) | 6-8 hrs | Deep LangGraph knowledge, state management, agent patterns |
| 3 | "Fundamentals of Building AI Agents" (Coursera/IBM) | 3-4 hrs | Agent vocabulary, design patterns (skim if short on time) |
| — | "Prompt Engineering Tutorial" (YouTube) | 2 hrs | Prompt design for structured output (watch during build phase if needed) |
| — | "Build AI Agents using MCP" (Optional) | Skip | Not needed for this project |

### What to Focus On While Learning

When watching LangGraph content, pay specific attention to:

- How `StateGraph` is defined with `TypedDict`
- How `add_node()` registers a Python function as a graph node
- How `add_conditional_edges()` works — THIS IS YOUR FEEDBACK LOOP
- How state is passed between nodes and updated
- How `graph.compile()` turns the graph into a runnable app

You do NOT need to learn:
- LangChain agents (you're using raw Gemini SDK)
- LangChain prompt templates (you're using plain strings)
- LangChain memory (your state is in the LangGraph StateGraph)
- Tool calling via LangChain (you're using Gemini's native Google Search)

---

## 13. Day-by-Day Implementation Schedule

### WEEK 1: Learn (Days 1-7)

| Day | Activity | Who | Output |
|-----|----------|-----|--------|
| Day 1 | Watch "Building Effective Agents with LangGraph" YouTube video | All 3 together | Shared understanding of nodes, edges, conditional edges |
| Day 2 | Start Coursera "Agentic AI with LangChain and LangGraph" | All 3 individually | Complete Module 1 |
| Day 3 | Continue Coursera course | All 3 individually | Complete Module 2 |
| Day 4 | Continue Coursera course | All 3 individually | Complete Module 3+ |
| Day 5 | Finish Coursera course + experiment | All 3 individually | Build a tiny 2-node LangGraph as practice |
| Day 6 | Team sync: review spec, assign tasks, set up GitHub repo | All 3 together | Repo created, branches set up, tasks assigned |
| Day 7 | Set up dev environment: install LangGraph, google-genai, Streamlit. Get a Gemini API key. Test a basic Gemini call with Google Search Grounding. | All 3 together | Everyone has a working dev environment, one successful API call each |

### WEEK 2: Build Core (Days 8-14)

| Day | Activity | Deliverable |
|-----|----------|-------------|
| Day 8 | Build project skeleton: config.py, schemas, base agent class, empty agent files | Running project that imports everything without errors |
| Day 9 | Build Researcher agent: Gemini + Google Search Grounding, test with "Stripe" | Researcher returns structured JSON with 4+ competitors |
| Day 10 | Build Categorizer agent: test with Researcher's real output | Categorizer takes raw snippets, returns clean structured JSON |
| Day 11 | Build Analyst agent: test with Categorizer's real output | Analyst produces SWOT with 2+ points per quadrant |
| Day 12 | Build Evaluator agent: test with intentionally incomplete data | Evaluator scores < 75 on bad data, identifies correct gaps, generates search queries |
| Day 13 | Build LangGraph Orchestrator: wire all 4 agents as nodes, add conditional edge | End-to-end run: company name → full analysis with feedback loop |
| Day 14 | Integration testing: run 3 different companies, fix bugs, handle edge cases | System works reliably for "Stripe", "Notion", and "Figma" |

### WEEK 3: Polish + Submit (Days 15-21)

| Day | Activity | Deliverable |
|-----|----------|-------------|
| Day 15 | Build Streamlit dashboard: input form, progress bar, status text | Basic working dashboard that runs the orchestrator |
| Day 16 | Dashboard continued: add tabs (Executive Summary, SWOT, Comparison, Recommendations), score cards, agent logs section | Full dashboard with all display sections |
| Day 17 | Add PDF export: markdown-to-PDF conversion, download button | "Download PDF" button works in Streamlit |
| Day 18 | Testing marathon: run 5+ companies, capture results, screenshots | Collection of results for the report |
| Day 19 | Write report.md: problem statement, system design, workflow, results | Complete written report ready to submit |
| Day 20 | Prepare demo: pick the best company example that triggers a retry loop, practice presentation, record backup video | Demo script ready, backup recording done |
| Day 21 | Final code cleanup, push to main branch, submit | Everything submitted |

### Buffer Strategy

Days 14 and 18 have built-in slack. If you fall behind in Week 2, you have Day 14 to catch up. If integration takes longer, Day 18 absorbs it. Do NOT skip the backup demo recording on Day 20 — if the API is slow during your presentation, you'll need it.

---

## 14. Task List (Unassigned)

See the separate **TASK_CHECKLIST.md** for the full assignable checklist with checkboxes.

---

## 15. How This Meets Every Grading Criterion

### Criterion 1: Depth of Agentic Design

**"Clear evidence of multi-step reasoning"**
- 4 sequential agents, each performing distinct reasoning
- System cannot produce output by skipping any step (Remove-and-Break test passes)

**"Meaningful interaction between components"**
- Each agent transforms data into a different shape (raw text → structured JSON → strategic objects → numeric scores)
- Agents don't just pass the same string around
- The Evaluator's suggested_queries directly control what the Researcher searches for in the next round

**How to prove it in demo:** Run with Evaluator disabled → show incomplete output. Enable it → show refined output. Side-by-side comparison.

### Criterion 2: Workflow Quality

**"Logical structure and flow"**
- Two flow patterns: linear (happy path) and feedback loop (agentic path)
- Implemented as a LangGraph StateGraph with conditional edges — not a hidden while loop
- Safety valve: max 3 iterations prevents infinite loops

**"Appropriate use of iteration"**
- Evaluator says EXACTLY what's missing (not "try again")
- Researcher only searches for SPECIFIC gaps (not full broad research)
- Categorizer MERGES new data (doesn't overwrite)
- Each iteration is cheaper and faster than the last
- Termination condition: score threshold + max retries

### Criterion 3: Implementation

**"Functional and well-organized code"**
- One file per agent, all following the same interface pattern
- Typed schemas define contracts between agents
- Config separated from logic
- LangGraph graph structure is self-documenting

**"Clear separation of components"**
- Orchestrator knows about agents; agents don't know about each other
- Each agent: takes state in, returns state updates out
- Independently testable: feed sample input to any agent, check output

### Criterion 4: Clarity of Explanation

**Key sentences for the report and presentation:**

> "We used LangGraph StateGraph to implement our orchestrator because the conditional edge pattern directly maps to our feedback loop — the graph literally decides whether to retry or finalize based on the Evaluator's score."

> "We chose not to create a separate Reporter agent because report formatting is a presentation concern, not a reasoning task. Our Orchestrator handles the final output template, keeping agent count focused on agents that actually reason."

> "We set the evaluation threshold at 75 rather than 100 because competitive intelligence is inherently incomplete. Requiring perfection would cause infinite loops. The 75 threshold balances completeness with practical convergence — in our testing, most queries converge within 2 iterations."

> "The Evaluator is independent from the Analyst for the same reason a code reviewer shouldn't review their own code. If the same agent writes and grades the SWOT, the feedback loop has no credibility."

---

## 16. Demo Strategy

### The Script

1. Open Streamlit dashboard
2. Type "Stripe" + "Payment Processing"
3. Click Analyze
4. Narrate the progress bar: "Watch — it's researching competitors now..."
5. **THE MONEY SHOT:** "Notice the Evaluator scored this 64. It found 3 gaps. Now watch the system go back for targeted research... and the score jumped to 83. That's the agentic feedback loop in action."
6. Show the tabbed report
7. Click Download PDF
8. Open the Agent Logs tab: "Here you can see every step — which agent ran, what it produced, why the Evaluator failed the first round"

### Backup Plan

| Scenario | Action |
|----------|--------|
| API is slow | Play the backup video recorded on Day 20 |
| Score passes first try (no retry) | Lower threshold to 90 in sidebar before demo to force a retry |
| JSON parsing breaks | Show the log where error handling catches it — demonstrates robustness |
| Someone asks "why not 5 agents?" | Explain the Reporter removal decision (see Decisions Log) |

---

## 17. Risks & Limitations

### Technical Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Gemini free tier rate limits during testing marathon | Medium | Spread testing across multiple days, use Day 14 buffer |
| JSON parsing failures from Gemini | Medium | Fallback parser: strip markdown fences, find braces, graceful degradation |
| Google Search Grounding returns low-quality results | Medium | Evaluator catches gaps, targeted re-research fills them |
| LangGraph learning curve slows Week 2 | Medium | Day 7 practice session, start with skeleton code |
| Slow API during live demo | High | Pre-recorded backup demo |
| Merge conflicts on GitHub | Low | Branches per person, merge to main only when tested |

### Inherent Limitations

- **Public data only.** Private companies with minimal web presence produce lower-quality reports.
- **Completeness not accuracy.** Evaluator checks coverage, not factual accuracy. A future fact-checking agent could address this.
- **English only.** Prompts and search are English-focused. International competitors may be underrepresented.
- **Single snapshot.** No ongoing monitoring. Report reflects data at time of analysis.
- **Free tier constraints.** Gemini 2.0 Flash is strong but not as capable as Claude Opus or GPT-4 at nuanced strategic analysis.

---

## 18. Repository Structure

```
competitor-intel/
│
├── main.py                     # CLI entry point
├── orchestrator.py             # LangGraph StateGraph with conditional edges
├── config.py                   # Settings: thresholds, weights, model config
├── app.py                      # Streamlit dashboard
├── requirements.txt            # langgraph, google-genai, streamlit, fpdf2
├── README.md                   # Setup and run instructions
├── report.md                   # Written deliverable for submission
├── PROJECT_SPEC.md             # This document
├── TASK_CHECKLIST.md           # Assignable task list with checkboxes
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Base class: Gemini call wrapper, JSON parser
│   ├── researcher.py           # Agent 1: web search + data gathering
│   ├── categorizer.py          # Agent 2: raw → structured JSON + merge logic
│   ├── analyst.py              # Agent 3: SWOT + comparisons + threat ranking
│   └── evaluator.py            # Agent 4: scoring + gap detection
│
└── models/
    ├── __init__.py
    └── schemas.py              # Data contracts between agents
```

---

*This document is self-contained. Any engineer, LLM, or team member can read this spec and build the system from scratch without additional context. All decisions are documented with rationale.*
