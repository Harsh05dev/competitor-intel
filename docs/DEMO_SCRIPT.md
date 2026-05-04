# Demo Script — Competitor Intelligence Dashboard
## CS 301 Agentic AI Presentation

---

## Before the Demo Starts
- Have the terminal open and `.env` file ready with Gemini API key
- Have the browser open at `http://localhost:8501`
- Start Streamlit beforehand: `streamlit run ui/app.py`
- Use **"Notion"** + **"productivity software"** as your demo company (good chance of retry loop)
- Have a backup: **"Stripe"** + **"fintech"** if Notion doesn't trigger a retry

---

## What Each Person Says (2 min each)

### Harsh — System Overview (2 min)
> "Our project automates competitor research using a multi-agent agentic AI system.
> The problem we're solving is that manual competitor analysis takes hours and is inconsistent.
> Our system takes a company name and industry, and automatically finds competitors,
> extracts market signals, and produces a structured intelligence report.
> The key thing that makes this agentic — not just a simple API call — is the feedback loop.
> The system evaluates its own output quality and loops back to improve it if the score is too low."

**Point to the architecture diagram in the sidebar.**

---

### Rayansh — Backend & Agents (2 min)
> "The backend has two main agents. The Researcher agent calls the Gemini API
> to find competitors and extract facts about them — pricing, features, funding signals.
> The Evaluator agent then scores that data on a 0 to 100 scale.
> If the score is below 70, it identifies exactly what's missing — like 'no pricing data for Adyen'
> — and generates specific search queries to fill those gaps.
> The Orchestrator manages the loop — it decides whether to retry or finalize
> based on the score and the iteration count. Maximum 3 iterations, then it finalizes
> with a low-confidence warning if needed."

**Show the `main.py` and `agents/` folder briefly in VS Code.**

---

### Shippy — Dashboard (2 min)
> "I built the frontend dashboard in Streamlit. You can see the input form here —
> you enter the target company and industry, then click Run.
> The progress bar shows each agent as it runs in real time.
> Once it's done, you get four metric cards — the quality score, pass or fail,
> how many competitors were found, and how many iterations it took.
> The Competitors tab shows each company with the raw research snippets.
> The Gaps tab shows exactly what data was missing and what queries the system
> used to try to fix it. This is where you can really see the agentic behavior —
> the system identified its own weaknesses and acted on them."

**Actually run the demo live while talking.**

---

## Live Demo Steps (Shippy runs this)

1. Make sure Streamlit is running: `streamlit run ui/app.py`
2. In the browser, type **Notion** in Target Company, **productivity software** in Industry
3. Click **▶ RUN**
4. Narrate the progress bar:
   > "You can see the Researcher agent running now... now the Evaluator is scoring..."
5. When results appear, point to the score card:
   - If score < 70: *"Score came back at [X] — below our threshold of 70, so watch — it's going to loop"*
   - If score ≥ 70: *"Passed on the first try — score is [X] out of 100"*
6. Click the **Competitors** tab — point to one competitor and read a snippet
7. Click **Gaps & Queries** tab:
   > "These are the gaps the Evaluator identified, and these are the specific queries
   > it generated to address them — this is the feedback loop in action"

---

## Likely "Why" Questions — Your Answers

| Question | Answer |
|----------|--------|
| Why 4 agents? | Each agent has one job — separation of concerns makes the system easier to debug and extend |
| Why threshold 70? | Empirically tuned — below 70 usually means missing key fields like pricing or funding |
| Why Gemini? | Free tier available, good JSON output, supports Google Search grounding |
| Why max 3 iterations? | Diminishing returns — testing showed most runs converge by iteration 2 |
| Why Streamlit? | Fast to build, easy to demo, no frontend framework needed |
| What's agentic about it? | The system evaluates its own output and decides what to do next — it's not a fixed pipeline |

---

## If Something Goes Wrong

| Problem | Fix |
|---------|-----|
| API error / no key | Type key into the sidebar API Key field |
| Gemini quota error | Switch to "Stripe" + "fintech" — simpler query |
| UI not loading | Run `streamlit run ui/app.py` in terminal |
| Empty results | The model fallback may have failed — check terminal for error |

---

## Key Phrases to Use
- *"multi-agent agentic workflow"*
- *"iterative self-evaluation loop"*
- *"the system decides what to do next based on its own output"*
- *"quality-controlled research pipeline"*
