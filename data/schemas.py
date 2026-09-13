from datetime import date, datetime

from pydantic import BaseModel

# ── Company Enrichment ──────────────────────────────────────────


class Technographics(BaseModel):
    technologies: list[str] = []  # e.g. ["React", "AWS", "Salesforce"]
    categories: list[str] = []  # e.g. ["CRM", "Cloud Infrastructure"]


class FundingSummary(BaseModel):
    total_raised: float | None = None
    latest_round_type: str | None = None  # e.g. "Series B"
    latest_round_amount: float | None = None
    latest_round_date: date | None = None


class CompanyEnrichment(BaseModel):
    company_name: str
    domain: str | None = None
    industry: str | None = None
    description: str | None = None
    employee_count: int | None = None
    founded_date: date | None = None
    location: str | None = None
    technographics: Technographics = Technographics()
    funding: FundingSummary = FundingSummary()


class CompanyEnrichmentResponse(BaseModel):
    """Wrapper for the Company Enrichment API response."""

    company: CompanyEnrichment


# ── Company Search ──────────────────────────────────────────────


class CompanySearchResult(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    total_funding: float | None = None
    description: str | None = None


class CompanySearchResponse(BaseModel):
    results: list[CompanySearchResult] = []
    total_count: int = 0


# ── Jobs API ────────────────────────────────────────────────────


class JobPosting(BaseModel):
    title: str
    department: str | None = None
    location: str | None = None
    posted_date: date | None = None
    company_name: str


class JobsResponse(BaseModel):
    jobs: list[JobPosting] = []
    total_count: int = 0


# ── Headcount Timeseries ────────────────────────────────────────


class HeadcountDataPoint(BaseModel):
    date: date
    headcount: int


class HeadcountTimeseriesResponse(BaseModel):
    company_name: str
    facet: str | None = None  # "department", "location", or None for total
    series: list[HeadcountDataPoint] = []


# ── Funding Milestone Timeseries ────────────────────────────────


class FundingMilestone(BaseModel):
    date: date
    round_type: str
    amount: float | None = None
    investors: list[str] = []
    valuation: float | None = None
    pre_money_valuation: float | None = None


class FundingMilestoneTimeseriesResponse(BaseModel):
    company_name: str
    milestones: list[FundingMilestone] = []


# ── Decision Makers ─────────────────────────────────────────────


class DecisionMaker(BaseModel):
    name: str
    title: str
    linkedin_url: str | None = None
    seniority: str | None = None  # "C-level", "VP", "Director"
    company_name: str


class DecisionMakersResponse(BaseModel):
    company_name: str
    decision_makers: list[DecisionMaker] = []


# ── Person Screener ─────────────────────────────────────────────


class PersonScreenerResult(BaseModel):
    name: str
    title: str
    company_name: str
    linkedin_url: str | None = None
    seniority: str | None = None
    location: str | None = None


class PersonScreenerResponse(BaseModel):
    results: list[PersonScreenerResult] = []
    total_count: int = 0


# ── Investor Portfolio ──────────────────────────────────────────


class InvestorPortfolioResponse(BaseModel):
    investor_name: str
    portfolio_companies: list[CompanySearchResult] = []


# ── LinkedIn Posts ──────────────────────────────────────────────


class LinkedInPost(BaseModel):
    author_name: str
    author_title: str | None = None
    content: str
    posted_date: datetime
    engagement: int | None = None  # likes + comments


class LinkedInPostsResponse(BaseModel):
    company_name: str
    posts: list[LinkedInPost] = []


# ── Web Traffic ─────────────────────────────────────────────────


class WebTrafficDataPoint(BaseModel):
    date: date
    monthly_visits: int


class WebTrafficResponse(BaseModel):
    domain: str
    series: list[WebTrafficDataPoint] = []
