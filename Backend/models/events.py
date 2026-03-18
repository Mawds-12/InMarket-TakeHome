from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from datetime import datetime


class BaseEvent(BaseModel):
    """Base event model for all WebSocket events."""
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StageStartedEvent(BaseEvent):
    """Event emitted when a processing stage begins."""
    event_type: Literal["stage_started"] = "stage_started"
    stage: Literal["jurisdiction", "issue_extraction", "retrieval", "reduction", "brief_writing"]
    data: Dict[str, Any] = Field(default_factory=dict)


class StageCompletedEvent(BaseEvent):
    """Event emitted when a processing stage completes."""
    event_type: Literal["stage_completed"] = "stage_completed"
    stage: Literal["jurisdiction", "issue_extraction", "retrieval", "reduction", "brief_writing"]
    duration_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IssueExtractedEvent(BaseEvent):
    """Event emitted after issue extraction completes."""
    event_type: Literal["issue_extracted"] = "issue_extracted"
    issue_label: str
    topic_tags: list[str]
    case_query_preview: str
    bill_query_preview: str
    need_bills: bool
    fact_points_count: int
    token_usage: Optional[Dict[str, int]] = None


class RetrievalStartedEvent(BaseEvent):
    """Event emitted when retrieval begins."""
    event_type: Literal["retrieval_started"] = "retrieval_started"
    case_query_preview: str
    bill_query_preview: Optional[str]
    search_mode: str
    state: str


class RetrievalCompletedEvent(BaseEvent):
    """Event emitted when retrieval completes."""
    event_type: Literal["retrieval_completed"] = "retrieval_completed"
    case_count: int
    bill_count: int
    mcp_call_details: Dict[str, Any]


class ReductionCompletedEvent(BaseEvent):
    """Event emitted when relevance reduction completes."""
    event_type: Literal["reduction_completed"] = "reduction_completed"
    input_count: int
    filtered_count: int
    token_usage: Optional[Dict[str, int]] = None


class BriefCompletedEvent(BaseEvent):
    """Event emitted when brief writing completes."""
    event_type: Literal["brief_completed"] = "brief_completed"
    authority_count: int
    token_usage: Optional[Dict[str, int]] = None


class AnalysisCompleteEvent(BaseEvent):
    """Event emitted when entire analysis completes."""
    event_type: Literal["analysis_complete"] = "analysis_complete"
    total_duration_ms: int
    total_tokens: Optional[int] = None
    brief_response: Dict[str, Any]


class ErrorEvent(BaseEvent):
    """Event emitted when an error occurs."""
    event_type: Literal["error"] = "error"
    stage: Optional[str] = None
    message: str
    error_type: str
