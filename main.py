from agents.researcher import ResearcherAgent
from agents.evaluator import EvaluatorAgent


class Orchestrator:
    def __init__(self):
        self.researcher = ResearcherAgent()
        self.evaluator = EvaluatorAgent()
        self.max_iterations = 3

    def initialize_state(self, company="Stripe", industry="fintech"):
        return {
            "target_company": company,
            "industry": industry,
            "iteration": 0,
            "research_results": [],
            "categorized_competitors": [],
            "evaluation": {}
        }

    def should_continue(self, state):
        # stop if passed OR max iterations reached
        if state["evaluation"].get("passed"):
            return False

        if state["iteration"] >= self.max_iterations:
            return False

        return True

    def run(self, company="Stripe", industry="fintech"):
        state = self.initialize_state(company, industry)

        print("\n=== STARTING ORCHESTRATION ===")

        while True:
            print(f"\n--- ITERATION {state['iteration'] + 1} ---")

            # ------------------------
            # STEP 1: RESEARCH
            # ------------------------
            research_output = self.researcher.research(state)
            state.update(research_output)

            print("\n[Research Output]")
            print(state["research_results"])

            # simple pass-through (you can later add categorizer agent here)
            state["categorized_competitors"] = state["research_results"]

            # ------------------------
            # STEP 2: EVALUATE
            # ------------------------
            eval_output = self.evaluator.evaluate(state)
            state.update(eval_output)

            print("\n[Evaluation]")
            print(state["evaluation"])

            # ------------------------
            # STEP 3: DECISION NODE
            # ------------------------
            if not self.should_continue(state):
                break

            print("\n🔁 Looping with improvements...")

        print("\n=== FINAL RESULT ===")
        print(state["evaluation"])

        return state


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()