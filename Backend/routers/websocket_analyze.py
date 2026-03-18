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


async def rank_authorities(
    issue_bundle,
    raw_cases: list,
    raw_bills: list,
    callbacks=None
) -> list:
    """
    Simple keyword-based ranking system that replaces LLM filtering.
    Always returns results, never empty.
    """
    from models.schemas import Authority
    from models.internal import RawCase, RawBill
    
    # Extract keywords from issue bundle
    issue_keywords = []
    if issue_bundle.case_query:
        issue_keywords.extend(issue_bundle.case_query.lower().split())
    if issue_bundle.bill_query:
        issue_keywords.extend(issue_bundle.bill_query.lower().split())
    if issue_bundle.topic_tags:
        issue_keywords.extend([tag.lower() for tag in issue_bundle.topic_tags])
    
    # Remove common words and duplicates
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
    issue_keywords = [kw for kw in set(issue_keywords) if kw not in stop_words and len(kw) > 2]
    
    authorities = []
    
    # Score and process cases
    scored_cases = []
    for case in raw_cases:
        score = 0
        snippet_lower = case.snippet.lower()
        title_lower = case.case_name.lower()
        
        # Count keyword matches in snippet and title
        for keyword in issue_keywords:
            snippet_matches = snippet_lower.count(keyword)
            title_matches = title_lower.count(keyword)
            score += snippet_matches * 2 + title_matches * 3  # Title matches weighted higher
        
        # Bonus for recent cases (last 10 years)
        if case.date:
            try:
                year = int(case.date[:4])
                if year >= 2014:
                    score += 1
            except:
                pass
        
        # Bonus for higher courts
        court_lower = case.court.lower()
        if any(term in court_lower for term in ['supreme', 'appellate', 'court of appeal']):
            score += 1
        
        # Bonus for published cases
        if case.status == 'Published':
            score += 0.5
        
        # Bonus for cited cases
        if case.cite_count > 10:
            score += 0.5
        
        if score > 0:  # Only include if some relevance
            scored_cases.append((case, score))
    
    # Sort by score, take top 5
    scored_cases.sort(key=lambda x: x[1], reverse=True)
    top_cases = [case for case, score in scored_cases[:5]]
    
    # Convert cases to Authority objects
    for case in top_cases:
        authorities.append(Authority(
            kind="case",
            title=case.case_name,
            citation=case.citation,
            court=case.court,
            date=case.date,
            url=case.url,
            why_pertinent=f"Relevant to {issue_bundle.issue_label} based on keyword matching",
            key_point=case.snippet[:200] + "..." if len(case.snippet) > 200 else case.snippet,
            status=case.status,
            judge=case.judge,
            posture=case.posture,
            cite_count=case.cite_count
        ))
    
    # Score and process bills
    scored_bills = []
    for bill in raw_bills:
        score = 0
        title_lower = bill.title.lower()
        
        # Count keyword matches in title
        for keyword in issue_keywords:
            title_matches = title_lower.count(keyword)
            score += title_matches * 3
        
        # Bonus for recent bills
        if bill.latest_action_date:
            try:
                year = int(bill.latest_action_date[:4])
                if year >= 2019:
                    score += 1
            except:
                pass
        
        # Bonus for bills with sponsors
        if bill.sponsors and len(bill.sponsors) > 0:
            score += 0.5
        
        if score > 0:  # Only include if some relevance
            scored_bills.append((bill, score))
    
    # Sort bills by score, take top 3
    scored_bills.sort(key=lambda x: x[1], reverse=True)
    top_bills = [bill for bill, score in scored_bills[:3]]
    
    # Convert bills to Authority objects
    for bill in top_bills:
        authorities.append(Authority(
            kind="bill",
            title=bill.title,
            citation=None,
            court=None,
            date=bill.latest_action_date,
            url=bill.url,
            why_pertinent=f"Relevant to {issue_bundle.issue_label} based on keyword matching",
            key_point=f"Legislative action: {bill.latest_action}",
            sponsors=bill.sponsors
        ))
    
    # If no authorities found (rare edge case), return top cases anyway
    if not authorities and raw_cases:
        # Return top 3 cases regardless of score
        for case in raw_cases[:3]:
            authorities.append(Authority(
                kind="case",
                title=case.case_name,
                citation=case.citation,
                court=case.court,
                date=case.date,
                url=case.url,
                why_pertinent="Available case law for reference",
                key_point=case.snippet[:200] + "..." if len(case.snippet) > 200 else case.snippet,
                status=case.status,
                judge=case.judge,
                posture=case.posture,
                cite_count=case.cite_count
            ))
    
    print(f"[RANKING] Processed {len(raw_cases)} cases + {len(raw_bills)} bills -> {len(authorities)} authorities")
    return authorities


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
        
        print(f"[STAGE] Issue extraction complete: duration={duration_ms}ms, tokens={token_usage}")
        
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
        
        print(f"[STAGE] Retrieval complete: cases={len(raw_cases)}, bills={len(raw_bills)}, case_duration={case_metadata['duration_ms']}ms, bill_duration={bill_metadata['duration_ms']}ms")
        
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
        
        # Stage C: Authority Ranking (replaces LLM filtering)
        stage_start = time.time()
        await emit_event(websocket, StageStartedEvent(stage="ranking"))
        
        pertinent_authorities = await rank_authorities(
            issue_bundle,
            raw_cases,
            raw_bills
        )
        
        duration_ms = int((time.time() - stage_start) * 1000)
        
        print(f"[STAGE] Authority ranking complete: duration={duration_ms}ms, input={len(raw_cases) + len(raw_bills)}, selected={len(pertinent_authorities)}")
        print(f"[DEBUG] Raw cases: {len(raw_cases)}, Raw bills: {len(raw_bills)}")
        if pertinent_authorities:
            print(f"[DEBUG] First authority: {pertinent_authorities[0].title}")
        else:
            print(f"[DEBUG] No authorities returned - this is the problem!")
            print(f"[DEBUG] Issue bundle: {issue_bundle.issue_label}")
            if raw_cases:
                print(f"[DEBUG] First case snippet: {raw_cases[0].snippet[:100]}...")
        
        await emit_event(websocket, ReductionCompletedEvent(
            input_count=len(raw_cases) + len(raw_bills),
            filtered_count=len(pertinent_authorities),
            token_usage={"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "requests": 0}
        ))
        
        await emit_event(websocket, StageCompletedEvent(
            stage="ranking",
            duration_ms=duration_ms,
            metadata={"filtered_count": len(pertinent_authorities)}
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
        
        print(f"[STAGE] Brief writing complete: duration={duration_ms}ms, authorities={len(pertinent_authorities)}, tokens={token_usage}")
        
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
        
        print(f"[COMPLETE] Analysis finished: total_duration={total_duration_ms}ms, total_tokens={total_tokens}")
        print(f"[COMPLETE] Token breakdown: issue_extraction + reduction + brief_writing = {total_tokens}")
        
        await emit_event(websocket, AnalysisCompleteEvent(
            total_duration_ms=total_duration_ms,
            total_tokens=total_tokens,
            brief_response=brief_response.model_dump()
        ))
        
        await websocket.close()
        print("Analysis completed successfully")
        
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
