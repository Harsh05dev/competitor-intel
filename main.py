"""
main.py — Entry point and backward-compatible Orchestrator wrapper

Shippy's ui/app.py imports Orchestrator from this file and calls:
    orch = Orchestrator()
    result = orch.run(company=company, industry=industry)

This wrapper keeps that interface intact while delegating the actual
agentic logic to the LangGraph orchestrator in orchestrator.py.

You can also run this directly from the terminal:
    python main.py
    python main.py "Notion" "productivity"
"""

import sys
from typing import Optional

from orchestrator import run_analysis


class Orchestrator:
    """
    Thin wrapper around the LangGraph run_analysis() function.
    Exists solely to maintain backward compatibility with ui/app.py
    which does: from main import Orchestrator
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def run(self, company: str = "Stripe", industry: str = "fintech") -> dict:
        """
        Run the full LangGraph agentic pipeline and return the final state.

        The returned state dict contains:
          - evaluation: {score, passed, gaps, suggested_queries, breakdown}
          - research_results: list of raw competitor data
          - categorized_competitors: list of structured competitor data
          - analysis: {swot, comparison_matrix, threat_ranking, opportunity_gaps}
          - final_output: formatted markdown report string
          - iteration: number of iterations used
          - logs: full execution trace
          - status: "complete"
        """
        return run_analysis(company=company, industry=industry, api_key=self.api_key)


if __name__ == "__main__":
    company  = sys.argv[1] if len(sys.argv) > 1 else "Stripe"
    industry = sys.argv[2] if len(sys.argv) > 2 else "fintech"

    orch   = Orchestrator()
    result = orch.run(company=company, industry=industry)

    ev = result.get("evaluation", {})
    print(f"\nFinal Score:   {ev.get('score', 0)}/100")
    print(f"Passed:        {ev.get('passed', False)}")
    print(f"Iterations:    {result.get('iteration', 0)}")
    print(f"\nFinal Report:\n{result.get('final_output', 'No report generated')}")

    print("\n── Agent Logs ──")
    for log in result.get("logs", []):
        print(f"  {log}")
