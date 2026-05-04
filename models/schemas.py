
from typing import List, TypedDict, Optional


# -------------------------
# Researcher Output
# -------------------------
class ResearchResult(TypedDict):
    company_name: str
    raw_snippets: List[str]
    sources: List[str]


# -------------------------
# Categorizer Output
# -------------------------
class CategorizedCompetitor(TypedDict):
    company_name: str
    pricing: Optional[str]
    key_features: List[str]
    target_audience: Optional[str]
    funding: Optional[str]
    hiring_signals: List[str]
    recent_news: List[str]
    customer_sentiment: Optional[str]


# -------------------------
# Analyst Output
# -------------------------
class SWOT(TypedDict):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]


class ComparisonEntry(TypedDict):
    company_name: str
    pricing_tier: str
    primary_strength: str
    primary_weakness: str
    target_market: str
    threat_level: str


class AnalysisResult(TypedDict):
    swot: SWOT
    comparison_matrix: List[ComparisonEntry]
    threat_ranking: List[str]
    opportunity_gaps: List[str]


# -------------------------
# Evaluator Output (YOUR MAIN PART)
# -------------------------
class ScoreDetail(TypedDict):
    score: int
    notes: str


class EvaluationBreakdown(TypedDict):
    competitor_count: ScoreDetail
    pricing_coverage: ScoreDetail
    feature_coverage: ScoreDetail
    funding_data: ScoreDetail
    hiring_signals: ScoreDetail
    swot_depth: ScoreDetail
    recency: ScoreDetail


class EvaluationResult(TypedDict):
    score: int
    passed: bool
    breakdown: EvaluationBreakdown
    gaps: List[str]
    suggested_queries: List[str]


# -------------------------
# LangGraph State
# -------------------------
class AgentState(TypedDict):
    target_company: str
    industry: str
    iteration: int

    research_results: List[ResearchResult]
    categorized_competitors: List[CategorizedCompetitor]

    analysis: AnalysisResult
    evaluation: EvaluationResult

    final_output: str
    status: str
    logs: List[str]