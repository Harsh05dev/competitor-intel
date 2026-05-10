# Competitor Intelligence Dashboard (Agentic AI)

A multi-agent system that performs automated competitor research and produces a quality-controlled intelligence report. Built for **CS 301 — Agentic AI**.

🔗 **Live demo:** [competitor-intel-kard998mv6uejrcu5dz88w.streamlit.app](https://competitor-intel-kard998mv6uejrcu5dz88w.streamlit.app/) — runs in DEMO mode out of the box (no API key needed). Toggle to LIVE mode in the sidebar and paste a Gemini key to run real analyses.

Given a target company and its industry, the system uses a **LangGraph** state machine of four specialized agents to find competitors, structure their data, generate strategic analysis (SWOT, comparison matrix, threat ranking), and **score its own output**. If the score falls below the threshold, the graph loops back through the Researcher with targeted gap-filling queries — a real iterative feedback loop, not a fixed pipeline.

## Team

- Harsh
- Rayansh
- Shippy

## Why This Is Agentic

The system is genuinely agentic because the **graph branches on the quality of its own output**:

- The Evaluator scores each report 0–100 on six weighted criteria.
- A LangGraph **conditional edge** routes execution: `score >= 70` → finalize, otherwise → retry.
- On retry, the Evaluator's *suggested queries* directly shape the Researcher's next run, so the second pass fills only the gaps identified in the first.

The agentic logic is encoded in the graph itself, not buried inside an `if/else` in a loop.

## Architecture

```
                ┌────────────┐
   start ─────▶ │ Researcher │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ Categorizer│
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │  Analyst   │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ Evaluator  │  (quality gate, conditional edge)
                └─────┬──────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
   score < 70                  score >= 70
   AND iter < 3                OR   iter >= 3
        │                            │
        ▼                            ▼
   Researcher (retry,         format_report ──▶ END
   targeted queries)
```

## Agents

| Agent | File | Role |
|-------|------|------|
| **Researcher** | `agents/researcher.py` | Uses Gemini with Google Search Grounding to find 4 competitors and gather pricing, features, funding, hiring signals, news, and sentiment. On retries, runs *targeted* searches against the Evaluator's gap-filling queries instead of redoing broad research. |
| **Categorizer** | `agents/categorizer.py` | Converts raw research snippets into clean, structured JSON per competitor. On retries, **merges** new data into existing data with a fill-gaps strategy — never overwriting good data already collected. |
| **Analyst** | `agents/analyst.py` | Synthesizes structured competitor data into a **SWOT analysis** (≥2 evidence-backed points per quadrant), a **comparison matrix** (pricing tier, threat level, target market per competitor), a **threat ranking**, and a list of **opportunity gaps**. |
| **Evaluator** | `agents/evaluator.py` | Independent quality gate. Scores the report 0–100 across 6 weighted criteria (competitor count, pricing coverage, feature coverage, funding data, hiring signals, SWOT depth). Identifies specific gaps and emits targeted follow-up queries. Independent from the Analyst by design — the same agent must not both write and grade the analysis. |

## Tech Stack

- **Python 3.11+**
- **LangGraph** — `StateGraph` orchestration with conditional edges
- **google-genai** — Gemini SDK (`gemini-2.5-flash-lite` by default), with Google Search Grounding
- **Streamlit** — interactive dashboard UI
- **fpdf2** — PDF export of the final report
- **python-dotenv** — local environment management

See [`requirements.txt`](./requirements.txt) for the exact dependency list.

## Repository Layout

```
competitor-intel/
├── agents/                 # 4 specialized agents
│   ├── researcher.py
│   ├── categorizer.py
│   ├── analyst.py
│   └── evaluator.py
├── models/
│   └── schemas.py          # TypedDict schemas for state + agent I/O
├── ui/
│   └── app.py              # Streamlit dashboard
├── scripts/                # Smoke tests for Gemini + individual agents
│   ├── gemini_basic_test.py
│   ├── gemini_grounding_test.py
│   ├── list_models.py
│   ├── test_researcher.py
│   └── test_evaluator.py
├── docs/
│   ├── PROJECT_SPEC_V2.md  # design spec
│   ├── TASK_CHECKLIST.md   # execution plan
│   └── report.md           # final written report
├── orchestrator.py         # LangGraph StateGraph (the agentic core)
├── main.py                 # CLI entry point + Orchestrator wrapper
├── config.py               # Model + threshold + weight configuration
└── requirements.txt
```

## Setup

### 1) Clone the repo

```bash
git clone https://github.com/Harsh05dev/competitor-intel.git
cd competitor-intel
```

### 2) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

Create a `.env` file in the repo root:

```env
GEMINI_API_KEY=your_primary_api_key_here
GEMINI_API_KEY_2=optional_backup_key
GEMINI_MODEL=gemini-2.5-flash-lite
```

`GEMINI_API_KEY_2` is optional — used as a fallback if the primary key hits quota.

## Running the System

### Hosted (no setup)

The dashboard is deployed on Streamlit Community Cloud:

**[competitor-intel-kard998mv6uejrcu5dz88w.streamlit.app](https://competitor-intel-kard998mv6uejrcu5dz88w.streamlit.app/)**

Opens in DEMO mode by default — pre-computed Stripe vs fintech results, no API key required. Toggle to LIVE mode in the sidebar and paste a Gemini key to analyze a custom company end-to-end.

### Streamlit dashboard (local)

```bash
streamlit run ui/app.py
```

Then enter a target company and industry in the form. The dashboard will stream agent progress, display the full SWOT, comparison matrix, threat ranking, opportunity gaps, evaluation breakdown, and final markdown report — and offer a PDF download.

### Command line

```bash
python main.py "Stripe" "fintech"
```

The CLI prints the final score, iteration count, the formatted markdown report, and the full agent log trace.

### Individual agent smoke tests

```bash
python scripts/gemini_basic_test.py        # validate Gemini API key
python scripts/gemini_grounding_test.py    # validate Google Search Grounding
python scripts/test_researcher.py          # run Researcher in isolation
python scripts/test_evaluator.py           # run Evaluator in isolation
python scripts/list_models.py              # list available Gemini models
```

## Configuration

Tunable settings live in `config.py`:

| Setting | Default | Purpose |
|---------|---------|---------|
| `MODEL_NAME` | `gemini-2.5-flash-lite` | Gemini model for all agents |
| `EVALUATION_THRESHOLD` | `70` | Minimum score required to finalize |
| `MAX_ITERATIONS` | `3` | Hard cap on retry loops (safety valve) |
| `MAX_COMPETITORS` | `4` | Max competitors gathered per run |
| `MAX_GAPS_PER_RETRY` | `6` | Cap on follow-up queries fed back to the Researcher |
| `EVAL_WEIGHTS` | dict summing to 100 | Weights for the 6 evaluation criteria |

The default `EVAL_WEIGHTS`:

```python
{
    "competitor_count":  15,
    "pricing_coverage":  20,
    "feature_coverage":  20,
    "funding_data":      15,
    "hiring_signals":    10,
    "swot_depth":        20,
}
```

## How the Loop Works (Stripe example)

1. **Round 1 — broad research.** Researcher finds 4 competitors (PayPal, Square, Adyen, Braintree) with raw snippets. Categorizer structures them. Analyst produces SWOT + matrix. Evaluator scores `61/100` and emits gap queries like `"Adyen pricing tiers 2024"` and `"Square hiring signals"`.
2. **Conditional edge.** Score `61 < 70`, iteration `1 < 3` → route `retry` → back to Researcher.
3. **Round 2 — targeted research.** Researcher only searches for the gap queries. Categorizer **merges** the new fields into existing competitor records. Analyst regenerates SWOT with richer data. Evaluator scores `78/100`.
4. **Finalize.** Score `78 >= 70` → route `finalize` → `format_report` → END. The final markdown report is rendered in the Streamlit dashboard with a HIGH confidence badge.

## Documentation

- System design / spec: [`docs/PROJECT_SPEC_V2.md`](./docs/PROJECT_SPEC_V2.md)
- Execution / task plan: [`docs/TASK_CHECKLIST.md`](./docs/TASK_CHECKLIST.md)
- Final written report: [`docs/report.md`](./docs/report.md)

## Security Notes

- Never commit secrets to git.
- Keep `.env` local and rotate API keys if accidentally exposed.
- `.gitignore` is configured to ignore `.env`, `__pycache__/`, and `*.pyc`.

## License

Course project repository. Add a formal license if publishing beyond class use.
