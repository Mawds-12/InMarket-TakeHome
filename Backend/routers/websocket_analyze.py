from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import time
from models.schemas import AnalyzeRequest
from models.events import (
    StageStartedEvent, StageCompletedEvent, IssueExtractedEvent,
    RetrievalStartedEvent, RetrievalCompletedEvent, ReductionCompletedEvent,
    BriefCompletedEvent, AnalysisCompleteEvent, ErrorEvent
)
from chains.issue_extractor import extract_issue
from chains.relevance_reducer import reduce_to_pertinent
from chains.brief_writer import write_brief
from tools.case_tool import fetch_cases
from tools.bill_tool import fetch_bills
from tools.geo_tool import infer_state_from_ip
from utils.token_counter import TokenCountingCallback
from exceptions import LLMError, MCPError

router = APIRouter()


async def emit_event(websocket: WebSocket, event):
    """Send event to WebSocket client."""
    await websocket.send_text(event.model_dump_json())


async def _truncate_query(query: str, max_length: int = 80) -> str:
    """Truncate query string for display."""
    if len(query) <= max_length:
        return query
    return query[:max_length] + "..."


@router.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis with progress updates.
    
    Query parameters:
        question: Legal question
        clause_text: Optional clause text
        state_override: Optional state override
        search_mode: Search mode (semantic/keyword)
    """
    await websocket.accept()
    
    overall_start = time.time()
    total_tokens = 0
    
    try:
        # Parse request from query params
        params = dict(websocket.query_params)
        question = params.get("question", "")
        clause_text = params.get("clause_text", "")
        state_override = params.get("state_override")
        search_mode = params.get("search_mode", "semantic")
        
        if not question:
            await emit_event(websocket, ErrorEvent(
                message="Question is required",
                error_type="ValidationError"
            ))
            await websocket.close()
            return
        
        # Stage 0: Jurisdiction
        stage_start = time.time()
        await emit_event(websocket, StageStartedEvent(stage="jurisdiction"))
        
        if state_override:
            state = state_override
            state_was_inferred = False
        else:
            # For WebSocket, we don't have easy access to client IP
            # Default to CA or accept as param
            state = params.get("detected_state", "CA")
            state_was_inferred = True
        
        duration_ms = int((time.time() - stage_start) * 1000)
        await emit_event(websocket, StageCompletedEvent(
            stage="jurisdiction",
            duration_ms=duration_ms,
            metadata={"state": state, "inferred": state_was_inferred}
        ))
        
        # Stage A: Issue Extraction
        stage_start = time.time()
        await emit_event(websocket, StageStartedEvent(stage="issue_extraction"))
        
        token_callback = TokenCountingCallback()
        issue_bundle = await extract_issue(
            question,
            state,
            clause_text,
            callbacks=[token_callback]
        )
        
        duration_ms = int((time.time() - stage_start) * 1000)
        token_usage = token_callback.get_usage()
        total_tokens += token_usage.get("total_tokens", 0)
        
        await emit_event(websocket, IssueExtractedEvent(
            issue_label=issue_bundle.issue_label,
            topic_tags=issue_bundle.topic_tags,
            case_query_preview=await _truncate_query(issue_bundle.case_query),
            bill_query_preview=await _truncate_query(issue_bundle.bill_query),
            need_bills=issue_bundle.need_bills,
            fact_points_count=len(issue_bundle.fact_sensitive_points),
            token_usage=token_usage
        ))
        
        await emit_event(websocket, StageCompletedEvent(
            stage="issue_extraction",
            duration_ms=duration_ms,
            metadata={"token_usage": token_usage}
        ))
        
        # Stage B: Retrieval
        stage_start = time.time()
        await emit_event(websocket, RetrievalStartedEvent(
            case_query_preview=await _truncate_query(issue_bundle.case_query),
            bill_query_preview=await _truncate_query(issue_bundle.bill_query) if issue_bundle.need_bills else None,
            search_mode=search_mode,
            state=state
        ))
        
        # Run parallel retrieval
        tasks = [fetch_cases(issue_bundle, state, search_mode)]
        if issue_bundle.need_bills:
            tasks.append(fetch_bills(issue_bundle, state))
        
        results = await asyncio.gather(*tasks)
        
        raw_cases, case_metadata = results[0]
        raw_bills, bill_metadata = results[1] if len(results) > 1 else ([], {"duration_ms": 0, "count": 0})
        
        duration_ms = int((time.time() - stage_start) * 1000)
        
        await emit_event(websocket, RetrievalCompletedEvent(
            case_count=len(raw_cases),
            bill_count=len(raw_bills),
            mcp_call_details={
                "cases": case_metadata,
                "bills": bill_metadata
            }
        ))
        
        await emit_event(websocket, StageCompletedEvent(
            stage="retrieval",
            duration_ms=duration_ms,
            metadata={
                "case_count": len(raw_cases),
                "bill_count": len(raw_bills)
            }
        ))
        
        # Stage C: Relevance Reduction
        stage_start = time.time()
        await emit_event(websocket, StageStartedEvent(stage="reduction"))
        
        token_callback = TokenCountingCallback()
        pertinent_authorities = await reduce_to_pertinent(
            issue_bundle,
            raw_cases,
            raw_bills,
            callbacks=[token_callback]
        )
        
        duration_ms = int((time.time() - stage_start) * 1000)
        token_usage = token_callback.get_usage()
        total_tokens += token_usage.get("total_tokens", 0)
        
        await emit_event(websocket, ReductionCompletedEvent(
            input_count=len(raw_cases) + len(raw_bills),
            filtered_count=len(pertinent_authorities),
            token_usage=token_usage
        ))
        
        await emit_event(websocket, StageCompletedEvent(
            stage="reduction",
            duration_ms=duration_ms,
            metadata={"token_usage": token_usage}
        ))
        
        # Stage D: Brief Writing
        stage_start = time.time()
        await emit_event(websocket, StageStartedEvent(stage="brief_writing"))
        
        token_callback = TokenCountingCallback()
        brief_response = await write_brief(
            issue_bundle,
            pertinent_authorities,
            state,
            state_was_inferred,
            callbacks=[token_callback]
        )
        
        duration_ms = int((time.time() - stage_start) * 1000)
        token_usage = token_callback.get_usage()
        total_tokens += token_usage.get("total_tokens", 0)
        
        await emit_event(websocket, BriefCompletedEvent(
            authority_count=len(pertinent_authorities),
            token_usage=token_usage
        ))
        
        await emit_event(websocket, StageCompletedEvent(
            stage="brief_writing",
            duration_ms=duration_ms,
            metadata={"token_usage": token_usage}
        ))
        
        # Analysis Complete
        total_duration_ms = int((time.time() - overall_start) * 1000)
        await emit_event(websocket, AnalysisCompleteEvent(
            total_duration_ms=total_duration_ms,
            total_tokens=total_tokens,
            brief_response=brief_response.model_dump()
        ))
        
        await websocket.close()
        
    except LLMError as e:
        await emit_event(websocket, ErrorEvent(
            stage="llm",
            message=str(e),
            error_type="LLMError"
        ))
        await websocket.close()
        
    except MCPError as e:
        await emit_event(websocket, ErrorEvent(
            stage="mcp",
            message=str(e),
            error_type="MCPError"
        ))
        await websocket.close()
        
    except WebSocketDisconnect:
        pass
        
    except Exception as e:
        await emit_event(websocket, ErrorEvent(
            message=f"Unexpected error: {str(e)}",
            error_type="UnexpectedError"
        ))
        await websocket.close()
