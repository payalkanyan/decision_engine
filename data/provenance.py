from datetime import datetime

from pydantic import BaseModel


class ProvenanceRecord(BaseModel):
    """Attached to every score. AGENTS.md §4: if a score can't produce
    this record, it's not done."""

    criterion_id: str
    raw_value: float
    source_field: str  # e.g. "company_enrichment.technographics.technologies"
    api_call_id: str  # unique ID for the cached API call that sourced this
    timestamp: datetime
