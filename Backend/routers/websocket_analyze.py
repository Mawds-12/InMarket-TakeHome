from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import time
import logging

logger = logging.getLogger(__name__)
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


@router.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """Simple test WebSocket endpoint."""
    logger.info("Test WebSocket connection attempt received")
    await websocket.accept()
    logger.info("Test WebSocket connection accepted")
    await websocket.send_text("Connected!")
    await websocket.close()
    logger.info("Test WebSocket connection closed")


async def emit_event(websocket: WebSocket, event):
    """Send event to WebSocket client."""
    event_json = event.model_dump_json()
    logger.debug(f"Emitting event: {event.event_type}")
    await websocket.send_text(event_json)


async def _truncate_query(query: str, max_length: int = 80) -> str:
    """Truncate query string for display."""
    if len(query) <= max_length:
        return query
    return query[:max_length] + "..."


@router.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis with progress updates.
    
    Expects JSON message with analysis parameters:
        question: Legal question (required)
        clause_text: Optional clause text
        state_override: Optional state override
        search_mode: Search mode (semantic/keyword)
        detected_state: Pre-detected state code
    """
    logger.info(f"WebSocket connection attempt received from {websocket.client}")
    logger.info(f"WebSocket headers: {dict(websocket.headers)}")
    
    # Get origin from headers
    origin = websocket.headers.get("origin", "http://localhost:3000")
    logger.info(f"WebSocket origin: {origin}")
    
    try:
        # Accept with explicit origin (allows CORS)
        await websocket.accept()
        logger.info("WebSocket connection accepted successfully")
    except Exception as e:
        logger.error(f"Failed to accept WebSocket connection: {type(e).__name__}: {str(e)}")
        raise
    
    overall_start = time.time()
    total_tokens = 0
    
    try:
        # Receive analysis parameters from client
        logger.info("Waiting for analysis parameters from client...")
        data = await websocket.receive_text()
        logger.info(f"Received raw data: {data}")
        request_data = json.loads(data)
        logger.info(f"Parsed request data: {request_data}")
        
        question = request_data.get("question", "")
        clause_text = request_data.get("clause_text", "")
        state_override = request_data.get("state_override")
        search_mode = request_data.get("search_mode", "semantic")
        detected_state = request_data.get("detected_state", "CA")
        
        if not question:
            logger.warning("Validation failed: Question is required")
            await emit_event(websocket, ErrorEvent(
                message="Question is required",
                error_type="ValidationError"
            ))
            await websocket.close()
            return
        
        logger.info(f"Starting analysis - Question: {question[:100]}..., State: {state_override or detected_state}")
        
        # Stage 0: Jurisdiction
        stage_start = time.time()
        logger.info("Starting stage: jurisdiction")
        await emit_event(websocket, StageStartedEvent(stage="jurisdiction"))
        
        if state_override:
            state = state_override
            state_was_inferred = False
        else:
            state = detected_state
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
        logger.info("Analysis completed successfully")
        
    except LLMError as e:
        logger.error(f"LLM error during analysis: {str(e)}")
        await emit_event(websocket, ErrorEvent(
            stage="llm",
            message=str(e),
            error_type="LLMError"
        ))
        await websocket.close()
        
    except MCPError as e:
        logger.error(f"MCP error during analysis: {str(e)}")
        await emit_event(websocket, ErrorEvent(
            stage="mcp",
            message=str(e),
            error_type="MCPError"
        ))
        await websocket.close()
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
        
    except Exception as e:
        logger.error(f"Unexpected error during WebSocket analysis: {str(e)}", exc_info=True)
        await emit_event(websocket, ErrorEvent(
            message=f"Unexpected error: {str(e)}",
            error_type="UnexpectedError"
        ))
        await websocket.close()
    finally:
        logger.info("WebSocket connection closed")
