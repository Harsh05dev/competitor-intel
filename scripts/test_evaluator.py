import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from agents.evaluator import EvaluatorAgent

agent = EvaluatorAgent()

dummy_state = {
    "categorized_competitors": [
        {
            "company_name": "Stripe",
            "pricing": "2.9% + 30¢",
            "key_features": ["payments", "api", "subscriptions"],
            "target_audience": "developers",
            "funding": "IPO",
            "hiring_signals": ["100+ jobs"],
            "recent_news": ["expansion"],
            "customer_sentiment": "positive"
        }
    ],
    "analysis": {
        "swot": {
            "strengths": ["strong API", "global", "scalable"],
            "weaknesses": ["fees"],
            "opportunities": ["AI"],
            "threats": ["competition"]
        }
    }
}

result = agent.evaluate(dummy_state)

print(result)