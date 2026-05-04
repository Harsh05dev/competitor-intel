from agents.researcher import ResearcherAgent

agent = ResearcherAgent()

state = {
    "target_company": "Stripe",
    "industry": "fintech",
    "iteration": 0
}

result = agent.research(state)

print(result)