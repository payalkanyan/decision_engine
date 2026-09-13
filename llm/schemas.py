from pydantic import BaseModel


class GoalClassification(BaseModel):
    """Output of classify.py: free-text goal → structured taxonomy."""

    goal: str
    taxonomy_tags: list[str] = []  # e.g. ["speech-to-text", "tts", "voice-agents"]
    search_keywords: list[str] = []  # for Crustdata company_search queries
    build_signals: list[str] = []  # what to look for in own company data
    partner_signals: list[str] = []
    acquire_signals: list[str] = []


class StrategyNarrative(BaseModel):
    """Output of synthesize.py: scored evidence → written strategy."""

    recommendation_summary: str
    path_analysis: dict[str, str]  # {"build": "...", "partner": "...", "acquire": "..."}
    trade_offs: str
    key_risks: list[str] = []
