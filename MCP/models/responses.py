# models/responses.py
#
# Pydantic models for MCP tool response schemas.
# These document the structure of data returned by tools.

from pydantic import BaseModel
from typing import Optional, List


class GeoResponse(BaseModel):
    """Response from get_default_state_from_ip tool."""
    country: str
    state: Optional[str]
    state_code: Optional[str]
    confidence: str = "default_only"


class Case(BaseModel):
    """Individual case result from CourtListener."""
    case_name: str
    court: str
    date: str
    citation: Optional[str]
    snippet: str
    url: str
    raw_score: float


class Bill(BaseModel):
    """Individual bill result from Open States."""
    bill_id: str
    title: str
    state: str
    session: str
    url: str
    latest_action: str
    latest_action_date: str
    status: List[str]
