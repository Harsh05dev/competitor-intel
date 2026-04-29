# Competitor Intelligence Dashboard (Agentic AI)

Multi-agent system for automated competitor research and analysis, built for a CS 301 Agentic AI project.

Given a target company and industry, the system is designed to produce a quality-controlled competitor intelligence report using a LangGraph workflow with iterative feedback.

## Team

- Harsh
- Rayansh
- Shippy

## Project Goal

Manual competitor research is slow and inconsistent. This project aims to automate it with a structured, agentic pipeline that:

- Finds 4-5 key competitors
- Extracts market signals (pricing, features, funding, hiring, news, sentiment)
- Produces strategic outputs (SWOT, comparison matrix, threat ranking, opportunity gaps)
- Evaluates report quality and loops for targeted re-research when quality is low

## Planned System Design

The target architecture (from `docs/PROJECT_SPEC_V2.md`) uses:

- 4 agents: Researcher, Categorizer, Analyst, Evaluator
- LangGraph `StateGraph` orchestration
- Conditional routing:
  - score >= 75 -> finalize
  - score < 75 and iteration < 3 -> retry targeted research
  - iteration >= 3 -> finalize with low-confidence warning

High-level flow:

1. `researcher` -> gathers raw competitor snippets
2. `categorizer` -> converts raw snippets into structured competitor records
3. `analyst` -> generates SWOT and strategic comparisons
4. `evaluator` -> scores quality and suggests gap-filling queries
5. `format_report` -> compiles final output for dashboard/PDF

## Current Repository Status

This repo currently contains Phase 0 foundation work and placeholders for later phases.

Implemented now:

- `config.py` with model and evaluation settings
- `scratch_langgraph_test.py` (small working 2-node LangGraph practice)
- Smoke tests:
  - `scripts/gemini_basic_test.py`
  - `scripts/gemini_grounding_test.py`
- Project structure for agents/models/orchestrator/app

Not implemented yet (currently empty placeholders):

- `agents/base_agent.py`
- `agents/researcher.py`
- `agents/categorizer.py`
- `agents/analyst.py`
- `agents/evaluator.py`
- `models/schemas.py`
- `orchestrator.py`
- `main.py`
- `app.py`

## Tech Stack

- Python 3.11+
- LangGraph
- Gemini API (`gemini-2.0-flash`)
- Google Search Grounding (via Gemini API)
- Streamlit (planned UI)
- fpdf2 (planned PDF export)

Installed dependencies (see `requirements.txt`):

- `langgraph`
- `google-generativeai`
- `streamlit`
- `fpdf2`
- `python-dotenv`

## Setup

### 1) Clone and enter the repo

```bash
git clone https://github.com/Harsh05dev/competitor-intel.git
cd competitor-intel
```

### 2) Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

Create/update `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

## Run Existing Smoke Tests

### Basic Gemini text test (no grounding)

```bash
python scripts/gemini_basic_test.py
```

Expected behavior:

- Validates `GEMINI_API_KEY`
- Calls Gemini model once
- Prints a one-sentence response

### Gemini test with Google Search Grounding

```bash
python scripts/gemini_grounding_test.py
```

Expected behavior:

- Calls Gemini with grounding/search tool enabled
- Returns competitor-oriented answer with source-oriented output

### LangGraph practice graph

```bash
python scratch_langgraph_test.py
```

Expected behavior:

- Runs a tiny conditional graph
- Demonstrates basic `StateGraph` and `add_conditional_edges` flow

## Configuration

Key settings in `config.py`:

- `MODEL_NAME = "gemini-2.0-flash"`
- `EVALUATION_THRESHOLD = 75`
- `MAX_ITERATIONS = 3`
- Weighted evaluation criteria (`EVAL_WEIGHTS`) summing to 100

## Documentation

- System design/spec: `docs/PROJECT_SPEC_V2.md`
- Execution/task plan: `docs/TASK_CHECKLIST.md`
- Final written report template/work area: `docs/report.md`

## Roadmap (from Checklist)

1. Implement schemas and base agent utilities
2. Implement 4 specialized agents
3. Build LangGraph orchestrator with retry loop
4. Add Streamlit dashboard and progress callbacks
5. Add PDF export and end-to-end testing
6. Polish, report writing, and demo prep

## Security Notes

- Never commit secrets to git.
- Keep `.env` local and rotate API keys if accidentally exposed.
- `.gitignore` is configured to ignore `.env`, `__pycache__/`, and `*.pyc`.

## License

Course project repository. Add a formal license if publishing beyond class use.
