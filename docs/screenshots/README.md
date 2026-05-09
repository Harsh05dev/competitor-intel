# Screenshots

Drop the dashboard screenshots here. The report (`docs/report.md`) embeds:

- `stripe-dashboard.png` — full results page after a Stripe / fintech run
  (metrics row + SWOT tab visible)

To capture:

1. `streamlit run ui/app.py`
2. Mode = DEMO, Target = `⚡ Stripe / fintech ← demo`
3. Click **▶ RUN**, wait for the metrics row
4. Take a full-page screenshot, save as `stripe-dashboard.png` in this folder

Optional second screenshot for the report:

- `agent-logs.png` — the **Raw State** tab showing the per-iteration agent logs
  (proves the retry loop ran)
