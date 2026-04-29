# Task Checklist — Competitor Intelligence Dashboard

**Instructions:** Assign each task to one person (Harsh / Rayansh / Shippy). Write your name next to the task. Each task should have exactly one owner.

---

## Phase 0: Learning (Week 1, Days 1-7)

### Shared Learning
- [ ] **OWNER: ___** | Watch "Building Effective Agents with LangGraph" YouTube video and share notes with team
- [ ] **OWNER: ___** | Complete Coursera "Agentic AI with LangChain and LangGraph" (all modules)
- [ ] **OWNER: ___** | Skim Coursera "Fundamentals of Building AI Agents" (optional, for vocabulary)

### Environment Setup (Day 6-7)
- [ ] **OWNER: ___** | Create GitHub repo with branch structure (main + one branch per person)
- [ ] **OWNER: ___** | Write initial requirements.txt (langgraph, google-generativeai, streamlit, fpdf2)
- [ ] **OWNER: ___** | Get Gemini API key and test a basic call (text generation, no search)
- [ ] **OWNER: ___** | Test Gemini with Google Search Grounding enabled (verify search works)
- [ ] **OWNER: ___** | Build a tiny 2-node LangGraph as practice (input → process → output with conditional edge)
- [ ] **OWNER: ___** | Create the project folder structure (all empty files in place)

---

## Phase 1: Foundation (Week 2, Day 8)

### Config & Schemas
- [ ] **OWNER: ___** | Implement `config.py` — model name, API key handling, evaluation threshold (75), max iterations (3), eval weights
- [ ] **OWNER: ___** | Implement `models/schemas.py` — define all data shapes as dataclasses or TypedDicts:
  - ResearchResult (company_name, raw_snippets, sources)
  - CategorizedCompetitor (company_name, pricing, key_features, target_audience, funding, hiring_signals, recent_news, customer_sentiment)
  - AnalysisResult (swot, comparison_matrix, threat_ranking, opportunity_gaps)
  - EvaluationResult (score, passed, breakdown, gaps, suggested_queries)
  - AgentState for LangGraph (target_company, industry, iteration, all intermediate data, logs)

### Base Agent
- [ ] **OWNER: ___** | Implement `agents/base_agent.py`:
  - Gemini API call wrapper (google-genai SDK)
  - Optional Google Search Grounding toggle
  - JSON response parser with fallback (strip markdown fences, find braces)
  - Logging method

---

## Phase 2: Agents (Week 2, Days 9-12)

### Agent 1: Researcher
- [ ] **OWNER: ___** | Implement `agents/researcher.py`:
  - System prompt (from spec)
  - Broad research mode (Round 1): takes company name + industry
  - Targeted research mode (Round 2+): takes suggested_queries from Evaluator
  - Enable Google Search Grounding for this agent only
- [ ] **OWNER: ___** | Test Researcher standalone: input "Stripe" + "Payment Processing" → verify JSON output has 4+ competitors with raw snippets
- [ ] **OWNER: ___** | Test Researcher targeted mode: input 2-3 specific gap queries → verify it returns focused results

### Agent 2: Categorizer
- [ ] **OWNER: ___** | Implement `agents/categorizer.py`:
  - System prompt (from spec)
  - Main structuring function: raw snippets → clean JSON per competitor
  - merge_with_existing() function for iteration rounds (fill nulls, combine lists, deduplicate, never overwrite)
- [ ] **OWNER: ___** | Test Categorizer standalone: feed Researcher's real output → verify clean JSON with all 7 fields per competitor
- [ ] **OWNER: ___** | Test merge function: feed two rounds of data → verify gaps filled without overwriting existing data

### Agent 3: Analyst
- [ ] **OWNER: ___** | Implement `agents/analyst.py`:
  - System prompt (from spec)
  - Takes categorized competitors → produces SWOT + comparison matrix + threat ranking + opportunity gaps
- [ ] **OWNER: ___** | Test Analyst standalone: feed Categorizer's real output → verify SWOT has 2+ points per quadrant
- [ ] **OWNER: ___** | Test edge case: feed sparse data (1-2 competitors, missing fields) → verify it still produces reasonable output

### Agent 4: Evaluator
- [ ] **OWNER: ___** | Implement `agents/evaluator.py`:
  - System prompt (from spec)
  - Scoring function: calculate weighted score from 7 criteria
  - Gap identification + suggested query generation
  - Pass/fail determination (score >= threshold from config)
- [ ] **OWNER: ___** | Test Evaluator with GOOD data: feed complete competitor data + strong SWOT → verify score >= 75
- [ ] **OWNER: ___** | Test Evaluator with BAD data: feed incomplete data (missing pricing, sparse SWOT) → verify score < 75 AND gaps list is accurate AND suggested_queries are specific search terms

---

## Phase 3: Orchestrator (Week 2, Days 13-14)

### LangGraph Integration
- [ ] **OWNER: ___** | Implement `orchestrator.py` — LangGraph StateGraph:
  - Define AgentState TypedDict
  - Add 4 agent nodes + 1 format_report node
  - Add fixed edges: researcher → categorizer → analyst → evaluator
  - Add conditional edge after evaluator: route_after_evaluation function
  - Set entry point to researcher
  - Compile graph
- [ ] **OWNER: ___** | Implement route_after_evaluation function:
  - score >= 75 → "finalize"
  - iteration >= 3 → "finalize" (with low-confidence flag)
  - else → "retry"
- [ ] **OWNER: ___** | Implement format_report_node:
  - Takes all state data
  - Formats into markdown sections (executive summary, SWOT, comparison table, recommendations)
  - No separate LLM call needed — can be template-based or one Gemini call
- [ ] **OWNER: ___** | Implement callback system: orchestrator sends status updates that Streamlit can display
- [ ] **OWNER: ___** | Implement `main.py` CLI entry point for testing without Streamlit

### Integration Testing
- [ ] **OWNER: ___** | End-to-end test #1: "Stripe" + "Payment Processing" → full report
- [ ] **OWNER: ___** | End-to-end test #2: "Notion" + "Productivity Software" → full report
- [ ] **OWNER: ___** | End-to-end test #3: "Figma" + "Design Tools" → full report
- [ ] **OWNER: ___** | Verify feedback loop: find or create a case where Round 1 scores < 75, confirm retry fires and score improves
- [ ] **OWNER: ___** | Test safety valve: set max_iterations=1, verify system outputs with low-confidence warning
- [ ] **OWNER: ___** | Handle edge cases: empty search results, JSON parse failures, API timeouts

---

## Phase 4: Dashboard + PDF (Week 3, Days 15-17)

### Streamlit Dashboard
- [ ] **OWNER: ___** | Implement `app.py` — basic layout:
  - Input form: company name text field + industry text field + "Analyze" button
  - Sidebar: settings (API key, quality threshold slider, max iterations slider)
  - System architecture diagram in sidebar
- [ ] **OWNER: ___** | Add progress display:
  - Progress bar that advances as each agent runs
  - Status text showing current step ("Researching competitors...", "Evaluating quality...")
  - Iteration counter if system retries
- [ ] **OWNER: ___** | Add results display:
  - Score cards row: confidence score, iterations used, competitors found, remaining gaps
  - Tabbed sections: Executive Summary | SWOT Analysis | Comparison Table | Recommendations
  - Score progression display (if multiple iterations)
- [ ] **OWNER: ___** | Add agent logs section:
  - Expandable section showing full execution trace
  - Evaluation breakdown with per-criterion scores and progress bars
- [ ] **OWNER: ___** | Connect dashboard to orchestrator via callback system

### PDF Export
- [ ] **OWNER: ___** | Implement markdown-to-PDF conversion (fpdf2 or md2pdf or similar)
- [ ] **OWNER: ___** | Add "Download PDF" button to Streamlit dashboard
- [ ] **OWNER: ___** | Test PDF output: verify it contains all report sections and is readable

---

## Phase 5: Polish + Report (Week 3, Days 18-20)

### Testing & Results
- [ ] **OWNER: ___** | Run 5+ different companies through the system, record results
- [ ] **OWNER: ___** | Capture at least one run that triggers a retry loop (for demo + report)
- [ ] **OWNER: ___** | Record iteration score progressions (e.g., "Round 1: 62, Round 2: 83")
- [ ] **OWNER: ___** | Take screenshots of dashboard for the report
- [ ] **OWNER: ___** | Note any failures or edge cases for the limitations section

### Written Report
- [ ] **OWNER: ___** | Write report.md — Problem Statement section (half page)
- [ ] **OWNER: ___** | Write report.md — System Design section (1 page + architecture diagram)
- [ ] **OWNER: ___** | Write report.md — Agentic Workflow section (1 page: walkthrough of example with scores per round)
- [ ] **OWNER: ___** | Write report.md — Key Results & Observations section (half page: convergence stats, limitations)
- [ ] **OWNER: ___** | Write report.md — Team Contributions table
- [ ] **OWNER: ___** | Review entire report for consistency and grammar

### Code Cleanup
- [ ] **OWNER: ___** | Add docstrings to all files and functions
- [ ] **OWNER: ___** | Remove debug prints, clean up commented-out code
- [ ] **OWNER: ___** | Update README.md with final setup instructions
- [ ] **OWNER: ___** | Merge all branches to main, verify main branch runs end-to-end

---

## Phase 6: Demo Prep (Week 3, Day 20-21)

### Presentation
- [ ] **OWNER: ___** | Pick the best company example that triggers a retry loop for live demo
- [ ] **OWNER: ___** | Write demo script: what to type, what to narrate at each step
- [ ] **OWNER: ___** | Each person rehearses explaining their components (2 min each)
- [ ] **OWNER: ___** | Record backup demo video (in case API is slow during presentation)
- [ ] **OWNER: ___** | Prepare for "why" questions: why 4 agents? why no Reporter? why threshold 75? why Gemini?

### Final Submission
- [ ] **OWNER: ___** | Final end-to-end test on main branch
- [ ] **OWNER: ___** | Package everything: code + report + README
- [ ] **OWNER: ___** | Submit

---

## Quick Reference: Task Counts

| Phase | Tasks | Estimated Time |
|-------|-------|---------------|
| Phase 0: Learning | 9 tasks | Days 1-7 |
| Phase 1: Foundation | 3 tasks | Day 8 |
| Phase 2: Agents | 13 tasks | Days 9-12 |
| Phase 3: Orchestrator | 11 tasks | Days 13-14 |
| Phase 4: Dashboard + PDF | 8 tasks | Days 15-17 |
| Phase 5: Polish + Report | 11 tasks | Days 18-20 |
| Phase 6: Demo | 7 tasks | Days 20-21 |
| **Total** | **62 tasks** | **21 days** |

Target: ~21 tasks per person (roughly equal split).

---

## Integration Points (Coordinate These!)

These tasks require two or more people to sync up. Flag them early:

| Integration Point | Who Needs to Sync | When |
|-------------------|-------------------|------|
| Agent output format matches schema | Agent builders + Schema owner | Day 9 (before building agents) |
| Orchestrator can call all agents | Orchestrator owner + all agent owners | Day 13 |
| Dashboard callback matches orchestrator events | Dashboard owner + Orchestrator owner | Day 15 |
| Evaluator output displays correctly in dashboard | Evaluator owner + Dashboard owner | Day 16 |
| PDF contains all report sections from format_report_node | PDF owner + Orchestrator owner | Day 17 |
| All branches merged to main | Everyone | Day 20 |

---

*Print this out, write names on it, hang it on your wall. Check off tasks as you go.*
