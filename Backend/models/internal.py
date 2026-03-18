# models/internal.py
#
# Pydantic models shared between chain stages.
# These shapes never leave the Backend - they are not API response shapes.

from pydantic import BaseModel, Field
from typing import Optional


class IssueBundle(BaseModel):
    """
    Output of Stage A (Issue Extraction).
    Drives all downstream retrieval and ranking.
    """
    issue_label: str = Field(
        ...,
        description="Short label for the legal issue"
    )
    topic_tags: list[str] = Field(
        ...,
        description="List of topic tags for categorization"
    )
    case_query: str = Field(
        ...,
        description="Search query optimized for case law databases"
    )
    bill_query: str = Field(
        ...,
        description="Search query optimized for legislative databases"
    )
    fact_sensitive_points: list[str] = Field(
        ...,
        description="Specific factual questions that could change the outcome"
    )
    need_bills: bool = Field(
        ...,
        description="Whether legislation is relevant to this issue"
    )


class RawCase(BaseModel):
    """
    Raw case result from MCP service.
    Input to Stage C (Relevance Reduction).
    """
    case_name: str
    court: str
    date: str
    citation: Optional[str] = None
    snippet: str
    url: str
    raw_score: float


class RawBill(BaseModel):
    """
    Raw bill result from MCP service.
    Input to Stage C (Relevance Reduction).
    """
    bill_id: str
    title: str
    state: str
    session: str
    url: str
    latest_action: str
    latest_action_date: str
    status: list[str]
